"""Unit tests for pipeline/landmark_overlay.py (task 123)."""

import pytest

from pipeline.landmark_overlay import (
    deserialize_overlay_frames,
    scope_to_boundary_range,
    serialize_frames_for_overlay,
)
from pipeline.phase_segmentation import PhaseBoundary
from pipeline.pose_extraction import FrameLandmarks, Landmark


def _frame(idx: int, x: float = 0.5) -> FrameLandmarks:
    return FrameLandmarks(
        frame_index=idx,
        timestamp_ms=idx * 33,
        landmarks=[Landmark(x=x, y=0.5, z=0.1, visibility=1.0, presence=1.0) for _ in range(33)],
    )


def test_serialize_drops_z_visibility_presence():
    frames = [_frame(0), _frame(1)]
    serialized = serialize_frames_for_overlay(frames)
    assert len(serialized) == 2
    assert serialized[0]["frame_index"] == 0
    assert serialized[0]["timestamp_ms"] == 0
    assert len(serialized[0]["landmarks"]) == 33
    assert serialized[0]["landmarks"][0] == [0.5, 0.5]


def test_serialize_raises_on_missing_landmarks():
    frames = [_frame(0), FrameLandmarks(frame_index=1, timestamp_ms=33, landmarks=None)]
    with pytest.raises(ValueError):
        serialize_frames_for_overlay(frames)


def test_round_trip_preserves_xy():
    frames = [_frame(0, x=0.4), _frame(1, x=0.6)]
    serialized = serialize_frames_for_overlay(frames)
    restored = deserialize_overlay_frames(serialized)
    assert len(restored) == 2
    assert restored[0].landmarks[0].x == 0.4
    assert restored[1].landmarks[0].x == 0.6
    assert restored[0].frame_index == 0
    assert restored[0].timestamp_ms == 0


def test_scope_to_boundary_range_slices_correctly():
    frames = [_frame(i) for i in range(10)]
    boundaries = [
        PhaseBoundary(phase_name="load", start_frame=2, end_frame=4),
        PhaseBoundary(phase_name="release", start_frame=5, end_frame=7),
    ]
    scoped = scope_to_boundary_range(frames, boundaries)
    assert [f.frame_index for f in scoped] == [2, 3, 4, 5, 6, 7]
