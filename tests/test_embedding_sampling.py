"""Unit tests for pipeline/embedding/sampling.py (task 100)."""

import random

from pipeline.embedding.sampling import PhaseRecord, generate_triplets


def _record(qb: str, clip: str, phase: str) -> PhaseRecord:
    return PhaseRecord(qb_name=qb, clip_id=clip, phase_name=phase, feature_vector={"x": 1.0})


def test_generates_same_qb_same_phase_anchor_positive_pairs():
    records = [
        _record("josh_allen", "clip1", "release"),
        _record("josh_allen", "clip2", "release"),
        _record("patrick_mahomes", "clip1", "release"),
        _record("patrick_mahomes", "clip2", "release"),
    ]
    triplets = generate_triplets(records, rng=random.Random(0))

    assert len(triplets) > 0
    for triplet in triplets:
        assert triplet.anchor.qb_name == triplet.positive.qb_name
        assert triplet.anchor.clip_id != triplet.positive.clip_id
        assert triplet.anchor.phase_name == triplet.positive.phase_name == triplet.negative.phase_name
        assert triplet.negative.qb_name != triplet.anchor.qb_name


def test_skips_qb_with_only_one_clip_in_a_phase():
    records = [
        _record("josh_allen", "clip1", "release"),  # only one clip -- no positive available
        _record("patrick_mahomes", "clip1", "release"),
        _record("patrick_mahomes", "clip2", "release"),
    ]
    triplets = generate_triplets(records, rng=random.Random(0))
    assert all(t.anchor.qb_name == "patrick_mahomes" for t in triplets)


def test_skips_phase_with_only_one_qb():
    records = [
        _record("josh_allen", "clip1", "release"),
        _record("josh_allen", "clip2", "release"),
        _record("josh_allen", "clip3", "release"),
    ]
    triplets = generate_triplets(records, rng=random.Random(0))
    assert triplets == []


def test_no_records_returns_no_triplets():
    assert generate_triplets([]) == []


def test_phases_are_kept_separate():
    records = [
        _record("josh_allen", "clip1", "release"),
        _record("josh_allen", "clip2", "release"),
        _record("patrick_mahomes", "clip1", "release"),
        _record("josh_allen", "clip1", "stride"),
        _record("patrick_mahomes", "clip1", "stride"),
        # patrick_mahomes has only one clip in "stride" -- no pair for that QB/phase.
    ]
    triplets = generate_triplets(records, rng=random.Random(0))
    for triplet in triplets:
        assert triplet.anchor.phase_name == "release"
        assert triplet.anchor.qb_name == "josh_allen"
