import argparse
from pathlib import Path
from core.scene_detector import SceneDetector

def main():
    parser = argparse.ArgumentParser(
        description="Automated video editor with scene detection and processing"
    )
    parser.add_argument("input_video", help="Path to input video file")
    parser.add_argument("-o", "--output_video", help="Output video path", default=None)
    parser.add_argument("-t", "--threshold", type=float, default=0.9,
                       help="Histogram correlation threshold (default: 0.9)")
    parser.add_argument("-s", "--slow_factor", type=float, default=1.0,
                       help="Output video speed factor (default: 1.0)")
    
    args = parser.parse_args()
    
    detector = SceneDetector()
    timestamps = detector.process_video(
        input_path=args.input_video,
        output_path=args.output_video,
        threshold=args.threshold,
        slow_factor=args.slow_factor
    )
    
    print("\nDetection complete!")
    print(f" - Processed video saved to: {detector._get_output_path(args.input_video)}")
    print(f" - Timestamps saved to: inspiration/timestamp_yamls/{Path(args.input_video).stem}_timestamps.yml")

if __name__ == "__main__":
    main()