"""Coaching-note generation (V1 "Coaching Notes" section): turns feature
deltas between a user's throw and the matched reference QB into short,
numeric-grounded coaching sentences. See docs/coaching_schema.md and
docs/coaching_prompt.md for the schema and the LLM's fixed system prompt.
"""

from __future__ import annotations

from dataclasses import dataclass

# Feature key -> (phase, unit), per docs/coaching_schema.md. Every key
# extract_phase_features() can return must be listed here -- build_deltas()
# raises on anything missing rather than guessing a phase/unit.
FEATURE_METADATA: dict[str, tuple[str, str]] = {
    "shoulder_rotation_angle_deg": ("release", "deg"),
    "elbow_angle_deg": ("release", "deg"),
    "release_arm_velocity": ("release", "shoulder_widths/sec"),
    "stride_length": ("stride", "shoulder_widths"),
    "hip_shoulder_separation_deg": ("arm_cock", "deg"),
    "acceleration_rate": ("acceleration", "shoulder_widths/sec^2"),
    "follow_through_deceleration_rate": ("follow_through", "shoulder_widths/sec^2"),
}
for _phase in ("load", "stride", "arm_cock", "acceleration", "follow_through"):
    FEATURE_METADATA[f"{_phase}_duration_sec"] = (_phase, "sec")
    FEATURE_METADATA[f"{_phase}_duration_frac"] = (_phase, "fraction")


@dataclass
class Delta:
    phase: str
    metric_name: str
    user_value: float
    reference_value: float
    delta: float
    unit: str


def build_deltas(user_features: dict[str, float], matched_qb_features: dict[str, float]) -> list[Delta]:
    """One Delta per metric present in both feature dicts, per
    docs/coaching_schema.md. Raises on a metric key with no entry in
    FEATURE_METADATA, rather than silently guessing its phase/unit.
    """
    shared_metrics = user_features.keys() & matched_qb_features.keys()

    deltas = []
    for metric_name in shared_metrics:
        if metric_name not in FEATURE_METADATA:
            raise ValueError(f"no phase/unit mapping for feature '{metric_name}' in FEATURE_METADATA")
        phase, unit = FEATURE_METADATA[metric_name]
        user_value = user_features[metric_name]
        reference_value = matched_qb_features[metric_name]
        deltas.append(
            Delta(
                phase=phase,
                metric_name=metric_name,
                user_value=user_value,
                reference_value=reference_value,
                delta=user_value - reference_value,
                unit=unit,
            )
        )

    deltas.sort(key=lambda d: (d.phase, d.metric_name))
    return deltas
