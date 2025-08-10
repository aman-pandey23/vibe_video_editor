# main.py
import argparse
from pathlib import Path

from core.detection.scene_detector import SceneDetector
from core.composition.video_composer import VideoComposer
from utils.config.config_utils import load_config
from utils.file_ops.project_paths import ProjectFS

# --- Optional: tiny helper to create dummy sources (kept here for convenience) ---
def _make_dummy_clip_cv2(path: Path, color_bgr=(0, 0, 255), duration=3, size=(1280, 720), label="DUMMY"):
    import cv2, numpy as np
    fps = 30
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(path), fourcc, fps, size)
    h, w = size[1], size[0]
    for _ in range(int(fps * duration)):
        frame = np.full((h, w, 3), color_bgr, dtype=np.uint8)
        cv2.putText(frame, label, (50, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4, cv2.LINE_AA)
        out.write(frame)
    out.release()

def init_project(base_dir: Path, project: str, create_dummies: bool = False):
    paths = ProjectFS(base_dir=base_dir, project=project)
    paths.ensure_dirs()

    # Drop a README into the project with quick instructions (optional nicety)
    readme = paths.project_root / "README.txt"
    if not readme.exists():
        readme.write_text(
            "Project skeleton created.\n\n"
            "Put your reference (beat) video into ./input/\n"
            "Put your source clips into ./sources/\n"
            "Then run:\n"
            f"  python main.py detect  --config config/default_config.yml --project {project}\n"
            f"  python main.py compose --config config/default_config.yml --project {project}\n"
        )

    if create_dummies:
        (paths.sources_dir).mkdir(parents=True, exist_ok=True)
        _make_dummy_clip_cv2(paths.sources_dir / "dummy_1.mp4", (0, 0, 255), 4, label="DUMMY 1")
        _make_dummy_clip_cv2(paths.sources_dir / "dummy_2.mp4", (0, 255, 0), 5, label="DUMMY 2")
        _make_dummy_clip_cv2(paths.sources_dir / "dummy_3.mp4", (255, 0, 0), 6, label="DUMMY 3")

    return paths

def run_detect(config: dict, project: str):
    detector = SceneDetector(config, project_name=project)
    print("Starting video analysis...")
    detector.process_video()
    print("\nDetection completed successfully!")
    print(f" - Detected events: {len(detector.get_event_timestamps)}")
    print(f" - Output video: {detector.get_output_path}")
    print(f" - Timestamps file: {detector.get_timestamps_path}")

def run_compose(config: dict, project: str, seed=None, tag=None) -> str:
    composer = VideoComposer(config, project_name=project, seed=seed)
    if tag is None and seed is not None:
        tag = f"seed{seed}"
    print(f"Composing from project timestamps: {project} (seed={seed}, tag={tag})")
    out = composer.create_edit(variant_tag=tag)
    print(f"\nComposition done!\n - Output video: {out}")
    return out

def _variant_tag_from_index(prefix: str, idx: int) -> str:
    # v001, v002... or seed42...
    if prefix.lower().startswith("seed"):
        return f"{prefix}{idx}"
    return f"{prefix}{idx:03d}"

def main():
    parser = argparse.ArgumentParser(
        description="Vibe Video Editor - Project init, detection, composing, and variants",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # init
    init_parser = subparsers.add_parser('init', help="Create a new project skeleton")
    init_parser.add_argument("-c", "--config", type=lambda p: Path(p).resolve(), required=True,
                             help="Path to YAML config file")
    init_parser.add_argument("-p", "--project", type=str, required=True,
                             help="Project name (creates projects/<name>/...)")
    init_parser.add_argument("--with-dummies", action="store_true",
                             help="Also create a few dummy source clips for quick testing")

    # detect
    detect_parser = subparsers.add_parser('detect', help="Analyze video for scene transitions")
    detect_parser.add_argument("-c", "--config", type=lambda p: Path(p).resolve(), required=True,
                               help="Path to YAML config file")
    detect_parser.add_argument("-p", "--project", type=str, required=True,
                               help="Project name")

    # compose (single)
    compose_parser = subparsers.add_parser('compose', help="Make a clip-sync video from timestamps")
    compose_parser.add_argument("-c", "--config", type=lambda p: Path(p).resolve(), required=True,
                                help="Path to YAML config file")
    compose_parser.add_argument("-p", "--project", type=str, required=True,
                                help="Project name")
    compose_parser.add_argument("--seed", type=int, default=None,
                                help="Random seed for deterministic composition")
    compose_parser.add_argument("--tag", type=str, default=None,
                                help="Variant tag to suffix filenames (e.g., 'seed42' or 'v001')")

    # compose-multi (many variants)
    multi_parser = subparsers.add_parser('compose-multi', help="Generate multiple variant edits")
    multi_parser.add_argument("-c", "--config", type=lambda p: Path(p).resolve(), required=True,
                              help="Path to YAML config file")
    multi_parser.add_argument("-p", "--project", type=str, required=True,
                              help="Project name")
    multi_parser.add_argument("--count", type=int, required=True,
                              help="How many variants to render")
    multi_parser.add_argument("--seed", type=int, default=0,
                              help="Base seed; each variant uses seed+index")
    multi_parser.add_argument("--tag-prefix", type=str, default="v",
                              help="Prefix for variant tags (e.g., 'v' -> v001.., 'seed' -> seed1..)")

    # pipeline (detect -> compose)
    pipe_parser = subparsers.add_parser('pipeline', help="Run detection then composition in one go")
    pipe_parser.add_argument("-c", "--config", type=lambda p: Path(p).resolve(), required=True,
                             help="Path to YAML config file")
    pipe_parser.add_argument("-p", "--project", type=str, required=True,
                             help="Project name")
    pipe_parser.add_argument("--skip-detect", action="store_true",
                             help="Skip detection (use existing timestamps)")
    pipe_parser.add_argument("--seed", type=int, default=None,
                             help="Random seed for deterministic composition")
    pipe_parser.add_argument("--tag", type=str, default=None,
                             help="Variant tag to suffix filenames")

    args = parser.parse_args()

    try:
        if args.command == 'init':
            print(f"\nLoading configuration from: {args.config}")
            config = load_config(args.config)
            base_dir = Path(config.get('base_dir', 'projects')).resolve()
            paths = init_project(base_dir, args.project, create_dummies=args.with_dummies)
            print(f"Project created at: {paths.project_root}")
            print(f" - Put your reference/beat video in: {paths.input_dir}")
            print(f" - Put your source clips in: {paths.sources_dir}")
            print("Then run detection and composition:\n"
                  f"  python main.py detect  --config {args.config} --project {args.project}\n"
                  f"  python main.py compose --config {args.config} --project {args.project}")

        elif args.command == 'detect':
            print(f"\nLoading configuration from: {args.config}")
            config = load_config(args.config)
            run_detect(config, args.project)

        elif args.command == 'compose':
            print(f"\nLoading configuration from: {args.config}")
            config = load_config(args.config)
            run_compose(config, args.project, seed=args.seed, tag=args.tag)

        elif args.command == 'compose-multi':
            print(f"\nLoading configuration from: {args.config}")
            config = load_config(args.config)
            outputs = []
            for i in range(1, args.count + 1):
                the_seed = args.seed + i
                tag = _variant_tag_from_index(args.tag_prefix, i) if args.tag_prefix else f"seed{the_seed}"
                print(f"\n[Variant {i}/{args.count}] seed={the_seed}, tag={tag}")
                out = run_compose(config, args.project, seed=the_seed, tag=tag)
                outputs.append(out)
            print("\nAll variants rendered:")
            for o in outputs:
                print(" -", o)

        elif args.command == 'pipeline':
            print(f"\nLoading configuration from: {args.config}")
            config = load_config(args.config)
            if not args.skip_detect:
                run_detect(config, args.project)
            run_compose(config, args.project, seed=args.seed, tag=args.tag)

    except FileNotFoundError as e:
        print(f"\nFile error: {str(e)}")
    except ValueError as e:
        print(f"\nConfiguration error: {str(e)}")
    except RuntimeError as e:
        print(f"\nProcessing error: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
