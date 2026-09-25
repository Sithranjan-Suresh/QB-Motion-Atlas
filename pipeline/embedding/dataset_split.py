"""Clip-level, QB-stratified train/validation/held-out-test split (task
101), per docs/embedding_methodology.md's ratios and small-N handling.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

TRAIN_FRACTION = 0.70
VAL_FRACTION = 0.15
TEST_FRACTION = 0.15
# A QB with fewer than this many clips can't be split into three
# meaningful groups -- all of its clips go to train instead of rounding a
# split down to zero and pretending it's represented in val/test.
MIN_CLIPS_FOR_SPLIT = 3


@dataclass
class DatasetSplit:
    train: list[str] = field(default_factory=list)
    val: list[str] = field(default_factory=list)
    test: list[str] = field(default_factory=list)


def split_clips(clip_ids_by_qb: dict[str, list[str]], rng: random.Random | None = None) -> DatasetSplit:
    """Splits each QB's clip_ids independently (stratified by QB) so every
    split has proportional representation across QBs wherever there's
    enough data to do so. A QB with fewer than MIN_CLIPS_FOR_SPLIT clips has
    all of them placed in train -- see docs/embedding_methodology.md's
    "Small-N handling."
    """
    rng = rng or random.Random()
    split = DatasetSplit()

    for clip_ids in clip_ids_by_qb.values():
        shuffled = list(clip_ids)
        rng.shuffle(shuffled)

        if len(shuffled) < MIN_CLIPS_FOR_SPLIT:
            split.train.extend(shuffled)
            continue

        n = len(shuffled)
        n_val = max(1, round(n * VAL_FRACTION))
        n_test = max(1, round(n * TEST_FRACTION))
        # train gets whatever's left, guaranteeing val/test don't consume
        # the entire clip list if fractions round up on a small n.
        n_val = min(n_val, n - 1)
        n_test = min(n_test, n - n_val - 1) if n - n_val > 1 else 0
        n_train = n - n_val - n_test

        split.train.extend(shuffled[:n_train])
        split.val.extend(shuffled[n_train : n_train + n_val])
        split.test.extend(shuffled[n_train + n_val :])

    return split
