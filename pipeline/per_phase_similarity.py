"""Per-phase feature grouping and comparison (task 116) -- V2's "Per-Phase
Breakdown" feature needs a match/score/confidence *per phase*
(full_context.md: "your stride phase resembles Herbert, your release
resembles Stafford"), not just one overall score.
pipeline/similarity.py::compare_features() assumes the fixed V0 5-feature
set; this handles an arbitrary per-phase subset of
extract_phase_features()'s 17 keys instead.
"""

from __future__ import annotations

import math

from pipeline.coaching import FEATURE_METADATA
from pipeline.feature_scale import SCALE_ALL


def group_features_by_phase(features: dict[str, float]) -> dict[str, dict[str, float]]:
    """Splits a flat feature dict (extract_phase_features()'s output) into
    one sub-dict per phase, using coaching.py's FEATURE_METADATA mapping
    (the same table build_deltas() already relies on)."""
    grouped: dict[str, dict[str, float]] = {}
    for key, value in features.items():
        if key not in FEATURE_METADATA:
            raise ValueError(f"no phase mapping for feature '{key}' in FEATURE_METADATA")
        phase, _unit = FEATURE_METADATA[key]
        grouped.setdefault(phase, {})[key] = value
    return grouped


def compare_phase_features(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Similarity in (0, 1] between two per-phase feature dicts, scale-
    normalized per feature (via SCALE_ALL) and averaged over whichever
    features both sides share -- unlike similarity.py's compare_features(),
    this doesn't assume a fixed feature set, since different phases have
    different feature counts (feature_definitions.md).
    """
    shared_keys = sorted(set(vec_a) & set(vec_b))
    if not shared_keys:
        raise ValueError("no shared features between the two phase vectors to compare")

    squared_terms = [((vec_a[k] - vec_b[k]) / SCALE_ALL[k]) ** 2 for k in shared_keys]
    # Mean (not sum) so a phase with more features isn't penalized relative
    # to a phase with fewer just from accumulating more squared terms.
    distance = math.sqrt(sum(squared_terms) / len(squared_terms))
    return 1.0 / (1.0 + distance)
