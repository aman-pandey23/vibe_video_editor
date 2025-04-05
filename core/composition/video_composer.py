import random
from moviepy import VideoFileClip, concatenate_videoclips
from pathlib import Path
import yaml

class VideoComposer:
    def __init__(self, config):
        self.config = config
        self.source_videos = self._load_source_videos()
        
    def create_edit(self, project_name):
        timestamps = self._load_timestamps(project_name)
        clip_durations = self._calculate_clip_durations(timestamps)
        clips = self._select_clips(clip_durations)
        final = concatenate_videoclips(clips)
        
        output_path = self._get_output_path(project_name)
        final.write_videofile(output_path, **self.config['output_settings'])
    
    def _load_timestamps(self, project_name):
        ts_path = Path(f"inspiration/timestamp_yamls/{project_name}_timestamps.yml")
        with open(ts_path) as f:
            data = yaml.safe_load(f)
        return data['timestamps']
    
    def _calculate_clip_durations(self, timestamps):
        return [j-i for i,j in zip(timestamps[:-1], timestamps[1:])]
    
    def _select_clips(self, durations):
        clips = []
        used_segments = []
        
        for duration in durations:
            source = random.choice(self.source_videos)
            clip = self._get_random_clip(source, duration, used_segments)
            clips.append(clip)
            
        return clips
    
    def _get_random_clip(self, source_path, duration, used_segments):
        with VideoFileClip(source_path) as src:
            max_start = src.duration - duration
            while True:
                start = random.uniform(0, max_start)
                end = start + duration
                if not self._is_overlapping(start, end, used_segments):
                    used_segments.append((start, end))
                    return src.subclip(start, end)
    
    def _is_overlapping(self, start, end, existing):
        return any((start < e and end > s) for s,e in existing)
    
    def _load_source_videos(self):
        return [str(p) for p in Path("source_videos").glob("*") if p.suffix in [".mp4", ".mov"]]
    
    def _get_output_path(self, project_name):
        output_dir = Path(self.config['output_settings']['output_dir'])
        output_dir.mkdir(exist_ok=True)
        return str(output_dir / f"{project_name}_edit.mp4")