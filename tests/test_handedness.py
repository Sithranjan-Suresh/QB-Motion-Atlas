"""Unit tests for pipeline/handedness.py -- left-handed detection and
mirroring correctness (task 42), synthetic landmarks only."""

import math

from pipeline.handedness import (
    LEFT_RIGHT_PAIRS,
    canonicalize_handedness,
    detect_handedness,
    mirror_landmarks,
)
from pipeline.pose_extraction import FrameLandmarks, Landmark

N_FRAMES = 20
NUM_LANDMARKS = 33


def _lm(x: float, y: float, z: float = 0.0, visibility: float = 1.0, presence: float = 1.0) -> Landmark:
    return Landmark(x=x, y=y, z=z, visibility=visibility, presence=presence)


def _right_handed_throw_frames() -> list[FrameLandmarks]:
    """Right wrist (16) swings through a wide arc; left wrist (15) stays put --
    a synthetic clip that should register as right-handed."""
    frames = []
    for i in range(N_FRAMES):
        t = i / (N_FRAMES - 1)
        landmarks = [_lm(0.1 * idx, 0.02 * idx, z=0.01 * idx) for idx in range(NUM_LANDMARKS)]
        landmarks[15] = _lm(0.4, 0.5, z=0.01 * 15)  # left wrist: stationary
        landmarks[16] = _lm(0.6 + 0.3 * math.sin(math.pi * t), 0.5, z=0.01 * 16)  # right wrist: swings
        frames.append(FrameLandmarks(frame_index=i, timestamp_ms=int(i * 33), landmarks=landmarks))
    return frames


def test_detect_handedness_right():
    frames = _right_handed_throw_frames()
    assert detect_handedness(frames) == "right"


def test_detect_handedness_left_on_mirrored_clip():
    frames = _right_handed_throw_frames()
    mirrored = mirror_landmarks(frames)
    assert detect_handedness(mirrored) == "left"


def test_mirror_flips_x_and_preserves_other_fields():
    frames = _right_handed_throw_frames()
    mirrored = mirror_landmarks(frames)
    for original_frame, mirrored_frame in zip(frames, mirrored):
        for idx in range(NUM_LANDMARKS):
            orig = original_frame.landmarks[idx]
            # x is flipped for every landmark (before any left/right index swap).
            assert math.isclose(1.0 - orig.x, _find_mirrored_x(mirrored_frame, orig), abs_tol=1e-9)


def _find_mirrored_x(mirrored_frame: FrameLandmarks, orig_lm: Landmark) -> float:
    # z/visibility/presence are untouched by mirroring, so the same landmark
    # (wherever it ended up after the left/right swap) can be located by them.
    for lm in mirrored_frame.landmarks:
        if lm.z == orig_lm.z and lm.visibility == orig_lm.visibility:
            return lm.x
    raise AssertionError("could not locate mirrored landmark")


def test_mirror_swaps_left_right_pairs():
    frames = _right_handed_throw_frames()
    mirrored = mirror_landmarks(frames)
    for original_frame, mirrored_frame in zip(frames, mirrored):
        for left_idx, right_idx in LEFT_RIGHT_PAIRS:
            # the mirrored frame's left-index slot holds the flipped version of
            # the original's right-index landmark (same z/visibility identity).
            assert mirrored_frame.landmarks[left_idx].z == original_frame.landmarks[right_idx].z
            assert mirrored_frame.landmarks[right_idx].z == original_frame.landmarks[left_idx].z


def test_mirror_is_involution():
    frames = _right_handed_throw_frames()
    round_tripped = mirror_landmarks(mirror_landmarks(frames))
    for original_frame, round_tripped_frame in zip(frames, round_tripped):
        for idx in range(NUM_LANDMARKS):
            assert math.isclose(original_frame.landmarks[idx].x, round_tripped_frame.landmarks[idx].x, abs_tol=1e-9)


def test_canonicalize_handedness_right_unchanged():
    frames = _right_handed_throw_frames()
    canonical, handedness = canonicalize_handedness(frames)
    assert handedness == "right"
    assert canonical[0].landmarks[16].x == frames[0].landmarks[16].x


def test_canonicalize_handedness_left_gets_mirrored():
    frames = _right_handed_throw_frames()
    left_handed_clip = mirror_landmarks(frames)
    canonical, handedness = canonicalize_handedness(left_handed_clip)
    assert handedness == "left"
    # after canonicalizing, the throwing motion should be back on the right
    # wrist, matching the original right-handed clip's right-wrist trajectory.
    for canonical_frame, original_frame in zip(canonical, frames):
        assert math.isclose(canonical_frame.landmarks[16].x, original_frame.landmarks[16].x, abs_tol=1e-9)
