"""Overall high/medium/low confidence scoring (task 55), per
docs/confidence_scoring.md.
"""

from __future__ import annotations

from pipeline.phase_segmentation import PhaseBoundary
from pipeline.pose_extraction import FrameLandmarks

# V1 placeholders -- see docs/confidence_scoring.md's caveat on all three
# constants here (equal weighting, these two thresholds).
HIGH_THRESHOLD = 0.7
MEDIUM_THRESHOLD = 0.4


def pose_completeness(frames: list[FrameLandmarks]) -> float:
    """Fraction of frames with zero interpolated joints -- every landmark on
    that frame came from a real MediaPipe detection, not landmark_filter.py's
    gap-filling."""
    if not frames:
        return 0.0
    fully_real = sum(
        1 for f in frames if f.landmarks is not None and all(not lm.interpolated for lm in f.landmarks)
    )
    return fully_real / len(frames)


def average_boundary_confidence(boundaries: list[PhaseBoundary]) -> float:
    """Mean of the six PhaseBoundary.confidence values from segment_heuristic()."""
    if not boundaries:
        return 0.0
    return sum(b.confidence for b in boundaries) / len(boundaries)


def similarity_margin(similarity_scores: list[float]) -> float:
    """Gap between the top-1 and top-2 similarity scores (highest first) -- a
    large margin means the top match clearly beats the runner-up. With only
    one candidate score, that score itself stands in for margin (no runner-up
    to compare against); with none, there's nothing to be confident about."""
    if not similarity_scores:
        return 0.0
    ranked = sorted(similarity_scores, reverse=True)
    if len(ranked) == 1:
        return ranked[0]
    return ranked[0] - ranked[1]


def compute_confidence(
    frames: list[FrameLandmarks],
    boundaries: list[PhaseBoundary],
    similarity_scores: list[float],
) -> str:
    """Overall confidence level ("high" | "medium" | "low") from the three
    signals in docs/confidence_scoring.md, equally weighted."""
    overall = (
        pose_completeness(frames) + average_boundary_confidence(boundaries) + similarity_margin(similarity_scores)
    ) / 3

    if overall >= HIGH_THRESHOLD:
        return "high"
    if overall >= MEDIUM_THRESHOLD:
        return "medium"
    return "low"
