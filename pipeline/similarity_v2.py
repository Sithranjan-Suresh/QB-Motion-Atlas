"""V2 combined similarity (task 110): hand-engineered feature distance (V0)
+ DTW whole-motion shape (V1) + learned embedding distance (V2), per
docs/similarity_methodology.md's V2 section.
"""

from __future__ import annotations

import math

from pipeline.similarity import compare_features
from pipeline.similarity_dtw import dtw_similarity


def embedding_similarity(embedding_a: list[float], embedding_b: list[float]) -> float:
    """Cosine similarity between two embeddings, mapped from its natural
    [-1, 1] range to (0, 1] so it's on the same scale as the other two
    similarity layers (both already (0, 1], via 1/(1+distance))."""
    if len(embedding_a) != len(embedding_b):
        raise ValueError("embeddings must have the same dimensionality")

    dot = sum(a * b for a, b in zip(embedding_a, embedding_b))
    norm_a = math.sqrt(sum(a * a for a in embedding_a))
    norm_b = math.sqrt(sum(b * b for b in embedding_b))
    if norm_a == 0 or norm_b == 0:
        raise ValueError("embedding_similarity requires non-zero-norm embeddings")

    cosine = dot / (norm_a * norm_b)
    return (cosine + 1.0) / 2.0


def combined_similarity_v2(
    feature_vec_a: dict[str, float],
    feature_vec_b: dict[str, float],
    trajectory_a: list[list[float]],
    trajectory_b: list[list[float]],
    embedding_a: list[float],
    embedding_b: list[float],
    feature_weight: float = 1 / 3,
    dtw_weight: float = 1 / 3,
    embedding_weight: float = 1 / 3,
) -> float:
    """Overall V2 similarity: equal-weighted V0 feature distance + V1 DTW +
    V2 embedding distance. Equal weighting is a placeholder pending task
    111's empirical tuning against real retrieval accuracy -- still blocked
    on the same YouTube network-access issue as the rest of this project's
    real-data work (docs/research_log.md), same caveat as
    similarity.py/similarity_dtw.py's existing placeholder weights.
    """
    feature_score = compare_features(feature_vec_a, feature_vec_b)
    dtw_score = dtw_similarity(trajectory_a, trajectory_b)
    embed_score = embedding_similarity(embedding_a, embedding_b)
    return feature_weight * feature_score + dtw_weight * dtw_score + embedding_weight * embed_score
