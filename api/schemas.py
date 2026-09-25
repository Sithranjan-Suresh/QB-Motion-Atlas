"""Pydantic request/response schemas for the FastAPI app (task 68)."""

from __future__ import annotations

from pydantic import BaseModel


class UploadCreatedResponse(BaseModel):
    upload_id: str
    status: str


class UploadStatusResponse(BaseModel):
    upload_id: str
    status: str
    rejection_reason: str | None = None


class CoachingNoteResponse(BaseModel):
    phase: str
    note: str


class PhaseResultResponse(BaseModel):
    matched_qb_name: str
    score: float
    confidence: str


class AnalysisResultResponse(BaseModel):
    upload_id: str
    matched_qb_name: str | None
    matched_clip_id: str | None
    overall_similarity_score: float
    confidence_level: str
    coaching_notes: list[CoachingNoteResponse]
    phase_results: dict[str, PhaseResultResponse]


class QBSummaryResponse(BaseModel):
    qb_name: str
    clip_count: int
