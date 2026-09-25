// MediaPipe Pose's 33-landmark topology (pipeline/pose_extraction.py), the
// subset of joint connections relevant to a throwing motion -- shared by
// SkeletonOverlayPlayer's canvas draw for both the video-overlay mode and
// the reference-clip skeleton-only mode.
export const POSE_CONNECTIONS: [number, number][] = [
  [0, 11],
  [0, 12], // head -> shoulders (rough neck)
  [11, 12], // shoulders
  [11, 13],
  [13, 15], // left arm
  [12, 14],
  [14, 16], // right (throwing) arm
  [11, 23],
  [12, 24], // torso sides
  [23, 24], // hips
  [23, 25],
  [25, 27], // left leg
  [24, 26],
  [26, 28], // right leg
  [27, 29],
  [29, 31],
  [27, 31], // left foot
  [28, 30],
  [30, 32],
  [28, 32], // right foot
];
