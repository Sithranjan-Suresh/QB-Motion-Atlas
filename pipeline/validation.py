"""Upload validation: computable rules from docs/validation_rules.md, run
against a user's uploaded video before it proceeds to phase segmentation.

Checked in order (camera angle -> full body -> single throw) since a bad
angle or missing body makes throw detection meaningless; the first failing
rule determines the rejection_reason.
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy.signal import find_peaks

from pipeline.landmark_filter import DEFAULT_VISIBILITY_THRESHOLD
from pipeline.phase_segmentation import _velocity_series
from pipeline.pose_extraction import FrameLandmarks

# MediaPipe Pose landmark indices used by validation.
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
RIGHT_WRIST = 16  # throwing side

REQUIRED_VISIBLE_JOINTS = [NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP, LEFT_KNEE, RIGHT_KNEE]

# V0/V1 placeholder thresholds -- untuned against real uploads, per
# docs/validation_rules.md's caveats.
CAMERA_ANGLE_MAX_RATIO = 0.5
JOINT_VISIBILITY_THRESHOLD = DEFAULT_VISIBILITY_THRESHOLD
FULL_BODY_MIN_FRAME_FRACTION = 0.9
SINGLE_THROW_PEAK_HEIGHT = 0.15  # units/sec, same order of magnitude as phase_segmentation's onset threshold
SINGLE_THROW_MIN_PEAK_DISTANCE_FRAMES = 10

REJECTION_BAD_CAMERA_ANGLE = "bad_camera_angle"
REJECTION_BODY_NOT_FULLY_VISIBLE = "body_not_fully_visible"
REJECTION_NO_THROW_DETECTED = "no_throw_detected"
REJECTION_MULTIPLE_THROWS_DETECTED = "multiple_throws_detected"


@dataclass
class ValidationResult:
    status: str  # "pass" | "reject"
    rejection_reason: str | None = None


def _xy(frame: FrameLandmarks, landmark_idx: int) -> tuple[float, float]:
    lm = frame.landmarks[landmark_idx]
    return lm.x, lm.y


def _midpoint(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2


def _check_camera_angle(frames: list[FrameLandmarks]) -> bool:
    ratios = []
    for frame in frames:
        shoulder_l, shoulder_r = _xy(frame, LEFT_SHOULDER), _xy(frame, RIGHT_SHOULDER)
        hip_l, hip_r = _xy(frame, LEFT_HIP), _xy(frame, RIGHT_HIP)
        shoulder_span_x = abs(shoulder_r[0] - shoulder_l[0])
        shoulder_mid = _midpoint(shoulder_l, shoulder_r)
        hip_mid = _midpoint(hip_l, hip_r)
        torso_length = ((shoulder_mid[0] - hip_mid[0]) ** 2 + (shoulder_mid[1] - hip_mid[1]) ** 2) ** 0.5
        if torso_length == 0:
            continue
        ratios.append(shoulder_span_x / torso_length)
    if not ratios:
        return False
    return (sum(ratios) / len(ratios)) <= CAMERA_ANGLE_MAX_RATIO


def _check_full_body_visible(frames: list[FrameLandmarks]) -> bool:
    visible_count = 0
    for frame in frames:
        if all(frame.landmarks[j].visibility >= JOINT_VISIBILITY_THRESHOLD for j in REQUIRED_VISIBLE_JOINTS):
            visible_count += 1
    return (visible_count / len(frames)) >= FULL_BODY_MIN_FRAME_FRACTION


def _count_throw_peaks(frames: list[FrameLandmarks], fps: float) -> int:
    wrist_vel = _velocity_series(frames, RIGHT_WRIST, fps)
    wrist_speed = [(vx**2 + vy**2) ** 0.5 for vx, vy in wrist_vel]
    peaks, _ = find_peaks(
        wrist_speed,
        height=SINGLE_THROW_PEAK_HEIGHT,
        distance=SINGLE_THROW_MIN_PEAK_DISTANCE_FRAMES,
    )
    return len(peaks)


def validate_upload(frames: list[FrameLandmarks], fps: float) -> ValidationResult:
    """Validate an uploaded clip's landmarks against docs/validation_rules.md.

    Requires every frame to have detected landmarks (run
    `filter_low_confidence_landmarks` first), same precondition as
    `segment_heuristic` and `extract_phase_features`.
    """
    if not frames or any(f.landmarks is None for f in frames):
        raise ValueError("validate_upload requires landmarks on every frame -- filter gaps first")

    if not _check_camera_angle(frames):
        return ValidationResult("reject", REJECTION_BAD_CAMERA_ANGLE)

    if not _check_full_body_visible(frames):
        return ValidationResult("reject", REJECTION_BODY_NOT_FULLY_VISIBLE)

    num_peaks = _count_throw_peaks(frames, fps)
    if num_peaks == 0:
        return ValidationResult("reject", REJECTION_NO_THROW_DETECTED)
    if num_peaks > 1:
        return ValidationResult("reject", REJECTION_MULTIPLE_THROWS_DETECTED)

    return ValidationResult("pass", None)
