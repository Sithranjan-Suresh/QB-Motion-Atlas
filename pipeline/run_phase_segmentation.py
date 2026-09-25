"""V0 batch runner: heuristic phase segmentation over every seed clip's pose data.

Usage: python -m pipeline.run_phase_segmentation
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import cv2

from pipeline.landmark_filter import filter_low_confidence_landmarks, smooth_jitter
from pipeline.phase_segmentation import segment_heuristic
from pipeline.pose_extraction import FrameLandmarks

POSE_RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "pose_raw"
TRIMMED_DIR = Path(__file__).resolve().parent.parent / "data" / "trimmed"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "phase_boundaries_raw"


def _clip_fps(clip_id: str) -> float:
    qb_name, clip_name = clip_id.split("__", 1)
    video_path = TRIMMED_DIR / qb_name / f"{clip_name}.mp4"
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.release()
    return fps


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for pose_path in sorted(POSE_RAW_DIR.glob("*.json")):
        clip_id = pose_path.stem
        fps = _clip_fps(clip_id)

        data = json.loads(pose_path.read_text())
        frames = [FrameLandmarks.from_dict(d) for d in data]
        frames = filter_low_confidence_landmarks(frames)
        frames = smooth_jitter(frames)

        # Mirrors orchestrator.py's real-upload path (tasks 70-72): a real
        # clip can still have an unfillable gap (e.g. a trailing camera pan
        # filter_low_confidence_landmarks correctly refuses to extrapolate
        # across) -- found for real running this against actual re-downloaded
        # seed footage for the first time in this cloud session (2026-09-25),
        # where the original run_phase_segmentation.py had no such guard and
        # crashed outright on the first real gap it ever saw.
        if any(f.landmarks is None for f in frames):
            gaps = [f.frame_index for f in frames if f.landmarks is None]
            print(f"{clip_id}: skipped -- unfillable pose gap at frame(s) {gaps}")
            continue

        boundaries = segment_heuristic(frames, fps=fps)

        out_path = OUTPUT_DIR / f"{clip_id}.json"
        out_path.write_text(json.dumps([asdict(b) for b in boundaries]))
        print(f"{clip_id}: {[(b.phase_name, b.start_frame, b.end_frame) for b in boundaries]}")
        print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
