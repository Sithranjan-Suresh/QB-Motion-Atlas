"""Coaching-note generation (V1 "Coaching Notes" section): turns feature
deltas between a user's throw and the matched reference QB into short,
numeric-grounded coaching sentences. See docs/coaching_schema.md and
docs/coaching_prompt.md for the schema and the LLM's fixed system prompt.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Callable

VALID_PHASES = {"load", "stride", "arm_cock", "acceleration", "release", "follow_through"}
MAX_NOTE_LENGTH = 200

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


def _format_delta_sentence(delta: Delta) -> str:
    if delta.delta > 0:
        direction = "higher than"
    elif delta.delta < 0:
        direction = "lower than"
    else:
        direction = "the same as"
    phase_label = delta.phase.replace("_", " ")
    metric_label = delta.metric_name.replace("_", " ")
    return f"In your {phase_label} phase, your {metric_label} was {abs(delta.delta):.2f} {delta.unit} {direction} the reference."


def fallback_coaching_notes(deltas: list[Delta]) -> list[dict]:
    """Deterministic, template-based coaching notes -- no LLM involved (task
    61). Used whenever the LLM call fails or its output doesn't pass
    validation (task 60), so a result is never blocked on the LLM being
    available or well-behaved. One note per phase present in `deltas`, built
    from the first delta recorded for that phase (deltas are already sorted
    by (phase, metric_name) in build_deltas(), so this is deterministic).
    """
    notes = []
    seen_phases = set()
    for delta in deltas:
        if delta.phase in seen_phases:
            continue
        seen_phases.add(delta.phase)
        notes.append({"phase": delta.phase, "note": _format_delta_sentence(delta)})
    return notes


class LLMOutputInvalid(Exception):
    """Raised when an LLM response doesn't conform to docs/coaching_prompt.md's
    output schema -- caught by generate_coaching_notes() to trigger the
    rule-based fallback, never surfaced to the caller directly."""


def _validate_llm_output(raw_response: str, allowed_phases: set[str]) -> list[dict]:
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as e:
        raise LLMOutputInvalid(f"response is not valid JSON: {e}") from e

    if not isinstance(parsed, list) or not parsed:
        raise LLMOutputInvalid("expected a non-empty JSON list")

    for item in parsed:
        if not isinstance(item, dict) or set(item.keys()) != {"phase", "note"}:
            raise LLMOutputInvalid(f"item has the wrong shape: {item!r}")
        if item["phase"] not in allowed_phases:
            raise LLMOutputInvalid(f"phase '{item['phase']}' was not in the input deltas")
        note = item["note"]
        if not isinstance(note, str) or not note.strip():
            raise LLMOutputInvalid("note must be a non-empty string")
        if len(note) > MAX_NOTE_LENGTH:
            raise LLMOutputInvalid(f"note exceeds {MAX_NOTE_LENGTH} characters")
        if not any(ch.isdigit() for ch in note):
            raise LLMOutputInvalid("note doesn't appear to reference a number")

    return parsed


def generate_coaching_notes(deltas: list[Delta], llm_client: Callable[[list[dict]], str]) -> list[dict]:
    """Task 60: call `llm_client` (any callable taking the serialized Delta
    list and returning the raw response string -- see docs/coaching_prompt.md
    for why this is injectable rather than a hardcoded SDK call) and validate
    its output against the fixed schema. Falls back to
    fallback_coaching_notes() on any error -- a bad/unreachable LLM call, a
    non-JSON response, or output that fails schema validation -- so a result
    is never blocked on the LLM behaving.
    """
    if not deltas:
        return []

    allowed_phases = {d.phase for d in deltas}
    payload = [asdict(d) for d in deltas]

    try:
        raw_response = llm_client(payload)
        return _validate_llm_output(raw_response, allowed_phases)
    except Exception:
        return fallback_coaching_notes(deltas)
