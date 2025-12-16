# Audio Reference Mode Guide

## Overview

Audio Reference Mode uses **beat detection** from an audio file to generate timestamps for video editing. Instead of analyzing a reference video, you provide an audio file (MP3, WAV, etc.) and the system detects the beats/BPM to create a rhythmically-synced video edit.

## How It Works

1. **Beat Detection**: Uses `librosa` to analyze the audio file and detect beats
2. **BPM Estimation**: Automatically calculates the tempo (BPM) of the song
3. **Timestamp Generation**: Creates cut points based on detected beats
4. **Configurable Pacing**: Adjust how often clips change relative to beats

## Requirements

Install librosa for audio analysis:
```bash
pip install librosa
```

## Quick Start

### 1. Create Project with Audio Mode Config

```bash
python main.py init --config config/audio_reference_config.yml --project my_audio_edit
```

### 2. Add Your Audio File

Place your audio file in the `input/` directory:
```bash
projects/my_audio_edit/input/
  └── my_song.mp3  # or .wav, .m4a, .flac, etc.
```

Supported audio formats: `.mp3`, `.wav`, `.m4a`, `.flac`, `.aac`, `.ogg`

### 3. Add Source Video Clips

Place your video clips in the `sources/` directory:
```bash
projects/my_audio_edit/sources/
  ├── clip1.mp4
  ├── clip2.mp4
  └── clip3.mp4
```

### 4. Run Detection

```bash
python main.py detect --config config/audio_reference_config.yml --project my_audio_edit
```

This will:
- Analyze the audio file
- Detect beats and estimate BPM
- Generate timestamps based on beat detection
- Save timestamps to `timestamps/my_audio_edit_timestamps.yml`

**Output:**
```
Starting audio beat detection...
Processing audio: projects/my_audio_edit/input/my_song.mp3
Audio duration: 180.50 seconds
Sample rate: 44100 Hz
Detected BPM: 128.45
Detected 45 beats
Timestamps saved to: timestamps/my_audio_edit_timestamps.yml
```

### 5. Compose Video

```bash
python main.py compose --config config/audio_reference_config.yml --project my_audio_edit
```

This creates a video edit where clips change on the beat!

## Configuration Parameters

Edit `config/audio_reference_config.yml` to customize behavior:

### `clip_change_frequency`

Controls how often clips change relative to beats:

- **`1`**: Change on every beat (very fast, high energy)
  - Good for: EDM, fast-paced songs, high-energy edits
  - Example: 128 BPM song = ~128 cuts per minute

- **`2`**: Change every 2 beats (medium pace, most common)
  - Good for: Most pop, hip-hop, rock songs
  - Example: 128 BPM song = ~64 cuts per minute

- **`4`**: Change every 4 beats (slower, more relaxed)
  - Good for: Ballads, slower songs, cinematic edits
  - Example: 128 BPM song = ~32 cuts per minute

### `min_clip_duration`

Minimum time (in seconds) between cuts. Prevents clips from being too short.

- Default: `0.5` seconds
- Increase for: Longer clips, more cinematic feel
- Decrease for: Faster-paced edits (but clips must be long enough)

### `max_clip_duration`

Maximum time (in seconds) between cuts. If beats are far apart, intermediate cuts will be added.

- Default: `5.0` seconds
- Increase for: Allow longer gaps between cuts
- Decrease for: More consistent pacing

## Example Configurations

### Fast-Paced EDM Edit
```yaml
audio_beat_detection:
  clip_change_frequency: 1    # Every beat
  min_clip_duration: 0.3      # Allow shorter clips
  max_clip_duration: 3.0       # Keep pace tight
```

### Medium-Paced Pop Edit
```yaml
audio_beat_detection:
  clip_change_frequency: 2    # Every 2 beats (default)
  min_clip_duration: 0.5      # Standard minimum
  max_clip_duration: 5.0      # Standard maximum
```

### Cinematic/Slow Edit
```yaml
audio_beat_detection:
  clip_change_frequency: 4    # Every 4 beats
  min_clip_duration: 1.0      # Longer clips
  max_clip_duration: 8.0      # Allow longer gaps
```

## Workflow Examples

### Full Pipeline (Detection + Composition)

```bash
python main.py pipeline --config config/audio_reference_config.yml --project my_audio_edit
```

### Generate Multiple Variants

After detection, generate multiple random edits:

```bash
# Generate 5 different edits with different clip selections
python main.py compose-multi \
  --config config/audio_reference_config.yml \
  --project my_audio_edit \
  --count 5 \
  --seed 0
```

### Use Specific Seed

```bash
python main.py compose \
  --config config/audio_reference_config.yml \
  --project my_audio_edit \
  --seed 42
```

## Timestamps YAML Format

The generated timestamps file includes metadata:

```yaml
project: my_audio_edit
source_audio: projects/my_audio_edit/input/my_song.mp3
detection_time: '2025-01-15T10:30:00.123456'
detection_mode: audio_reference
bpm: 128.45
audio_duration: 180.5
num_beats_detected: 45
timestamps:
  - 0.0
  - 0.468
  - 0.936
  - 1.404
  # ... more timestamps
```

## Tips & Best Practices

1. **Audio Quality**: Use high-quality audio files for better beat detection
2. **Source Clips**: Ensure source clips are longer than your `min_clip_duration`
3. **BPM Matching**: The system works with any BPM, but very slow (<60 BPM) or very fast (>200 BPM) songs may need parameter adjustment
4. **Multiple Variants**: Use different seeds to generate multiple edit versions from the same beat timestamps
5. **Custom Audio**: You can use `music_source: <path>` in config to use a different audio file for the final video (instead of the input audio)

## Troubleshooting

### "librosa is required"
```bash
pip install librosa
```

### "No beats detected"
- Check audio file format (MP3, WAV, etc.)
- Ensure audio file has clear rhythm/beats
- Very ambient/noise tracks may not detect beats well

### "Too many/few cuts"
- Adjust `clip_change_frequency` (higher = fewer cuts, lower = more cuts)
- Adjust `min_clip_duration` and `max_clip_duration`

### "Audio file not found"
- Ensure audio file is in `projects/<project>/input/`
- Check file extension is supported (.mp3, .wav, .m4a, etc.)

## Comparison: Video vs Audio Mode

| Feature | Video Reference Mode | Audio Reference Mode |
|---------|---------------------|---------------------|
| Input | Video file | Audio file |
| Detection Method | Histogram correlation | Beat tracking (librosa) |
| Best For | Matching existing video edits | Music-synced edits |
| Config File | `default_config.yml` | `audio_reference_config.yml` |
| Parameters | `threshold` | `clip_change_frequency`, `min/max_duration` |
| Output | Scene transition timestamps | Beat-based timestamps |

Both modes use the same composition engine, so you can switch between them easily!

