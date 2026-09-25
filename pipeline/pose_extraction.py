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


def extract_pose(
    video_path: str | Path,
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> list[FrameLandmarks]:
    """Run MediaPipe PoseLandmarker over every frame of `video_path`.

    Returns one `FrameLandmarks` per frame, in frame order. A frame where no
    pose was detected gets `landmarks=None` rather than being dropped, so
    downstream code can still reason about gaps by frame index / timestamp.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=RunningMode.VIDEO,
        num_poses=1,
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

            if result.pose_landmarks:
                # num_poses=1, so at most one pose in result.pose_landmarks.
                raw_landmarks = result.pose_landmarks[0]
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
