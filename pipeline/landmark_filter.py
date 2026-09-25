"""Per-joint low-confidence interpolation over short gaps.

MediaPipe reports a `visibility` score per landmark per frame. A joint can be
individually low-visibility (occluded, motion blur) even when the rest of the
pose tracks fine, and a whole frame can have no detection at all. Rather than
dropping those frames, interpolate each affected joint from the nearest good
frames on either side -- but only across short gaps. A gap that's too long,
or missing a good frame on one side (e.g. at a clip boundary), is left alone
so a fabricated interpolation never masquerades as a real observation.
"""

from __future__ import annotations

import copy

from scipy.signal import savgol_filter

from pipeline.pose_extraction import NUM_LANDMARKS, FrameLandmarks, Landmark

DEFAULT_VISIBILITY_THRESHOLD = 0.5
DEFAULT_MAX_GAP_FRAMES = 5
DEFAULT_SMOOTHING_WINDOW = 5  # frames; must be odd for savgol_filter
DEFAULT_SMOOTHING_POLYORDER = 2


def _is_low_confidence(frame: FrameLandmarks, joint_index: int, threshold: float) -> bool:
    if frame.landmarks is None:
        return True
    return frame.landmarks[joint_index].visibility < threshold


def _interpolate_value(start: float, end: float, step: int, total_steps: int) -> float:
    t = step / total_steps
    return start + (end - start) * t


def filter_low_confidence_landmarks(
    frames: list[FrameLandmarks],
    visibility_threshold: float = DEFAULT_VISIBILITY_THRESHOLD,
    max_gap_frames: int = DEFAULT_MAX_GAP_FRAMES,
) -> list[FrameLandmarks]:
    """Return a new list of frames with short low-confidence joint gaps interpolated."""
    frames = copy.deepcopy(frames)

    for joint_index in range(NUM_LANDMARKS):
        i = 0
        while i < len(frames):
            if not _is_low_confidence(frames[i], joint_index, visibility_threshold):
                i += 1
                continue

            gap_start = i
            while i < len(frames) and _is_low_confidence(frames[i], joint_index, visibility_threshold):
                i += 1
            gap_end = i  # exclusive

            gap_len = gap_end - gap_start
            has_before = gap_start > 0 and frames[gap_start - 1].landmarks is not None
            has_after = gap_end < len(frames) and frames[gap_end].landmarks is not None

            if gap_len > max_gap_frames or not has_before or not has_after:
                continue  # leave this run untouched -- real gap, not fabricated

            before = frames[gap_start - 1].landmarks[joint_index]
            after = frames[gap_end].landmarks[joint_index]

            for step, frame_idx in enumerate(range(gap_start, gap_end), start=1):
                frame = frames[frame_idx]
                if frame.landmarks is None:
                    frame.landmarks = [
                        Landmark(x=0.0, y=0.0, z=0.0, visibility=0.0, presence=0.0)
                        for _ in range(NUM_LANDMARKS)
                    ]
                frame.landmarks[joint_index] = Landmark(
                    x=_interpolate_value(before.x, after.x, step, gap_len + 1),
                    y=_interpolate_value(before.y, after.y, step, gap_len + 1),
                    z=_interpolate_value(before.z, after.z, step, gap_len + 1),
                    visibility=_interpolate_value(before.visibility, after.visibility, step, gap_len + 1),
                    presence=_interpolate_value(before.presence, after.presence, step, gap_len + 1),
                    interpolated=True,
                )

    return frames


def smooth_jitter(
    frames: list[FrameLandmarks],
    window: int = DEFAULT_SMOOTHING_WINDOW,
    polyorder: int = DEFAULT_SMOOTHING_POLYORDER,
) -> list[FrameLandmarks]:
    """V1 hardening (task 39): apply a light Savitzky-Golay smoothing pass to each joint's
    (x, y) trajectory, reducing frame-to-frame jitter that the velocity-threshold logic in
    phase_segmentation.py and validation.py is sensitive to.

    Run this *after* `filter_low_confidence_landmarks` -- smoothing only reduces noise in
    data that's already there, it never fills gaps. Only z, visibility, and presence are left
    untouched (z isn't used downstream yet, and smoothing visibility/presence would blur the
    genuine confidence dips that gap-detection logic elsewhere relies on). Smoothing is only
    applied within a contiguous run of detected frames at least `window` long; shorter runs
    are left as-is rather than smoothed over too small a sample to be meaningful.
    """
    frames = copy.deepcopy(frames)
    n = len(frames)

    for joint_index in range(NUM_LANDMARKS):
        i = 0
        while i < n:
            if frames[i].landmarks is None:
                i += 1
                continue

            run_start = i
            while i < n and frames[i].landmarks is not None:
                i += 1
            run_end = i  # exclusive
            run_len = run_end - run_start

            if run_len < window:
                continue  # too short to smooth meaningfully -- leave untouched

            xs = [frames[j].landmarks[joint_index].x for j in range(run_start, run_end)]
            ys = [frames[j].landmarks[joint_index].y for j in range(run_start, run_end)]
            smoothed_x = savgol_filter(xs, window, polyorder)
            smoothed_y = savgol_filter(ys, window, polyorder)

            for offset, frame_idx in enumerate(range(run_start, run_end)):
                lm = frames[frame_idx].landmarks[joint_index]
                frames[frame_idx].landmarks[joint_index] = Landmark(
                    x=float(smoothed_x[offset]),
                    y=float(smoothed_y[offset]),
                    z=lm.z,
                    visibility=lm.visibility,
                    presence=lm.presence,
                    interpolated=lm.interpolated,
                )

    return frames
