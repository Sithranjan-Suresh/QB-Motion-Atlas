"""Unit tests for pipeline/confidence.py (task 56): confidence must degrade
correctly as pose completeness, boundary confidence, or similarity margin
worsen -- synthetic inputs only."""

import pytest

from pipeline.confidence import (
    average_boundary_confidence,
    compute_confidence,
    pose_completeness,
    similarity_margin,
)
from pipeline.phase_segmentation import PhaseBoundary
from pipeline.pose_extraction import FrameLandmarks, Landmark


def _frame(interpolated: bool) -> FrameLandmarks:
    landmarks = [Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0, interpolated=interpolated) for _ in range(33)]
    return FrameLandmarks(frame_index=0, timestamp_ms=0, landmarks=landmarks)


def _boundaries(confidence: float) -> list[PhaseBoundary]:
    names = ["load", "stride", "arm_cock", "acceleration", "release", "follow_through"]
    return [PhaseBoundary(name, 0, 1, confidence=confidence) for name in names]


def test_pose_completeness_all_real():
    frames = [_frame(interpolated=False) for _ in range(10)]
    assert pose_completeness(frames) == 1.0


def test_pose_completeness_half_interpolated():
    frames = [_frame(interpolated=(i % 2 == 0)) for i in range(10)]
    assert pose_completeness(frames) == 0.5


def test_pose_completeness_empty():
    assert pose_completeness([]) == 0.0


def test_average_boundary_confidence():
    assert average_boundary_confidence(_boundaries(0.8)) == pytest.approx(0.8)
    assert average_boundary_confidence([]) == 0.0


def test_similarity_margin_two_candidates():
    assert similarity_margin([0.5, 0.95]) == pytest.approx(0.45)


def test_similarity_margin_single_candidate():
    assert similarity_margin([0.6]) == 0.6


def test_similarity_margin_empty():
    assert similarity_margin([]) == 0.0


def test_confidence_high_on_clean_inputs():
    frames = [_frame(interpolated=False) for _ in range(10)]
    boundaries = _boundaries(1.0)
    assert compute_confidence(frames, boundaries, [0.95, 0.5]) == "high"


def test_confidence_degrades_with_pose_gaps():
    clean_frames = [_frame(interpolated=False) for _ in range(10)]
    gappy_frames = [_frame(interpolated=(i % 2 == 0)) for i in range(10)]
    boundaries = _boundaries(1.0)
    assert compute_confidence(clean_frames, boundaries, [0.95, 0.5]) == "high"
    assert compute_confidence(gappy_frames, boundaries, [0.95, 0.5]) == "medium"


def test_confidence_degrades_with_weak_boundaries():
    frames = [_frame(interpolated=False) for _ in range(10)]
    assert compute_confidence(frames, _boundaries(1.0), [0.95, 0.5]) == "high"
    assert compute_confidence(frames, _boundaries(0.1), [0.95, 0.5]) == "medium"


def test_confidence_low_when_everything_is_bad():
    frames = [_frame(interpolated=True) for _ in range(10)]
    boundaries = _boundaries(0.1)
    assert compute_confidence(frames, boundaries, [0.3, 0.28]) == "low"


def test_confidence_handles_no_similarity_scores():
    frames = [_frame(interpolated=False) for _ in range(10)]
    boundaries = _boundaries(1.0)
    # no crash with an empty candidate list -- margin contributes 0.
    level = compute_confidence(frames, boundaries, [])
    assert level in ("high", "medium", "low")
