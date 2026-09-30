"""Postgres-backed job queue for upload analysis (task 136).

The `uploads` table is the queue: a row with validation_status='processing'
is a pending job. Workers claim a row with SELECT ... FOR UPDATE SKIP LOCKED,
so several workers (threads here, or separate `python -m api.worker`
processes) never grab the same upload. A claim older than JOB_TIMEOUT_SEC
counts as abandoned (worker crashed, or the host redeployed mid-job) and is
retried; after JOB_MAX_ATTEMPTS the upload is marked failed with
REJECTION_PROCESSING_FAILED instead of sitting in "processing" forever.

Each job runs in a spawned child process by default: a hard timeout can
actually kill a hung MediaPipe/OpenCV call, and the memory those libraries
hold is returned to the OS when the child exits instead of accumulating in
the web process.

JOB_RUNNER picks how jobs start:
- "worker" (default): WORKER_CONCURRENCY background threads in the API
  process poll the queue. Needs no extra service, which suits free hosting.
- "inline": each upload runs in-process right after its POST response
  (FastAPI BackgroundTasks). Used by the test suite, where monkeypatched
  pipeline functions wouldn't carry over into a child process.
- "none": this process never runs jobs; run `python -m api.worker` separately.
"""

from __future__ import annotations

import datetime
import logging
import multiprocessing
import os
import threading
import time

from sqlalchemy import or_

from api.retention import purge_expired_uploads
from api.storage import get_storage
from db.base import get_session_factory
from db.models import Upload
from pipeline.constants import REJECTION_PROCESSING_FAILED

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 2.0
RETENTION_SWEEP_INTERVAL_SEC = 3600.0
_LAST_ERROR_MAX_CHARS = 2000


def job_runner() -> str:
    return os.environ.get("JOB_RUNNER", "worker")


def _max_attempts() -> int:
    return int(os.environ.get("JOB_MAX_ATTEMPTS", "3"))


def _job_timeout_sec() -> float:
    return float(os.environ.get("JOB_TIMEOUT_SEC", "300"))


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _claimable_filter(stale_before: datetime.datetime):
    return (
        Upload.validation_status == "processing",
        Upload.attempts < _max_attempts(),
        or_(Upload.locked_at.is_(None), Upload.locked_at < stale_before),
    )


def claim_next_upload(upload_id: str | None = None) -> str | None:
    """Atomically claims the oldest claimable upload (or exactly `upload_id`
    if given), bumping its attempt count. Returns its id, or None."""
    stale_before = _now() - datetime.timedelta(seconds=_job_timeout_sec())
    session_factory = get_session_factory()
    with session_factory() as session:
        query = session.query(Upload).filter(*_claimable_filter(stale_before))
        if upload_id is not None:
            query = query.filter(Upload.id == upload_id)
        upload = query.order_by(Upload.created_at).with_for_update(skip_locked=True).first()
        if upload is None:
            return None
        upload.locked_at = _now()
        upload.attempts += 1
        claimed_id = upload.id
        session.commit()
        return claimed_id


def fail_exhausted_uploads() -> int:
    """Marks uploads that used every attempt (and whose last claim has gone
    stale, so nothing is still running them) as failed."""
    stale_before = _now() - datetime.timedelta(seconds=_job_timeout_sec())
    session_factory = get_session_factory()
    with session_factory() as session:
        rows = (
            session.query(Upload)
            .filter(
                Upload.validation_status == "processing",
                Upload.attempts >= _max_attempts(),
                or_(Upload.locked_at.is_(None), Upload.locked_at < stale_before),
            )
            .with_for_update(skip_locked=True)
            .all()
        )
        for upload in rows:
            upload.validation_status = "failed"
            upload.rejection_reason = REJECTION_PROCESSING_FAILED
            upload.locked_at = None
        session.commit()
        return len(rows)


def queue_depth() -> int:
    session_factory = get_session_factory()
    with session_factory() as session:
        return session.query(Upload).filter(Upload.validation_status == "processing").count()


def _run_pipeline_child(upload_id: str, video_path: str) -> None:
    # Imported here so the spawned child loads MediaPipe, not the parent.
    from pipeline.orchestrator import run_pipeline_for_upload

    run_pipeline_for_upload(upload_id, video_path=video_path)


def _run_isolated(upload_id: str, video_path: str) -> None:
    ctx = multiprocessing.get_context("spawn")
    process = ctx.Process(target=_run_pipeline_child, args=(upload_id, video_path), daemon=True)
    process.start()
    process.join(_job_timeout_sec())
    if process.is_alive():
        process.terminate()
        process.join(10)
        raise TimeoutError(f"pipeline exceeded {_job_timeout_sec():.0f}s")
    if process.exitcode != 0:
        raise RuntimeError(f"pipeline child exited with code {process.exitcode}")


def _record_failure(upload_id: str, error: BaseException) -> None:
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            return
        upload.last_error = f"{type(error).__name__}: {error}"[:_LAST_ERROR_MAX_CHARS]
        # Releasing the lock makes it claimable again right away (if any
        # attempts remain) instead of waiting out JOB_TIMEOUT_SEC.
        upload.locked_at = None
        if upload.attempts >= _max_attempts():
            upload.validation_status = "failed"
            upload.rejection_reason = REJECTION_PROCESSING_FAILED
        session.commit()


def run_job(upload_id: str, isolate: bool = True) -> None:
    """Runs one already-claimed upload through the pipeline. Never raises:
    failures are recorded on the row for retry or final failure."""
    session_factory = get_session_factory()
    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is None:
            return
        key = upload.video_path

    started = time.monotonic()
    try:
        with get_storage().local_copy(key) as video_path:
            if isolate:
                _run_isolated(upload_id, str(video_path))
            else:
                from pipeline.orchestrator import run_pipeline_for_upload

                run_pipeline_for_upload(upload_id, video_path=video_path)
    except Exception as error:  # noqa: BLE001 -- any failure is recorded, never raised
        logger.exception("upload job failed", extra={"upload_id": upload_id})
        _record_failure(upload_id, error)
        return

    with session_factory() as session:
        upload = session.get(Upload, upload_id)
        if upload is not None:
            upload.locked_at = None
            session.commit()
    logger.info(
        "upload job finished",
        extra={"upload_id": upload_id, "duration_sec": round(time.monotonic() - started, 2)},
    )


def process_upload_inline(upload_id: str) -> None:
    """JOB_RUNNER=inline entry point, called from BackgroundTasks."""
    if claim_next_upload(upload_id) is not None:
        run_job(upload_id, isolate=False)


def work_forever(stop_event: threading.Event | None = None, isolate: bool = True) -> None:
    stop_event = stop_event or threading.Event()
    last_sweep = 0.0
    while not stop_event.is_set():
        try:
            if time.monotonic() - last_sweep >= RETENTION_SWEEP_INTERVAL_SEC:
                purge_expired_uploads()
                last_sweep = time.monotonic()
            fail_exhausted_uploads()
            upload_id = claim_next_upload()
        except Exception:  # noqa: BLE001 -- DB blip; keep the loop alive
            logger.exception("worker poll failed")
            upload_id = None
        if upload_id is None:
            stop_event.wait(POLL_INTERVAL_SEC)
            continue
        run_job(upload_id, isolate=isolate)


def start_worker_threads(stop_event: threading.Event) -> list[threading.Thread]:
    concurrency = max(1, int(os.environ.get("WORKER_CONCURRENCY", "1")))
    threads = []
    for i in range(concurrency):
        thread = threading.Thread(target=work_forever, args=(stop_event,), name=f"upload-worker-{i}", daemon=True)
        thread.start()
        threads.append(thread)
    return threads


if __name__ == "__main__":
    from api.logging_config import configure_logging

    configure_logging()
    logger.info("standalone worker starting")
    work_forever()
