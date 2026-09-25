"""FastAPI app entry point (task 68). Endpoints are added incrementally in
tasks 69-76; this is the scaffold: app instance + a health check.

Run locally: uvicorn api.main:app --reload
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import cv2
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import func

from api.schemas import (
    AnalysisResultResponse,
    ComparisonResponse,
    LandmarkSequenceResponse,
    QBSummaryResponse,
    UploadCreatedResponse,
    UploadStatusResponse,
)
from api.storage import save_upload
from db.base import get_session_factory
from db.models import AnalysisResult, LandmarkSequence, QBReferenceClip, Upload
from pipeline.landmark_overlay import deserialize_overlay_frames
from pipeline.orchestrator import run_pipeline_for_upload
from pipeline.similarity_dtw import build_frame_trajectory, dtw_align

app = FastAPI(title="QB Motion Atlas API")

# The frontend (task 78) runs on a different origin (localhost:3000 in dev,
# the deployed Vercel URL in prod, task 92) than this API -- without CORS
# headers, every browser fetch from it is silently blocked. Configurable via
# CORS_ALLOWED_ORIGINS (comma-separated) so the deployed origin can be added
# without a code change; defaults to the local Next.js dev server.
_cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Task 76: request validation constants. Duration ceiling matches
# full_context.md's "5-15 second side-view video" upload expectation, with a
# small buffer for encoding/rounding slop. video/webm added for task 121 --
# MediaRecorder (the live webcam capture path) records to webm, not mp4.
ALLOWED_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/webm"}
MAX_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_DURATION_SEC = 15.5
# Found missing during task 89's edge-case review: a "too-short" clip has no
# floor at all without this. 2.0s is a conservative technical minimum -- not
# the product's 5s *recommended* floor (that's sourcing guidance to the
# user, not a hard cutoff) -- below which no real load-through-follow-
# through motion could physically fit even at a fast tempo.
MIN_DURATION_SEC = 2.0


def _video_fps_and_duration_sec(video_path: Path) -> tuple[float, float] | None:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        return None
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    if not fps or not frame_count:
        return None
    return fps, frame_count / fps


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/uploads", response_model=UploadCreatedResponse, status_code=201)
async def create_upload(file: UploadFile, background_tasks: BackgroundTasks) -> UploadCreatedResponse:
    """Task 69: accept a multipart video upload, save it to local storage,
    and create the `uploads` row. Task 70: trigger the full pipeline
    (pipeline/orchestrator.py) as a background job -- it writes the
    validation outcome or AnalysisResult (tasks 71-72) back to the DB itself
    once it finishes, asynchronously to this response. Task 76: reject an
    obviously-bad request (wrong file type, too large, too long) with a
    clear 4xx *before* creating any DB row or committing to processing it --
    distinct from pipeline/validation.py's pose-based rejections, which need
    a saved, decodable file to even run.
    """
    # Browsers report MediaRecorder's blob type with a codecs parameter
    # (e.g. "video/webm;codecs=vp9", task 121) -- compare against the base
    # MIME type only, found via real Playwright browser testing rejecting
    # every real webcam recording outright until this was split off.
    base_content_type = (file.content_type or "").split(";")[0].strip()
    if base_content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {file.content_type}")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"file exceeds the {MAX_UPLOAD_SIZE_BYTES} byte limit")

    upload_id = str(uuid.uuid4())
    video_path = save_upload(upload_id, file.filename or "upload.mp4", contents)

    probe = _video_fps_and_duration_sec(video_path)
    if probe is None:
        video_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="could not read video file")
    fps, duration_sec = probe
    if duration_sec > MAX_DURATION_SEC:
        video_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400, detail=f"video is {duration_sec:.1f}s, longer than the {MAX_DURATION_SEC}s limit"
        )
    if duration_sec < MIN_DURATION_SEC:
        video_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400, detail=f"video is {duration_sec:.1f}s, shorter than the {MIN_DURATION_SEC}s minimum"
        )

    session_factory = get_session_factory()
    with session_factory() as session:
        upload = Upload(id=upload_id, video_path=str(video_path), validation_status="processing", fps=fps)
        session.add(upload)
        session.commit()

    background_tasks.add_task(run_pipeline_for_upload, upload_id)

    return UploadCreatedResponse(upload_id=upload_id, status="processing")


@app.get("/uploads/{upload_id}/status", response_model=UploadStatusResponse)
def get_upload_status(upload_id: str) -> UploadStatusResponse:
    """Task 73."""
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            raise HTTPException(status_code=404, detail="upload not found")
        return UploadStatusResponse(
            upload_id=upload.id,
            status=upload.validation_status,
            rejection_reason=upload.rejection_reason,
        )


@app.get("/results/{upload_id}", response_model=AnalysisResultResponse)
def get_results(upload_id: str) -> AnalysisResultResponse:
    """Task 74. 404s both when the upload doesn't exist and when it's still
    processing (or was rejected, so no AnalysisResult was ever written) --
    the client is expected to check `/uploads/{id}/status` first to tell
    those cases apart, per docs/coaching_prompt.md's / frontend task 85's
    "not ready yet" handling.
    """
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            raise HTTPException(status_code=404, detail="upload not found")

        result = session.query(AnalysisResult).filter_by(upload_id=upload_id).one_or_none()
        if result is None:
            raise HTTPException(status_code=404, detail="result not ready")

        return AnalysisResultResponse(
            upload_id=upload_id,
            matched_qb_name=result.matched_qb_name,
            matched_clip_id=result.matched_clip_id,
            overall_similarity_score=result.overall_similarity_score,
            confidence_level=result.confidence_level,
            coaching_notes=result.coaching_notes,
            phase_results=result.phase_results,
        )


_VIDEO_MEDIA_TYPES = {".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}


@app.get("/uploads/{upload_id}/video")
def get_upload_video(upload_id: str) -> FileResponse:
    """Tasks 124-125: serves the upload's own saved file back for playback --
    only ever the user's own footage (never a reference clip's), so there's
    no licensing concern here the way there would be for re-serving
    copyrighted reference-clip video (see docs/research_log.md's note on why
    the synced comparison, task 125, renders the matched QB as a skeleton-
    only animation instead of streaming its source video)."""
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            raise HTTPException(status_code=404, detail="upload not found")

        video_path = Path(upload.video_path)
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="video file not found")

        media_type = _VIDEO_MEDIA_TYPES.get(video_path.suffix.lower(), "application/octet-stream")
        return FileResponse(video_path, media_type=media_type)


@app.get("/uploads/{upload_id}/landmarks", response_model=LandmarkSequenceResponse)
def get_upload_landmarks(upload_id: str) -> LandmarkSequenceResponse:
    """Task 123-124: the upload's own per-frame landmark sequence, for
    SkeletonOverlayPlayer to draw on top of the user's own video. 404s the
    same two ways as /results/{id} -- not found, or not written yet
    (rejected upload, or still processing)."""
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            raise HTTPException(status_code=404, detail="upload not found")

        sequence = session.query(LandmarkSequence).filter_by(upload_id=upload_id).one_or_none()
        if sequence is None:
            raise HTTPException(status_code=404, detail="landmark data not ready")

        return LandmarkSequenceResponse(fps=sequence.fps, frames=sequence.frames)


@app.get("/results/{upload_id}/comparison", response_model=ComparisonResponse)
def get_comparison(upload_id: str) -> ComparisonResponse:
    """Task 125: user + matched-reference-clip landmark sequences plus their
    DTW frame alignment, for the synced side-by-side view. `reference` and
    `alignment` are null (not a 404) when the upload has no match yet or the
    matched clip has no landmark data of its own -- same honest-gap pattern
    as everywhere else in this project, since the user's own overlay (task
    124) is still fully usable without a reference to compare against.
    """
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            raise HTTPException(status_code=404, detail="upload not found")

        result = session.query(AnalysisResult).filter_by(upload_id=upload_id).one_or_none()
        user_sequence = session.query(LandmarkSequence).filter_by(upload_id=upload_id).one_or_none()
        if result is None or user_sequence is None:
            raise HTTPException(status_code=404, detail="result not ready")

        user_response = LandmarkSequenceResponse(fps=user_sequence.fps, frames=user_sequence.frames)

        if result.matched_clip_id is None:
            return ComparisonResponse(user=user_response, reference=None, reference_qb_name=None, alignment=None)

        reference_sequence = (
            session.query(LandmarkSequence).filter_by(reference_clip_id=result.matched_clip_id).one_or_none()
        )
        if reference_sequence is None:
            return ComparisonResponse(
                user=user_response, reference=None, reference_qb_name=result.matched_qb_name, alignment=None
            )

        user_trajectory = build_frame_trajectory(deserialize_overlay_frames(user_sequence.frames), user_sequence.fps)
        reference_trajectory = build_frame_trajectory(
            deserialize_overlay_frames(reference_sequence.frames), reference_sequence.fps
        )
        alignment, _distance = dtw_align(user_trajectory, reference_trajectory)

        return ComparisonResponse(
            user=user_response,
            reference=LandmarkSequenceResponse(fps=reference_sequence.fps, frames=reference_sequence.frames),
            reference_qb_name=result.matched_qb_name,
            alignment=[list(pair) for pair in alignment],
        )


@app.get("/qbs", response_model=list[QBSummaryResponse])
def list_qbs() -> list[QBSummaryResponse]:
    """Task 75: reference QB list + clip counts. Archetype labels (per the
    checklist's "reference QB list + archetype labels") are a V2 concept --
    they'd come from the learned embedding model's clustering, which doesn't
    exist yet; qb_name + clip_count is what's actually backed by real data
    right now.
    """
    session_factory = get_session_factory()
    with session_factory() as session:
        rows = (
            session.query(QBReferenceClip.qb_name, func.count(QBReferenceClip.id))
            .group_by(QBReferenceClip.qb_name)
            .order_by(QBReferenceClip.qb_name)
            .all()
        )
        return [QBSummaryResponse(qb_name=qb_name, clip_count=count) for qb_name, count in rows]
