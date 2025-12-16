# utils/file_ops/project_paths.py
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ProjectFS:
    base_dir: Path
    project: str

    def __post_init__(self):
        self.project_root = self.base_dir / self.project
        # canonical subdirs
        self.input_dir = self.project_root / "input"
        self.sources_dir = self.project_root / "sources"
        self.timestamps_dir = self.project_root / "timestamps"
        self.processed_dir = self.project_root / "processed"
        self.rendered_dir = self.project_root / "rendered"

    # canonical files
    def input_video(self) -> Path:
        # pick the first mp4/mov/m4v in input/
        for p in self.input_dir.glob("*"):
            if p.suffix.lower() in {".mp4", ".mov", ".m4v"}:
                return p
        # if none present, return a non-existing default (caller should error nicely)
        return self.input_dir / "input.mp4"

    def input_audio(self) -> Path:
        # pick the first audio file in input/ (mp3, wav, m4a, etc.)
        for p in self.input_dir.glob("*"):
            if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"}:
                return p
        # if none present, return a non-existing default (caller should error nicely)
        return self.input_dir / "input.mp3"

    def timestamps_yaml(self) -> Path:
        return self.timestamps_dir / f"{self.project}_timestamps.yml"

    def processed_video(self) -> Path:
        return self.processed_dir / f"{self.project}_processed.mp4"

    def ensure_dirs(self):
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        self.timestamps_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.rendered_dir.mkdir(parents=True, exist_ok=True)
