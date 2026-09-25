"""Serialization between pipeline/pose_extraction.py's FrameLandmarks and the
compact (x, y)-only JSON shape stored in db/models.py::LandmarkSequence
(task 123) -- used for the skeleton overlay (task 124) and the DTW-synced
comparison (task 125). z/visibility/presence are dropped: nothing that
consumes this data (canvas drawing, build_frame_trajectory) needs them.
"""

from __future__ import annotations

from pipeline.pose_extraction import FrameLandmarks, Landmark


def serialize_frames_for_overlay(frames: list[FrameLandmarks]) -> list[dict]:
    """Every frame here is assumed to already have landmarks -- gaps are the
    caller's job to filter/reject before this point, same as
    phase_segmentation.py and features.py's own preconditions."""
    serialized = []
    for frame in frames:
        if frame.landmarks is None:
            raise ValueError(f"frame {frame.frame_index} has no landmarks -- filter gaps first")
        serialized.append(
            {
                "frame_index": frame.frame_index,
                "timestamp_ms": frame.timestamp_ms,
                "landmarks": [[lm.x, lm.y] for lm in frame.landmarks],
            }
        )
    return serialized


def deserialize_overlay_frames(data: list[dict]) -> list[FrameLandmarks]:
    """Reconstructs FrameLandmarks from serialize_frames_for_overlay()'s
    output, for feeding back into x/y-only pipeline code (e.g.
    pipeline/similarity_dtw.py::build_frame_trajectory). z/visibility/
    presence are filled with harmless placeholders since nothing here reads
    them.
    """
    return [
        FrameLandmarks(
            frame_index=d["frame_index"],
            timestamp_ms=d["timestamp_ms"],
            landmarks=[Landmark(x=x, y=y, z=0.0, visibility=1.0, presence=1.0) for x, y in d["landmarks"]],
        )
        for d in data
    ]


def scope_to_boundary_range(frames: list[FrameLandmarks], boundaries) -> list[FrameLandmarks]:
    """Slices to the frame range actually covered by phase boundaries (the
    task's "scoped to compared phases") -- normally the whole clip, but a
    clip whose boundaries don't reach frame 0 or the last frame (shouldn't
    happen with segment_heuristic today, but not guaranteed by the type)
    would only store what was actually analyzed."""
    start = min(b.start_frame for b in boundaries)
    end = max(b.end_frame for b in boundaries)
    return [f for f in frames if start <= f.frame_index <= end]
