"""Unit tests for eval/pck.py (task 130) -- synthetic predicted/ground-truth
landmark pairs, since no real hand-labeled ground truth exists yet."""

import pytest

from eval.pck import compute_pck, compute_pck_over_frames

REFERENCE_DISTANCE = 1.0  # e.g. a unit "shoulder width"


def test_identical_landmarks_are_all_correct():
    landmarks = [(0.1, 0.2), (0.5, 0.5), (0.9, 0.8)]
    assert compute_pck(landmarks, landmarks, REFERENCE_DISTANCE) == 1.0


def test_landmarks_within_threshold_are_correct():
    ground_truth = [(0.5, 0.5)]
    # 0.1 units away, well within 0.2 * 1.0 = 0.2 threshold
    predicted = [(0.6, 0.5)]
    assert compute_pck(predicted, ground_truth, REFERENCE_DISTANCE, threshold_fraction=0.2) == 1.0


def test_landmarks_outside_threshold_are_incorrect():
    ground_truth = [(0.5, 0.5)]
    # 0.5 units away, outside 0.2 * 1.0 = 0.2 threshold
    predicted = [(1.0, 0.5)]
    assert compute_pck(predicted, ground_truth, REFERENCE_DISTANCE, threshold_fraction=0.2) == 0.0


def test_partial_correctness():
    ground_truth = [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]
    predicted = [(0.0, 0.0), (1.0, 1.0), (5.0, 5.0), (5.0, 5.0)]  # first 2 correct, last 2 way off
    assert compute_pck(predicted, ground_truth, REFERENCE_DISTANCE, threshold_fraction=0.2) == 0.5


def test_larger_reference_distance_widens_the_threshold():
    ground_truth = [(0.5, 0.5)]
    predicted = [(0.6, 0.5)]  # 0.1 units away
    assert compute_pck(predicted, ground_truth, reference_distance=0.1, threshold_fraction=0.2) == 0.0
    assert compute_pck(predicted, ground_truth, reference_distance=10.0, threshold_fraction=0.2) == 1.0


def test_mismatched_lengths_raise():
    with pytest.raises(ValueError):
        compute_pck([(0.0, 0.0)], [(0.0, 0.0), (1.0, 1.0)], REFERENCE_DISTANCE)


def test_compute_pck_over_frames_pools_across_frames():
    predicted_frames = [[(0.0, 0.0), (5.0, 5.0)], [(1.0, 1.0), (1.0, 1.0)]]
    ground_truth_frames = [[(0.0, 0.0), (0.0, 0.0)], [(1.0, 1.0), (1.0, 1.0)]]
    reference_distances = [1.0, 1.0]
    # frame 1: 1/2 correct, frame 2: 2/2 correct -> pooled 3/4
    result = compute_pck_over_frames(predicted_frames, ground_truth_frames, reference_distances, threshold_fraction=0.2)
    assert result == 0.75
