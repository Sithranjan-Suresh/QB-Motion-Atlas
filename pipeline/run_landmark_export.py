"""V0/V1 batch runner: export per-frame landmark sequences (task 123) for
every reference clip that has both pose data and phase boundaries already
computed -- same convention as run_features.py, and the same filtering it
needs to match exactly (both derive from the boundaries run_phase_segmentation.py
computed on filtered+smoothed frames).

Usage: python -m pipeline.run_landmark_export
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2

from pipeline.landmark_filter import filter_low_confidence_landmarks, smooth_jitter
from pipeline.landmark_overlay import scope_to_boundary_range, serialize_frames_for_overlay
from pipeline.phase_segmentation import PhaseBoundary
from pipeline.pose_extraction import FrameLandmarks

POSE_RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "pose_raw"
BOUNDARIES_DIR = Path(__file__).resolve().parent.parent / "data" / "phase_boundaries_raw"
TRIMMED_DIR = Path(__file__).resolve().parent.parent / "data" / "trimmed"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "landmarks_raw"


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
        frames = filter_low_confidence_landmarks(frames)
        frames = smooth_jitter(frames)
        if any(f.landmarks is None for f in frames):
            gaps = [f.frame_index for f in frames if f.landmarks is None]
            print(f"{clip_id}: skipped -- unfillable pose gap at frame(s) {gaps}")
            continue

        boundaries = [PhaseBoundary(**b) for b in json.loads(boundaries_path.read_text())]
        scoped = scope_to_boundary_range(frames, boundaries)
        serialized = serialize_frames_for_overlay(scoped)

        out_path = OUTPUT_DIR / f"{clip_id}.json"
        out_path.write_text(json.dumps({"fps": fps, "frames": serialized}))
        print(f"{clip_id}: wrote {out_path} ({len(serialized)} frames)")
        clip_count += 1

    if clip_count == 0:
        print(f"No clips processed -- {POSE_RAW_DIR} and/or {BOUNDARIES_DIR} are empty.")


if __name__ == "__main__":
    main()
