"""PCK (Percentage of Correct Keypoints) metric for pose-extraction
accuracy (task 130) -- fraction of predicted landmarks within a threshold
distance of ground truth, normalized by a body-scale reference distance so
the threshold means the same thing regardless of how large the person
appears in frame.

Reference distance convention: shoulder width, matching this project's
existing body-scale normalization (pipeline/features.py's
_mean_shoulder_width, task 24) -- PCK/PCKh in the pose-estimation
literature commonly normalizes by head size instead, but reusing this
project's own established reference unit is more consistent than
introducing a second one.

Note (2026-09-25): no hand-labeled ground-truth keypoints exist to run
this against yet -- same YouTube network-access blocker as the rest of
this project's real-data work (docs/research_log.md). Validated with
synthetic predicted/ground-truth landmark pairs in tests/test_pck.py.
"""

from __future__ import annotations

import math

DEFAULT_THRESHOLD_FRACTION = 0.2


def compute_pck(
    predicted: list[tuple[float, float]],
    ground_truth: list[tuple[float, float]],
    reference_distance: float,
    threshold_fraction: float = DEFAULT_THRESHOLD_FRACTION,
) -> float:
    """PCK@threshold_fraction for one frame: fraction of landmarks whose
    predicted (x, y) is within `threshold_fraction * reference_distance` of
    its ground-truth position.
    """
    if len(predicted) != len(ground_truth):
        raise ValueError(f"predicted has {len(predicted)} landmarks, ground_truth has {len(ground_truth)}")
    if not predicted:
        raise ValueError("compute_pck requires at least one landmark")
    if reference_distance <= 0:
        raise ValueError("reference_distance must be positive")

    threshold = threshold_fraction * reference_distance
    correct = sum(
        1 for (px, py), (gx, gy) in zip(predicted, ground_truth) if math.hypot(px - gx, py - gy) <= threshold
    )
    return correct / len(predicted)


def compute_pck_over_frames(
    predicted_frames: list[list[tuple[float, float]]],
    ground_truth_frames: list[list[tuple[float, float]]],
    reference_distances: list[float],
    threshold_fraction: float = DEFAULT_THRESHOLD_FRACTION,
) -> float:
    """Aggregate PCK across multiple frames -- one predicted/ground-truth
    landmark set and one reference distance per frame -- by pooling every
    landmark comparison across all frames into a single PCK, rather than
    averaging per-frame PCKs (which would over-weight a frame with fewer
    landmarks, not applicable here since every frame has the same 33, but
    pooling is the more standard definition regardless).
    """
    if not (len(predicted_frames) == len(ground_truth_frames) == len(reference_distances)):
        raise ValueError("predicted_frames, ground_truth_frames, and reference_distances must be the same length")
    if not predicted_frames:
        raise ValueError("compute_pck_over_frames requires at least one frame")

    total_correct = 0
    total_landmarks = 0
    for predicted, ground_truth, reference_distance in zip(predicted_frames, ground_truth_frames, reference_distances):
        if len(predicted) != len(ground_truth):
            raise ValueError("each frame's predicted/ground_truth landmark counts must match")
        threshold = threshold_fraction * reference_distance
        total_correct += sum(
            1 for (px, py), (gx, gy) in zip(predicted, ground_truth) if math.hypot(px - gx, py - gy) <= threshold
        )
        total_landmarks += len(predicted)

    return total_correct / total_landmarks
