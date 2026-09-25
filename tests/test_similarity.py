"""Unit tests for pipeline/similarity.py (task 87) -- synthetic feature
vectors only."""

import pytest

from pipeline.similarity import DEFAULT_WEIGHTS, FEATURE_ORDER, compare_features

BASE_VECTOR = {
    "shoulder_rotation_angle_deg": 70.0,
    "elbow_angle_deg": 140.0,
    "stride_length": 0.9,
    "hip_shoulder_separation_deg": 48.0,
    "release_arm_velocity": 2.5,
}


def test_identical_vectors_score_one():
    assert compare_features(BASE_VECTOR, dict(BASE_VECTOR)) == 1.0


def test_different_vectors_score_less_than_one():
    other = dict(BASE_VECTOR, elbow_angle_deg=90.0, release_arm_velocity=0.5)
    score = compare_features(BASE_VECTOR, other)
    assert 0.0 < score < 1.0


def test_more_different_vectors_score_lower():
    slightly_off = dict(BASE_VECTOR, elbow_angle_deg=135.0)
    very_off = dict(BASE_VECTOR, elbow_angle_deg=20.0, shoulder_rotation_angle_deg=-90.0)

    score_slight = compare_features(BASE_VECTOR, slightly_off)
    score_very = compare_features(BASE_VECTOR, very_off)
    assert score_very < score_slight < 1.0


def test_symmetric():
    other = dict(BASE_VECTOR, elbow_angle_deg=100.0)
    assert compare_features(BASE_VECTOR, other) == pytest.approx(compare_features(other, BASE_VECTOR))


def test_missing_feature_raises():
    incomplete = {k: v for k, v in BASE_VECTOR.items() if k != "elbow_angle_deg"}
    with pytest.raises(ValueError):
        compare_features(BASE_VECTOR, incomplete)


def test_custom_weights_change_the_score():
    other = dict(BASE_VECTOR, elbow_angle_deg=90.0)
    zero_weight_on_elbow = {name: (0.0 if name == "elbow_angle_deg" else w) for name, w in DEFAULT_WEIGHTS.items()}

    default_score = compare_features(BASE_VECTOR, other)
    reweighted_score = compare_features(BASE_VECTOR, other, weights=zero_weight_on_elbow)

    # ignoring the one feature that actually differs should score higher (more similar)
    assert reweighted_score > default_score
    assert reweighted_score == 1.0


def test_feature_order_matches_default_weights_keys():
    assert set(FEATURE_ORDER) == set(DEFAULT_WEIGHTS.keys())
