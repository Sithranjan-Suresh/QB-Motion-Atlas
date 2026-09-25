"""Integration tests for the FastAPI app (task 77): full good-video and
bad-video upload flows against a real local Postgres, plus request
validation. Unlike the rest of the test suite (synthetic data only, no
external dependencies), these need the local Postgres from
docs/database_setup.md running and DATABASE_URL configured -- skipped
automatically if it isn't reachable, rather than hard-failing a fresh
checkout that hasn't run task 63's setup yet.
"""

from __future__ import annotations

import math
import subprocess
import uuid

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from api.main import app
from db.base import get_session_factory
from db.models import AnalysisResult, LandmarkSequence, PhaseBoundaryRow, QBReferenceClip, QBReferenceFeature, Upload
from pipeline.landmark_overlay import serialize_frames_for_overlay
from pipeline.pose_extraction import FrameLandmarks, Landmark

try:
    _session_factory = get_session_factory()
    with _session_factory() as _session:
        _session.execute(__import__("sqlalchemy").text("SELECT 1"))
except (RuntimeError, OperationalError):
    pytest.skip("local Postgres not reachable -- see docs/database_setup.md", allow_module_level=True)


REFERENCE_CLIP_ID = "test_qb__integration_clip"
REFERENCE_FEATURES = {
    "shoulder_rotation_angle_deg": 70.0,
    "elbow_angle_deg": 140.0,
    "stride_length": 0.9,
    "hip_shoulder_separation_deg": 45.0,
    "release_arm_velocity": 2.5,
    "load_duration_sec": 0.2,
    "load_duration_frac": 0.2,
    "stride_duration_sec": 0.2,
    "stride_duration_frac": 0.2,
    "arm_cock_duration_sec": 0.2,
    "arm_cock_duration_frac": 0.2,
    "acceleration_duration_sec": 0.13,
    "acceleration_duration_frac": 0.13,
    "follow_through_duration_sec": 0.23,
    "follow_through_duration_frac": 0.23,
    "acceleration_rate": 100.0,
    "follow_through_deceleration_rate": 50.0,
}


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    session_factory = get_session_factory()
    with session_factory() as session:
        yield session


@pytest.fixture
def seeded_reference_clip(db_session):
    """One real reference clip + overall feature row (phase_name=None), plus
    a release-phase feature row (task 116) so the good-flow test also has
    something to match against for the per-phase breakdown. Cleaned up
    afterward."""
    clip = QBReferenceClip(
        clip_id=REFERENCE_CLIP_ID,
        qb_name="test_qb",
        source_url="https://example.invalid/test",
        license_note="test fixture",
        timestamp_range="0:00-1:00",
        camera_angle="near-side-view",
        validation_status="pass",
    )
    feature = QBReferenceFeature(clip_id=REFERENCE_CLIP_ID, phase_name=None, feature_vector=REFERENCE_FEATURES)
    release_feature = QBReferenceFeature(
        clip_id=REFERENCE_CLIP_ID,
        phase_name="release",
        feature_vector={
            "elbow_angle_deg": REFERENCE_FEATURES["elbow_angle_deg"],
            "release_arm_velocity": REFERENCE_FEATURES["release_arm_velocity"],
        },
    )
    db_session.add_all([clip, feature, release_feature])
    db_session.commit()
    yield clip
    db_session.query(QBReferenceFeature).filter_by(clip_id=REFERENCE_CLIP_ID).delete()
    db_session.query(QBReferenceClip).filter_by(clip_id=REFERENCE_CLIP_ID).delete()
    db_session.commit()


def _cleanup_upload(db_session, upload_id: str) -> None:
    db_session.query(AnalysisResult).filter_by(upload_id=upload_id).delete()
    db_session.query(PhaseBoundaryRow).filter_by(upload_id=upload_id).delete()
    db_session.query(LandmarkSequence).filter_by(upload_id=upload_id).delete()
    db_session.query(Upload).filter_by(id=upload_id).delete()
    db_session.commit()


def _write_synthetic_video(path: str, num_frames: int, fps: float = 30.0) -> None:
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (320, 240))
    for i in range(num_frames):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        frame[:] = (i * 5 % 255, 100, 150)
        out.write(frame)
    out.release()


def _write_synthetic_webm_video(path: str, duration_sec: float, fps: float = 30.0) -> None:
    # MediaRecorder (the live webcam capture path, tasks 119-121) records to
    # webm, not mp4/quicktime -- ffmpeg's lavfi testsrc + libvpx generates a
    # real webm file to exercise that path end-to-end, the same way
    # OpenCV/MediaPipe will actually receive a browser-recorded clip.
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=duration={duration_sec}:size=320x240:rate={fps}",
            "-c:v", "libvpx", "-b:v", "500k", path,
        ],
        check=True, capture_output=True,
    )


def _throw_frames(n: int = 60, fps: float = 30.0) -> list[FrameLandmarks]:
    """A synthetic clip with a real detectable single throw -- same
    construction validated in tests/test_validation.py and
    tests/test_coaching.py, reused here to exercise the API's success path."""

    def lm(x, y):
        return Landmark(x=x, y=y, z=0.0, visibility=1.0, presence=1.0)

    frames = []
    for i in range(n):
        t = i / (n - 1)
        landmarks = [lm(0.5, 0.5) for _ in range(33)]
        landmarks[0] = lm(0.46, 0.3)
        landmarks[11] = lm(0.45, 0.4)
        landmarks[12] = lm(0.55 - 0.1 * t, 0.4 + 0.1 * t)
        landmarks[14] = lm(0.6, 0.45)
        landmarks[15] = lm(0.4, 0.5)  # stationary left wrist -> right-handed
        landmarks[16] = lm(0.5 + 0.3 * math.sin(math.pi * i / n), 0.5)
        landmarks[23] = lm(0.45, 0.6)
        landmarks[24] = lm(0.47, 0.6)
        landmarks[25] = lm(0.45, 0.75)
        landmarks[26] = lm(0.46, 0.75)
        landmarks[27] = lm(0.4 + 0.15 * min(t / 0.4, 1.0), 0.75)
        frames.append(FrameLandmarks(i, int(i * 1000 / fps), landmarks))
    return frames


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_bad_video_flow_rejects_no_person_video(client, db_session, tmp_path):
    video_path = str(tmp_path / "no_person.mp4")
    _write_synthetic_video(video_path, num_frames=60)  # >= MIN_DURATION_SEC, so this exercises the
    # pipeline's own no_pose_detected rejection (task 70-72), not the request-level too-short check (task 89).

    with open(video_path, "rb") as f:
        resp = client.post("/uploads", files={"file": ("no_person.mp4", f, "video/mp4")})
    assert resp.status_code == 201
    upload_id = resp.json()["upload_id"]

    status_resp = client.get(f"/uploads/{upload_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "rejected"
    assert status_resp.json()["rejection_reason"] == "no_pose_detected"

    results_resp = client.get(f"/results/{upload_id}")
    assert results_resp.status_code == 404

    _cleanup_upload(db_session, upload_id)


def test_good_video_flow_produces_a_match(client, db_session, seeded_reference_clip, tmp_path, monkeypatch):
    video_path = str(tmp_path / "throw.mp4")
    _write_synthetic_video(video_path, num_frames=60)

    monkeypatch.setattr("pipeline.orchestrator.extract_pose", lambda path: _throw_frames())

    with open(video_path, "rb") as f:
        resp = client.post("/uploads", files={"file": ("throw.mp4", f, "video/mp4")})
    assert resp.status_code == 201
    upload_id = resp.json()["upload_id"]

    status_resp = client.get(f"/uploads/{upload_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "passed"

    results_resp = client.get(f"/results/{upload_id}")
    assert results_resp.status_code == 200
    body = results_resp.json()
    assert body["matched_qb_name"] == "test_qb"
    assert body["matched_clip_id"] == REFERENCE_CLIP_ID
    assert 0.0 < body["overall_similarity_score"] <= 1.0
    assert body["confidence_level"] in ("high", "medium", "low")
    assert len(body["coaching_notes"]) > 0
    assert "release" in body["phase_results"]
    assert body["phase_results"]["release"]["matched_qb_name"] == "test_qb"
    assert 0.0 < body["phase_results"]["release"]["score"] <= 1.0
    assert body["phase_results"]["release"]["confidence"] in ("high", "medium", "low")

    landmarks_resp = client.get(f"/uploads/{upload_id}/landmarks")
    assert landmarks_resp.status_code == 200
    landmarks_body = landmarks_resp.json()
    assert landmarks_body["fps"] > 0
    assert len(landmarks_body["frames"]) > 0
    assert len(landmarks_body["frames"][0]["landmarks"]) == 33

    video_resp = client.get(f"/uploads/{upload_id}/video")
    assert video_resp.status_code == 200
    assert video_resp.headers["content-type"] == "video/mp4"
    assert len(video_resp.content) > 0

    _cleanup_upload(db_session, upload_id)


@pytest.fixture
def seeded_reference_landmarks(db_session):
    """Task 123/125: a synthetic per-frame landmark sequence for
    REFERENCE_CLIP_ID, so the comparison-endpoint test has real DTW
    alignment to compute against instead of always hitting the
    no-reference-landmark-data gap."""
    sequence = LandmarkSequence(
        reference_clip_id=REFERENCE_CLIP_ID, fps=30.0, frames=serialize_frames_for_overlay(_throw_frames(n=60))
    )
    db_session.add(sequence)
    db_session.commit()
    yield sequence
    db_session.query(LandmarkSequence).filter_by(reference_clip_id=REFERENCE_CLIP_ID).delete()
    db_session.commit()


def test_comparison_endpoint_returns_alignment_with_reference_landmarks(
    client, db_session, seeded_reference_clip, seeded_reference_landmarks, tmp_path, monkeypatch
):
    video_path = str(tmp_path / "throw.mp4")
    _write_synthetic_video(video_path, num_frames=60)
    monkeypatch.setattr("pipeline.orchestrator.extract_pose", lambda path: _throw_frames())

    with open(video_path, "rb") as f:
        resp = client.post("/uploads", files={"file": ("throw.mp4", f, "video/mp4")})
    upload_id = resp.json()["upload_id"]
    client.get(f"/uploads/{upload_id}/status")  # ensure background pipeline has run before polling results

    comparison_resp = client.get(f"/results/{upload_id}/comparison")
    assert comparison_resp.status_code == 200
    body = comparison_resp.json()
    assert body["reference_qb_name"] == "test_qb"
    assert body["reference"] is not None
    assert len(body["reference"]["frames"]) == 60
    assert body["alignment"] is not None
    assert len(body["alignment"]) > 0
    assert body["alignment"][0] == [0, 0]
    assert body["alignment"][-1] == [len(body["user"]["frames"]) - 1, len(body["reference"]["frames"]) - 1]

    _cleanup_upload(db_session, upload_id)


def test_comparison_endpoint_returns_null_reference_without_landmark_data(
    client, db_session, seeded_reference_clip, tmp_path, monkeypatch
):
    """No seeded_reference_landmarks fixture here -- the match exists
    (seeded_reference_clip) but its LandmarkSequence doesn't, the honest gap
    the endpoint is documented to handle without 404ing."""
    video_path = str(tmp_path / "throw.mp4")
    _write_synthetic_video(video_path, num_frames=60)
    monkeypatch.setattr("pipeline.orchestrator.extract_pose", lambda path: _throw_frames())

    with open(video_path, "rb") as f:
        resp = client.post("/uploads", files={"file": ("throw.mp4", f, "video/mp4")})
    upload_id = resp.json()["upload_id"]
    client.get(f"/uploads/{upload_id}/status")

    comparison_resp = client.get(f"/results/{upload_id}/comparison")
    assert comparison_resp.status_code == 200
    body = comparison_resp.json()
    assert body["reference_qb_name"] == "test_qb"
    assert body["reference"] is None
    assert body["alignment"] is None
    assert body["user"]["frames"]  # the user's own overlay data is still there

    _cleanup_upload(db_session, upload_id)


def test_webcam_recorded_webm_flow_produces_a_match(client, db_session, seeded_reference_clip, tmp_path, monkeypatch):
    """Tasks 119-121: a browser-recorded webm (not mp4/quicktime) goes
    through the exact same real pipeline as a file upload -- content-type
    acceptance (api/main.py::ALLOWED_CONTENT_TYPES), duration probing, and
    pose extraction all need to actually work against webm, not just be
    assumed to. Uses the exact content-type string a real browser's
    MediaRecorder blob carries ("video/webm;codecs=vp9", with the codecs
    parameter) -- a real Playwright browser test caught this being rejected
    outright until create_upload() started stripping that parameter."""
    video_path = str(tmp_path / "webcam-throw.webm")
    _write_synthetic_webm_video(video_path, duration_sec=2.5)

    monkeypatch.setattr("pipeline.orchestrator.extract_pose", lambda path: _throw_frames())

    with open(video_path, "rb") as f:
        resp = client.post("/uploads", files={"file": ("webcam-throw.webm", f, "video/webm;codecs=vp9")})
    assert resp.status_code == 201
    upload_id = resp.json()["upload_id"]

    status_resp = client.get(f"/uploads/{upload_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "passed"

    results_resp = client.get(f"/results/{upload_id}")
    assert results_resp.status_code == 200
    assert results_resp.json()["matched_qb_name"] == "test_qb"

    _cleanup_upload(db_session, upload_id)


@pytest.mark.parametrize(
    "content_type,contents,expected_status",
    [
        pytest.param("text/plain", b"not a video", 400, id="wrong-content-type"),
        pytest.param("video/mp4", b"0" * (101 * 1024 * 1024), 400, id="oversized-body"),
    ],
)
def test_upload_request_validation_rejects_bad_input(client, content_type, contents, expected_status):
    resp = client.post("/uploads", files={"file": ("bad.mp4", contents, content_type)})
    assert resp.status_code == expected_status


def test_upload_request_validation_rejects_too_long_video(client, tmp_path):
    video_path = str(tmp_path / "long.mp4")
    _write_synthetic_video(video_path, num_frames=600)  # 20s at 30fps
    with open(video_path, "rb") as f:
        resp = client.post("/uploads", files={"file": ("long.mp4", f, "video/mp4")})
    assert resp.status_code == 400
    assert "longer than" in resp.json()["detail"]


def test_upload_request_validation_rejects_too_short_video(client, tmp_path):
    # Found missing during task 89's edge-case review -- there was no floor at all.
    video_path = str(tmp_path / "short.mp4")
    _write_synthetic_video(video_path, num_frames=15)  # 0.5s at 30fps
    with open(video_path, "rb") as f:
        resp = client.post("/uploads", files={"file": ("short.mp4", f, "video/mp4")})
    assert resp.status_code == 400
    assert "shorter than" in resp.json()["detail"]


def test_get_qbs_returns_real_seeded_qbs(client):
    resp = client.get("/qbs")
    assert resp.status_code == 200
    qb_names = {row["qb_name"] for row in resp.json()}
    # from data/provenance.csv, seeded by db/seed.py (task 66)
    assert {"josh_allen", "lamar_jackson", "patrick_mahomes"}.issubset(qb_names)


def test_status_and_results_404_for_unknown_upload(client):
    unknown_id = str(uuid.uuid4())
    assert client.get(f"/uploads/{unknown_id}/status").status_code == 404
    assert client.get(f"/results/{unknown_id}").status_code == 404
