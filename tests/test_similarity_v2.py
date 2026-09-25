"""Unit tests for pipeline/similarity_v2.py (tasks 110-111 wiring) --
synthetic feature vectors, trajectories, and embeddings."""

import pytest

from pipeline.similarity_v2 import combined_similarity_v2, embedding_similarity

FEATURES = {
    "shoulder_rotation_angle_deg": 70.0,
    "elbow_angle_deg": 140.0,
    "stride_length": 0.9,
    "hip_shoulder_separation_deg": 48.0,
    "release_arm_velocity": 2.5,
}
TRAJECTORY = [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]]


def test_embedding_similarity_identical_vectors():
    embedding = [0.5, 0.5, 0.5, 0.5]
    assert embedding_similarity(embedding, embedding) == pytest.approx(1.0)


def test_embedding_similarity_opposite_vectors():
    assert embedding_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(0.0)


def test_embedding_similarity_orthogonal_vectors():
    assert embedding_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.5)


def test_embedding_similarity_mismatched_dims_raises():
    with pytest.raises(ValueError):
        embedding_similarity([1.0, 0.0], [1.0, 0.0, 0.0])


def test_embedding_similarity_zero_norm_raises():
    with pytest.raises(ValueError):
        embedding_similarity([0.0, 0.0], [1.0, 0.0])


def test_combined_similarity_v2_identical_inputs_scores_one():
    score = combined_similarity_v2(
        FEATURES, FEATURES, TRAJECTORY, TRAJECTORY, [0.5, 0.5], [0.5, 0.5]
    )
    assert score == pytest.approx(1.0)


def test_combined_similarity_v2_respects_custom_weights():
    other_features = dict(FEATURES, elbow_angle_deg=90.0)
    # zero out everything except the embedding term, which is identical -> should score 1.0
    score = combined_similarity_v2(
        FEATURES,
        other_features,
        TRAJECTORY,
        [[10.0, 20.0], [20.0, 30.0], [30.0, 40.0]],
        [0.5, 0.5],
        [0.5, 0.5],
        feature_weight=0.0,
        dtw_weight=0.0,
        embedding_weight=1.0,
    )
    assert score == pytest.approx(1.0)
