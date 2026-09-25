"""V1 DTW similarity layer: aligns two throws' per-frame trajectories despite
different clip lengths/timing, complementing the V0 per-phase feature
distance (pipeline/similarity.py) with a whole-motion shape comparison.
See docs/similarity_methodology.md for why both layers exist and how
they're combined.
"""

from __future__ import annotations

import math

from pipeline.features import LEFT_SHOULDER, RIGHT_SHOULDER, _elbow_angle_deg, _line_angle_deg, _mean_shoulder_width
from pipeline.phase_segmentation import _velocity_series
from pipeline.pose_extraction import FrameLandmarks
from pipeline.similarity import compare_features

RIGHT_WRIST = 16  # throwing side


def build_frame_trajectory(frames: list[FrameLandmarks], fps: float) -> list[list[float]]:
    """Per-frame [elbow_angle_deg, shoulder_rotation_angle_deg, normalized_wrist_speed]
    across the whole clip, for DTW alignment -- contrast with features.py's
    per-phase snapshot values. wrist_speed is body-scale normalized the same
    way as features.py's release_arm_velocity (task 24).
    """
    if any(f.landmarks is None for f in frames):
        raise ValueError("build_frame_trajectory requires landmarks on every frame -- filter gaps first")

    wrist_vel = _velocity_series(frames, RIGHT_WRIST, fps)
    shoulder_width = _mean_shoulder_width(frames, 0, len(frames) - 1)

    trajectory = []
    for i in range(len(frames)):
        elbow_angle_deg = _elbow_angle_deg(frames, i)
        shoulder_rotation_angle_deg = _line_angle_deg(frames, i, LEFT_SHOULDER, RIGHT_SHOULDER)
        vx, vy = wrist_vel[i]
        wrist_speed = math.hypot(vx, vy) / shoulder_width
        trajectory.append([elbow_angle_deg, shoulder_rotation_angle_deg, wrist_speed])
    return trajectory


def _euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def dtw_align(seq_a: list[list[float]], seq_b: list[list[float]]) -> tuple[list[tuple[int, int]], float]:
    """Classic dynamic time warping over two multivariate frame sequences.

    Returns (alignment, distance): `alignment` is the warping path as a list
    of (i, j) frame-index pairs from (0, 0) to (len(seq_a)-1, len(seq_b)-1);
    `distance` is the cumulative per-frame Euclidean cost along that path.
    O(len(seq_a) * len(seq_b)) time and space -- fine at the seed-clip scale
    (hundreds of frames) this project runs at.
    """
    n, m = len(seq_a), len(seq_b)
    if n == 0 or m == 0:
        raise ValueError("dtw_align requires non-empty sequences")

    cost = [[math.inf] * (m + 1) for _ in range(n + 1)]
    cost[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            step_cost = _euclidean(seq_a[i - 1], seq_b[j - 1])
            cost[i][j] = step_cost + min(cost[i - 1][j], cost[i][j - 1], cost[i - 1][j - 1])

    alignment: list[tuple[int, int]] = []
    i, j = n, m
    while i > 0 and j > 0:
        alignment.append((i - 1, j - 1))
        candidates = [
            (cost[i - 1][j - 1], (i - 1, j - 1)),
            (cost[i - 1][j], (i - 1, j)),
            (cost[i][j - 1], (i, j - 1)),
        ]
        _, (i, j) = min(candidates, key=lambda c: c[0])
    alignment.reverse()

    return alignment, cost[n][m]


def dtw_similarity(seq_a: list[list[float]], seq_b: list[list[float]]) -> float:
    """Similarity score in (0, 1] from DTW distance, normalized by the warping
    path's length so it's comparable regardless of clip length (an unnormalized
    DTW cost grows with sequence length even for a perfect match)."""
    alignment, distance = dtw_align(seq_a, seq_b)
    normalized_distance = distance / len(alignment)
    return 1.0 / (1.0 + normalized_distance)


def combined_similarity(
    feature_vec_a: dict[str, float],
    feature_vec_b: dict[str, float],
    trajectory_a: list[list[float]],
    trajectory_b: list[list[float]],
    feature_weight: float = 0.5,
    dtw_weight: float = 0.5,
) -> float:
    """Task 51: overall similarity combining the V0 per-phase feature distance
    (pipeline/similarity.py::compare_features) with the V1 DTW whole-motion
    shape distance. Equal weighting is a placeholder pending task 53's
    empirical tuning against real reference-set retrieval accuracy -- see
    docs/similarity_methodology.md.
    """
    feature_similarity = compare_features(feature_vec_a, feature_vec_b)
    trajectory_similarity = dtw_similarity(trajectory_a, trajectory_b)
    return feature_weight * feature_similarity + dtw_weight * trajectory_similarity
