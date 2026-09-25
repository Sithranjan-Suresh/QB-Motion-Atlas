"""V0 hand-engineered similarity: weighted Euclidean distance over the
five-feature vectors from pipeline/features.py, per engineering_spec.md's
"interpretable features (weighted distance)" layer.

Feature scale note: the five features from docs/feature_definitions.md are
in mixed units (degrees vs. shoulder-width ratios), so raw Euclidean
distance would be dominated by whichever feature happens to have the
largest numeric range (the angle features, up to ~180). SCALE below divides
each feature by its expected typical range before differencing, so no
feature dominates just because of its units.

WEIGHTS and SCALE are V0 defaults (equal weighting once scaled) -- task 26
("sanity-check same-QB throws score closer than cross-QB throws") is meant
to empirically retune these against the real reference set, but that task
is currently blocked (this environment can't reach YouTube to source the
seed clips; see docs/research_log.md's 2026-09-25 entry). Revisit these
constants once task 26 actually runs.
"""

from __future__ import annotations

import math

FEATURE_ORDER = [
    "shoulder_rotation_angle_deg",
    "elbow_angle_deg",
    "stride_length",
    "hip_shoulder_separation_deg",
    "release_arm_velocity",
]

# Expected typical range per feature, used to bring mixed units onto a
# comparable scale before weighting. Angle features: ~180 (full range).
# Ratio features (already shoulder-width-normalized): ~1-2 is a typical
# throw's stride/velocity magnitude -- rough V0 placeholders, not measured.
SCALE = {
    "shoulder_rotation_angle_deg": 180.0,
    "elbow_angle_deg": 180.0,
    "stride_length": 1.5,
    "hip_shoulder_separation_deg": 90.0,
    "release_arm_velocity": 2.0,
}

# Equal weighting across all five features -- a deliberately neutral V0
# starting point given there's no labeled data yet to justify weighting
# any one feature more heavily than another.
DEFAULT_WEIGHTS = {name: 1.0 for name in FEATURE_ORDER}


def compare_features(
    vec_a: dict[str, float],
    vec_b: dict[str, float],
    weights: dict[str, float] | None = None,
) -> float:
    """Similarity score in (0, 1] between two feature dicts from
    `extract_phase_features` -- 1.0 means identical, decreasing toward 0
    as the scaled weighted Euclidean distance between them grows.
    """
    weights = weights if weights is not None else DEFAULT_WEIGHTS
    missing_a = set(FEATURE_ORDER) - vec_a.keys()
    missing_b = set(FEATURE_ORDER) - vec_b.keys()
    if missing_a or missing_b:
        raise ValueError(f"missing features: vec_a={missing_a or None}, vec_b={missing_b or None}")

    squared_terms = []
    for name in FEATURE_ORDER:
        scaled_diff = (vec_a[name] - vec_b[name]) / SCALE[name]
        squared_terms.append(weights[name] * scaled_diff**2)

    distance = math.sqrt(sum(squared_terms))
    return 1.0 / (1.0 + distance)
