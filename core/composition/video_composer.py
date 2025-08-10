import random
import json
from pathlib import Path
import yaml
from typing import List, Tuple, Optional
from moviepy.editor import VideoFileClip, concatenate_videoclips

from utils.audio_ops.audio_utils import extract_audio_from_video, overlay_audio_on_video
from utils.file_ops.project_paths import ProjectFS


class VideoComposer:
    def __init__(self, config: dict, project_name: str, seed: Optional[int] = None):
        self.global_cfg = config
        self.cfg = config.get("composer", {})

        base_dir = Path(config.get('base_dir', 'projects')).resolve()
        self.paths = ProjectFS(base_dir=base_dir, project=project_name)
        self.paths.ensure_dirs()

        self.allowed_exts = tuple(self.cfg.get("allowed_exts", [".mp4", ".mov", ".m4v"]))
        self.target_resolution = tuple(self.cfg.get("target_resolution", [])) or None
        self.max_selection_attempts = int(self.cfg.get("max_selection_attempts", 50))
        self.allow_reuse_segments = bool(self.cfg.get("allow_reuse_segments", False))

        out_cfg = self.cfg.get("output_settings", {}).copy()
        # We always render into the project's rendered_dir; keep only write_videofile kwargs here
        self.output_settings = out_cfg

        self.music_source = self.cfg.get("music_source", None)

        # NEW: deterministic randomness
        self.seed = seed
        if self.seed is not None:
            random.seed(self.seed)

        self.sources: dict[str, VideoFileClip] = {}
        self.used: dict[str, List[Tuple[float, float]]] = {}

    def create_edit(self, variant_tag: Optional[str] = None) -> str:
        """
        Build a composed edit. If variant_tag is provided (e.g., 'v001' or 'seed42'),
        outputs are saved with that tag in filenames.
        """
        timestamps = self._load_timestamps()
        durations = self._calculate_clip_durations(timestamps)
        self._open_sources()

        try:
            clips = self._select_clips(durations)
            if self.target_resolution:
                w, h = self.target_resolution
                clips = [c.resize(newsize=(w, h)) for c in clips]

            # Choose output file names (no dependency on optional ProjectFS variant helpers)
            proj = self.paths.project
            suffix = f"_{variant_tag}" if variant_tag else ""
            base_mp4 = self.paths.rendered_dir / f"{proj}_edit{suffix}.mp4"
            base_mp3 = self.paths.rendered_dir / f"{proj}_audio{suffix}.mp3"
            base_with_audio = self.paths.rendered_dir / f"{proj}_edit{suffix}_with_audio.mp4"

            self.paths.rendered_dir.mkdir(parents=True, exist_ok=True)

            final = concatenate_videoclips(clips, method="compose")
            final.write_videofile(str(base_mp4), **self.output_settings)
            final.close()

            # small metadata next to the video (useful for tracking)
            meta = {
                "seed": self.seed,
                "variant_tag": variant_tag,
                "num_clips": len(clips),
                "allow_reuse_segments": self.allow_reuse_segments,
            }
            (base_mp4.with_suffix(".json")).write_text(json.dumps(meta, indent=2))

            # === Audio handling ===
            if self.music_source:
                if self.music_source == "auto":
                    input_video = self.paths.input_video()
                    if not input_video.exists():
                        raise FileNotFoundError(f"Project input video not found: {input_video}")
                    extract_audio_from_video(str(input_video), str(base_mp3))
                    audio_path = base_mp3
                else:
                    audio_path = Path(self.music_source)
                    if not audio_path.exists():
                        raise FileNotFoundError(f"Audio file not found: {audio_path}")

                overlay_audio_on_video(str(base_mp4), str(audio_path), str(base_with_audio))
                return str(base_with_audio)

            return str(base_mp4)

        finally:
            self._close_sources()

    # ---------- internals ----------
    def _load_timestamps(self) -> List[float]:
        ts_path = self.paths.timestamps_yaml()
        if not ts_path.exists():
            raise FileNotFoundError(f"Timestamp YAML not found: {ts_path}")
        with open(ts_path, "r") as f:
            data = yaml.safe_load(f) or {}
        ts = data.get("timestamps", [])
        if not ts or len(ts) < 2:
            raise ValueError("Need at least 2 timestamps to compute clip durations.")
        return ts

    def _calculate_clip_durations(self, timestamps: List[float]) -> List[float]:
        return [max(0.0, j - i) for i, j in zip(timestamps[:-1], timestamps[1:]) if j > i]

    def _open_sources(self):
        candidates = sorted([p for p in self.paths.sources_dir.glob("*") if p.suffix.lower() in self.allowed_exts])
        if not candidates:
            raise FileNotFoundError(f"No source videos found in {self.paths.sources_dir} with {self.allowed_exts}")
        for p in candidates:
            clip = VideoFileClip(str(p))
            self.sources[str(p)] = clip
            self.used[str(p)] = []

    def _close_sources(self):
        for clip in self.sources.values():
            try:
                clip.close()
            except Exception:
                pass
        self.sources.clear()
        self.used.clear()

    def _select_clips(self, durations: List[float]):
        out = []
        source_paths = list(self.sources.keys())
        for dur in durations:
            if dur <= 0.0:
                continue
            selected = self._select_one_clip(source_paths, dur)
            if selected is None:
                selected = self._best_possible_clip(source_paths, dur)
                if selected is None:
                    raise RuntimeError(f"Could not pick clip for duration ~{dur:.3f}s from any source.")
            out.append(selected)
        return out

    def _select_one_clip(self, source_paths: List[str], duration: float) -> Optional[VideoFileClip]:
        attempts = 0
        while attempts < self.max_selection_attempts:
            attempts += 1
            spath = random.choice(source_paths)
            src = self.sources[spath]
            if src.duration <= duration + 0.05:
                continue
            max_start = src.duration - duration - 0.02
            start = random.uniform(0.0, max_start)
            end = start + duration
            if self.allow_reuse_segments or not self._overlaps(spath, start, end):
                self.used[spath].append((start, end))
                return src.subclip(start, end)
        return None

    def _best_possible_clip(self, source_paths: List[str], duration: float) -> Optional[VideoFileClip]:
        best_clip = None
        best_len = 0.0
        for spath in source_paths:
            src = self.sources[spath]
            window = min(duration, max(0.0, src.duration - 0.02))
            if window <= 0.0:
                continue
            for _ in range(10):
                if window > src.duration - 0.02:
                    continue
                start = random.uniform(0.0, src.duration - window - 0.02)
                end = start + window
                if self.allow_reuse_segments or not self._overlaps(spath, start, end):
                    if window > best_len:
                        best_len = window
                        best_clip = src.subclip(start, end)
                        if abs(window - duration) < 0.05:
                            break
        return best_clip

    def _overlaps(self, spath: str, start: float, end: float) -> bool:
        segs = self.used.get(spath, [])
        return any((start < e and end > s) for s, e in segs)
