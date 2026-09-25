"""Integration test for db/seed.py::seed_landmark_sequences (task 123) --
against the real local Postgres, same skip-if-unreachable pattern as
tests/test_api.py and tests/test_pgvector.py.
"""

from __future__ import annotations

import json

import pytest
from sqlalchemy.exc import OperationalError

from db.base import get_session_factory
from db.models import LandmarkSequence, QBReferenceClip
from db.seed import seed_landmark_sequences

try:
    _session_factory = get_session_factory()
    with _session_factory() as _session:
        _session.execute(__import__("sqlalchemy").text("SELECT 1"))
except (RuntimeError, OperationalError):
    pytest.skip("local Postgres not reachable -- see docs/database_setup.md", allow_module_level=True)


TEST_CLIP_ID = "seed_landmarks_test_qb__clip0"


@pytest.fixture
def db_session():
    session_factory = get_session_factory()
    with session_factory() as session:
        yield session


@pytest.fixture
def seeded_clip(db_session):
    clip = QBReferenceClip(
        clip_id=TEST_CLIP_ID,
        qb_name="seed_landmarks_test_qb",
        source_url="https://example.invalid/test",
        license_note="test fixture",
        timestamp_range="0:00-1:00",
        camera_angle="near-side-view",
        validation_status="pass",
    )
    db_session.add(clip)
    db_session.commit()
    yield clip
    db_session.query(LandmarkSequence).filter_by(reference_clip_id=TEST_CLIP_ID).delete()
    db_session.query(QBReferenceClip).filter_by(clip_id=TEST_CLIP_ID).delete()
    db_session.commit()


def test_seed_landmark_sequences_loads_from_landmarks_raw(db_session, seeded_clip, tmp_path, monkeypatch):
    landmarks_dir = tmp_path / "landmarks_raw"
    landmarks_dir.mkdir()
    (landmarks_dir / f"{TEST_CLIP_ID}.json").write_text(
        json.dumps({"fps": 30.0, "frames": [{"frame_index": 0, "timestamp_ms": 0, "landmarks": [[0.5, 0.5]] * 33}]})
    )
    monkeypatch.setattr("db.seed.LANDMARKS_DIR", landmarks_dir)

    count = seed_landmark_sequences(db_session)
    db_session.commit()

    assert count == 1
    row = db_session.query(LandmarkSequence).filter_by(reference_clip_id=TEST_CLIP_ID).one()
    assert row.fps == 30.0
    assert len(row.frames) == 1
    assert len(row.frames[0]["landmarks"]) == 33


def test_seed_landmark_sequences_is_idempotent(db_session, seeded_clip, tmp_path, monkeypatch):
    landmarks_dir = tmp_path / "landmarks_raw"
    landmarks_dir.mkdir()
    (landmarks_dir / f"{TEST_CLIP_ID}.json").write_text(
        json.dumps({"fps": 30.0, "frames": [{"frame_index": 0, "timestamp_ms": 0, "landmarks": [[0.5, 0.5]] * 33}]})
    )
    monkeypatch.setattr("db.seed.LANDMARKS_DIR", landmarks_dir)

    seed_landmark_sequences(db_session)
    db_session.commit()
    seed_landmark_sequences(db_session)
    db_session.commit()

    rows = db_session.query(LandmarkSequence).filter_by(reference_clip_id=TEST_CLIP_ID).all()
    assert len(rows) == 1


def test_seed_landmark_sequences_skips_orphan_clip(db_session, tmp_path, monkeypatch):
    landmarks_dir = tmp_path / "landmarks_raw"
    landmarks_dir.mkdir()
    (landmarks_dir / "no_such_clip.json").write_text(json.dumps({"fps": 30.0, "frames": []}))
    monkeypatch.setattr("db.seed.LANDMARKS_DIR", landmarks_dir)

    count = seed_landmark_sequences(db_session)
    assert count == 0
