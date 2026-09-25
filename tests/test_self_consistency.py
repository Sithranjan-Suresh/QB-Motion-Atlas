"""Unit tests for eval/self_consistency.py (task 128) -- synthetic feature
vectors, using the real pipeline/similarity.py::compare_features."""

import random

from eval.self_consistency import perturb_feature_vector, self_consistency_score
from pipeline.similarity import compare_features

BASE = {
    "shoulder_rotation_angle_deg": 70.0,
    "elbow_angle_deg": 140.0,
    "stride_length": 0.9,
    "hip_shoulder_separation_deg": 48.0,
    "release_arm_velocity": 2.5,
}


def test_zero_noise_gives_perfect_consistency():
    score = self_consistency_score(BASE, compare_features, noise_fraction=0.0, num_trials=5, rng=random.Random(0))
    assert score == 1.0


def test_small_noise_gives_high_consistency():
    score = self_consistency_score(BASE, compare_features, noise_fraction=0.01, num_trials=30, rng=random.Random(0))
    assert score > 0.9


def test_large_noise_gives_lower_consistency_than_small_noise():
    small_noise_score = self_consistency_score(
        BASE, compare_features, noise_fraction=0.01, num_trials=30, rng=random.Random(0)
    )
    large_noise_score = self_consistency_score(
        BASE, compare_features, noise_fraction=0.5, num_trials=30, rng=random.Random(0)
    )
    assert large_noise_score < small_noise_score


def test_perturb_feature_vector_keeps_all_keys():
    perturbed = perturb_feature_vector(BASE, noise_fraction=0.1, rng=random.Random(0))
    assert set(perturbed.keys()) == set(BASE.keys())
    assert perturbed != BASE  # actually perturbed, not a no-op


def test_perturb_handles_near_zero_values():
    vector = {"x": 0.0}
    perturbed = perturb_feature_vector(vector, noise_fraction=0.1, rng=random.Random(0))
    # should still get *some* perturbation via the absolute floor, not stay exactly 0.0
    assert perturbed["x"] != 0.0
