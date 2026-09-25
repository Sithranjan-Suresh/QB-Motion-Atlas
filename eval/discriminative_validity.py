"""Discriminative-validity metric (task 129): inter-QB vs. intra-QB
distance in a given vector space -- feature space now, embedding space
once one exists (task 111's "re-run... confirm improvement over the
V1-only baseline" needs exactly this comparison run twice, before/after).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from eval.retrieval_accuracy import LabeledVector


@dataclass(frozen=True)
class DiscriminativeValidityResult:
    mean_intra_label_distance: float
    mean_inter_label_distance: float
    ratio: float  # inter / intra; > 1.0 means different-label items are farther apart than same-label items


def compute_discriminative_validity(
    items: list[LabeledVector], distance_fn: Callable[[dict[str, float], dict[str, float]], float]
) -> DiscriminativeValidityResult:
    """Good discriminative validity means same-label (same-QB) items cluster
    more tightly (low intra-label distance) than different-label items are
    spread apart (high inter-label distance) -- i.e. ratio > 1.0, and the
    higher the better.
    """
    intra_distances: list[float] = []
    inter_distances: list[float] = []

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            distance = distance_fn(items[i].vector, items[j].vector)
            if items[i].label == items[j].label:
                intra_distances.append(distance)
            else:
                inter_distances.append(distance)

    if not intra_distances or not inter_distances:
        raise ValueError(
            "need at least one same-label pair and one different-label pair to compute discriminative validity"
        )

    mean_intra = sum(intra_distances) / len(intra_distances)
    mean_inter = sum(inter_distances) / len(inter_distances)
    ratio = mean_inter / mean_intra if mean_intra > 0 else float("inf")

    return DiscriminativeValidityResult(mean_intra, mean_inter, ratio)
