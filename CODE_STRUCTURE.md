# Vibe Video Editor - Code Structure Documentation

## Overview

The Vibe Video Editor is a modular Python-based video editing system that:
1. **Detects** scene transitions in a reference video using histogram analysis
2. **Extracts** timestamps from detected transitions
3. **Composes** new videos by selecting and arranging clips from source videos based on those timestamps

The system uses a clean, modular architecture with clear separation of concerns.

---

## Architecture

### Core Modules

#### 1. **Scene Detection** (`core/detection/scene_detector.py`)
- **Purpose**: Analyzes a reference video to detect scene transitions/cuts
- **Method**: Histogram correlation analysis between consecutive frames
- **Input**: Reference video from `projects/<project>/input/`
- **Output**: 
  - `projects/<project>/processed/<project>_processed.mp4` - Visualization video with event markers
  - `projects/<project>/timestamps/<project>_timestamps.yml` - YAML file with detected timestamps

**Key Components:**
- `SceneDetector` class: Main detection orchestrator
- `_process_with_cv2_capture()`: Primary processing path using OpenCV
- `_process_with_moviepy_reader()`: Fallback path using MoviePy
- `_remux_with_ffmpeg()`: Optional post-processing to ensure compatibility

**Algorithm:**
1. Reads video frame-by-frame
2. Computes HSV histogram for each frame
3. Compares consecutive frame histograms using correlation
4. When correlation < threshold → scene transition detected
5. Saves timestamp and overlays "EVENT" text on visualization video

#### 2. **Video Composition** (`core/composition/video_composer.py`)
- **Purpose**: Creates edited videos by selecting clips from source videos based on detected timestamps
- **Input**: Timestamps YAML file from detection phase
- **Output**: 
  - `projects/<project>/rendered/<project>_edit[_tag].mp4` - Video without audio
  - `projects/<project>/rendered/<project>_audio[_tag].mp3` - Extracted audio
  - `projects/<project>/rendered/<project>_edit[_tag]_with_audio.mp4` - Final video with audio
  - `projects/<project>/rendered/<project>_edit[_tag].json` - Metadata about the edit

**Key Components:**
- `VideoComposer` class: Main composition orchestrator
- `_load_timestamps()`: Loads timestamps from YAML
- `_calculate_clip_durations()`: Converts timestamps to clip durations
- `_select_clips()`: Selects appropriate clips for each duration
- `_select_one_clip()`: Randomly selects a clip segment (with seed support)
- `_best_possible_clip()`: Fallback when exact duration can't be found

**Algorithm:**
1. Loads timestamps from YAML
2. Calculates duration for each segment (difference between consecutive timestamps)
3. For each duration:
   - Randomly selects a source video
   - Randomly selects a start time within that video
   - Extracts a clip of the required duration
   - Tracks used segments to avoid overlaps (if `allow_reuse_segments: false`)
4. Concatenates all clips
5. Optionally resizes to target resolution
6. Extracts audio from reference video (if `music_source: auto`)
7. Overlays audio onto composed video

**Seed Support:**
- Uses Python's `random.seed()` for deterministic clip selection
- Same seed → same clip selection order
- Enables generating multiple variants from same timestamps

---

### Utility Modules

#### 3. **File Operations** (`utils/file_ops/project_paths.py`)
- **Purpose**: Manages project directory structure and file paths
- **Key Component**: `ProjectFS` dataclass

**Directory Structure:**
```
projects/<project>/
  ├── input/        # Reference video
  ├── sources/      # Source clips
  ├── timestamps/   # Generated timestamp YAMLs
  ├── processed/    # Detection visualization videos
  └── rendered/     # Final composed videos
```

**Methods:**
- `input_video()`: Finds first video in input/ directory
- `timestamps_yaml()`: Returns path to timestamps YAML
- `processed_video()`: Returns path to processed visualization video
- `ensure_dirs()`: Creates all required directories

#### 4. **Video Utilities** (`utils/video_ops/video_utils.py`)
- **Purpose**: Low-level video processing functions
- **Functions:**
  - `compute_histogram(frame)`: Computes normalized HSV histogram for scene detection
  - `overlay_event_text(frame, text)`: Overlays text on frame for visualization

#### 5. **Audio Utilities** (`utils/audio_ops/audio_utils.py`)
- **Purpose**: Audio extraction and overlay operations
- **Functions:**
  - `extract_audio_from_video()`: Extracts audio track from video as MP3
  - `overlay_audio_on_video()`: Overlays audio onto video, matching lengths

#### 6. **Config Utilities** (`utils/config/config_utils.py`)
- **Purpose**: Configuration file loading
- **Function:**
  - `load_config()`: Loads and parses YAML configuration files

---

### Entry Point

#### 7. **Main CLI** (`main.py`)
- **Purpose**: Command-line interface for all operations
- **Commands:**
  - `init`: Creates new project structure
  - `detect`: Runs scene detection on reference video
  - `compose`: Creates composed video from timestamps
  - `compose-multi`: Generates multiple variant edits
  - `pipeline`: Runs detection + composition in sequence

**Helper Functions:**
- `_make_dummy_clip_cv2()`: Creates dummy test videos (used by `--with-dummies` flag)
- `_variant_tag_from_index()`: Generates variant tags (v001, v002, etc.)

---

## Configuration System

### Config File (`config/default_config.yml`)

```yaml
base_dir: "projects"  # Base directory for all projects

scene_detection:
  threshold: 0.90  # Histogram correlation threshold (0.0-1.0, lower = more sensitive)

composer:
  allowed_exts: [".mp4", ".mov", ".m4v"]  # Supported video formats
  # target_resolution: [1280, 720]  # Optional: resize all clips
  allow_reuse_segments: true  # Allow reusing same segments from sources
  max_selection_attempts: 80  # Max attempts to find non-overlapping clip
  music_source: auto  # "auto" to extract from reference, or path to MP3
  output_settings:
    codec: libx264
    audio_codec: aac
    fps: 30
```

### Timestamps YAML Format

Generated by `SceneDetector`, stored in `timestamps/<project>_timestamps.yml`:

```yaml
project: test_video
source_video: /path/to/reference/video.mp4
detection_time: '2025-08-10T21:34:37.040168'
timestamps:
  - 0.39666666666666667
  - 0.8633333333333334
  - 1.0133333333333334
  # ... more timestamps
```

---

## Data Flow

### Detection Phase
```
Reference Video (input/)
    ↓
SceneDetector.process_video()
    ↓
Frame-by-frame histogram analysis
    ↓
Detected timestamps
    ↓
[processed/<project>_processed.mp4]  [timestamps/<project>_timestamps.yml]
```

### Composition Phase
```
Timestamps YAML
    ↓
VideoComposer.create_edit()
    ↓
Calculate clip durations
    ↓
Select clips from sources/
    ↓
Concatenate clips
    ↓
Extract audio (if music_source: auto)
    ↓
Overlay audio
    ↓
[rendered/<project>_edit[_tag].mp4]  [rendered/<project>_edit[_tag]_with_audio.mp4]
```

---

## Dependencies

- **moviepy**: Video editing, clip manipulation, audio handling
- **opencv-python**: Video reading, frame processing, histogram computation
- **pyyaml**: Configuration and timestamp file parsing
- **numpy**: Array operations (used by OpenCV and MoviePy)
- **ffmpeg**: Required by MoviePy for video encoding/decoding

---

## Testing & Working Components

### Tested Workflow
1. ✅ Project initialization (`init` command)
2. ✅ Scene detection with OpenCV path
3. ✅ Scene detection fallback with MoviePy
4. ✅ Timestamp YAML generation
5. ✅ Clip selection from source videos
6. ✅ Video composition and concatenation
7. ✅ Audio extraction from reference video
8. ✅ Audio overlay on composed video
9. ✅ Variant generation with seeds
10. ✅ Multiple variant generation (`compose-multi`)

### Example Projects
- `projects/test_video/`: Contains test data with detected timestamps
- `projects/my_reel/`: Contains example project with multiple rendered variants

---

## Code Quality Improvements Made

1. ✅ Removed unused variant helper functions from `ProjectFS`
2. ✅ Removed commented-out code from `video_utils.py`
3. ✅ Removed empty `vid_edit_viz.py` file
4. ✅ Removed unused `slow_factor` parameter from scene detection
5. ✅ Simplified `config_utils.py` by removing unused path processing
6. ✅ Updated configuration file to remove unused `slow_factor`

---

## Extension Points

The modular architecture allows for easy extension:

1. **New Detection Methods**: Add to `core/detection/` (e.g., audio-based detection)
2. **New Composition Strategies**: Extend `VideoComposer` or create new composers
3. **New Transitions**: Add transition effects in `utils/video_ops/`
4. **New Output Formats**: Extend `VideoComposer.create_edit()` output handling
5. **New CLI Commands**: Add subparsers in `main.py`

---

## Notes

- The system is designed to work with any video format supported by OpenCV/MoviePy
- Scene detection uses histogram correlation, which works well for cuts but may miss gradual transitions
- Clip selection uses random sampling with seed support for reproducibility
- The system tracks used segments to avoid overlaps unless `allow_reuse_segments: true`
- Audio is automatically matched to video length (trimmed or looped as needed)

