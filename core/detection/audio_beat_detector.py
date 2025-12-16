import yaml
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Optional

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

from utils.file_ops.project_paths import ProjectFS


class AudioBeatDetector:
    """
    Detects beats in audio files and generates timestamps for video editing.
    Uses librosa for beat tracking and tempo estimation.
    """
    
    def __init__(self, config: dict, project_name: str):
        if not LIBROSA_AVAILABLE:
            raise ImportError(
                "librosa is required for audio beat detection. "
                "Install with: pip install librosa"
            )
        
        self.global_cfg = config
        self.cfg = config.get('audio_beat_detection', {})
        self._validate_config()

        base_dir = Path(config.get('base_dir', 'projects')).resolve()
        self.paths = ProjectFS(base_dir=base_dir, project=project_name)
        self.paths.ensure_dirs()

        self.beat_timestamps: List[float] = []
        self.timestamps_path = None
        self.bpm: Optional[float] = None

    def _validate_config(self):
        """Validate configuration parameters"""
        required_keys = []
        for key in required_keys:
            if key not in self.cfg:
                raise ValueError(f"Missing required config key: 'audio_beat_detection.{key}'")

    def process_audio(self) -> List[float]:
        """
        Process audio file to detect beats and generate timestamps.
        
        Returns:
            List of beat timestamps in seconds
        """
        input_path = self.paths.input_audio()
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input audio not found: {input_path}")

        print(f"Processing audio: {input_path}")
        
        # Load audio file
        y, sr = librosa.load(str(input_path), sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        print(f"Audio duration: {duration:.2f} seconds")
        print(f"Sample rate: {sr} Hz")
        
        # Estimate tempo (BPM)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
        self.bpm = tempo
        
        print(f"Detected BPM: {self.bpm:.2f}")
        
        # Store original detected beats for reference (not used for generation, just for info)
        original_beats = beats.tolist()
        
        # Apply BPM-based timestamp generation
        self._apply_beat_filtering(duration)
        
        print(f"Generated {len(self.beat_timestamps)} timestamps")
        
        # Save timestamps
        self._save_timestamps(input_path, duration)
        
        return self.beat_timestamps

    def _apply_beat_filtering(self, audio_duration: float):
        """
        Generate timestamps based on BPM and beat fraction.
        Uses BPM to calculate exact timing for beat/half-beat/quarter-beat switching.
        
        Args:
            audio_duration: Actual duration of the audio file in seconds
        """
        # Get beat fraction (e.g., 1.0 = every beat, 0.5 = every half beat, 0.25 = every quarter beat)
        beat_fraction = float(self.cfg.get('beat_fraction', 1.0))
        min_duration = float(self.cfg.get('min_clip_duration', 0.1))  # Minimum seconds
        
        if self.bpm is None or self.bpm <= 0:
            print("Warning: BPM not detected, using detected beats as-is")
            return
        
        # Calculate beat interval in seconds
        beat_interval = 60.0 / self.bpm  # seconds per beat
        clip_interval = beat_interval * beat_fraction  # seconds per clip change
        
        print(f"Beat interval: {beat_interval:.3f}s per beat")
        print(f"Clip change interval: {clip_interval:.3f}s (beat_fraction={beat_fraction})")
        
        # Generate timestamps based on BPM and beat fraction, using actual audio duration
        generated_timestamps = []
        current_time = 0.0
        
        while current_time < audio_duration:
            generated_timestamps.append(current_time)
            current_time += clip_interval
        
        # Ensure we include the end timestamp
        if len(generated_timestamps) > 0 and generated_timestamps[-1] < audio_duration - 0.1:
            generated_timestamps.append(audio_duration)
        
        # Apply minimum duration filter
        if min_duration > 0 and len(generated_timestamps) > 1:
            filtered = [generated_timestamps[0]]
            for ts in generated_timestamps[1:]:
                if ts - filtered[-1] >= min_duration:
                    filtered.append(ts)
            generated_timestamps = filtered
        
        self.beat_timestamps = generated_timestamps
        print(f"Generated {len(self.beat_timestamps)} timestamps based on BPM ({self.bpm:.2f}) and beat_fraction ({beat_fraction})")

    def _save_timestamps(self, input_path: Path, duration: float):
        """Save detected timestamps to YAML file"""
        self.timestamps_path = self.paths.timestamps_yaml()
        
        # Ensure we have at least 2 timestamps (start and end)
        timestamps = self.beat_timestamps.copy()
        if len(timestamps) == 0:
            timestamps = [0.0, duration]
        elif len(timestamps) == 1:
            timestamps.append(duration)
        else:
            # Ensure last timestamp doesn't exceed duration
            if timestamps[-1] < duration - 0.1:
                timestamps.append(duration)
        
        # Convert all numpy types to native Python types for YAML compatibility
        timestamps = [float(ts) for ts in timestamps]
        
        with open(self.timestamps_path, 'w') as f:
            yaml.dump({
                'project': self.paths.project,
                'source_audio': str(input_path),
                'detection_time': datetime.now().isoformat(),
                'detection_mode': 'audio_reference',
                'bpm': float(self.bpm) if self.bpm is not None else None,
                'beat_fraction': float(self.cfg.get('beat_fraction', 1.0)),
                'audio_duration': float(duration),
                'num_beats_detected': int(len(self.beat_timestamps)),
                'timestamps': timestamps
            }, f, default_flow_style=False)
        
        print(f"Timestamps saved to: {self.timestamps_path}")

    @property
    def get_beat_timestamps(self) -> List[float]:
        return self.beat_timestamps

    @property
    def get_timestamps_path(self) -> str:
        return str(self.timestamps_path) if self.timestamps_path else None

    @property
    def get_bpm(self) -> Optional[float]:
        return self.bpm

