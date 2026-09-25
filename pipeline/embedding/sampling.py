"""Triplet sampling for the V2 embedding model (task 100), per
docs/embedding_methodology.md's triplet definition: anchor/positive = same
QB, same phase, different clip; negative = different QB, same phase.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseRecord:
    qb_name: str
    clip_id: str
    phase_name: str
    feature_vector: dict[str, float]


@dataclass(frozen=True)
class Triplet:
    anchor: PhaseRecord
    positive: PhaseRecord
    negative: PhaseRecord


def generate_triplets(records: list[PhaseRecord], rng: random.Random | None = None) -> list[Triplet]:
    """One triplet per (anchor, positive) same-QB-same-phase pair, each
    paired with a randomly sampled different-QB-same-phase negative.

    A QB needs at least 2 clips for a given phase to serve as an anchor for
    that phase (nothing to pair it with otherwise); a phase needs at least 2
    distinct QBs represented to have any negatives to sample from at all --
    both are silently skipped rather than erroring, since a small or
    lopsided reference set is expected before task 99's dataset expansion
    (blocked) actually grows it.
    """
    rng = rng or random.Random()

    records_by_phase: dict[str, list[PhaseRecord]] = {}
    for record in records:
        records_by_phase.setdefault(record.phase_name, []).append(record)

    triplets: list[Triplet] = []
    for phase_records in records_by_phase.values():
        by_qb: dict[str, list[PhaseRecord]] = {}
        for record in phase_records:
            by_qb.setdefault(record.qb_name, []).append(record)

        if len(by_qb) < 2:
            continue  # no other QB in this phase to draw a negative from

        for qb_name, qb_records in by_qb.items():
            if len(qb_records) < 2:
                continue  # nothing to pair this QB's one clip with

            other_qb_records = [r for r in phase_records if r.qb_name != qb_name]

            for anchor in qb_records:
                for positive in qb_records:
                    if positive.clip_id == anchor.clip_id:
                        continue
                    negative = rng.choice(other_qb_records)
                    triplets.append(Triplet(anchor=anchor, positive=positive, negative=negative))

    return triplets
