"""Self-consistency metric (task 128): stability of a feature vector's
similarity score under small measurement noise, standing in for "repeat
runs" -- there's no way to physically re-record the same real throw
multiple times to test true repeat-run stability, so this simulates the
kind of small variation real repeat measurements would have (pose
jitter, slightly different frame sampling) instead.
"""

from __future__ import annotations

import random
from typing import Callable


def perturb_feature_vector(
    feature_vector: dict[str, float], noise_fraction: float, rng: random.Random
) -> dict[str, float]:
    """Perturbs each value by +/- noise_fraction * |value| (with a small
    absolute floor so a near-zero feature still gets *some* perturbation),
    simulating small measurement noise rather than a genuinely different
    throw."""
    perturbed = {}
    for key, value in feature_vector.items():
        scale = max(abs(value), 1e-3) * noise_fraction
        perturbed[key] = value + rng.uniform(-scale, scale)
    return perturbed


def self_consistency_score(
    feature_vector: dict[str, float],
    similarity_fn: Callable[[dict[str, float], dict[str, float]], float],
    noise_fraction: float = 0.05,
    num_trials: int = 20,
    rng: random.Random | None = None,
) -> float:
    """Average similarity between `feature_vector` and `num_trials`
    small-noise perturbations of itself. Close to 1.0 means the downstream
    similarity score is stable under small input variation; a low score
    means small measurement noise could flip a close match.
    """
    rng = rng or random.Random()
    scores = [
        similarity_fn(feature_vector, perturb_feature_vector(feature_vector, noise_fraction, rng))
        for _ in range(num_trials)
    ]
    return sum(scores) / len(scores)
