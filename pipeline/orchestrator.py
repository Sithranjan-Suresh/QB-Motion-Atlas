"""Full pipeline orchestration for one upload (tasks 70-72): pose extraction
through coaching notes, writing the outcome (rejection or AnalysisResult)
back to the DB. A plain function rather than being embedded in the API
route handler, so it's directly callable both as a FastAPI BackgroundTasks
job and from a standalone script/test (task 88's end-to-end smoke test).
"""

from __future__ import annotations

from pathlib import Path

import cv2

from db.base import get_session_factory
from db.models import AnalysisResult, PhaseBoundaryRow, QBReferenceClip, QBReferenceFeature, Upload
from pipeline.coaching import build_deltas, fallback_coaching_notes
from pipeline.confidence import HIGH_THRESHOLD, MEDIUM_THRESHOLD, compute_confidence, similarity_margin
from pipeline.constants import REJECTION_NO_POSE_DETECTED
from pipeline.features import extract_phase_features
from pipeline.handedness import canonicalize_handedness
from pipeline.landmark_filter import filter_low_confidence_landmarks, smooth_jitter
from pipeline.per_phase_similarity import compare_phase_features, group_features_by_phase
from pipeline.phase_segmentation import segment_heuristic
from pipeline.pose_extraction import extract_pose
from pipeline.similarity import compare_features
from pipeline.validation import validate_upload


def _compute_phase_results(session, user_features: dict[str, float]) -> dict[str, dict]:
    """Task 116: per-phase match/score/confidence, one entry per phase that
    has any reference data with that phase populated -- a phase with none
    yet is simply absent from the result (same honest-gap pattern as
    matched_qb_name being nullable overall). Confidence here is a
    simplification of pipeline/confidence.py's full formula: just the
    top1-vs-top2 similarity margin among that phase's candidates, since
    pose-completeness and boundary-confidence are clip-level signals, not
    meaningfully different per phase.
    """
    phase_results: dict[str, dict] = {}
    user_phase_features = group_features_by_phase(user_features)

    for phase_name, phase_vector in user_phase_features.items():
        candidates = session.query(QBReferenceFeature).filter(QBReferenceFeature.phase_name == phase_name).all()
        if not candidates:
            continue

        best_candidate = None
        best_score = -1.0
        scores = []
        for candidate in candidates:
            try:
                score = compare_phase_features(phase_vector, candidate.feature_vector)
            except ValueError:
                continue  # no shared feature keys with this candidate -- skip
            scores.append(score)
            if score > best_score:
                best_score = score
                best_candidate = candidate

        if best_candidate is None:
            continue

        matched_clip = session.query(QBReferenceClip).filter_by(clip_id=best_candidate.clip_id).one()
        margin = similarity_margin(scores)
        confidence = "high" if margin >= HIGH_THRESHOLD else "medium" if margin >= MEDIUM_THRESHOLD else "low"

        phase_results[phase_name] = {
            "matched_qb_name": matched_clip.qb_name,
            "score": best_score,
            "confidence": confidence,
        }

    return phase_results


def _video_fps(video_path: Path) -> float:
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.release()
    return fps


def run_pipeline_for_upload(upload_id: str) -> None:
    """Runs pose extraction -> filtering -> handedness -> validation ->
    (if it passes) phase segmentation -> features -> similarity -> confidence
    -> coaching notes, and writes the result back to `upload_id`'s row. Never
    raises on a bad/unanalyzable video -- that's a rejection, not an error.
    """
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            return

        video_path = Path(upload.video_path)
        fps = upload.fps or _video_fps(video_path)

        frames = extract_pose(video_path)
        frames = filter_low_confidence_landmarks(frames)
        frames = smooth_jitter(frames)

        # canonicalize_handedness (like validate_upload, segment_heuristic, etc.)
        # requires landmarks on every frame -- check for that *before* calling
        # it, not after, since a frame that's still gapped past filtering
        # means a real "no pose detected" rejection, not a bug to raise on.
        if not frames or any(f.landmarks is None for f in frames):
            upload.validation_status = "rejected"
            upload.rejection_reason = REJECTION_NO_POSE_DETECTED
            session.commit()
            return

        frames, _handedness = canonicalize_handedness(frames)

        validation = validate_upload(frames, fps)
        if validation.status == "reject":
            upload.validation_status = "rejected"
            upload.rejection_reason = validation.rejection_reason
            session.commit()
            return

        boundaries = segment_heuristic(frames, fps)
        user_features = extract_phase_features(frames, boundaries, fps)

        # V0-layer feature-distance similarity only (pipeline/similarity.py) --
        # the DTW layer (similarity_dtw.py) needs each reference clip's raw
        # per-frame trajectory, which qb_reference_features doesn't store
        # (only the per-phase feature_vector); wiring that in is future work,
        # not required by this task.
        reference_rows = (
            session.query(QBReferenceFeature).filter(QBReferenceFeature.phase_name.is_(None)).all()
        )
        best_match: QBReferenceFeature | None = None
        best_score = -1.0
        all_scores: list[float] = []
        for row in reference_rows:
            score = compare_features(user_features, row.feature_vector)
            all_scores.append(score)
            if score > best_score:
                best_score = score
                best_match = row

        confidence_level = compute_confidence(frames, boundaries, all_scores)
        phase_results = _compute_phase_results(session, user_features)

        if best_match is not None:
            matched_clip = session.query(QBReferenceClip).filter_by(clip_id=best_match.clip_id).one()
            deltas = build_deltas(user_features, best_match.feature_vector)
            # No project-specific LLM API key is configured (docs/coaching_prompt.md) --
            # go straight to the rule-based notes rather than a live LLM call.
            coaching_notes = fallback_coaching_notes(deltas)
            matched_qb_name = matched_clip.qb_name
            matched_clip_id = matched_clip.clip_id
            overall_score = best_score
        else:
            # Honest "no reference data to match against yet" state -- see
            # db/models.py's note on matched_qb_name being nullable.
            matched_qb_name = None
            matched_clip_id = None
            overall_score = 0.0
            coaching_notes = []

        upload.validation_status = "passed"
        session.add(
            AnalysisResult(
                upload_id=upload.id,
                matched_qb_name=matched_qb_name,
                matched_clip_id=matched_clip_id,
                overall_similarity_score=overall_score,
                confidence_level=confidence_level,
                coaching_notes=coaching_notes,
                phase_results=phase_results,
            )
        )
        for boundary in boundaries:
            session.add(
                PhaseBoundaryRow(
                    upload_id=upload.id,
                    phase_name=boundary.phase_name,
                    start_frame=boundary.start_frame,
                    end_frame=boundary.end_frame,
                    detection_method=boundary.detection_method,
                    confidence=boundary.confidence,
                )
            )
        session.commit()
