"""Unit tests for pipeline/per_phase_similarity.py (task 116)."""

import pytest

from pipeline.per_phase_similarity import compare_phase_features, group_features_by_phase


def test_group_features_by_phase_splits_correctly():
    features = {
        "elbow_angle_deg": 140.0,
        "release_arm_velocity": 2.5,
        "stride_length": 0.9,
        "stride_duration_sec": 0.2,
        "hip_shoulder_separation_deg": 48.0,
    }
    grouped = group_features_by_phase(features)
    assert grouped["release"] == {"elbow_angle_deg": 140.0, "release_arm_velocity": 2.5}
    assert grouped["stride"] == {"stride_length": 0.9, "stride_duration_sec": 0.2}
    assert grouped["arm_cock"] == {"hip_shoulder_separation_deg": 48.0}


def test_group_features_by_phase_raises_on_unmapped_key():
    with pytest.raises(ValueError):
        group_features_by_phase({"made_up_feature": 1.0})


def test_compare_phase_features_identical_scores_one():
    vec = {"elbow_angle_deg": 140.0, "release_arm_velocity": 2.5}
    assert compare_phase_features(vec, dict(vec)) == 1.0


def test_compare_phase_features_different_scores_less_than_one():
    vec_a = {"elbow_angle_deg": 140.0, "release_arm_velocity": 2.5}
    vec_b = {"elbow_angle_deg": 90.0, "release_arm_velocity": 0.5}
    score = compare_phase_features(vec_a, vec_b)
    assert 0.0 < score < 1.0


def test_compare_phase_features_uses_only_shared_keys():
    vec_a = {"elbow_angle_deg": 140.0, "release_arm_velocity": 2.5}
    vec_b = {"elbow_angle_deg": 140.0}  # missing release_arm_velocity -- only shared key compared
    assert compare_phase_features(vec_a, vec_b) == 1.0


def test_compare_phase_features_raises_with_no_shared_keys():
    with pytest.raises(ValueError):
        compare_phase_features({"elbow_angle_deg": 140.0}, {"stride_length": 0.9})
