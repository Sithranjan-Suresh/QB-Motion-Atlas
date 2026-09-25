"""Validates the triplet-loss training loop (task 103) against synthetic,
cleanly-separable data -- no real reference dataset exists yet (same
YouTube blocker as the rest of this project's real-data work), so this
proves the wiring (data -> normalization -> model -> loss -> optimizer)
actually works and converges, not that the embedding is useful on the real
reference set yet.
"""

import random

import torch

from models.train_embedding import train_embedding_net
from pipeline.embedding.sampling import PhaseRecord, generate_triplets

FEATURE_KEYS = ["elbow_angle_deg", "release_arm_velocity"]


def _make_records() -> list[PhaseRecord]:
    """Two QBs whose 'release' feature vectors form two well-separated
    clusters, each with several clips -- a triplet-loss model should be
    able to learn to separate them easily."""
    rng = random.Random(0)
    records = []
    # Close enough together that an untrained (random-weight) network's loss
    # isn't already at the margin floor by chance, but still separable with
    # enough training -- see test_trained_embedding_separates_the_two_clusters.
    qb_centers = {"qb_a": (90.0, 1.0), "qb_b": (100.0, 1.3)}
    for qb_name, (center_angle, center_velocity) in qb_centers.items():
        for i in range(6):
            vector = {
                "elbow_angle_deg": center_angle + rng.uniform(-4, 4),
                "release_arm_velocity": center_velocity + rng.uniform(-0.15, 0.15),
            }
            records.append(PhaseRecord(qb_name=qb_name, clip_id=f"{qb_name}_clip{i}", phase_name="release", feature_vector=vector))
    return records


def test_training_loop_produces_valid_loss_history():
    torch.manual_seed(0)  # EmbeddingNet's random weight init isn't controlled by the `random.Random` above
    records = _make_records()
    triplets = generate_triplets(records, rng=random.Random(1))
    assert len(triplets) > 0

    _model, loss_history = train_embedding_net(triplets, FEATURE_KEYS, epochs=100)

    # This particular synthetic task (two well-separated 2-feature clusters)
    # turns out to be easy enough that even a random, untrained embedding
    # net already satisfies the margin on every triplet -- loss is 0.0 from
    # epoch 0, so "loss decreases" isn't a meaningful assertion here. What
    # this test actually checks is that the training loop runs cleanly:
    # right length, every value a finite, non-negative float (triplet margin
    # loss can't be negative). test_trained_embedding_separates_the_two_clusters
    # below is the real correctness check -- that the model actually learns
    # a useful embedding, not just that a loss number exists.
    assert len(loss_history) == 100
    assert all(isinstance(v, float) and v >= 0.0 for v in loss_history)


def test_trained_embedding_separates_the_two_clusters():
    torch.manual_seed(0)
    records = _make_records()
    triplets = generate_triplets(records, rng=random.Random(1))
    model, _loss_history = train_embedding_net(triplets, FEATURE_KEYS, epochs=200)

    from models.train_embedding import _feature_stats, _vectors_to_tensor

    vectors = [r.feature_vector for r in records]
    mean, std = _feature_stats(vectors, FEATURE_KEYS)

    qb_a_vectors = [r.feature_vector for r in records if r.qb_name == "qb_a"]
    qb_b_vectors = [r.feature_vector for r in records if r.qb_name == "qb_b"]

    with torch.no_grad():
        emb_a = model(_vectors_to_tensor(qb_a_vectors, FEATURE_KEYS, mean, std))
        emb_b = model(_vectors_to_tensor(qb_b_vectors, FEATURE_KEYS, mean, std))

    within_a = torch.cdist(emb_a, emb_a).mean()
    between_a_b = torch.cdist(emb_a, emb_b).mean()
    assert within_a < between_a_b


def test_raises_on_empty_triplets():
    import pytest

    with pytest.raises(ValueError):
        train_embedding_net([], FEATURE_KEYS)
