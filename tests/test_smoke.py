"""Task 88: end-to-end local pipeline smoke test, pose extraction mocked to
synthetic throw landmarks (no real 'known test video' is available in this
environment -- see pipeline/run_smoke_test.py's module docstring)."""

from unittest.mock import patch

import cv2
import numpy as np

from pipeline.run_smoke_test import run_smoke_test
from tests.conftest import make_throw_frames


def _write_placeholder_video(path: str, num_frames: int = 60, fps: float = 30.0) -> None:
    # run_smoke_test still needs a real, openable video file to read fps
    # from (_video_fps) even though extract_pose itself is mocked below.
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (320, 240))
    for _ in range(num_frames):
        out.write(np.zeros((240, 320, 3), dtype=np.uint8))
    out.release()


def test_run_smoke_test_populates_every_field(tmp_path):
    video_path = str(tmp_path / "placeholder.mp4")
    _write_placeholder_video(video_path)

    with patch("pipeline.run_smoke_test.extract_pose", return_value=make_throw_frames(n=60)):
        result = run_smoke_test(video_path)

    assert result["handedness"] == "right"
    assert result["validation_status"] == "pass"
    assert [b.phase_name for b in result["boundaries"]] == [
        "load",
        "stride",
        "arm_cock",
        "acceleration",
        "release",
        "follow_through",
    ]
    assert len(result["features"]) == 17
    assert all(isinstance(v, float) for v in result["features"].values())
    assert 0.0 < result["similarity_score"] <= 1.0
    assert result["confidence"] in ("high", "medium", "low")
    assert len(result["coaching_notes"]) > 0
    assert all("phase" in note and "note" in note for note in result["coaching_notes"])
