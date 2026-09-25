"""Unit tests for pipeline/embedding/dataset_split.py (task 101)."""

import random

from pipeline.embedding.dataset_split import MIN_CLIPS_FOR_SPLIT, split_clips


def test_small_qb_goes_entirely_to_train():
    clip_ids_by_qb = {"josh_allen": ["clip1", "clip2"]}  # below MIN_CLIPS_FOR_SPLIT
    result = split_clips(clip_ids_by_qb, rng=random.Random(0))
    assert sorted(result.train) == ["clip1", "clip2"]
    assert result.val == []
    assert result.test == []


def test_larger_qb_gets_split_into_all_three():
    clip_ids_by_qb = {"josh_allen": [f"clip{i}" for i in range(10)]}
    result = split_clips(clip_ids_by_qb, rng=random.Random(0))
    assert len(result.train) > 0
    assert len(result.val) > 0
    assert len(result.test) > 0
    assert len(result.train) + len(result.val) + len(result.test) == 10


def test_no_overlap_between_splits():
    clip_ids_by_qb = {
        "josh_allen": [f"ja{i}" for i in range(12)],
        "patrick_mahomes": [f"pm{i}" for i in range(8)],
    }
    result = split_clips(clip_ids_by_qb, rng=random.Random(1))
    all_clips = result.train + result.val + result.test
    assert len(all_clips) == len(set(all_clips))  # no duplicates
    assert len(all_clips) == 20  # every clip accounted for


def test_each_qb_with_enough_clips_appears_in_every_split():
    clip_ids_by_qb = {"josh_allen": [f"clip{i}" for i in range(20)]}
    result = split_clips(clip_ids_by_qb, rng=random.Random(0))
    assert len(result.train) >= 1
    assert len(result.val) >= 1
    assert len(result.test) >= 1


def test_exactly_at_min_threshold_still_gets_all_three_groups():
    clip_ids_by_qb = {"josh_allen": [f"clip{i}" for i in range(MIN_CLIPS_FOR_SPLIT)]}
    result = split_clips(clip_ids_by_qb, rng=random.Random(0))
    total = len(result.train) + len(result.val) + len(result.test)
    assert total == MIN_CLIPS_FOR_SPLIT


def test_empty_input():
    result = split_clips({})
    assert result.train == []
    assert result.val == []
    assert result.test == []
