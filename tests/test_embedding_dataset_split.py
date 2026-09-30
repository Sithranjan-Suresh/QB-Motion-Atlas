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


def test_clips_from_same_session_stay_in_same_split():
    clip_ids = [f"clip{i}" for i in range(10)]
    session_by_clip = {"clip0": "proday", "clip1": "proday", "clip2": "proday"}
    for seed in range(20):
        result = split_clips({"marcus_mariota": clip_ids}, rng=random.Random(seed), session_by_clip=session_by_clip)
        homes = [
            name for name, clips in (("train", result.train), ("val", result.val), ("test", result.test))
            if "clip0" in clips
        ]
        home = getattr(result, homes[0])
        assert "clip1" in home and "clip2" in home
        assert len(result.train) + len(result.val) + len(result.test) == 10


def test_min_threshold_counts_sessions_not_clips():
    # Three clips but only two sessions: can't fill train/val/test honestly.
    clip_ids_by_qb = {"marcus_mariota": ["clip1", "clip2", "clip3"]}
    session_by_clip = {"clip1": "oregon_proday", "clip2": "oregon_proday"}
    result = split_clips(clip_ids_by_qb, rng=random.Random(0), session_by_clip=session_by_clip)
    assert sorted(result.train) == ["clip1", "clip2", "clip3"]
    assert result.val == []
    assert result.test == []


def test_session_mapping_from_provenance(tmp_path):
    from pipeline.embedding.dataset_split import session_by_clip_from_provenance

    csv_path = tmp_path / "provenance.csv"
    csv_path.write_text(
        "qb_name,clip_id,source_session\n"
        "marcus_mariota,clip1,oregon_proday\n"
        "marcus_mariota,clip2,oregon_proday\n"
        "marcus_mariota,clip3,\n"
        "josh_allen,clip1,oregon_proday\n"
    )
    mapping = session_by_clip_from_provenance(csv_path)
    assert mapping == {
        "marcus_mariota__clip1": "marcus_mariota::oregon_proday",
        "marcus_mariota__clip2": "marcus_mariota::oregon_proday",
        "josh_allen__clip1": "josh_allen::oregon_proday",
    }


def test_real_provenance_groups_mariota_proday():
    from pipeline.embedding.dataset_split import session_by_clip_from_provenance

    mapping = session_by_clip_from_provenance()
    assert (
        mapping["marcus_mariota__clip1_espn_oregon_proday"] == mapping["marcus_mariota__clip2_nfl_oregon_proday"]
    )
