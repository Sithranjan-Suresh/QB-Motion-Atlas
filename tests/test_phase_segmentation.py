"""Unit tests for pipeline/phase_segmentation.py (task 87) -- synthetic
landmarks only, per tests/conftest.py."""

import copy

import pytest

from pipeline.phase_segmentation import PHASE_NAMES, segment_heuristic
from tests.conftest import make_throw_frames

FPS = 30.0


def test_segment_heuristic_returns_all_six_phases_in_order():
    frames = make_throw_frames(n=60, fps=FPS)
    boundaries = segment_heuristic(frames, FPS)

    assert [b.phase_name for b in boundaries] == PHASE_NAMES
    # phases are contiguous and non-decreasing: end of phase i == start of phase i+1
    for i in range(len(boundaries) - 1):
        assert boundaries[i].end_frame == boundaries[i + 1].start_frame
    assert boundaries[0].start_frame == 0
    assert boundaries[-1].end_frame == len(frames) - 1


def test_segment_heuristic_confidences_in_range():
    frames = make_throw_frames(n=60, fps=FPS)
    boundaries = segment_heuristic(frames, FPS)
    for b in boundaries:
        assert 0.0 <= b.confidence <= 1.0


def test_segment_heuristic_load_confidence_is_always_one():
    # load.start_frame is the clip boundary (frame 0), not a detected
    # inflection -- see phase_definitions.md.
    frames = make_throw_frames(n=60, fps=FPS)
    boundaries = segment_heuristic(frames, FPS)
    load = next(b for b in boundaries if b.phase_name == "load")
    assert load.confidence == 1.0


def test_segment_heuristic_requires_landmarks_on_every_frame():
    frames = make_throw_frames(n=30, fps=FPS)
    frames[10].landmarks = None
    with pytest.raises(ValueError):
        segment_heuristic(frames, FPS)


def test_occluded_release_frame_degrades_confidence_not_failure():
    frames = make_throw_frames(n=30, fps=FPS)
    boundaries = segment_heuristic(frames, FPS)
    release = next(b for b in boundaries if b.phase_name == "release")

    occluded_frames = copy.deepcopy(frames)
    occluded_frames[release.start_frame].landmarks[16].visibility = 0.1  # right wrist
    occluded_boundaries = segment_heuristic(occluded_frames, FPS)
    occluded_release = next(b for b in occluded_boundaries if b.phase_name == "release")

    assert occluded_release.confidence < release.confidence
