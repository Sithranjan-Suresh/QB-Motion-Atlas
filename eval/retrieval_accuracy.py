"""Leave-one-out top-k retrieval accuracy (task 127) -- formalizes the V0
sanity check (task 26: "same-QB throws score closer than cross-QB
throws") into a reusable, similarity-function-agnostic metric, so it can
be run against either the V0/V1 hand-engineered similarity
(pipeline/similarity.py::compare_features) or the V2 embedding distance
with the same code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class LabeledVector:
    label: str  # the identity being retrieved, e.g. qb_name
    item_id: str  # unique id for this item, e.g. clip_id or "clip_id/phase"
    vector: dict[str, float]


def leave_one_out_retrieval_accuracy(
    items: list[LabeledVector],
    similarity_fn: Callable[[dict[str, float], dict[str, float]], float],
    k_values: tuple[int, ...] = (1, 3),
) -> dict[int, float]:
    """For each item, scores it against every *other* item (never itself --
    that would trivially retrieve a perfect match) and checks whether an
    item sharing its label appears in the top k by similarity. Returns
    {k: accuracy} for each k in k_values.
    """
    if len(items) < 2:
        raise ValueError("need at least 2 items to compute leave-one-out retrieval accuracy")

    correct_counts = {k: 0 for k in k_values}

    for i, query in enumerate(items):
        candidates = items[:i] + items[i + 1 :]
        ranked = sorted(candidates, key=lambda c: similarity_fn(query.vector, c.vector), reverse=True)
        ranked_labels = [c.label for c in ranked]

        for k in k_values:
            if query.label in ranked_labels[:k]:
                correct_counts[k] += 1

    return {k: count / len(items) for k, count in correct_counts.items()}
