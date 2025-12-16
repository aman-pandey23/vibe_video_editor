# Audio Reference Mode - Implementation Summary

## What Was Added

A new **Audio Reference Mode** has been integrated into the Vibe Video Editor, allowing you to create video edits synchronized to music beats instead of analyzing a reference video.

## New Files Created

1. **`core/detection/audio_beat_detector.py`**
   - New module for audio beat detection
   - Uses `librosa` library for beat tracking and BPM estimation
   - Configurable parameters for clip change frequency

2. **`config/audio_reference_config.yml`**
   - Configuration file specifically for audio mode
   - Contains audio beat detection parameters

3. **`AUDIO_MODE_GUIDE.md`**
   - Comprehensive guide for using audio mode
   - Examples, tips, and troubleshooting

## Modified Files

1. **`main.py`**
   - Added `AudioBeatDetector` import
   - Updated `run_detect()` to route to correct detector based on mode
   - Updated project initialization messages for both modes

2. **`core/composition/video_composer.py`**
   - Updated audio handling to detect mode from timestamps YAML
   - In audio mode, uses input audio file directly instead of extracting from video

3. **`utils/file_ops/project_paths.py`**
   - Added `input_audio()` method to find audio files in input directory

4. **`config/default_config.yml`**
   - Added `mode: "video_reference"` to explicitly mark video mode

5. **`README.md`**
   - Updated with information about both modes
   - Added audio mode quick start section

## How It Works

### Detection Flow

1. **Audio Mode**: `AudioBeatDetector.process_audio()`
   - Loads audio file using librosa
   - Detects beats and estimates BPM
   - Applies filtering based on config (clip_change_frequency, min/max duration)
   - Saves timestamps to YAML with metadata (BPM, detection_mode, etc.)

2. **Video Mode**: `SceneDetector.process_video()` (unchanged)
   - Analyzes video frames for scene transitions
   - Uses histogram correlation

### Composition Flow

Both modes use the same `VideoComposer`, which:
- Loads timestamps from YAML
- Detects mode from YAML metadata
- In audio mode: uses input audio file directly
- In video mode: extracts audio from reference video

## Usage Examples

### Audio Mode - Quick Start

```bash
# 1. Create project
python main.py init --config config/audio_reference_config.yml --project my_beat_edit

# 2. Add audio file to: projects/my_beat_edit/input/my_song.mp3
# 3. Add video clips to: projects/my_beat_edit/sources/

# 4. Run detection + composition
python main.py pipeline --config config/audio_reference_config.yml --project my_beat_edit
```

### Video Mode - Quick Start (unchanged)

```bash
# 1. Create project
python main.py init --config config/default_config.yml --project my_video_edit

# 2. Add video file to: projects/my_video_edit/input/reference.mp4
# 3. Add video clips to: projects/my_video_edit/sources/

# 4. Run detection + composition
python main.py pipeline --config config/default_config.yml --project my_video_edit
```

## Configuration Parameters

### Audio Mode (`audio_reference_config.yml`)

```yaml
audio_beat_detection:
  clip_change_frequency: 2    # Every N beats (1=fast, 2=medium, 4=slow)
  min_clip_duration: 0.5      # Minimum seconds between cuts
  max_clip_duration: 5.0      # Maximum seconds between cuts
```

### Video Mode (`default_config.yml`)

```yaml
scene_detection:
  threshold: 0.90  # Histogram correlation threshold
```

## Key Features

1. **Automatic Mode Detection**: System automatically routes to correct detector based on config `mode` field
2. **Shared Composition Engine**: Both modes use the same video composition logic
3. **Mode Metadata**: Timestamps YAML includes `detection_mode` for proper audio handling
4. **Backward Compatible**: Existing video mode projects continue to work unchanged

## Dependencies

- **librosa**: Required for audio mode (install with `pip install librosa`)
- All existing dependencies remain the same

## Testing

To test audio mode:

1. Install librosa: `pip install librosa`
2. Create a test project with audio file
3. Run detection and verify BPM is detected
4. Run composition and verify video is created with audio synced to beats

## Future Enhancements

Potential improvements:
- Support for custom beat patterns
- Visual beat visualization (like video mode's processed video)
- Advanced filtering options (e.g., only strong beats)
- Multi-track audio support

