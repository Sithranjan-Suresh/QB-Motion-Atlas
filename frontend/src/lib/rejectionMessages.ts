// Mirrors pipeline/constants.py::REJECTION_MESSAGES -- one source of truth
// in spirit (task 38), kept in lockstep by hand across the Python/TS
// language boundary since there's no shared codegen step for this yet. If
// you change one side, change the other.

export const REJECTION_MESSAGES: Record<string, string> = {
  bad_camera_angle:
    "Camera angle looks frontal/behind rather than to your throwing side. Move the camera to your throwing-arm side, roughly perpendicular to your body.",
  body_not_fully_visible:
    "Can't see your full body (head to mid-thigh) through the whole throw. Back up or reframe so your legs and throwing arm stay in frame.",
  no_throw_detected:
    "Didn't detect a throwing motion in this clip. Make sure the full load-through-release motion is visible.",
  multiple_throws_detected:
    "Detected more than one throwing motion in this clip. Upload a single throw per video.",
  no_pose_detected:
    "Couldn't detect a person in this video at all. Make sure you're clearly visible, well-lit, and not too far from the camera.",
};

export function rejectionMessage(reason: string | null): string {
  if (!reason) {
    return "This video was rejected for an unspecified reason.";
  }
  return REJECTION_MESSAGES[reason] ?? `This video was rejected: ${reason}`;
}
