"""FastAPI app entry point (task 68).

Run locally: uvicorn api.main:app --reload
"""

from __future__ import annotations

import contextlib
import logging
import os
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

import cv2
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, text

from api.schemas import (
    AnalysisResultResponse,
    ComparisonResponse,
    LandmarkSequenceResponse,
    QBSummaryResponse,
    UploadCreatedResponse,
    UploadStatusResponse,
)
from api import worker
from api.logging_config import configure_logging
from api.rate_limit import client_ip, upload_limiter
from api.retention import purge_upload, retention_days
from api.storage import get_storage, reference_clip_key, upload_key
from db.base import get_session_factory
from db.models import AnalysisResult, LandmarkSequence, PhaseBoundaryRow, QBReferenceClip, Upload
from pipeline.landmark_overlay import deserialize_overlay_frames
from pipeline.share_card import render_share_card
from pipeline.similarity_dtw import build_frame_trajectory, dtw_align
from pipeline.video_licensing import is_video_overlay_eligible

configure_logging()
logger = logging.getLogger("api")


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    stop_event = threading.Event()
    if worker.job_runner() == "worker":
        worker.start_worker_threads(stop_event)
        logger.info("upload worker threads started")
    yield
    stop_event.set()


app = FastAPI(title="QB Motion Atlas API", lifespan=lifespan)

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
_UPLOAD_CHUNK_BYTES = 1024 * 1024
# Beyond this many queued/running jobs, new uploads get a 503 instead of
# waiting behind a backlog they'd likely give up on.
MAX_QUEUED_UPLOADS = int(os.environ.get("MAX_QUEUED_UPLOADS", "20"))
# ISO-BMFF box types that can open an mp4/mov file, at bytes 4-8.
_MP4_BOX_TYPES = {b"ftyp", b"moov", b"mdat", b"wide", b"free", b"skip"}
_WEBM_MAGIC = b"\x1a\x45\xdf\xa3"
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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Rejects an oversized upload from its Content-Length header before the
    # multipart body is parsed at all.
    if request.method == "POST" and request.url.path == "/uploads":
        declared = request.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_UPLOAD_SIZE_BYTES + _UPLOAD_CHUNK_BYTES:
            return JSONResponse(
                status_code=413, content={"detail": f"file exceeds the {MAX_UPLOAD_SIZE_BYTES} byte limit"}
            )
    started = time.monotonic()
    response = await call_next(request)
    if request.url.path not in ("/health", "/health/ready"):
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.monotonic() - started) * 1000, 1),
            },
        )
    return response


@app.get("/health")
def health() -> dict:
    """Liveness: the process is up. Cheap enough for uptime pingers."""
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready() -> JSONResponse:
    """Readiness: the database answers and the queue isn't wedged."""
    checks: dict[str, object] = {}
    healthy = True
    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        checks["database"] = "ok"
        checks["queue_depth"] = worker.queue_depth()
    except Exception as error:  # noqa: BLE001
        healthy = False
        checks["database"] = f"error: {type(error).__name__}"
    checks["job_runner"] = worker.job_runner()
    checks["storage"] = type(get_storage()).__name__
    return JSONResponse(status_code=200 if healthy else 503, content={"status": "ok" if healthy else "error", **checks})


def _looks_like_video(head: bytes) -> bool:
    return head[4:8] in _MP4_BOX_TYPES or head.startswith(_WEBM_MAGIC)


async def _stream_to_temp_file(file: UploadFile, suffix: str) -> Path:
    """Copies the upload to a temp file in 1 MB chunks, enforcing the size
    cap as it goes -- never holds the whole video in memory."""
    fd, tmp_name = tempfile.mkstemp(suffix=suffix)
    tmp_path = Path(tmp_name)
    total = 0
    try:
        with os.fdopen(fd, "wb") as out:
            while chunk := await file.read(_UPLOAD_CHUNK_BYTES):
                total += len(chunk)
                if total > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(status_code=400, detail=f"file exceeds the {MAX_UPLOAD_SIZE_BYTES} byte limit")
                out.write(chunk)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
    return tmp_path


@app.post("/uploads", response_model=UploadCreatedResponse, status_code=201)
async def create_upload(request: Request, file: UploadFile, background_tasks: BackgroundTasks) -> UploadCreatedResponse:
    """Task 69: accept a multipart video upload, store it, and queue it
    (api/worker.py) -- the worker writes the validation outcome or
    AnalysisResult (tasks 71-72) back to the DB. Task 76: reject an
    obviously-bad request (wrong type, not actually a video, too large, too
    long/short) with a clear 4xx before creating any DB row -- distinct from
    pipeline/validation.py's pose-based rejections. Rate-limited per client
    and refused with a 503 when the queue is already full.
    """
    # Browsers report MediaRecorder's blob type with a codecs parameter
    # (e.g. "video/webm;codecs=vp9", task 121) -- compare against the base
    # MIME type only, found via real Playwright browser testing rejecting
    # every real webcam recording outright until this was split off.
    base_content_type = (file.content_type or "").split(";")[0].strip()
    if base_content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {file.content_type}")

    retry_after = upload_limiter.check(client_ip(request))
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="too many uploads from this address -- try again later",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )
    if worker.queue_depth() >= MAX_QUEUED_UPLOADS:
        raise HTTPException(
            status_code=503, detail="the analyzer is busy right now -- try again in a few minutes",
            headers={"Retry-After": "120"},
        )

    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".mp4", ".mov", ".webm"):
        ext = {"video/quicktime": ".mov", "video/webm": ".webm"}.get(base_content_type, ".mp4")

    tmp_path = await _stream_to_temp_file(file, ext)
    try:
        with open(tmp_path, "rb") as f:
            head = f.read(16)
        if not _looks_like_video(head):
            raise HTTPException(status_code=400, detail="file is not a readable video")

        probe = _video_fps_and_duration_sec(tmp_path)
        if probe is None:
            raise HTTPException(status_code=400, detail="could not read video file")
        fps, duration_sec = probe
        if duration_sec > MAX_DURATION_SEC:
            raise HTTPException(
                status_code=400, detail=f"video is {duration_sec:.1f}s, longer than the {MAX_DURATION_SEC}s limit"
            )
        if duration_sec < MIN_DURATION_SEC:
            raise HTTPException(
                status_code=400, detail=f"video is {duration_sec:.1f}s, shorter than the {MIN_DURATION_SEC}s minimum"
            )

        upload_id = str(uuid.uuid4())
        key = upload_key(upload_id, ext)
        get_storage().put_file(key, tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    session_factory = get_session_factory()
    with session_factory() as session:
        upload = Upload(id=upload_id, video_path=key, validation_status="processing", fps=fps)
        session.add(upload)
        session.commit()

    logger.info("upload queued", extra={"upload_id": upload_id, "duration_sec": round(duration_sec, 2)})
    if worker.job_runner() == "inline":
        background_tasks.add_task(worker.process_upload_inline, upload_id)

    return UploadCreatedResponse(upload_id=upload_id, status="processing")


@app.delete("/uploads/{upload_id}", status_code=204)
def delete_upload(upload_id: str) -> Response:
    """Deletes the user's video and everything derived from it. Anyone
    holding the upload id can do this -- the same trust model as viewing
    the results (the id is an unguessable UUID only its uploader has)."""
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            raise HTTPException(status_code=404, detail="upload not found")
        if upload.validation_status == "processing" and upload.locked_at is not None:
            raise HTTPException(status_code=409, detail="still processing -- try again when it finishes")
        purge_upload(session, upload)
        session.commit()
    return Response(status_code=204)


@app.get("/privacy/retention")
def get_retention_policy() -> dict:
    """Lets the frontend show the real retention period instead of a copy of it."""
    return {"upload_retention_days": retention_days()}


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


@app.get("/uploads/{upload_id}/video")
def get_upload_video(upload_id: str, request: Request) -> Response:
    """Tasks 124-125: serves the upload's own saved file back for playback
    (a redirect to a short-lived signed URL when storage is S3-compatible)."""
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            raise HTTPException(status_code=404, detail="upload not found")
        key = upload.video_path

    storage = get_storage()
    if not storage.exists(key):
        raise HTTPException(status_code=404, detail="video file not found")
    return storage.response(key, request)


TRIMMED_DIR = Path(__file__).resolve().parent.parent / "data" / "trimmed"


def _reference_clip_source_path(clip_id: str) -> Path:
    qb_name, clip_name = clip_id.split("__", 1)
    return TRIMMED_DIR / qb_name / f"{clip_name}.mp4"


def trim_video(source_path: Path, start_sec: float, end_sec: float, out_path: Path) -> bool:
    """Re-encodes `source_path` between the two timestamps into `out_path`
    (H.264 + faststart, so browsers can start playback before the whole file
    arrives). Returns whether it succeeded."""
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source_path), "-ss", f"{start_sec:.3f}",
            "-to", f"{end_sec:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", str(out_path),
        ],
        capture_output=True, text=True, timeout=120,
    )
    return result.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0


def _publish_trimmed_reference_video(clip_id: str, session) -> bool:
    """Task A3: never serves more of the source clip than the frame range
    actually covered by its phase boundaries. Production storage is filled
    ahead of time by scripts/publish_reference_data.py; this on-demand path
    covers local dev, where data/trimmed/ exists on the same machine. The
    result is cached in storage so the ffmpeg trim runs once per clip."""
    source_path = _reference_clip_source_path(clip_id)
    if not source_path.exists():
        return False

    boundaries = session.query(PhaseBoundaryRow).filter_by(reference_clip_id=clip_id).all()
    landmark_sequence = session.query(LandmarkSequence).filter_by(reference_clip_id=clip_id).one_or_none()
    if not boundaries or landmark_sequence is None:
        return False

    start_sec = min(b.start_frame for b in boundaries) / landmark_sequence.fps
    end_sec = max(b.end_frame for b in boundaries) / landmark_sequence.fps

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / f"{clip_id}.mp4"
        if not trim_video(source_path, start_sec, end_sec, out_path):
            return False
        get_storage().put_file(reference_clip_key(clip_id), out_path)
    return True


@app.get("/reference-clips/{clip_id}/video")
def get_reference_clip_video(clip_id: str, request: Request) -> Response:
    """Task A1: serves a reference clip's own video for the skeleton overlay
    -- only for clips classified video-overlay-eligible
    (pipeline/video_licensing.py). An ineligible clip (or every clip, if the
    REFERENCE_VIDEO_OVERLAY_ENABLED kill-switch is off) 404s here on
    purpose, the same way a "not ready yet" result 404s -- the frontend is
    expected to fall back to skeleton-only, not treat this as an error."""
    session_factory = get_session_factory()
    with session_factory() as session:
        clip = session.query(QBReferenceClip).filter_by(clip_id=clip_id).one_or_none()
        if clip is None:
            raise HTTPException(status_code=404, detail="reference clip not found")
        if not is_video_overlay_eligible(clip.license_note):
            raise HTTPException(status_code=404, detail="video overlay not available for this clip")

        storage = get_storage()
        key = reference_clip_key(clip_id)
        if not storage.exists(key) and not _publish_trimmed_reference_video(clip_id, session):
            raise HTTPException(status_code=404, detail="video file not found")

    return storage.response(key, request)


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

        reference_clip = session.query(QBReferenceClip).filter_by(clip_id=result.matched_clip_id).one_or_none()
        video_eligible = reference_clip is not None and is_video_overlay_eligible(reference_clip.license_note)
        # Task A7: only surfaced when the actual reference video is shown
        # (not the skeleton-only fallback) -- attributes the footage to its
        # source as a goodwill/fair-use gesture toward the original creator.
        source_url = reference_clip.source_url if video_eligible and reference_clip is not None else None

        reference_sequence = (
            session.query(LandmarkSequence).filter_by(reference_clip_id=result.matched_clip_id).one_or_none()
        )
        if reference_sequence is None:
            return ComparisonResponse(
                user=user_response,
                reference=None,
                reference_qb_name=result.matched_qb_name,
                alignment=None,
                reference_video_eligible=video_eligible,
                reference_clip_source_url=source_url,
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
            reference_video_eligible=video_eligible,
            reference_clip_source_url=source_url,
        )


@app.post("/results/{upload_id}/export")
def export_share_card(upload_id: str) -> Response:
    """Tasks 133-134: renders the shareable results card (pipeline/share_card.py,
    docs/share_card_design.md) as a PNG. Same 404 semantics as /results/{id}
    -- no result yet means nothing to export."""
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            raise HTTPException(status_code=404, detail="upload not found")

        result = session.query(AnalysisResult).filter_by(upload_id=upload_id).one_or_none()
        if result is None:
            raise HTTPException(status_code=404, detail="result not ready")

        png_bytes = render_share_card(
            matched_qb_name=result.matched_qb_name,
            overall_similarity_score=result.overall_similarity_score,
            confidence_level=result.confidence_level,
            phase_results=result.phase_results,
        )
        return Response(content=png_bytes, media_type="image/png")


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
