"""Session-level, QB-stratified train/validation/held-out-test split (task
101), per docs/embedding_methodology.md's ratios and small-N handling.

Clips filmed at the same session (same day, same field, same camera -- e.g.
marcus_mariota clip1 and clip2, two broadcasters' uploads of one Oregon pro
day) are near-duplicates, so they always land in the same split; otherwise
a "held-out" test clip could have its twin in train.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass, field
from pathlib import Path

PROVENANCE_CSV = Path(__file__).resolve().parents[2] / "data" / "provenance.csv"

TRAIN_FRACTION = 0.70
VAL_FRACTION = 0.15
TEST_FRACTION = 0.15
# A QB with fewer than this many distinct sessions can't be split into
# three meaningful groups -- all of its clips go to train instead of
# rounding a split down to zero and pretending it's represented in val/test.
MIN_CLIPS_FOR_SPLIT = 3


@dataclass
class DatasetSplit:
    train: list[str] = field(default_factory=list)
    val: list[str] = field(default_factory=list)
    test: list[str] = field(default_factory=list)


def split_clips(
    clip_ids_by_qb: dict[str, list[str]],
    rng: random.Random | None = None,
    session_by_clip: dict[str, str] | None = None,
) -> DatasetSplit:
    """Splits each QB's clips independently (stratified by QB) so every
    split has proportional representation across QBs wherever there's
    enough data to do so.

    `session_by_clip` maps a clip_id to its source-session key; clips that
    share a key (within the same QB) move between splits together. A clip
    with no entry is its own session. The ratios and MIN_CLIPS_FOR_SPLIT
    count sessions, not clips: a QB with fewer than MIN_CLIPS_FOR_SPLIT
    distinct sessions has all of its clips placed in train -- see
    docs/embedding_methodology.md's "Small-N handling."
    """
    rng = rng or random.Random()
    session_by_clip = session_by_clip or {}
    split = DatasetSplit()

    for clip_ids in clip_ids_by_qb.values():
        # Insertion-ordered grouping keeps the result deterministic for a
        # seeded rng.
        sessions: dict[str, list[str]] = {}
        for clip_id in clip_ids:
            sessions.setdefault(session_by_clip.get(clip_id, clip_id), []).append(clip_id)
        groups = list(sessions.values())
        rng.shuffle(groups)

        if len(groups) < MIN_CLIPS_FOR_SPLIT:
            for group in groups:
                split.train.extend(group)
            continue

        n = len(groups)
        n_val = max(1, round(n * VAL_FRACTION))
        n_test = max(1, round(n * TEST_FRACTION))
        # train gets whatever's left, guaranteeing val/test don't consume
        # the entire session list if fractions round up on a small n.
        n_val = min(n_val, n - 1)
        n_test = min(n_test, n - n_val - 1) if n - n_val > 1 else 0
        n_train = n - n_val - n_test

        for group in groups[:n_train]:
            split.train.extend(group)
        for group in groups[n_train : n_train + n_val]:
            split.val.extend(group)
        for group in groups[n_train + n_val :]:
            split.test.extend(group)

    return split


def session_by_clip_from_provenance(provenance_csv: str | Path = PROVENANCE_CSV) -> dict[str, str]:
    """Reads data/provenance.csv's `source_session` column into the
    `session_by_clip` mapping split_clips() takes, keyed by the
    "{qb_name}__{clip_id}" ids used everywhere downstream. A blank
    source_session means the clip is its own session, so it's left out.
    Session keys are prefixed with the QB so two QBs can't collide."""
    mapping: dict[str, str] = {}
    with Path(provenance_csv).open(newline="") as f:
        for row in csv.DictReader(f):
            session = (row.get("source_session") or "").strip()
            if session:
                mapping[f"{row['qb_name']}__{row['clip_id']}"] = f"{row['qb_name']}::{session}"
    return mapping
