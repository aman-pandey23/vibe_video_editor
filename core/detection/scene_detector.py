import cv2
import yaml
import numpy as np
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from utils.video_ops.video_utils import compute_histogram, overlay_event_text
from utils.file_ops.project_paths import ProjectFS


class SceneDetector:
    def __init__(self, config, project_name: str):
        self.global_cfg = config
        self.cfg = config['scene_detection']
        self._validate_config()

        base_dir = Path(config.get('base_dir', 'projects')).resolve()
        self.paths = ProjectFS(base_dir=base_dir, project=project_name)
        self.paths.ensure_dirs()

        self.event_timestamps = []
        self.output_path = None
        self.timestamps_path = None
        self.postprocess_remux = bool(self.cfg.get("postprocess_remux", True))  # 🔹 config toggle

    # ---------- public ----------
    def process_video(self):
        input_path = self.paths.input_video()
        threshold = float(self.cfg['threshold'])

        if not input_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_path}")

        self.output_path = str(self.paths.processed_video())
        print(f"Processing video: {input_path}")
        print(f"Output will be saved to: {self.output_path}")

        cap, ok = self._try_open_cv2_capture(input_path)
        if ok:
            self._process_with_cv2_capture(cap, threshold)
        else:
            print("OpenCV failed to open the video. Falling back to MoviePy reader...")
            self._process_with_moviepy_reader(input_path, threshold)

        self._save_timestamps(input_path)

        if self.postprocess_remux:
            self._remux_with_ffmpeg()

        return self.event_timestamps

    # ---------- cv2 path ----------
    def _try_open_cv2_capture(self, input_path: Path) -> Tuple[Optional[cv2.VideoCapture], bool]:
        cap = cv2.VideoCapture(str(input_path))
        if cap.isOpened():
            return cap, True
        try:
            cap2 = cv2.VideoCapture(str(input_path), cv2.CAP_FFMPEG)
            if cap2.isOpened():
                return cap2, True
        except Exception:
            pass
        return None, False

    def _process_with_cv2_capture(self, cap: cv2.VideoCapture, threshold: float):
        try:
            input_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            if np.isnan(input_fps) or input_fps <= 0:
                input_fps = 30.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.output_path, fourcc, input_fps, (width, height))
            if not out.isOpened():
                raise RuntimeError(f"Failed to initialize video writer at {self.output_path}")

            ret, frame = cap.read()
            if not ret or frame is None:
                raise RuntimeError("Could not read first frame from video.")
            frame = cv2.resize(frame, (width, height))
            prev_hist = compute_histogram(frame)
            out.write(frame)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame is None:
                    continue
                frame = cv2.resize(frame, (width, height))

                current_hist = compute_histogram(frame)
                hist_correlation = cv2.compareHist(prev_hist, current_hist, cv2.HISTCMP_CORREL)
                timestamp = (cap.get(cv2.CAP_PROP_POS_MSEC) or 0.0) / 1000.0

                if hist_correlation < threshold:
                    self.event_timestamps.append(timestamp)
                    frame = overlay_event_text(frame, "EVENT")

                out.write(frame)
                prev_hist = current_hist

            out.release()
        finally:
            cap.release()

    # ---------- MoviePy fallback ----------
    def _process_with_moviepy_reader(self, input_path: Path, threshold: float):
        from moviepy.editor import VideoFileClip

        with VideoFileClip(str(input_path)) as clip:
            input_fps = clip.fps or 30.0
            w, h = clip.size or (1280, 720)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.output_path, fourcc, input_fps, (w, h))
            if not out.isOpened():
                raise RuntimeError(f"Failed to initialize video writer at {self.output_path}")

            prev_hist = None
            frame_idx = 0
            for frame_rgb in clip.iter_frames(dtype="uint8", fps=input_fps):
                frame_bgr = cv2.resize(frame_rgb[:, :, ::-1], (w, h))

                if prev_hist is None:
                    prev_hist = compute_histogram(frame_bgr)
                    out.write(frame_bgr)
                    frame_idx += 1
                    continue

                current_hist = compute_histogram(frame_bgr)
                hist_correlation = cv2.compareHist(prev_hist, current_hist, cv2.HISTCMP_CORREL)
                timestamp = frame_idx / float(input_fps)

                if hist_correlation < threshold:
                    self.event_timestamps.append(timestamp)
                    frame_bgr = overlay_event_text(frame_bgr, "EVENT")

                out.write(frame_bgr)
                prev_hist = current_hist
                frame_idx += 1

            out.release()

    # ---------- utils ----------
    def _validate_config(self):
        if 'threshold' not in self.cfg:
            raise ValueError("Missing required config key: 'threshold'")

    def _save_timestamps(self, input_path: Path):
        self.timestamps_path = self.paths.timestamps_yaml()
        with open(self.timestamps_path, 'w') as f:
            yaml.dump({
                'project': self.paths.project,
                'source_video': str(input_path),
                'detection_time': datetime.now().isoformat(),
                'timestamps': self.event_timestamps
            }, f)

    def _remux_with_ffmpeg(self):
        """Re-encode to a universally playable MP4, overwriting the original."""
        try:
            tmp_path = Path(self.output_path).with_suffix(".tmp.mp4")
            subprocess.run([
                "ffmpeg", "-y", "-i", self.output_path,
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "aac", "-movflags", "+faststart",
                str(tmp_path)
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Replace original with fixed version
            Path(self.output_path).unlink(missing_ok=True)
            tmp_path.rename(self.output_path)
            print(f"Re-muxed and replaced original: {self.output_path}")

        except FileNotFoundError:
            print("⚠ ffmpeg not found — skipping re-mux. The file may still play fine in most players.")
        except subprocess.CalledProcessError as e:
            print(f"⚠ ffmpeg failed: {e.stderr.decode(errors='ignore')}")

    @property
    def get_event_timestamps(self):
        return self.event_timestamps

    @property
    def get_output_path(self):
        return self.output_path

    @property
    def get_timestamps_path(self):
        return str(self.timestamps_path) if self.timestamps_path else None
