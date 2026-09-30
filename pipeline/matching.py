"""Live overall match for one upload against every usable reference clip
(tasks 110/115), combining whichever similarity layers have data:

1. V0 feature distance (pipeline/similarity.py) -- always, from each clip's
   clip-level (phase_name=None) feature vector.
2. V1 DTW whole-motion shape (pipeline/similarity_dtw.py) -- when the clip
   has a stored landmark sequence (data/landmarks_raw, via db/seed.py).
3. V2 learned embedding (models/embedding_inference.py) -- when
   EMBEDDING_CHECKPOINTS_DIR holds a trained checkpoint for a phase and that
   clip's phase rows have backfilled embedding vectors
   (db/backfill_embeddings.py).

A clip's score is the weighted mean of the layers available *for that
clip*, with weights renormalized over them. The weights are placeholders
pending the retrieval-accuracy tuning of task 53/111, same as the constants
they replace -- see docs/similarity_methodology.md.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from db.models import LandmarkSequence, QBReferenceClip, QBReferenceFeature
from pipeline.handedness import canonicalize_handedness
from pipeline.landmark_overlay import deserialize_overlay_frames, scope_to_boundary_range
from pipeline.per_phase_similarity import group_features_by_phase
from pipeline.pose_extraction import FrameLandmarks
from pipeline.similarity import compare_features
from pipeline.similarity_dtw import build_frame_trajectory, dtw_similarity
from pipeline.similarity_v2 import embedding_similarity

logger = logging.getLogger(__name__)

LAYER_WEIGHTS = {"feature": 1 / 3, "dtw": 1 / 3, "embedding": 1 / 3}
# Reference clips whose provenance QC failed never serve as a match.
EXCLUDED_REFERENCE_STATUSES = ("fail",)
# DTW is O(n*m) in pure Python; resampling both trajectories to at most this
# many frames keeps ~40 reference clips well under a second in total.
MAX_DTW_FRAMES = 60


@dataclass
class ClipMatch:
    clip_id: str
    qb_name: str
    feature_vector: dict[str, float]
    score: float
    layers: dict[str, float] = field(default_factory=dict)


def combine_layers(layers: dict[str, float], weights: dict[str, float] = LAYER_WEIGHTS) -> float:
    total_weight = sum(weights[name] for name in layers)
    return sum(weights[name] * score for name, score in layers.items()) / total_weight


def _resample(trajectory: list[list[float]], max_frames: int = MAX_DTW_FRAMES) -> list[list[float]]:
    if len(trajectory) <= max_frames:
        return trajectory
    step = (len(trajectory) - 1) / (max_frames - 1)
    return [trajectory[round(i * step)] for i in range(max_frames)]


def _reference_trajectory(sequence: LandmarkSequence) -> list[list[float]] | None:
    """Stored reference landmarks are un-mirrored (they're drawn over the
    real video), so they're canonicalized here the same way the upload was
    before comparing -- otherwise a left-handed QB's arm angles would be
    compared against the wrong side."""
    try:
        frames = deserialize_overlay_frames(sequence.frames)
        if len(frames) < 3:
            return None
        frames, _handedness = canonicalize_handedness(frames)
        return _resample(build_frame_trajectory(frames, sequence.fps))
    except (ValueError, ZeroDivisionError, KeyError):
        return None


@lru_cache(maxsize=1)
def _load_embedders(checkpoints_dir: str) -> dict:
    root = Path(checkpoints_dir)
    if not root.is_dir():
        return {}
    from models.embedding_inference import EmbeddingInference

    embedders = {}
    for phase_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        try:
            embedders[phase_dir.name] = EmbeddingInference(phase_dir)
        except Exception:  # noqa: BLE001 -- one bad checkpoint shouldn't disable the rest
            logger.warning("could not load embedding checkpoint", extra={"phase": phase_dir.name}, exc_info=True)
    return embedders


def load_phase_embedders() -> dict:
    checkpoints_dir = os.environ.get("EMBEDDING_CHECKPOINTS_DIR")
    return _load_embedders(checkpoints_dir) if checkpoints_dir else {}


def _embedding_scores(session, user_features: dict[str, float], clip_ids: list[str]) -> dict[str, float]:
    """Mean embedding similarity per clip across the phases that have both a
    checkpoint and backfilled reference embeddings."""
    embedders = load_phase_embedders()
    if not embedders:
        return {}

    user_by_phase = group_features_by_phase(user_features)
    per_clip: dict[str, list[float]] = {}
    for phase_name, embedder in embedders.items():
        if phase_name not in user_by_phase:
            continue
        try:
            user_embedding = embedder.embed(user_by_phase[phase_name])
        except ValueError:
            continue  # user is missing a feature this phase's model needs
        rows = (
            session.query(QBReferenceFeature)
            .filter(QBReferenceFeature.phase_name == phase_name)
            .filter(QBReferenceFeature.clip_id.in_(clip_ids))
            .filter(QBReferenceFeature.embedding_vector.isnot(None))
            .all()
        )
        for row in rows:
            try:
                per_clip.setdefault(row.clip_id, []).append(
                    embedding_similarity(user_embedding, list(row.embedding_vector))
                )
            except ValueError:
                continue
    return {clip_id: sum(scores) / len(scores) for clip_id, scores in per_clip.items()}


def score_reference_clips(
    session,
    user_features: dict[str, float],
    canonical_frames: list[FrameLandmarks],
    boundaries,
    fps: float,
) -> list[ClipMatch]:
    """Every usable reference clip scored against the upload, best first."""
    rows = (
        session.query(QBReferenceFeature, QBReferenceClip)
        .join(QBReferenceClip, QBReferenceClip.clip_id == QBReferenceFeature.clip_id)
        .filter(QBReferenceFeature.phase_name.is_(None))
        .filter(QBReferenceClip.validation_status.notin_(EXCLUDED_REFERENCE_STATUSES))
        .all()
    )
    if not rows:
        return []
    clip_ids = [clip.clip_id for _feature, clip in rows]

    try:
        user_trajectory = _resample(build_frame_trajectory(scope_to_boundary_range(canonical_frames, boundaries), fps))
    except (ValueError, ZeroDivisionError):
        user_trajectory = None

    reference_trajectories: dict[str, list[list[float]] | None] = {}
    if user_trajectory:
        sequences = (
            session.query(LandmarkSequence).filter(LandmarkSequence.reference_clip_id.in_(clip_ids)).all()
        )
        reference_trajectories = {seq.reference_clip_id: _reference_trajectory(seq) for seq in sequences}

    embedding_scores = _embedding_scores(session, user_features, clip_ids)

    matches = []
    for feature_row, clip in rows:
        layers = {"feature": compare_features(user_features, feature_row.feature_vector)}
        reference_trajectory = reference_trajectories.get(clip.clip_id)
        if user_trajectory and reference_trajectory:
            layers["dtw"] = dtw_similarity(user_trajectory, reference_trajectory)
        if clip.clip_id in embedding_scores:
            layers["embedding"] = embedding_scores[clip.clip_id]
        matches.append(
            ClipMatch(
                clip_id=clip.clip_id,
                qb_name=clip.qb_name,
                feature_vector=feature_row.feature_vector,
                score=combine_layers(layers),
                layers=layers,
            )
        )

    matches.sort(key=lambda m: m.score, reverse=True)
    return matches
