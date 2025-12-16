# BPM-Based Video Editing Features

## Overview

The audio reference mode now uses **BPM-based clip syncing** for precise, rhythm-driven video edits. The system calculates exact timing based on the detected BPM and allows for sub-beat switching (faster than one beat).

## New Features

### 1. BPM-Based Clip Syncing

Instead of using detected beats directly, the system now:
- Detects BPM from the audio file
- Calculates exact beat intervals: `beat_interval = 60.0 / BPM` (seconds per beat)
- Generates timestamps based on BPM and beat fraction

**Example:**
- BPM: 120
- Beat interval: 0.5 seconds per beat
- With `beat_fraction: 0.5`: Clip changes every 0.25 seconds (half-beat)

### 2. Sub-Beat Switching (High-Velocity Edits)

The `beat_fraction` parameter now supports values **below 1.0** for ultra-fast edits:

- **`1.0`** = Every beat (standard)
- **`0.5`** = Every half beat (2x speed, high velocity)
- **`0.25`** = Every quarter beat (4x speed, very fast)
- **`0.125`** = Every eighth beat (8x speed, extreme)

**Formula:** `clip_change_interval = (60.0 / BPM) * beat_fraction`

### 3. Enhanced Random Clip Selection

The clip selection algorithm is now more random:

- **Shuffled source paths**: Source videos are shuffled for each selection
- **Random positioning zones**: Clips are selected from beginning (33%), middle (33%), or end (33%) of source videos
- **More attempts**: Increased from 10 to 20 attempts in fallback mode
- **Wider range**: More variation in start positions

### 4. Clip Overlapping

Clips can now overlap by a configurable amount (default: 1.5 seconds):

- **`clip_overlap: 0.0`** = No overlap (hard cuts)
- **`clip_overlap: 1.0`** = 1 second overlap (smooth transitions)
- **`clip_overlap: 1.5`** = 1.5 seconds overlap (very smooth, recommended)
- **`clip_overlap: 2.0`** = 2 seconds overlap (maximum smoothness)

**How it works:**
- Each clip is selected with extra duration (target + overlap)
- During composition, subsequent clips start from the overlap point
- Creates crossfade-like transitions between clips

## Configuration

### `config/audio_reference_config.yml`

```yaml
audio_beat_detection:
  # Beat fraction: How often clips change relative to beats
  beat_fraction: 0.5  # Every half beat (high velocity)
  min_clip_duration: 0.1  # Minimum seconds between cuts

composer:
  clip_overlap: 1.5  # 1.5 seconds overlap between clips
  max_selection_attempts: 100  # More attempts for randomness
  allow_reuse_segments: true  # Allow overlapping segments
```

## Usage Examples

### Ultra-Fast Edit (Quarter Beat)
```yaml
beat_fraction: 0.25  # Change every quarter beat
clip_overlap: 1.0    # 1 second overlap
```
**Result:** Very fast cuts, 4x the beat rate

### High-Velocity Edit (Half Beat)
```yaml
beat_fraction: 0.5   # Change every half beat
clip_overlap: 1.5    # 1.5 second overlap
```
**Result:** Fast cuts with smooth transitions

### Standard Edit (Every Beat)
```yaml
beat_fraction: 1.0   # Change every beat
clip_overlap: 0.5    # 0.5 second overlap
```
**Result:** Standard pace, moderate transitions

### Slow Edit (Every 2 Beats)
```yaml
beat_fraction: 2.0   # Change every 2 beats
clip_overlap: 2.0    # 2 second overlap
```
**Result:** Slower pace, very smooth transitions

## Technical Details

### BPM Calculation
- Uses `librosa.beat.beat_track()` for BPM estimation
- Calculates: `beat_interval = 60.0 / BPM`
- Generates timestamps: `timestamp = n * beat_interval * beat_fraction`

### Overlap Implementation
1. Clips are selected with duration: `target_duration + clip_overlap`
2. First clip uses full length
3. Subsequent clips start from `clip_overlap` seconds into the clip
4. Creates smooth crossfade effect

### Randomness Improvements
- Source path shuffling before each selection
- Zone-based random positioning (beginning/middle/end)
- Increased selection attempts
- Wider random range for start positions

## Performance Notes

- **Fast edits** (beat_fraction < 0.5) generate many timestamps
- **High overlap** (> 2.0s) may cause longer processing
- **More randomness** increases selection time but improves variety

## Tips

1. **For EDM/High-Energy**: Use `beat_fraction: 0.25` or `0.5`
2. **For Smooth Transitions**: Use `clip_overlap: 1.5` to `2.0`
3. **For Maximum Randomness**: Set `max_selection_attempts: 100+`
4. **For Very Short Clips**: Lower `min_clip_duration` to `0.05`

