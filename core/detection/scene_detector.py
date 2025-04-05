import cv2
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime
from utils.video_ops.video_utils import compute_histogram, overlay_event_text

class SceneDetector:
    def __init__(self, config):
        self.config = config['scene_detection']
        self._validate_config()
        self.event_timestamps = []
        self.output_path = None
        self.timestamps_path = None

    def process_video(self):
        input_path = self.config['input_path']
        threshold = self.config['threshold']
        slow_factor = self.config.get('slow_factor', 1)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_path}")

        self.output_path = self._get_output_path(input_path)
        print(f"Processing video: {input_path}")
        print(f"Output will be saved to: {self.output_path}")

        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise ValueError("Cannot open video file")

        input_fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        output_fps = input_fps / slow_factor

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, output_fps, (width, height))
        
        if not out.isOpened():
            raise RuntimeError(f"Failed to initialize video writer at {self.output_path}")

        ret, frame = cap.read()
        if frame is not None:
            prev_hist = compute_histogram(frame)
            out.write(frame)

        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"Stopped processing at {cap.get(cv2.CAP_PROP_POS_FRAMES)} frames")
                break

            if frame is None:
                print("Warning: Received empty frame")
                continue

            current_hist = compute_histogram(frame)
            hist_correlation = cv2.compareHist(prev_hist, current_hist, cv2.HISTCMP_CORREL)
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

            if hist_correlation < threshold:
                self.event_timestamps.append(timestamp)
                frame = overlay_event_text(frame, "EVENT")

            out.write(frame)
            prev_hist = current_hist

        cap.release()
        out.release()
        self._save_timestamps(input_path)
        return self.event_timestamps

    def _validate_config(self):
        required_keys = ['input_path', 'output_dir', 'threshold']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")

    def _save_timestamps(self, input_path):
        Path(self.config['yaml_dir']).mkdir(exist_ok=True)
        self.timestamps_path = Path(self.config['yaml_dir']) / f"{Path(input_path).stem}_timestamps.yml"
        
        with open(self.timestamps_path, 'w') as f:
            yaml.dump({
                'source_video': str(input_path),
                'detection_time': datetime.now().isoformat(),
                'timestamps': self.event_timestamps
            }, f)

    def _get_output_path(self, input_path):
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(exist_ok=True)
        return str(output_dir / f"{Path(input_path).stem}_processed.mp4")

    @property
    def get_event_timestamps(self):
        return self.event_timestamps

    @property
    def get_output_path(self):
        return self.output_path

    @property
    def get_timestamps_path(self):
        return self.timestamps_path