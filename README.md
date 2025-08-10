# Vibe Video Editor — User Guide

A clip-sync video editor that learns beat/cut timing from a **reference edit**, then auto-composes a new montage from your own clips. 🎬  
Supports generating **multiple unique edit versions** from the same detected timestamps using different seeds.

---

## 💻 1. Requirements

* **OS**: Linux/macOS (Windows should work, but paths/ffmpeg install may differ)
* **Python**: 3.9–3.11 (tested on 3.10) 🐍
* **FFmpeg**: Required by MoviePy.
    * **Linux**: `sudo apt install ffmpeg`
    * **macOS**: `brew install ffmpeg`

### Python Environment (Recommended)
```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Avoid potential NumPy 2.x/SciPy mismatches
pip install --upgrade pip
pip install "numpy<2" scipy matplotlib

# Core dependencies
pip install moviepy opencv-python pyyaml
````

---

## 📂 2. Project Structure

All work happens per-project inside the `projects/<project_name>/` directory. Each project is self-contained.

```
projects/<project_name>/
  ├── input/        # Your reference/beat video
  ├── sources/      # Source clips to cut from
  ├── timestamps/   # Auto-generated YAML of cut times
  ├── processed/    # Visualization video with detected events
  └── rendered/     # Final edits and extracted audio
```

The global configuration is in:

```
config/default_config.yml
```

---

## 📥 3. Media Placement

* **Reference/Beat video** → `projects/<name>/input/`
  The audio from this will be extracted (or use custom audio in config).
* **Source clips** → `projects/<name>/sources/`
  These are sliced and arranged according to detected timestamps.

---

## 🚀 4. Quick Start — Full Pipeline

```bash
# 1) Create the project structure
python main.py init --config config/default_config.yml --project my_reel --with-dummies

# 2) Put your reference video into:
#    projects/my_reel/input/<YOUR_VIDEO>.mp4

# 3) Add your own source clips to:
#    projects/my_reel/sources/

# 4) Run detection + composition
python main.py pipeline --config config/default_config.yml --project my_reel
```

**Outputs:**

```
processed/my_reel_processed.mp4          # Video with detection overlays
timestamps/my_reel_timestamps.yml        # Detected cut times
rendered/my_reel_edit.mp4                # Video only
rendered/my_reel_audio.mp3               # Extracted audio
rendered/my_reel_edit_with_audio.mp4     # Final video with audio
```

To **re-compose** without re-running detection:

```bash
python main.py pipeline --config config/default_config.yml --project my_reel --skip-detect
```

---

## 🔬 5. Step-by-Step Workflow

### 1) Initialize a project

```bash
python main.py init --config config/default_config.yml --project my_reel
```

(Add `--with-dummies` to auto-create sample clips.)

### 2) Add media

* Reference video → `input/`
* Source clips → `sources/`

### 3) Detect timestamps

```bash
python main.py detect --config config/default_config.yml --project my_reel
```

Generates:

* `timestamps/my_reel_timestamps.yml`
* `processed/my_reel_processed.mp4`

### 4) Compose edit

```bash
python main.py compose --config config/default_config.yml --project my_reel
```

Generates:

* `rendered/my_reel_edit.mp4`
* `rendered/my_reel_audio.mp3`
* `rendered/my_reel_edit_with_audio.mp4`

---

## 🎲 6. Multiple Random Versions (Seeds)

After detection, you can generate **multiple unique edits** from the same timestamps using different seeds.

```bash
# Generate edits with different seeds
python main.py compose --config config/default_config.yml --project my_reel --seed 42
python main.py compose --config config/default_config.yml --project my_reel --seed 99
python main.py compose --config config/default_config.yml --project my_reel --seed 2025
```

Output files are named with the seed:

```
rendered/my_reel_edit_seed42.mp4
rendered/my_reel_edit_with_audio_seed42.mp4
rendered/my_reel_edit_seed99.mp4
...
```

**Notes:**

* Same seed → identical clip order.
* Omit `--seed` → random order (not reproducible).
* No need to re-run detection.

**Example:**

```bash
for s in 1 2 3 4 5; do
    python main.py compose --config config/default_config.yml --project my_reel --seed $s
done
```

---

## ⚙️ 7. Config (`config/default_config.yml`)

```yaml
base_dir: "projects"

scene_detection:
  threshold: 0.90
  slow_factor: 1.0

composer:
  allowed_exts: [".mp4", ".mov", ".m4v"]
  target_resolution: [1280, 720]
  allow_reuse_segments: true
  max_selection_attempts: 80

  music_source: auto  # or path to custom mp3

  output_settings:
    codec: libx264
    audio_codec: aac
    fps: 30
```

---

## ⌨️ 8. CLI Commands

```bash
# Create new project
python main.py init --config config/default_config.yml --project <name> [--with-dummies]

# Detect timestamps
python main.py detect --config config/default_config.yml --project <name>

# Compose only
python main.py compose --config config/default_config.yml --project <name> [--seed N]

# Full pipeline
python main.py pipeline --config config/default_config.yml --project <name> [--skip-detect]
```

---

## 🛠️ 9. Troubleshooting

* **`ModuleNotFoundError: moviepy.editor`** → Install in correct venv.
* **NumPy/SciPy mismatch** → Use `"numpy<2"` and clean venv.
* **No audio in output** → Ensure reference has audio & `music_source: auto`.
* **Clip selection errors** → Add longer/more source clips or allow reuse.
* **`FFmpeg not found`** → Install via `sudo apt install ffmpeg` or `brew install ffmpeg`.

---

## 🎞️ 10. Example Session

```bash
source .venv/bin/activate

python main.py init --config config/default_config.yml --project my_reel --with-dummies
# Add your reference video to input/ and source clips to sources/

python main.py pipeline --config config/default_config.yml --project my_reel

# Generate extra random versions
python main.py compose --config config/default_config.yml --project my_reel --seed 10
python main.py compose --config config/default_config.yml --project my_reel --seed 11
```


