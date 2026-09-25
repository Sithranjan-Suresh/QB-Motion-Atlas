"""Left-handed thrower detection and mirroring (task 41).

The rest of the pipeline (phase_segmentation.py, features.py,
validation.py) assumes a canonical right-handed-thrower orientation. This
module detects which arm is actually doing the throwing and mirrors a
left-handed clip's landmarks onto that same convention, so downstream code
never has to special-case handedness itself.
"""

from __future__ import annotations

import copy

from pipeline.pose_extraction import FrameLandmarks

LEFT_WRIST = 15
RIGHT_WRIST = 16

# MediaPipe Pose's left<->right landmark index pairs (nose, 0, is on the
# midline and has no pair). Swapped together with the x-flip when mirroring,
# so e.g. what was landmark 11 (left shoulder) becomes landmark 12 (right
# shoulder) in the mirrored, canonical orientation.
LEFT_RIGHT_PAIRS = [
    (1, 4), (2, 5), (3, 6),  # eye inner/eye/eye outer
    (7, 8),  # ear
    (9, 10),  # mouth
    (11, 12),  # shoulder
    (13, 14),  # elbow
    (15, 16),  # wrist
    (17, 18),  # pinky
    (19, 20),  # index
    (21, 22),  # thumb
    (23, 24),  # hip
    (25, 26),  # knee
    (27, 28),  # ankle
    (29, 30),  # heel
    (31, 32),  # foot index
]


def _total_motion(frames: list[FrameLandmarks], landmark_idx: int) -> float:
    """Sum of frame-to-frame displacement for one landmark across the whole clip --
    a proxy for "how much did this arm move," used to tell the throwing arm from
    the non-throwing arm without needing an explicit ball/release detector."""
    total = 0.0
    prev = None
    for frame in frames:
        lm = frame.landmarks[landmark_idx]
        if prev is not None:
            total += ((lm.x - prev[0]) ** 2 + (lm.y - prev[1]) ** 2) ** 0.5
        prev = (lm.x, lm.y)
    return total


def detect_handedness(frames: list[FrameLandmarks]) -> str:
    """Returns "right" or "left" -- whichever wrist moves more across the clip is
    assumed to be the throwing arm."""
    if any(f.landmarks is None for f in frames):
        raise ValueError("detect_handedness requires landmarks on every frame -- filter gaps first")

    left_motion = _total_motion(frames, LEFT_WRIST)
    right_motion = _total_motion(frames, RIGHT_WRIST)
    return "left" if left_motion > right_motion else "right"


def mirror_landmarks(frames: list[FrameLandmarks]) -> list[FrameLandmarks]:
    """Mirror every frame horizontally (x' = 1 - x) and swap each left/right landmark
    pair, so a left-handed thrower's clip maps onto the canonical right-handed
    convention the rest of the pipeline assumes. z, visibility, and presence are
    unchanged -- z is depth from the camera, not left-right position."""
    frames = copy.deepcopy(frames)
    for frame in frames:
        if frame.landmarks is None:
            continue
        for lm in frame.landmarks:
            lm.x = 1.0 - lm.x
        for left_idx, right_idx in LEFT_RIGHT_PAIRS:
            frame.landmarks[left_idx], frame.landmarks[right_idx] = (
                frame.landmarks[right_idx],
                frame.landmarks[left_idx],
            )
    return frames


def canonicalize_handedness(frames: list[FrameLandmarks]) -> tuple[list[FrameLandmarks], str]:
    """Detect handedness and mirror onto the canonical right-handed orientation if
    needed. Returns (canonical_frames, detected_handedness) -- the detected value is
    kept for provenance/debugging even though downstream code only ever sees the
    canonical (right-handed) orientation."""
    handedness = detect_handedness(frames)
    if handedness == "left":
        return mirror_landmarks(frames), handedness
    return frames, handedness
