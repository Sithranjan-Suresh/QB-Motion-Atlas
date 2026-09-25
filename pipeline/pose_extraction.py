"""MediaPipe-based pose extraction for a single throwing-motion clip.

V0 scope: run MediaPipe's PoseLandmarker (VIDEO mode) over every frame of a
clip and return the raw per-frame landmark output. No smoothing, filtering,
or phase logic here -- that belongs to later pipeline stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    RunningMode,
)
import mediapipe as mp

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "pose_landmarker_lite.task"

# MediaPipe Pose's 33 landmark indices, for readability elsewhere in the pipeline.
NUM_LANDMARKS = 33


@dataclass
class Landmark:
    x: float
    y: float
    z: float
    visibility: float
    presence: float
    interpolated: bool = False


@dataclass
class FrameLandmarks:
    frame_index: int
    timestamp_ms: int
    landmarks: list[Landmark] | None  # None when no pose was detected in this frame

    def to_dict(self) -> dict:
        return {
            "frame_index": self.frame_index,
            "timestamp_ms": self.timestamp_ms,
            "landmarks": (
                [lm.__dict__ for lm in self.landmarks] if self.landmarks is not None else None
            ),
        }

    @staticmethod
    def from_dict(data: dict) -> "FrameLandmarks":
        landmarks = (
            [Landmark(**lm) for lm in data["landmarks"]] if data["landmarks"] is not None else None
        )
        return FrameLandmarks(data["frame_index"], data["timestamp_ms"], landmarks)


DEFAULT_MAX_POSES = 3
# If the top two candidate poses' scores are within this fraction of each
# other, the primary thrower can't be confidently picked -- treat the frame
# as undetected rather than guessing wrong (task 40).
PRIMARY_POSE_AMBIGUITY_MARGIN = 0.15


def _bbox(raw_landmarks) -> tuple[float, float, float, float]:
    xs = [lm.x for lm in raw_landmarks]
    ys = [lm.y for lm in raw_landmarks]
    return min(xs), max(xs), min(ys), max(ys)


def _primary_pose_score(raw_landmarks) -> float:
    """Larger, more-central bounding boxes score higher -- the primary thrower is
    assumed to be the largest person in frame closest to the frame center."""
    x_min, x_max, y_min, y_max = _bbox(raw_landmarks)
    area = (x_max - x_min) * (y_max - y_min)
    center_x, center_y = (x_min + x_max) / 2, (y_min + y_max) / 2
    center_distance = ((center_x - 0.5) ** 2 + (center_y - 0.5) ** 2) ** 0.5
    return area * (1.0 - min(center_distance, 1.0))


def _select_primary_pose(raw_poses):
    """Pick the primary-thrower pose from a frame's detected poses, or None if
    there's no clear winner (empty, or top two candidates too close to call)."""
    if not raw_poses:
        return None
    if len(raw_poses) == 1:
        return raw_poses[0]

    ranked = sorted(raw_poses, key=_primary_pose_score, reverse=True)
    best_score = _primary_pose_score(ranked[0])
    second_score = _primary_pose_score(ranked[1])
    if best_score == 0:
        return None
    if (best_score - second_score) / best_score < PRIMARY_POSE_AMBIGUITY_MARGIN:
        return None  # ambiguous -- reject rather than guess the wrong person
    return ranked[0]


def extract_pose(
    video_path: str | Path,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    max_poses: int = DEFAULT_MAX_POSES,
) -> list[FrameLandmarks]:
    """Run MediaPipe PoseLandmarker over every frame of `video_path`.

    Returns one `FrameLandmarks` per frame, in frame order. A frame where no
    pose was detected gets `landmarks=None` rather than being dropped, so
    downstream code can still reason about gaps by frame index / timestamp.
    When multiple people are detected in a frame (`max_poses` > 1), the
    primary thrower is selected via `_select_primary_pose` (largest,
    most-central bounding box); an ambiguous frame is also treated as
    undetected (task 40) rather than risking tracking the wrong person.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=RunningMode.VIDEO,
        num_poses=max_poses,
    )

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    results: list[FrameLandmarks] = []

    with PoseLandmarker.create_from_options(options) as landmarker:
        frame_index = 0
        while True:
            ok, frame_bgr = cap.read()
            if not ok:
                break

            timestamp_ms = int(round((frame_index / fps) * 1000))
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            raw_landmarks = _select_primary_pose(result.pose_landmarks)
            if raw_landmarks is not None:
                landmarks = [
                    Landmark(
                        x=lm.x,
                        y=lm.y,
                        z=lm.z,
                        visibility=lm.visibility,
                        presence=lm.presence,
                    )
                    for lm in raw_landmarks
                ]
            else:
                landmarks = None

            results.append(FrameLandmarks(frame_index, timestamp_ms, landmarks))
            frame_index += 1

    cap.release()
    return results
