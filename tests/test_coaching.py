"""Unit tests for pipeline/coaching.py (task 62): build_deltas correctness
and generate_coaching_notes' schema validation / fallback behavior."""

import json

import pytest

from pipeline.coaching import (
    FEATURE_METADATA,
    Delta,
    build_deltas,
    fallback_coaching_notes,
    generate_coaching_notes,
)


def test_build_deltas_computes_signed_delta_and_metadata():
    user = {"elbow_angle_deg": 141.4, "stride_length": 0.95}
    reference = {"elbow_angle_deg": 144.5, "stride_length": 0.95}
    deltas = build_deltas(user, reference)

    by_metric = {d.metric_name: d for d in deltas}
    assert by_metric["elbow_angle_deg"].phase == "release"
    assert by_metric["elbow_angle_deg"].unit == "deg"
    assert by_metric["elbow_angle_deg"].delta == pytest.approx(141.4 - 144.5)
    assert by_metric["stride_length"].delta == pytest.approx(0.0)


def test_build_deltas_only_includes_shared_metrics():
    user = {"elbow_angle_deg": 140.0, "stride_length": 1.0}
    reference = {"elbow_angle_deg": 145.0}  # missing stride_length
    deltas = build_deltas(user, reference)
    assert len(deltas) == 1
    assert deltas[0].metric_name == "elbow_angle_deg"


def test_build_deltas_raises_on_unmapped_feature():
    user = {"totally_made_up_feature": 1.0}
    reference = {"totally_made_up_feature": 2.0}
    with pytest.raises(ValueError):
        build_deltas(user, reference)


def test_feature_metadata_covers_expected_keys():
    # a spot-check against the mapping table in docs/coaching_schema.md
    assert FEATURE_METADATA["hip_shoulder_separation_deg"] == ("arm_cock", "deg")
    assert FEATURE_METADATA["acceleration_rate"] == ("acceleration", "shoulder_widths/sec^2")
    assert FEATURE_METADATA["stride_duration_frac"] == ("stride", "fraction")


def _sample_deltas() -> list[Delta]:
    return [
        Delta("release", "elbow_angle_deg", 141.4, 144.5, -3.1, "deg"),
        Delta("stride", "stride_length", 0.95, 1.10, -0.15, "shoulder_widths"),
    ]


def test_fallback_coaching_notes_one_per_phase():
    notes = fallback_coaching_notes(_sample_deltas())
    assert {n["phase"] for n in notes} == {"release", "stride"}
    assert all("note" in n and n["note"] for n in notes)


def test_generate_coaching_notes_accepts_valid_llm_output():
    deltas = _sample_deltas()

    def good_client(payload):
        return json.dumps(
            [
                {"phase": "release", "note": "Elbow angle is 3.1 deg tighter than the reference."},
                {"phase": "stride", "note": "Stride is 0.15 units shorter than the reference."},
            ]
        )

    notes = generate_coaching_notes(deltas, good_client)
    assert notes[0]["phase"] == "release"
    assert "3.1" in notes[0]["note"]


@pytest.mark.parametrize(
    "bad_client",
    [
        lambda payload: "not json",
        lambda payload: json.dumps([{"phase": "release", "note": "ok", "extra": 1}]),
        lambda payload: json.dumps([{"phase": "load", "note": "fabricated phase, delta 5"}]),
        lambda payload: json.dumps([{"phase": "release", "note": "no number here at all"}]),
        lambda payload: json.dumps([{"phase": "release", "note": ""}]),
        lambda payload: (_ for _ in ()).throw(RuntimeError("LLM unreachable")),
    ],
)
def test_generate_coaching_notes_falls_back_on_malformed_output(bad_client):
    deltas = _sample_deltas()
    result = generate_coaching_notes(deltas, bad_client)
    assert result == fallback_coaching_notes(deltas)


def test_generate_coaching_notes_empty_deltas_returns_empty():
    assert generate_coaching_notes([], lambda payload: "[]") == []
