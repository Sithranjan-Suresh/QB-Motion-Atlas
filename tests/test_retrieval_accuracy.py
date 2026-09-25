"""Unit tests for eval/retrieval_accuracy.py (task 127) -- synthetic
feature vectors, using the real pipeline/similarity.py::compare_features
as the similarity function (no real reference dataset exists yet)."""

import random

import pytest

from eval.retrieval_accuracy import LabeledVector, leave_one_out_retrieval_accuracy
from pipeline.similarity import compare_features

BASE = {
    "shoulder_rotation_angle_deg": 70.0,
    "elbow_angle_deg": 140.0,
    "stride_length": 0.9,
    "hip_shoulder_separation_deg": 48.0,
    "release_arm_velocity": 2.5,
}


def _make_items(separation: float, noise: float, rng: random.Random) -> list[LabeledVector]:
    items = []
    qb_offsets = {"josh_allen": 0.0, "patrick_mahomes": separation, "lamar_jackson": 2 * separation}
    for qb_name, offset in qb_offsets.items():
        for i in range(4):
            vector = {k: v + offset + rng.uniform(-noise, noise) for k, v in BASE.items()}
            items.append(LabeledVector(label=qb_name, item_id=f"{qb_name}_{i}", vector=vector))
    return items


def test_well_separated_clusters_get_perfect_retrieval():
    items = _make_items(separation=50.0, noise=1.0, rng=random.Random(0))
    accuracy = leave_one_out_retrieval_accuracy(items, compare_features, k_values=(1, 3))
    assert accuracy[1] == 1.0
    assert accuracy[3] == 1.0


def test_overlapping_clusters_score_worse_than_separated_ones():
    separated = _make_items(separation=50.0, noise=1.0, rng=random.Random(0))
    overlapping = _make_items(separation=0.5, noise=10.0, rng=random.Random(0))

    separated_acc = leave_one_out_retrieval_accuracy(separated, compare_features, k_values=(1,))
    overlapping_acc = leave_one_out_retrieval_accuracy(overlapping, compare_features, k_values=(1,))

    assert overlapping_acc[1] <= separated_acc[1]


def test_top_3_accuracy_is_at_least_top_1_accuracy():
    items = _make_items(separation=5.0, noise=8.0, rng=random.Random(2))
    accuracy = leave_one_out_retrieval_accuracy(items, compare_features, k_values=(1, 3))
    assert accuracy[3] >= accuracy[1]


def test_raises_with_fewer_than_two_items():
    with pytest.raises(ValueError):
        leave_one_out_retrieval_accuracy([LabeledVector("a", "1", BASE)], compare_features)
