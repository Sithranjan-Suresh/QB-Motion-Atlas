"""V0 batch runner: extract pose for every trimmed seed clip and save raw JSON.

Usage: python -m pipeline.run_pose_extraction
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.pose_extraction import extract_pose

TRIMMED_DIR = Path(__file__).resolve().parent.parent / "data" / "trimmed"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "pose_raw"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for qb_dir in sorted(TRIMMED_DIR.iterdir()):
        if not qb_dir.is_dir():
            continue
        for clip_path in sorted(qb_dir.glob("*.mp4")):
            clip_id = f"{qb_dir.name}__{clip_path.stem}"
            print(f"Extracting pose: {clip_id}")

            frames = extract_pose(clip_path)
            detected = sum(1 for f in frames if f.landmarks is not None)
            print(f"  {detected}/{len(frames)} frames with a detected pose")

            out_path = OUTPUT_DIR / f"{clip_id}.json"
            out_path.write_text(json.dumps([f.to_dict() for f in frames]))
            print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
