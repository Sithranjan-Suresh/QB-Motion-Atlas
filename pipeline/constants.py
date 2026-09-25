"""Shared rejection-reason codes and copy for upload validation
(docs/validation_rules.md), so the API layer and frontend render the same
message from one source of truth instead of duplicating strings.

The frontend doesn't exist yet (V1 backend/frontend tasks are still ahead
in implementation_checklist.md) -- this is the Python side of that shared
source; when the Next.js frontend is scaffolded, its copy should be
generated from (or kept in lockstep with) REJECTION_MESSAGES below rather
than re-authored independently.
"""

from __future__ import annotations

REJECTION_BAD_CAMERA_ANGLE = "bad_camera_angle"
REJECTION_BODY_NOT_FULLY_VISIBLE = "body_not_fully_visible"
REJECTION_NO_THROW_DETECTED = "no_throw_detected"
REJECTION_MULTIPLE_THROWS_DETECTED = "multiple_throws_detected"
# Cruder than the four above (which all assume landmarks exist on every
# frame, per validate_upload's precondition) -- pipeline/orchestrator.py's
# earlier, simpler failure: no person was detected in the clip at all.
REJECTION_NO_POSE_DETECTED = "no_pose_detected"

REJECTION_MESSAGES: dict[str, str] = {
    REJECTION_BAD_CAMERA_ANGLE: (
        "Camera angle looks frontal/behind rather than to your throwing side. "
        "Move the camera to your throwing-arm side, roughly perpendicular to your body."
    ),
    REJECTION_BODY_NOT_FULLY_VISIBLE: (
        "Can't see your full body (head to mid-thigh) through the whole throw. "
        "Back up or reframe so your legs and throwing arm stay in frame."
    ),
    REJECTION_NO_THROW_DETECTED: (
        "Didn't detect a throwing motion in this clip. "
        "Make sure the full load-through-release motion is visible."
    ),
    REJECTION_MULTIPLE_THROWS_DETECTED: (
        "Detected more than one throwing motion in this clip. Upload a single throw per video."
    ),
    REJECTION_NO_POSE_DETECTED: (
        "Couldn't detect a person in this video at all. "
        "Make sure you're clearly visible, well-lit, and not too far from the camera."
    ),
}
