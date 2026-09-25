"""Draw extracted pose landmarks back onto the source video for visual sanity-checking.

Usage: python -m pipeline.debug_overlay <video_path> <pose_json_path> <output_path>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
from mediapipe.tasks.python.vision import PoseLandmarksConnections

CONNECTIONS = [(c.start, c.end) for c in PoseLandmarksConnections.POSE_LANDMARKS]

POINT_COLOR = (0, 255, 0)  # BGR
LINE_COLOR = (0, 200, 255)
LOW_VISIBILITY_THRESHOLD = 0.5


def render_overlay(video_path: str | Path, pose_json_path: str | Path, output_path: str | Path) -> None:
    video_path, pose_json_path, output_path = Path(video_path), Path(pose_json_path), Path(output_path)

    frames_data = json.loads(pose_json_path.read_text())

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    frame_index = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame_data = frames_data[frame_index] if frame_index < len(frames_data) else None
        landmarks = frame_data["landmarks"] if frame_data else None

        if landmarks is not None:
            points_px = [(int(lm["x"] * width), int(lm["y"] * height)) for lm in landmarks]

            for start, end in CONNECTIONS:
                cv2.line(frame, points_px[start], points_px[end], LINE_COLOR, 2)

            for lm, (px, py) in zip(landmarks, points_px):
                color = POINT_COLOR if lm["visibility"] >= LOW_VISIBILITY_THRESHOLD else (0, 0, 255)
                cv2.circle(frame, (px, py), 4, color, -1)
        else:
            cv2.putText(
                frame, "NO POSE DETECTED", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2,
            )

        writer.write(frame)
        frame_index += 1

    cap.release()
    writer.release()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python -m pipeline.debug_overlay <video_path> <pose_json_path> <output_path>")
        sys.exit(1)
    render_overlay(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"Wrote overlay video to {sys.argv[3]}")
