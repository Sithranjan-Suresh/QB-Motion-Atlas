"""V0 per-phase feature extraction, per docs/feature_definitions.md.

Assumes a right-handed thrower in canonical orientation, same convention as
pipeline/phase_segmentation.py -- left-handed mirroring is a V1 concern
(task 41), not handled here.
"""

from __future__ import annotations

import math

from pipeline.phase_segmentation import PhaseBoundary, _velocity_series
from pipeline.pose_extraction import FrameLandmarks

# MediaPipe Pose landmark indices used by feature extraction.
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12  # throwing side
RIGHT_ELBOW = 14  # throwing side
RIGHT_WRIST = 16  # throwing side
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_ANKLE = 27  # lead leg for a right-handed thrower


def _boundary(boundaries: list[PhaseBoundary], phase_name: str) -> PhaseBoundary:
    for b in boundaries:
        if b.phase_name == phase_name:
            return b
    raise ValueError(f"no '{phase_name}' boundary in {[b.phase_name for b in boundaries]}")


def _xy(frames: list[FrameLandmarks], frame_idx: int, landmark_idx: int) -> tuple[float, float]:
    lm = frames[frame_idx].landmarks[landmark_idx]
    return lm.x, lm.y


def _line_angle_deg(frames: list[FrameLandmarks], frame_idx: int, from_idx: int, to_idx: int) -> float:
    """Angle in degrees of the line from_idx -> to_idx relative to the image's horizontal axis."""
    x0, y0 = _xy(frames, frame_idx, from_idx)
    x1, y1 = _xy(frames, frame_idx, to_idx)
    return math.degrees(math.atan2(y1 - y0, x1 - x0))


def _shoulder_width(frames: list[FrameLandmarks], frame_idx: int) -> float:
    x0, y0 = _xy(frames, frame_idx, LEFT_SHOULDER)
    x1, y1 = _xy(frames, frame_idx, RIGHT_SHOULDER)
    return math.hypot(x1 - x0, y1 - y0)


def _mean_shoulder_width(frames: list[FrameLandmarks], start_frame: int, end_frame: int) -> float:
    """Body-scale reference unit, averaged over [start_frame, end_frame] to reduce single-frame noise."""
    widths = [_shoulder_width(frames, i) for i in range(start_frame, end_frame + 1)]
    mean_width = sum(widths) / len(widths)
    if mean_width == 0:
        raise ValueError(f"degenerate zero shoulder width over frames [{start_frame}, {end_frame}]")
    return mean_width


def _elbow_angle_deg(frames: list[FrameLandmarks], frame_idx: int) -> float:
    shoulder = _xy(frames, frame_idx, RIGHT_SHOULDER)
    elbow = _xy(frames, frame_idx, RIGHT_ELBOW)
    wrist = _xy(frames, frame_idx, RIGHT_WRIST)
    v1 = (shoulder[0] - elbow[0], shoulder[1] - elbow[1])
    v2 = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 == 0 or mag2 == 0:
        raise ValueError(f"degenerate elbow triangle at frame {frame_idx}")
    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_angle))


def extract_phase_features(frames: list[FrameLandmarks], boundaries: list[PhaseBoundary], fps: float) -> dict[str, float]:
    """Extract the V0 five-feature set plus the V1 per-phase timing additions
    from docs/feature_definitions.md.

    `stride_length` and `release_arm_velocity` are body-scale normalized
    (divided by mean shoulder width over the frames they span) so they're
    comparable across clips shot at different camera distances; the three
    angle-based features are scale-invariant already. `acceleration_rate`
    and `follow_through_deceleration_rate` are normalized the same way.
    Every `{phase}_duration_sec` also has a `{phase}_duration_frac` sibling,
    normalized against the clip's total throw duration (task 47).

    Requires every frame to have detected landmarks (run
    `filter_low_confidence_landmarks` first if the raw extraction has gaps),
    same precondition as `segment_heuristic`.
    """
    if any(f.landmarks is None for f in frames):
        raise ValueError("extract_phase_features requires landmarks on every frame -- filter gaps first")

    release_frame = _boundary(boundaries, "release").start_frame

    shoulder_rotation_angle_deg = _line_angle_deg(frames, release_frame, LEFT_SHOULDER, RIGHT_SHOULDER)
    elbow_angle_deg = _elbow_angle_deg(frames, release_frame)

    stride = _boundary(boundaries, "stride")
    ankle_start = _xy(frames, stride.start_frame, LEFT_ANKLE)
    ankle_end = _xy(frames, stride.end_frame, LEFT_ANKLE)
    stride_length_raw = math.hypot(ankle_end[0] - ankle_start[0], ankle_end[1] - ankle_start[1])
    stride_length = stride_length_raw / _mean_shoulder_width(frames, stride.start_frame, stride.end_frame)

    arm_cock = _boundary(boundaries, "arm_cock")
    hip_shoulder_separation_deg = max(
        abs(
            _line_angle_deg(frames, t, LEFT_SHOULDER, RIGHT_SHOULDER)
            - _line_angle_deg(frames, t, LEFT_HIP, RIGHT_HIP)
        )
        for t in range(arm_cock.start_frame, arm_cock.end_frame + 1)
    )

    wrist_vel = _velocity_series(frames, RIGHT_WRIST, fps)
    wrist_speed = [(vx**2 + vy**2) ** 0.5 for vx, vy in wrist_vel]
    release_vx, release_vy = wrist_vel[release_frame]
    release_arm_velocity_raw = math.hypot(release_vx, release_vy)
    release_arm_velocity = release_arm_velocity_raw / _mean_shoulder_width(frames, release_frame, release_frame)

    features = {
        "shoulder_rotation_angle_deg": shoulder_rotation_angle_deg,
        "elbow_angle_deg": elbow_angle_deg,
        "stride_length": stride_length,
        "hip_shoulder_separation_deg": hip_shoulder_separation_deg,
        "release_arm_velocity": release_arm_velocity,
    }

    # V1 (task 46): per-phase timing, covering all six phases -- release is a
    # single frame by definition, so it has no duration.
    n = len(frames)
    total_duration_sec = (n - 1) / fps
    for phase_name in ("load", "stride", "arm_cock", "acceleration", "follow_through"):
        boundary = _boundary(boundaries, phase_name)
        duration_sec = (boundary.end_frame - boundary.start_frame) / fps
        features[f"{phase_name}_duration_sec"] = duration_sec
        # V1 (task 47): timing normalization relative to total throw duration.
        features[f"{phase_name}_duration_frac"] = duration_sec / total_duration_sec if total_duration_sec else 0.0

    acceleration = _boundary(boundaries, "acceleration")
    acceleration_duration_sec = features["acceleration_duration_sec"]
    if acceleration_duration_sec > 0:
        acceleration_speed_delta = wrist_speed[release_frame] - wrist_speed[acceleration.start_frame]
        features["acceleration_rate"] = (
            acceleration_speed_delta / acceleration_duration_sec
        ) / _mean_shoulder_width(frames, acceleration.start_frame, release_frame)
    else:
        features["acceleration_rate"] = 0.0

    follow_through = _boundary(boundaries, "follow_through")
    follow_through_duration_sec = features["follow_through_duration_sec"]
    if follow_through_duration_sec > 0:
        follow_through_speed_delta = wrist_speed[release_frame] - wrist_speed[n - 1]
        features["follow_through_deceleration_rate"] = (
            follow_through_speed_delta / follow_through_duration_sec
        ) / _mean_shoulder_width(frames, release_frame, n - 1)
    else:
        features["follow_through_deceleration_rate"] = 0.0

    return features
