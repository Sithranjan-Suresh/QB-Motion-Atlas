"""Integration tests for pgvector (tasks 112-115): real embedding_vector
column, real HNSW-indexed nearest-neighbor search, and the backfill
script -- against the real local Postgres (skipped if unreachable, same
pattern as tests/test_api.py). No real reference dataset exists yet, so
seeded with synthetic clips/features/embeddings.
"""

from __future__ import annotations

import random

import pytest
import torch
from sqlalchemy.exc import OperationalError

from db.backfill_embeddings import backfill_embeddings
from db.base import get_session_factory
from db.models import QBReferenceClip, QBReferenceFeature
from db.vector_search import find_nearest_by_embedding
from models.export_onnx import save_checkpoint
from models.train_embedding import train_embedding_net
from pipeline.embedding.sampling import PhaseRecord, generate_triplets

try:
    _session_factory = get_session_factory()
    with _session_factory() as _session:
        _session.execute(__import__("sqlalchemy").text("SELECT 1"))
except (RuntimeError, OperationalError):
    pytest.skip("local Postgres not reachable -- see docs/database_setup.md", allow_module_level=True)


TEST_CLIP_PREFIX = "pgvector_test_qb"
FEATURE_KEYS = ["elbow_angle_deg", "release_arm_velocity"]


@pytest.fixture
def db_session():
    session_factory = get_session_factory()
    with session_factory() as session:
        yield session


@pytest.fixture
def seeded_clips_and_features(db_session):
    """Two QBs' worth of clips/features with hand-set embedding_vector
    values forming two obviously-separated clusters, cleaned up after."""
    clips = []
    features = []
    clusters = {
        f"{TEST_CLIP_PREFIX}_a": [0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        f"{TEST_CLIP_PREFIX}_b": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.9],
    }
    for qb_name, base_embedding in clusters.items():
        for i in range(3):
            clip_id = f"{qb_name}__clip{i}"
            clips.append(
                QBReferenceClip(
                    clip_id=clip_id,
                    qb_name=qb_name,
                    source_url="https://example.invalid/test",
                    license_note="test fixture",
                    timestamp_range="0:00-1:00",
                    camera_angle="near-side-view",
                    validation_status="pass",
                )
            )
            features.append(
                QBReferenceFeature(
                    clip_id=clip_id,
                    phase_name="release",
                    feature_vector={"elbow_angle_deg": 140.0, "release_arm_velocity": 2.0},
                    embedding_vector=[v + 0.01 * i for v in base_embedding],
                )
            )
    db_session.add_all(clips + features)
    db_session.commit()
    yield clips, features

    db_session.query(QBReferenceFeature).filter(QBReferenceFeature.clip_id.like(f"{TEST_CLIP_PREFIX}%")).delete(
        synchronize_session=False
    )
    db_session.query(QBReferenceClip).filter(QBReferenceClip.clip_id.like(f"{TEST_CLIP_PREFIX}%")).delete(
        synchronize_session=False
    )
    db_session.commit()


def test_find_nearest_by_embedding_returns_closest_cluster(db_session, seeded_clips_and_features):
    query_embedding = [0.85, 0.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # close to cluster "a"
    results = find_nearest_by_embedding(db_session, "release", query_embedding, limit=3)

    assert len(results) == 3
    assert all(r.clip_id.startswith(f"{TEST_CLIP_PREFIX}_a") for r in results)


def test_find_nearest_by_embedding_respects_limit(db_session, seeded_clips_and_features):
    results = find_nearest_by_embedding(db_session, "release", [0.85, 0.15, 0, 0, 0, 0, 0, 0], limit=2)
    assert len(results) == 2


def test_backfill_embeddings_fills_null_rows(db_session, tmp_path):
    clip_id = f"{TEST_CLIP_PREFIX}_backfill__clip0"
    clip = QBReferenceClip(
        clip_id=clip_id,
        qb_name=f"{TEST_CLIP_PREFIX}_backfill",
        source_url="https://example.invalid/test",
        license_note="test fixture",
        timestamp_range="0:00-1:00",
        camera_angle="near-side-view",
        validation_status="pass",
    )
    feature = QBReferenceFeature(
        clip_id=clip_id, phase_name="release", feature_vector={"elbow_angle_deg": 140.0, "release_arm_velocity": 2.0}
    )
    db_session.add_all([clip, feature])
    db_session.commit()

    try:
        torch.manual_seed(0)
        records = [
            PhaseRecord(qb_name="qa", clip_id=f"qa{i}", phase_name="release", feature_vector={"elbow_angle_deg": 90 + i, "release_arm_velocity": 1.0 + 0.01 * i})
            for i in range(3)
        ] + [
            PhaseRecord(qb_name="qb", clip_id=f"qb{i}", phase_name="release", feature_vector={"elbow_angle_deg": 150 + i, "release_arm_velocity": 3.0 + 0.01 * i})
            for i in range(3)
        ]
        triplets = generate_triplets(records, rng=random.Random(0))
        result = train_embedding_net(triplets, FEATURE_KEYS, epochs=10)

        checkpoints_dir = tmp_path / "checkpoints"
        save_checkpoint(result.model, FEATURE_KEYS, result.mean, result.std, checkpoints_dir / "release")

        updated_count = backfill_embeddings(checkpoints_dir)
        assert updated_count == 1

        db_session.refresh(feature)
        assert feature.embedding_vector is not None
        assert len(feature.embedding_vector) == 8
    finally:
        db_session.query(QBReferenceFeature).filter_by(clip_id=clip_id).delete()
        db_session.query(QBReferenceClip).filter_by(clip_id=clip_id).delete()
        db_session.commit()


def test_backfill_embeddings_skips_phases_without_a_checkpoint(db_session, tmp_path):
    clip_id = f"{TEST_CLIP_PREFIX}_nocheckpoint__clip0"
    clip = QBReferenceClip(
        clip_id=clip_id,
        qb_name=f"{TEST_CLIP_PREFIX}_nocheckpoint",
        source_url="https://example.invalid/test",
        license_note="test fixture",
        timestamp_range="0:00-1:00",
        camera_angle="near-side-view",
        validation_status="pass",
    )
    feature = QBReferenceFeature(
        clip_id=clip_id, phase_name="stride", feature_vector={"stride_length": 0.9}
    )
    db_session.add_all([clip, feature])
    db_session.commit()

    try:
        empty_checkpoints_dir = tmp_path / "empty_checkpoints"
        empty_checkpoints_dir.mkdir()
        updated_count = backfill_embeddings(empty_checkpoints_dir)
        assert updated_count == 0

        db_session.refresh(feature)
        assert feature.embedding_vector is None
    finally:
        db_session.query(QBReferenceFeature).filter_by(clip_id=clip_id).delete()
        db_session.query(QBReferenceClip).filter_by(clip_id=clip_id).delete()
        db_session.commit()
