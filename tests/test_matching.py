"""Tests for pipeline/matching.py: layer combination, failed-QC exclusion,
the DTW layer (reference landmark sequences), and the embedding layer
(a real ONNX checkpoint + pgvector rows). Needs the local Postgres."""

from __future__ import annotations

import math

import pytest
import torch
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from db.base import get_session_factory
from db.models import LandmarkSequence, QBReferenceClip, QBReferenceFeature
from models.embedding_net import EmbeddingNet
from models.export_onnx import save_checkpoint
from pipeline import matching
from pipeline.features import extract_phase_features
from pipeline.handedness import canonicalize_handedness
from pipeline.landmark_overlay import serialize_frames_for_overlay
from pipeline.phase_segmentation import segment_heuristic
from pipeline.pose_extraction import FrameLandmarks, Landmark

try:
    with get_session_factory()() as _session:
        _session.execute(text("SELECT 1"))
except (RuntimeError, OperationalError):
    pytest.skip("local Postgres not reachable -- see docs/database_setup.md", allow_module_level=True)

FPS = 30.0


def _throw_frames(n: int = 60, amplitude: float = 0.3) -> list[FrameLandmarks]:
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
        landmarks[15] = lm(0.4, 0.5)
        landmarks[16] = lm(0.5 + amplitude * math.sin(math.pi * i / n), 0.5)
        landmarks[23] = lm(0.45, 0.6)
        landmarks[24] = lm(0.47, 0.6)
        landmarks[25] = lm(0.45, 0.75)
        landmarks[26] = lm(0.46, 0.75)
        landmarks[27] = lm(0.4 + 0.15 * min(t / 0.4, 1.0), 0.75)
        frames.append(FrameLandmarks(i, int(i * 1000 / FPS), landmarks))
    return frames


def _analyze(frames):
    canonical, _ = canonicalize_handedness(frames)
    boundaries = segment_heuristic(canonical, FPS)
    return canonical, boundaries, extract_phase_features(canonical, boundaries, FPS)


@pytest.fixture
def session():
    with get_session_factory()() as s:
        # Isolate from whatever the dev DB was seeded with.
        s.execute(text("UPDATE qb_reference_clips SET validation_status = 'parked:' || validation_status"))
        s.commit()
        yield s
        s.rollback()
        for model in (QBReferenceFeature, LandmarkSequence):
            s.query(model).filter(
                (getattr(model, "clip_id", None) if model is QBReferenceFeature else model.reference_clip_id).like(
                    "mtest_%"
                )
            ).delete(synchronize_session=False)
        s.query(QBReferenceClip).filter(QBReferenceClip.clip_id.like("mtest_%")).delete(synchronize_session=False)
        s.execute(
            text(
                "UPDATE qb_reference_clips SET validation_status = substring(validation_status from 8) "
                "WHERE validation_status LIKE 'parked:%'"
            )
        )
        s.commit()


def _add_clip(session, clip_id, qb_name, features, status="pass", frames=None):
    session.add(
        QBReferenceClip(
            clip_id=clip_id, qb_name=qb_name, source_url="https://example.invalid", license_note="test",
            timestamp_range="0-1", camera_angle="side", validation_status=status,
        )
    )
    session.flush()
    session.add(QBReferenceFeature(clip_id=clip_id, phase_name=None, feature_vector=features))
    if frames is not None:
        session.add(LandmarkSequence(reference_clip_id=clip_id, fps=FPS, frames=serialize_frames_for_overlay(frames)))
    session.commit()


def test_combine_layers_renormalizes_over_available_layers():
    assert matching.combine_layers({"feature": 0.6}) == pytest.approx(0.6)
    assert matching.combine_layers({"feature": 0.6, "dtw": 0.2}) == pytest.approx(0.4)


def test_resample_caps_length_and_keeps_endpoints():
    trajectory = [[float(i)] for i in range(200)]
    resampled = matching._resample(trajectory, 60)
    assert len(resampled) == 60
    assert resampled[0] == [0.0] and resampled[-1] == [199.0]


def test_failed_clips_are_never_matched(session):
    canonical, boundaries, features = _analyze(_throw_frames())
    _add_clip(session, "mtest_fail__c1", "qb_fail", features, status="fail")
    _add_clip(session, "mtest_ok__c1", "qb_ok", {k: v * 1.5 for k, v in features.items()})
    matches = matching.score_reference_clips(session, features, canonical, boundaries, FPS)
    assert [m.clip_id for m in matches] == ["mtest_ok__c1"]


def test_dtw_layer_used_when_landmarks_exist(session):
    frames = _throw_frames()
    canonical, boundaries, features = _analyze(frames)
    _add_clip(session, "mtest_dtw__c1", "qb_dtw", features, frames=frames)
    _add_clip(session, "mtest_nodtw__c1", "qb_nodtw", features)
    by_id = {m.clip_id: m for m in matching.score_reference_clips(session, features, canonical, boundaries, FPS)}
    assert set(by_id["mtest_dtw__c1"].layers) == {"feature", "dtw"}
    assert by_id["mtest_dtw__c1"].layers["dtw"] == pytest.approx(1.0)  # identical motion
    assert set(by_id["mtest_nodtw__c1"].layers) == {"feature"}


def test_dtw_prefers_the_closer_motion(session):
    user_frames = _throw_frames(amplitude=0.3)
    canonical, boundaries, features = _analyze(user_frames)
    # Same feature vector for both, so only DTW can separate them.
    _add_clip(session, "mtest_near__c1", "qb_near", features, frames=_throw_frames(amplitude=0.3))
    _add_clip(session, "mtest_far__c1", "qb_far", features, frames=_throw_frames(amplitude=0.05))
    matches = matching.score_reference_clips(session, features, canonical, boundaries, FPS)
    assert matches[0].clip_id == "mtest_near__c1"


def test_embedding_layer_used_with_checkpoint(session, tmp_path, monkeypatch):
    canonical, boundaries, features = _analyze(_throw_frames())
    release_keys = ["elbow_angle_deg", "release_arm_velocity"]
    torch.manual_seed(0)
    save_checkpoint(
        EmbeddingNet(input_dim=2), release_keys, torch.tensor([140.0, 2.0]), torch.tensor([10.0, 1.0]),
        tmp_path / "ckpt" / "release",
    )
    monkeypatch.setenv("EMBEDDING_CHECKPOINTS_DIR", str(tmp_path / "ckpt"))
    matching._load_embedders.cache_clear()

    _add_clip(session, "mtest_emb__c1", "qb_emb", features)
    embedder = matching.load_phase_embedders()["release"]
    session.add(
        QBReferenceFeature(
            clip_id="mtest_emb__c1",
            phase_name="release",
            feature_vector={k: features[k] for k in release_keys},
            embedding_vector=embedder.embed({k: features[k] for k in release_keys}),
        )
    )
    session.commit()

    (match,) = matching.score_reference_clips(session, features, canonical, boundaries, FPS)
    assert match.layers["embedding"] == pytest.approx(1.0, abs=1e-5)
    matching._load_embedders.cache_clear()
