"""Triplet-loss training loop for the V2 embedding model (task 103).

Usage as a library: train_embedding_net(triplets, feature_keys). A CLI
entry point that trains on the real reference set doesn't exist yet since
there's no real reference feature data to train on in this environment
(docs/research_log.md's YouTube network-access blocker) -- see
tests/test_train_embedding.py for validation against synthetic triplets.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn, optim

from models.embedding_net import EMBEDDING_DIM, EmbeddingNet
from pipeline.embedding.sampling import Triplet

MARGIN = 0.2
DEFAULT_EPOCHS = 100
DEFAULT_LR = 1e-2


@dataclass
class TrainingResult:
    model: EmbeddingNet
    loss_history: list[float]
    feature_keys: list[str]
    mean: torch.Tensor
    std: torch.Tensor


def _feature_stats(vectors: list[dict[str, float]], feature_keys: list[str]) -> tuple[torch.Tensor, torch.Tensor]:
    """Per-feature mean/std across `vectors`, for z-score normalization --
    the six feature dimensions are on wildly different scales (angles in
    degrees vs. shoulder-width ratios, per feature_definitions.md), and an
    unnormalized MLP input makes the larger-magnitude features dominate the
    loss just from their units, the same problem similarity.py's SCALE
    constants solve for the hand-engineered distance layer.
    """
    stacked = torch.tensor([[v[k] for k in feature_keys] for v in vectors], dtype=torch.float32)
    mean = stacked.mean(dim=0)
    std = stacked.std(dim=0)
    std = torch.where(std == 0, torch.ones_like(std), std)  # avoid divide-by-zero on a constant feature
    return mean, std


def _vectors_to_tensor(
    vectors: list[dict[str, float]], feature_keys: list[str], mean: torch.Tensor, std: torch.Tensor
) -> torch.Tensor:
    raw = torch.tensor([[v[k] for k in feature_keys] for v in vectors], dtype=torch.float32)
    return (raw - mean) / std


def train_embedding_net(
    triplets: list[Triplet],
    feature_keys: list[str],
    epochs: int = DEFAULT_EPOCHS,
    lr: float = DEFAULT_LR,
    embedding_dim: int = EMBEDDING_DIM,
) -> TrainingResult:
    """Trains one EmbeddingNet on `triplets`. All triplets must be for the
    same phase (i.e. every feature_vector has exactly `feature_keys`) --
    one network per phase, per docs/embedding_methodology.md. Returns the
    trained model, the per-epoch loss history (for logging/plotting, task
    105), and the normalization stats (feature_keys, mean, std) needed to
    preprocess new feature vectors identically at inference time
    (models/export_onnx.py::save_checkpoint bundles these with the model).
    """
    if not triplets:
        raise ValueError("train_embedding_net requires at least one triplet")

    anchor_vectors = [t.anchor.feature_vector for t in triplets]
    positive_vectors = [t.positive.feature_vector for t in triplets]
    negative_vectors = [t.negative.feature_vector for t in triplets]

    mean, std = _feature_stats(anchor_vectors + positive_vectors + negative_vectors, feature_keys)
    anchors = _vectors_to_tensor(anchor_vectors, feature_keys, mean, std)
    positives = _vectors_to_tensor(positive_vectors, feature_keys, mean, std)
    negatives = _vectors_to_tensor(negative_vectors, feature_keys, mean, std)

    model = EmbeddingNet(input_dim=len(feature_keys), embedding_dim=embedding_dim)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.TripletMarginLoss(margin=MARGIN)

    loss_history = []
    for _epoch in range(epochs):
        optimizer.zero_grad()
        loss = loss_fn(model(anchors), model(positives), model(negatives))
        loss.backward()
        optimizer.step()
        loss_history.append(loss.item())

    return TrainingResult(model=model, loss_history=loss_history, feature_keys=feature_keys, mean=mean, std=std)
