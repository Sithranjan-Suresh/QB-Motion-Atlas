"""Tests for the Postgres-backed job queue (api/worker.py), retention
(api/retention.py), DELETE /uploads/{id}, and the upload rate limiter.
Need the local Postgres (docs/database_setup.md); skipped without it."""

from __future__ import annotations

import datetime
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from api import worker
from api.rate_limit import SlidingWindowLimiter
from api.retention import purge_expired_uploads
from api.storage import get_storage
from db.base import get_session_factory
from db.models import Upload
from pipeline.constants import REJECTION_PROCESSING_FAILED

try:
    with get_session_factory()() as _session:
        _session.execute(text("SELECT 1"))
except (RuntimeError, OperationalError):
    pytest.skip("local Postgres not reachable -- see docs/database_setup.md", allow_module_level=True)


@pytest.fixture
def session():
    with get_session_factory()() as s:
        yield s


@pytest.fixture
def queued_upload(session, tmp_path):
    """A queued upload whose video exists in (test-local) storage. Any other
    queued rows left in the dev DB are parked so claim order is predictable."""
    session.execute(text("UPDATE uploads SET validation_status='parked' WHERE validation_status='processing'"))
    upload_id = str(uuid.uuid4())
    key = f"uploads/{upload_id}.mp4"
    src = tmp_path / "v.mp4"
    src.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    get_storage().put_file(key, src)
    session.add(Upload(id=upload_id, video_path=key, validation_status="processing", fps=30.0))
    session.commit()
    yield upload_id
    session.rollback()
    session.query(Upload).filter_by(id=upload_id).delete()
    session.execute(text("UPDATE uploads SET validation_status='processing' WHERE validation_status='parked'"))
    session.commit()


def _reload(session, upload_id):
    session.expire_all()
    return session.get(Upload, upload_id)


def test_claim_marks_lock_and_attempt(session, queued_upload):
    assert worker.claim_next_upload() == queued_upload
    upload = _reload(session, queued_upload)
    assert upload.attempts == 1 and upload.locked_at is not None
    # A fresh claim isn't handed out twice.
    assert worker.claim_next_upload() is None


def test_stale_claim_is_retried(session, queued_upload):
    worker.claim_next_upload()
    upload = _reload(session, queued_upload)
    upload.locked_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    session.commit()
    assert worker.claim_next_upload() == queued_upload
    assert _reload(session, queued_upload).attempts == 2


def test_pipeline_error_is_recorded_then_fails_after_max_attempts(session, queued_upload, monkeypatch):
    monkeypatch.setenv("JOB_MAX_ATTEMPTS", "2")

    def boom(upload_id, video_path=None):
        raise RuntimeError("mediapipe exploded")

    monkeypatch.setattr("pipeline.orchestrator.run_pipeline_for_upload", boom)

    worker.claim_next_upload()
    worker.run_job(queued_upload, isolate=False)
    upload = _reload(session, queued_upload)
    assert upload.validation_status == "processing"  # one attempt left
    assert upload.locked_at is None
    assert "mediapipe exploded" in upload.last_error

    worker.claim_next_upload()
    worker.run_job(queued_upload, isolate=False)
    upload = _reload(session, queued_upload)
    assert upload.validation_status == "failed"
    assert upload.rejection_reason == REJECTION_PROCESSING_FAILED


def test_exhausted_stale_upload_is_marked_failed(session, queued_upload, monkeypatch):
    monkeypatch.setenv("JOB_MAX_ATTEMPTS", "1")
    worker.claim_next_upload()
    upload = _reload(session, queued_upload)
    upload.locked_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    session.commit()
    assert worker.fail_exhausted_uploads() >= 1
    assert _reload(session, queued_upload).validation_status == "failed"


def test_isolated_run_times_out(session, queued_upload, monkeypatch):
    monkeypatch.setenv("JOB_TIMEOUT_SEC", "0.01")
    monkeypatch.setenv("JOB_MAX_ATTEMPTS", "1")
    worker.claim_next_upload()
    worker.run_job(queued_upload, isolate=True)  # spawn can't even start in 10ms
    upload = _reload(session, queued_upload)
    assert upload.validation_status == "failed"
    assert "TimeoutError" in upload.last_error


def test_retention_purges_old_finished_uploads(session, queued_upload):
    upload = _reload(session, queued_upload)
    upload.validation_status = "rejected"
    upload.created_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    key = upload.video_path
    session.commit()
    assert purge_expired_uploads() >= 1
    assert _reload(session, queued_upload) is None
    assert not get_storage().exists(key)


def test_retention_keeps_recent_uploads(session, queued_upload):
    upload = _reload(session, queued_upload)
    upload.validation_status = "rejected"
    session.commit()
    purge_expired_uploads()
    assert _reload(session, queued_upload) is not None


def test_delete_endpoint_removes_upload_and_video(session, queued_upload):
    from fastapi.testclient import TestClient

    from api.main import app

    upload = _reload(session, queued_upload)
    upload.validation_status = "rejected"
    key = upload.video_path
    session.commit()
    with TestClient(app) as client:
        assert client.delete(f"/uploads/{queued_upload}").status_code == 204
        assert client.get(f"/uploads/{queued_upload}/status").status_code == 404
        assert client.delete(f"/uploads/{queued_upload}").status_code == 404
    assert not get_storage().exists(key)


def test_delete_refuses_while_job_is_running(session, queued_upload):
    from fastapi.testclient import TestClient

    from api.main import app

    worker.claim_next_upload()
    with TestClient(app) as client:
        assert client.delete(f"/uploads/{queued_upload}").status_code == 409


def test_sliding_window_limiter():
    limiter = SlidingWindowLimiter(max_events=2, window_sec=10)
    assert limiter.check("ip", now=0) is None
    assert limiter.check("ip", now=1) is None
    assert limiter.check("ip", now=2) == pytest.approx(8)
    assert limiter.check("other-ip", now=2) is None
    assert limiter.check("ip", now=10.5) is None  # first event aged out


def test_upload_endpoint_returns_429_when_rate_limited(monkeypatch):
    from fastapi.testclient import TestClient

    from api import main

    monkeypatch.setattr(main, "upload_limiter", SlidingWindowLimiter(max_events=0, window_sec=60))
    with TestClient(main.app) as client:
        resp = client.post("/uploads", files={"file": ("a.mp4", b"x", "video/mp4")})
    assert resp.status_code == 429
    assert "retry-after" in resp.headers


def test_upload_endpoint_returns_503_when_queue_full(monkeypatch):
    from fastapi.testclient import TestClient

    from api import main

    monkeypatch.setattr(main, "MAX_QUEUED_UPLOADS", 0)
    with TestClient(main.app) as client:
        resp = client.post("/uploads", files={"file": ("a.mp4", b"x", "video/mp4")})
    assert resp.status_code == 503


def test_readiness_endpoint():
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        body = client.get("/health/ready").json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["job_runner"] == "inline"
