"""V0/V1 batch runner: extract per-phase features for every clip with both
pose data and phase boundaries already computed.

Usage: python -m pipeline.run_features

Note (2026-09-25): not runnable in the current cloud session -- data/pose_raw
and data/phase_boundaries_raw are empty here because this environment's
network policy blocks re-downloading the seed clips from YouTube (task 19-23
blocker, see docs/research_log.md). Written now so the plumbing is ready for
whenever real pose/boundary data exists again, same convention as
run_pose_extraction.py and run_phase_segmentation.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2

from pipeline.features import extract_phase_features
from pipeline.phase_segmentation import PhaseBoundary
from pipeline.pose_extraction import FrameLandmarks

POSE_RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "pose_raw"
BOUNDARIES_DIR = Path(__file__).resolve().parent.parent / "data" / "phase_boundaries_raw"
TRIMMED_DIR = Path(__file__).resolve().parent.parent / "data" / "trimmed"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "features_raw"


def _clip_fps(clip_id: str) -> float:
    qb_name, clip_name = clip_id.split("__", 1)
    video_path = TRIMMED_DIR / qb_name / f"{clip_name}.mp4"
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.release()
    return fps


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    clip_count = 0
    for pose_path in sorted(POSE_RAW_DIR.glob("*.json")):
        clip_id = pose_path.stem
        boundaries_path = BOUNDARIES_DIR / f"{clip_id}.json"
        if not boundaries_path.exists():
            print(f"{clip_id}: skipped, no phase boundaries found at {boundaries_path}")
            continue

        fps = _clip_fps(clip_id)
        frames = [FrameLandmarks.from_dict(d) for d in json.loads(pose_path.read_text())]
        boundaries = [PhaseBoundary(**b) for b in json.loads(boundaries_path.read_text())]

        features = extract_phase_features(frames, boundaries, fps)

        out_path = OUTPUT_DIR / f"{clip_id}.json"
        out_path.write_text(json.dumps(features, indent=2))
        print(f"{clip_id}: wrote {out_path}")
        clip_count += 1

    if clip_count == 0:
        print(f"No clips processed -- {POSE_RAW_DIR} and/or {BOUNDARIES_DIR} are empty.")


if __name__ == "__main__":
    main()
