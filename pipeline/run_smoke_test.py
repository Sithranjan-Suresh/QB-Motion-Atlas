"""End-to-end local pipeline smoke test (task 88): run a video through the
full pipeline directly -- pose extraction through coaching notes -- with no
API or database involved, asserting every output field actually populates.

Usage: python -m pipeline.run_smoke_test <video_path>

Note (2026-09-25): can't be run against a real "known test video" in this
cloud session -- the YouTube network-access blocker (docs/research_log.md)
means there's no real throw footage available to use as one. tests/test_smoke.py
exercises run_smoke_test() with pose extraction mocked to synthetic
landmarks, which verifies the full wiring end-to-end (every stage actually
runs and every field populates) using the same "validate with synthetic
data where real data is blocked" approach as the rest of this session.
Re-run this script for real once real footage exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2

from pipeline.coaching import build_deltas, fallback_coaching_notes
from pipeline.confidence import compute_confidence
from pipeline.features import extract_phase_features
from pipeline.handedness import canonicalize_handedness
from pipeline.landmark_filter import filter_low_confidence_landmarks, smooth_jitter
from pipeline.phase_segmentation import segment_heuristic
from pipeline.pose_extraction import extract_pose
from pipeline.similarity import compare_features
from pipeline.validation import validate_upload


def _video_fps(video_path: Path) -> float:
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.release()
    return fps


def run_smoke_test(video_path: str | Path) -> dict:
    """Runs every pipeline stage on `video_path` and asserts each one
    produces real output, returning a summary dict. No reference database
    exists in this standalone (non-API) context, so similarity/confidence/
    coaching are exercised against a deliberately-perturbed copy of the
    upload's own features standing in for "a reference clip" -- enough to
    prove every field populates end-to-end without needing a live DB.
    """
    video_path = Path(video_path)
    fps = _video_fps(video_path)

    frames = extract_pose(video_path)
    assert frames, "extract_pose returned no frames"

    frames = filter_low_confidence_landmarks(frames)
    frames = smooth_jitter(frames)
    assert not any(f.landmarks is None for f in frames), (
        "gaps remain after filtering -- no person detected throughout the clip?"
    )

    frames, handedness = canonicalize_handedness(frames)
    assert handedness in ("left", "right")

    validation = validate_upload(frames, fps)
    assert validation.status == "pass", f"validation rejected this clip: {validation.rejection_reason}"

    boundaries = segment_heuristic(frames, fps)
    assert len(boundaries) == 6
    for boundary in boundaries:
        assert 0.0 <= boundary.confidence <= 1.0

    features = extract_phase_features(frames, boundaries, fps)
    assert len(features) == 17

    reference_features = {k: v * 1.1 + 0.01 for k, v in features.items()}
    similarity_score = compare_features(features, reference_features)
    assert 0.0 < similarity_score <= 1.0

    confidence = compute_confidence(frames, boundaries, [similarity_score])
    assert confidence in ("high", "medium", "low")

    deltas = build_deltas(features, reference_features)
    assert len(deltas) == len(features)

    coaching_notes = fallback_coaching_notes(deltas)
    assert len(coaching_notes) > 0

    return {
        "handedness": handedness,
        "validation_status": validation.status,
        "boundaries": boundaries,
        "features": features,
        "similarity_score": similarity_score,
        "confidence": confidence,
        "coaching_notes": coaching_notes,
    }


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m pipeline.run_smoke_test <video_path>")
        sys.exit(1)

    result = run_smoke_test(sys.argv[1])
    print("Smoke test passed. Summary:")
    print(f"  handedness: {result['handedness']}")
    print(f"  validation: {result['validation_status']}")
    print(f"  phases: {[b.phase_name for b in result['boundaries']]}")
    print(f"  features: {len(result['features'])} keys")
    print(f"  similarity_score: {result['similarity_score']:.3f}")
    print(f"  confidence: {result['confidence']}")
    print(f"  coaching_notes: {len(result['coaching_notes'])} notes")


if __name__ == "__main__":
    main()
