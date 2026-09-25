"""V0 heuristic phase segmentation: velocity/angle thresholds on wrist and
shoulder trajectories, per docs/phase_definitions.md.

Assumes a right-handed thrower in canonical orientation (throwing arm =
right side, lead leg = left side) -- left-handed mirroring is a V1 concern
(task 41), not handled here.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.pose_extraction import FrameLandmarks

# MediaPipe Pose landmark indices used by the heuristic.
LEFT_ANKLE = 27  # lead leg for a right-handed thrower
RIGHT_SHOULDER = 12  # throwing side
RIGHT_WRIST = 16  # throwing side

PHASE_NAMES = ["load", "stride", "arm_cock", "acceleration", "release", "follow_through"]

# Empirically-reasonable V0 defaults on MediaPipe's normalized [0,1] coordinates.
# Re-tuned against hand-labeled gold boundaries in task 20 (V0) and task 43 (V1).
FORWARD_VELOCITY_ONSET = 0.15  # units/sec, lead-ankle x-velocity onset (Load -> Stride)
NEAR_ZERO_VELOCITY = 0.08  # units/sec, lead-ankle y-velocity settling (Stride -> Arm Cock)
SUSTAIN_FRAMES = 3  # consecutive frames a threshold crossing must hold to count


@dataclass
class PhaseBoundary:
    phase_name: str
    start_frame: int
    end_frame: int
    detection_method: str = "heuristic"
    # Confidence in this phase's start_frame being correctly located, in [0, 1] --
    # 1.0 for "load" (start=0 is the clip boundary, not a detected inflection).
    # Populated by `_inflection_confidence` (task 44) for later use in overall
    # confidence scoring (V1 "Confidence Scoring" section).
    confidence: float = 1.0


def _position(frames: list[FrameLandmarks], frame_idx: int, landmark_idx: int) -> tuple[float, float]:
    lm = frames[frame_idx].landmarks[landmark_idx]
    return lm.x, lm.y


def _velocity_series(frames: list[FrameLandmarks], landmark_idx: int, fps: float) -> list[tuple[float, float]]:
    """Per-frame (vx, vy) for one landmark; frame 0 gets (0, 0)."""
    velocities = [(0.0, 0.0)]
    for i in range(1, len(frames)):
        x0, y0 = _position(frames, i - 1, landmark_idx)
        x1, y1 = _position(frames, i, landmark_idx)
        velocities.append(((x1 - x0) * fps, (y1 - y0) * fps))
    return velocities


def _inflection_confidence(signal: list[float], frame_idx: int) -> float:
    """Confidence in [0, 1] that `frame_idx` is a real, sharp inflection point in
    `signal`, via the discrete second derivative (curvature) at that frame,
    normalized against the largest curvature found anywhere else in the same
    signal. A boundary detected at a sharp, unambiguous inflection scores near
    1.0; one detected on a flat or noisy stretch (where the curvature there is
    unremarkable next to the rest of the clip) scores low.
    """
    n = len(signal)
    if n < 3 or frame_idx <= 0 or frame_idx >= n - 1:
        return 0.0

    curvatures = [abs(signal[i + 1] - 2 * signal[i] + signal[i - 1]) for i in range(1, n - 1)]
    max_curvature = max(curvatures)
    if max_curvature == 0:
        return 0.0

    this_curvature = abs(signal[frame_idx + 1] - 2 * signal[frame_idx] + signal[frame_idx - 1])
    return this_curvature / max_curvature


def _first_sustained_crossing(values: list[float], threshold: float, sustain: int) -> int | None:
    """First index where `values` exceeds `threshold` for `sustain` consecutive frames."""
    run = 0
    for i, v in enumerate(values):
        if v > threshold:
            run += 1
            if run >= sustain:
                return i - sustain + 1
        else:
            run = 0
    return None


def segment_heuristic(frames: list[FrameLandmarks], fps: float) -> list[PhaseBoundary]:
    """Segment a single throw into the six phases from docs/phase_definitions.md.

    Requires every frame to have detected landmarks (run `filter_low_confidence_landmarks`
    first if the raw extraction has gaps).
    """
    if any(f.landmarks is None for f in frames):
        raise ValueError("segment_heuristic requires landmarks on every frame -- filter gaps first")

    n = len(frames)
    ankle_vel = _velocity_series(frames, LEFT_ANKLE, fps)
    wrist_vel = _velocity_series(frames, RIGHT_WRIST, fps)

    # 1. Load -> Stride: lead-ankle forward (x) velocity onset.
    ankle_vx = [abs(vx) for vx, _ in ankle_vel]
    stride_start = _first_sustained_crossing(ankle_vx, FORWARD_VELOCITY_ONSET, SUSTAIN_FRAMES) or 0

    # 2. Stride -> Arm Cock: lead-ankle vertical velocity settles back near zero
    #    (search only after the stride has begun, and only once it has risen above
    #    the settle threshold at least once, so we don't fire on frame-0 noise).
    ankle_vy = [abs(vy) for _, vy in ankle_vel]
    arm_cock_start = None
    was_moving = False
    for i in range(stride_start, n):
        if ankle_vy[i] > NEAR_ZERO_VELOCITY:
            was_moving = True
        elif was_moving:
            if all(ankle_vy[j] <= NEAR_ZERO_VELOCITY for j in range(i, min(i + SUSTAIN_FRAMES, n))):
                arm_cock_start = i
                break
    if arm_cock_start is None:
        arm_cock_start = min(stride_start + 1, n - 1)

    # 3. Arm Cock -> Acceleration (= Release): reversal point of wrist-relative-to-shoulder
    #    horizontal position -- the most negative (rearmost) point, i.e. the local minimum.
    relative_x = [
        frames[i].landmarks[RIGHT_WRIST].x - frames[i].landmarks[RIGHT_SHOULDER].x
        for i in range(n)
    ]
    search_start = arm_cock_start
    acceleration_start = min(
        range(search_start, n), key=lambda i: relative_x[i], default=search_start
    )

    # 4. Release: peak throwing-wrist speed between Arm Cock end and clip end.
    wrist_speed = [(vx**2 + vy**2) ** 0.5 for vx, vy in wrist_vel]
    release_frame = max(range(acceleration_start, n), key=lambda i: wrist_speed[i])

    # Guard against a degenerate ordering (can happen on a very short/noisy clip).
    stride_start = min(stride_start, n - 1)
    arm_cock_start = max(arm_cock_start, stride_start)
    acceleration_start = max(acceleration_start, arm_cock_start)
    release_frame = max(release_frame, acceleration_start)

    stride_confidence = _inflection_confidence(ankle_vx, stride_start)
    arm_cock_confidence = _inflection_confidence(ankle_vy, arm_cock_start)
    acceleration_confidence = _inflection_confidence(relative_x, acceleration_start)
    release_confidence = _inflection_confidence(wrist_speed, release_frame)

    boundaries = [
        PhaseBoundary("load", 0, stride_start, confidence=1.0),
        PhaseBoundary("stride", stride_start, arm_cock_start, confidence=stride_confidence),
        PhaseBoundary("arm_cock", arm_cock_start, acceleration_start, confidence=arm_cock_confidence),
        PhaseBoundary("acceleration", acceleration_start, release_frame, confidence=acceleration_confidence),
        PhaseBoundary("release", release_frame, release_frame, confidence=release_confidence),
        # follow_through's start is the same detected release_frame transition.
        PhaseBoundary("follow_through", release_frame, n - 1, confidence=release_confidence),
    ]
    return boundaries
