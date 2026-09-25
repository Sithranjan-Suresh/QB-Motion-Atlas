"""Unit tests for eval/discriminative_validity.py (task 129) -- synthetic
feature vectors with a plain Euclidean distance function."""

import math
import random

import pytest

from eval.discriminative_validity import compute_discriminative_validity
from eval.retrieval_accuracy import LabeledVector


def euclidean(a: dict[str, float], b: dict[str, float]) -> float:
    return math.sqrt(sum((a[k] - b[k]) ** 2 for k in a))


def _make_items(separation: float, noise: float, rng: random.Random) -> list[LabeledVector]:
    items = []
    for label, offset in [("qb_a", 0.0), ("qb_b", separation)]:
        for i in range(5):
            vector = {"x": offset + rng.uniform(-noise, noise), "y": offset + rng.uniform(-noise, noise)}
            items.append(LabeledVector(label=label, item_id=f"{label}_{i}", vector=vector))
    return items


def test_well_separated_clusters_give_high_ratio():
    items = _make_items(separation=100.0, noise=1.0, rng=random.Random(0))
    result = compute_discriminative_validity(items, euclidean)
    assert result.ratio > 5.0
    assert result.mean_inter_label_distance > result.mean_intra_label_distance


def test_overlapping_clusters_give_ratio_near_one():
    items = _make_items(separation=0.1, noise=10.0, rng=random.Random(0))
    result = compute_discriminative_validity(items, euclidean)
    assert 0.5 < result.ratio < 2.0


def test_separated_beats_overlapping():
    separated = compute_discriminative_validity(_make_items(100.0, 1.0, random.Random(0)), euclidean)
    overlapping = compute_discriminative_validity(_make_items(0.1, 10.0, random.Random(0)), euclidean)
    assert separated.ratio > overlapping.ratio


def test_raises_without_both_pair_types():
    single_label_items = [
        LabeledVector("qb_a", "1", {"x": 0.0}),
        LabeledVector("qb_a", "2", {"x": 1.0}),
    ]
    with pytest.raises(ValueError):
        compute_discriminative_validity(single_label_items, euclidean)
