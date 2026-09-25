"""Unit tests for pipeline/validation.py::validate_upload, per task 37 --
synthetic edge cases (no real seed-clip landmarks are used or needed here).
"""

import math

import pytest

from pipeline.pose_extraction import FrameLandmarks, Landmark
from pipeline.validation import (
    REJECTION_BAD_CAMERA_ANGLE,
    REJECTION_BODY_NOT_FULLY_VISIBLE,
    REJECTION_MULTIPLE_THROWS_DETECTED,
    REJECTION_NO_THROW_DETECTED,
    validate_upload,
)

N_FRAMES = 30
FPS = 30.0


def _lm(x: float, y: float, visibility: float = 1.0) -> Landmark:
    return Landmark(x=x, y=y, z=0.0, visibility=visibility, presence=1.0)


def _side_view_frame(frame_index: int, wrist_x: float, leg_visibility: float = 1.0) -> FrameLandmarks:
    """A near-side-view frame: narrow shoulder/hip span in x, full body visible."""
    landmarks = [_lm(0.5, 0.5) for _ in range(33)]
    landmarks[0] = _lm(0.46, 0.3)  # nose
    landmarks[11] = _lm(0.45, 0.4)  # left shoulder
    landmarks[12] = _lm(0.48, 0.4)  # right shoulder
    landmarks[23] = _lm(0.45, 0.6)  # left hip
    landmarks[24] = _lm(0.47, 0.6)  # right hip
    landmarks[25] = _lm(0.45, 0.75, leg_visibility)  # left knee
    landmarks[26] = _lm(0.46, 0.75, leg_visibility)  # right knee
    landmarks[16] = _lm(wrist_x, 0.5)  # throwing wrist
    return FrameLandmarks(frame_index=frame_index, timestamp_ms=int(frame_index * 1000 / FPS), landmarks=landmarks)


def _frontal_view_frame(frame_index: int, wrist_x: float) -> FrameLandmarks:
    """A frontal-view frame: wide shoulder/hip span in x -- should fail camera-angle check."""
    landmarks = [_lm(0.5, 0.5) for _ in range(33)]
    landmarks[0] = _lm(0.5, 0.3)
    landmarks[11] = _lm(0.3, 0.4)
    landmarks[12] = _lm(0.7, 0.4)
    landmarks[23] = _lm(0.35, 0.6)
    landmarks[24] = _lm(0.65, 0.6)
    landmarks[25] = _lm(0.35, 0.75)
    landmarks[26] = _lm(0.65, 0.75)
    landmarks[16] = _lm(wrist_x, 0.5)
    return FrameLandmarks(frame_index=frame_index, timestamp_ms=int(frame_index * 1000 / FPS), landmarks=landmarks)


def _one_throw_wrist_x(i: int) -> float:
    return 0.5 + 0.3 * math.sin(math.pi * i / N_FRAMES)


def _two_throws_wrist_x(i: int) -> float:
    return 0.5 + 0.3 * math.sin(2 * math.pi * i / N_FRAMES)


def test_happy_path_passes():
    frames = [_side_view_frame(i, _one_throw_wrist_x(i)) for i in range(N_FRAMES)]
    result = validate_upload(frames, FPS)
    assert result.status == "pass"
    assert result.rejection_reason is None


def test_no_throw_rejected():
    frames = [_side_view_frame(i, 0.5) for i in range(N_FRAMES)]  # wrist never moves
    result = validate_upload(frames, FPS)
    assert result.status == "reject"
    assert result.rejection_reason == REJECTION_NO_THROW_DETECTED


def test_multiple_throws_rejected():
    frames = [_side_view_frame(i, _two_throws_wrist_x(i)) for i in range(N_FRAMES)]
    result = validate_upload(frames, FPS)
    assert result.status == "reject"
    assert result.rejection_reason == REJECTION_MULTIPLE_THROWS_DETECTED


def test_bad_camera_angle_rejected():
    frames = [_frontal_view_frame(i, _one_throw_wrist_x(i)) for i in range(N_FRAMES)]
    result = validate_upload(frames, FPS)
    assert result.status == "reject"
    assert result.rejection_reason == REJECTION_BAD_CAMERA_ANGLE


def test_partial_occlusion_rejected():
    frames = [_side_view_frame(i, _one_throw_wrist_x(i), leg_visibility=0.1) for i in range(N_FRAMES)]
    result = validate_upload(frames, FPS)
    assert result.status == "reject"
    assert result.rejection_reason == REJECTION_BODY_NOT_FULLY_VISIBLE


def test_requires_landmarks_on_every_frame():
    frames = [_side_view_frame(i, _one_throw_wrist_x(i)) for i in range(N_FRAMES)]
    frames[5].landmarks = None
    with pytest.raises(ValueError):
        validate_upload(frames, FPS)
