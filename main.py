import argparse
from pathlib import Path
from core.detection.scene_detector import SceneDetector
from utils.config.config_utils import load_config

def main():
    parser = argparse.ArgumentParser(
        description="Vibe Video Editor - Automated Scene Detection",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Detection command
    detect_parser = subparsers.add_parser('detect', 
        help="Analyze video for scene transitions")
    detect_parser.add_argument(
        "-c", "--config",
        type=lambda p: Path(p).resolve(),
        required=True,
        help="Path to YAML config file"
    )

    args = parser.parse_args()

    try:
        if args.command == 'detect':
            print(f"\nLoading configuration from: {args.config}")
            config = load_config(args.config)
            
            print("\nInitializing scene detector...")
            detector = SceneDetector(config)
            
            print("Starting video analysis...")
            detector.process_video()
            
            print("\nDetection completed successfully!")
            print(f" - Detected events: {len(detector.get_event_timestamps)}")
            print(f" - Output video: {detector.get_output_path}")
            print(f" - Timestamps file: {detector.get_timestamps_path}")

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