"""Unit tests for pipeline/features.py (task 87) -- synthetic landmarks only."""

import pytest

from pipeline.features import extract_phase_features
from pipeline.phase_segmentation import segment_heuristic
from tests.conftest import make_throw_frames

FPS = 30.0
EXPECTED_KEYS = {
    "shoulder_rotation_angle_deg",
    "elbow_angle_deg",
    "stride_length",
    "hip_shoulder_separation_deg",
    "release_arm_velocity",
    "acceleration_rate",
    "follow_through_deceleration_rate",
} | {f"{phase}_duration_sec" for phase in ("load", "stride", "arm_cock", "acceleration", "follow_through")} | {
    f"{phase}_duration_frac" for phase in ("load", "stride", "arm_cock", "acceleration", "follow_through")
}


def _features(n: int = 60):
    frames = make_throw_frames(n=n, fps=FPS)
    boundaries = segment_heuristic(frames, FPS)
    return extract_phase_features(frames, boundaries, FPS), boundaries


def test_extract_phase_features_returns_all_expected_keys():
    features, _ = _features()
    assert set(features.keys()) == EXPECTED_KEYS


def test_angle_features_in_valid_ranges():
    features, _ = _features()
    assert -180 <= features["shoulder_rotation_angle_deg"] <= 180
    assert 0 <= features["elbow_angle_deg"] <= 180
    assert features["hip_shoulder_separation_deg"] >= 0


def test_normalized_features_are_nonnegative():
    features, _ = _features()
    assert features["stride_length"] >= 0
    assert features["release_arm_velocity"] >= 0


def test_duration_fractions_sum_to_one():
    features, _ = _features()
    frac_sum = sum(v for k, v in features.items() if k.endswith("_duration_frac"))
    assert frac_sum == pytest.approx(1.0)


def test_requires_landmarks_on_every_frame():
    frames = make_throw_frames(n=30, fps=FPS)
    boundaries = segment_heuristic(frames, FPS)
    frames[5].landmarks = None
    with pytest.raises(ValueError):
        extract_phase_features(frames, boundaries, FPS)
