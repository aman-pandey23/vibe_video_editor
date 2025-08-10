import argparse
import cv2
import numpy as np
from pathlib import Path

def make_clip(path, color_bgr, duration=3, size=(1280, 720), label=""):
    fps = 30
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(path), fourcc, fps, size)
    for _ in range(int(fps * duration)):
        frame = np.full((size[1], size[0], 3), color_bgr, dtype=np.uint8)
        if label:
            cv2.putText(frame, label, (50, size[1] // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4, cv2.LINE_AA)
        out.write(frame)
    out.release()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--project", required=True, help="Project name (projects/<name>/sources)")
    ap.add_argument("--base_dir", default="projects", help="Base projects directory")
    args = ap.parse_args()

    out_dir = Path(args.base_dir) / args.project / "sources"
    out_dir.mkdir(parents=True, exist_ok=True)

    make_clip(out_dir / "dummy_1.mp4", (0, 0, 255), 4, label="DUMMY 1")
    make_clip(out_dir / "dummy_2.mp4", (0, 255, 0), 5, label="DUMMY 2")
    make_clip(out_dir / "dummy_3.mp4", (255, 0, 0), 6, label="DUMMY 3")
    print(f"Dummy videos generated in {out_dir}/")

if __name__ == "__main__":
    main()
