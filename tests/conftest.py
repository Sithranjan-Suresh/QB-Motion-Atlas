"""Shared synthetic-data helpers for pipeline unit tests. No real seed-clip
footage is used or needed -- see docs/research_log.md's 2026-09-25 entry on
why (YouTube network-access blocker in this environment).
"""

from __future__ import annotations

import math

from pipeline.pose_extraction import FrameLandmarks, Landmark


def make_landmark(x: float, y: float, z: float = 0.0, visibility: float = 1.0) -> Landmark:
    return Landmark(x=x, y=y, z=z, visibility=visibility, presence=1.0)


def make_throw_frames(n: int = 30, fps: float = 30.0) -> list[FrameLandmarks]:
    """A synthetic clip with a plausible single throwing motion: the lead
    ankle steps forward early, shoulders/hips rotate slightly over time, and
    the throwing wrist moves along a smooth S-curve (a logistic, not a raw
    sine) so its *speed* -- not just its position -- peaks well inside the
    clip (~65% through) rather than at the very first/last frame. A sine's
    velocity peaks at the sine's zero-crossings, i.e. right at the clip's
    edges, which collides with segment_heuristic's edge-of-clip confidence
    guard -- this shape avoids that while still giving find_peaks() exactly
    one clean speed peak. Same construction reused across
    tests/test_validation.py, tests/test_coaching.py, tests/test_api.py, and
    tests/test_phase_segmentation.py.
    """
    frames = []
    for i in range(n):
        t = i / (n - 1)
        landmarks = [make_landmark(0.5, 0.5) for _ in range(33)]
        landmarks[0] = make_landmark(0.46, 0.3)  # nose
        landmarks[11] = make_landmark(0.45, 0.4)  # left shoulder
        landmarks[12] = make_landmark(0.55 - 0.1 * t, 0.4 + 0.1 * t)  # right shoulder
        landmarks[14] = make_landmark(0.6, 0.45)  # right elbow
        landmarks[15] = make_landmark(0.4, 0.5)  # left wrist (stationary -> right-handed)
        wrist_x = 0.4 + 0.15 * (1 + math.tanh(6 * (t - 0.65)))
        landmarks[16] = make_landmark(wrist_x, 0.5)  # right wrist
        landmarks[23] = make_landmark(0.45, 0.6)  # left hip
        landmarks[24] = make_landmark(0.47, 0.6)  # right hip
        landmarks[25] = make_landmark(0.45, 0.75)  # left knee
        landmarks[26] = make_landmark(0.46, 0.75)  # right knee
        landmarks[27] = make_landmark(0.4 + 0.15 * min(t / 0.4, 1.0), 0.75)  # left ankle
        frames.append(FrameLandmarks(frame_index=i, timestamp_ms=int(i * 1000 / fps), landmarks=landmarks))
    return frames
