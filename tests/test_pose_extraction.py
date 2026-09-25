"""Unit tests for pipeline/pose_extraction.py's primary-thrower selection
(task 42) -- synthetic bounding boxes, no real video/model needed."""

from pipeline.pose_extraction import _select_primary_pose


class _FakeLandmark:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


def _make_pose(center_x: float, center_y: float, half_size: float) -> list[_FakeLandmark]:
    """A minimal two-point "pose" bounding box, since _select_primary_pose only
    reads .x/.y off whatever landmark objects it's given."""
    return [
        _FakeLandmark(center_x - half_size, center_y - half_size),
        _FakeLandmark(center_x + half_size, center_y + half_size),
    ]


def test_single_person_happy_path():
    pose = _make_pose(0.5, 0.5, 0.2)
    assert _select_primary_pose([pose]) is pose


def test_no_detections_returns_none():
    assert _select_primary_pose([]) is None


def test_multi_person_selects_larger_more_central_pose():
    primary = _make_pose(0.5, 0.5, 0.25)  # large, centered -- the thrower
    bystander = _make_pose(0.1, 0.1, 0.03)  # small, in a corner -- background
    assert _select_primary_pose([bystander, primary]) is primary
    assert _select_primary_pose([primary, bystander]) is primary  # order-independent


def test_multi_person_ambiguous_rejected():
    left_person = _make_pose(0.45, 0.5, 0.2)
    right_person = _make_pose(0.55, 0.5, 0.2)  # nearly identical size/centrality
    assert _select_primary_pose([left_person, right_person]) is None
