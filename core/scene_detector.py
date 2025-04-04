import cv2
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime
from utils.video_utils import compute_histogram, overlay_event_text

class SceneDetector:
    def __init__(self, config_path=None):
        self.config = {
            'threshold': 0.90,
            'slow_factor': 1.0,
            'output_dir': 'output',
            'yaml_dir': 'inspiration/timestamp_yamls'
        }
        
    def process_video(self, input_path, output_path=None, threshold=None, slow_factor=None):
        threshold = threshold or self.config['threshold']
        slow_factor = slow_factor or self.config['slow_factor']
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")

        # Video properties
        input_fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        output_fps = input_fps / slow_factor

        # Setup output
        output_path = self._get_output_path(input_path) if not output_path else output_path
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, output_fps, (width, height))

        # Processing loop
        event_timestamps = []
        ret, frame = cap.read()
        prev_hist = compute_histogram(frame)
        out.write(frame)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            current_hist = compute_histogram(frame)
            hist_correlation = cv2.compareHist(prev_hist, current_hist, cv2.HISTCMP_CORREL)
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

            if hist_correlation < threshold:
                event_timestamps.append(timestamp)
                frame = overlay_event_text(frame, "EVENT")

            out.write(frame)
            prev_hist = current_hist

        cap.release()
        out.release()
        self._save_timestamps(input_path, event_timestamps)
        return event_timestamps

    def _save_timestamps(self, input_path, timestamps):
        Path(self.config['yaml_dir']).mkdir(exist_ok=True)
        output_file = Path(self.config['yaml_dir']) / f"{Path(input_path).stem}_timestamps.yml"
        
        with open(output_file, 'w') as f:
            yaml.dump({
                'source_video': str(input_path),
                'detection_time': datetime.now().isoformat(),
                'timestamps': timestamps
            }, f)

    def _get_output_path(self, input_path):
        Path(self.config['output_dir']).mkdir(exist_ok=True)
        return str(Path(self.config['output_dir']) / f"{Path(input_path).stem}_processed.mp4")