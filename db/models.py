"""SQLAlchemy models for the five V1 tables (task 64), per
engineering_spec.md's Database / Data Model section.
"""

from __future__ import annotations

import datetime
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

# Must match models/embedding_net.py::EMBEDDING_DIM. Duplicated as a plain
# constant (not imported) so the db/ layer doesn't have to pull in torch
# just to know a dimensionality.
EMBEDDING_DIM = 8


def _uuid_str() -> str:
    return str(uuid.uuid4())


class Upload(Base):
    """A user's uploaded clip and its processing/validation state."""

    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    video_path: Mapped[str] = mapped_column(String, nullable=False)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    # "pending" | "processing" | "passed" | "rejected", per validation.py's ValidationResult.
    validation_status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    # one of pipeline/constants.py's REJECTION_* codes, set only when rejected.
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    phase_boundaries: Mapped[list["PhaseBoundaryRow"]] = relationship(back_populates="upload")
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(back_populates="upload")


class QBReferenceClip(Base):
    """One reference QB clip, mirroring a data/provenance.csv row (task 8)."""

    __tablename__ = "qb_reference_clips"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    # matches the "{qb_name}__{clip_name}" convention used throughout pipeline/run_*.py.
    clip_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    qb_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    license_note: Mapped[str] = mapped_column(String, nullable=False)
    timestamp_range: Mapped[str] = mapped_column(String, nullable=False)
    camera_angle: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    validation_status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    features: Mapped[list["QBReferenceFeature"]] = relationship(back_populates="clip")
    phase_boundaries: Mapped[list["PhaseBoundaryRow"]] = relationship(back_populates="reference_clip")


class QBReferenceFeature(Base):
    """extract_phase_features() output for one reference clip, per
    engineering_spec.md's qb_reference_features table: "clip_id (FK),
    phase_name, feature_vector (JSON...), embedding_vector (pgvector...)".

    embedding_vector is a real pgvector column now (task 112) -- fixed at
    EMBEDDING_DIM (8, models/embedding_net.py) since every phase's
    EmbeddingNet shares that output dimensionality even though their input
    dimensionality differs (docs/embedding_methodology.md).
    """

    __tablename__ = "qb_reference_features"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    clip_id: Mapped[str] = mapped_column(ForeignKey("qb_reference_clips.clip_id"), nullable=False)
    # nullable: some of features.py's output (e.g. release-instant angles) is
    # a single clip-level value, not tied to one phase -- see feature_definitions.md.
    phase_name: Mapped[str | None] = mapped_column(String, nullable=True)
    feature_vector: Mapped[dict] = mapped_column(JSON, nullable=False)
    embedding_vector: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    extracted_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clip: Mapped["QBReferenceClip"] = relationship(back_populates="features")


class AnalysisResult(Base):
    """The full result payload for one upload's analysis (POST /uploads' end state)."""

    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id"), nullable=False)
    # nullable: honestly represents "no reference data to match against yet"
    # (task 70) rather than fabricating a match when qb_reference_features is
    # empty -- still the current state until the V1 dataset expansion
    # (task 29, blocked on this environment's YouTube network-access issue).
    matched_qb_name: Mapped[str | None] = mapped_column(String, nullable=True)
    matched_clip_id: Mapped[str | None] = mapped_column(
        ForeignKey("qb_reference_clips.clip_id"), nullable=True
    )
    overall_similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String, nullable=False)  # "high" | "medium" | "low"
    coaching_notes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # [{phase, note}, ...]
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    upload: Mapped["Upload"] = relationship(back_populates="analysis_results")


class PhaseBoundaryRow(Base):
    """One PhaseBoundary (pipeline/phase_segmentation.py) row, for either an
    upload or a reference clip -- exactly one of upload_id / reference_clip_id
    is set, matching the pipeline's dual use of segment_heuristic() on both.
    """

    __tablename__ = "phase_boundaries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    upload_id: Mapped[str | None] = mapped_column(ForeignKey("uploads.id"), nullable=True)
    reference_clip_id: Mapped[str | None] = mapped_column(
        ForeignKey("qb_reference_clips.clip_id"), nullable=True
    )
    phase_name: Mapped[str] = mapped_column(String, nullable=False)
    start_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    end_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    detection_method: Mapped[str] = mapped_column(String, nullable=False, default="heuristic")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    upload: Mapped["Upload | None"] = relationship(back_populates="phase_boundaries")
    reference_clip: Mapped["QBReferenceClip | None"] = relationship(back_populates="phase_boundaries")
