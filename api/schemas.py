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


class LandmarkFrameResponse(BaseModel):
    frame_index: int
    timestamp_ms: int
    landmarks: list[list[float]]  # 33 [x, y] pairs


class LandmarkSequenceResponse(BaseModel):
    fps: float
    frames: list[LandmarkFrameResponse]


class ComparisonResponse(BaseModel):
    """Task 125: the data a synced side-by-side comparison view needs --
    the user's own landmark sequence, the matched reference clip's (null if
    none exists yet, same honest-gap pattern as everywhere else), and the
    DTW frame-index alignment between them when both are present.
    """

    user: LandmarkSequenceResponse
    reference: LandmarkSequenceResponse | None
    reference_qb_name: str | None
    alignment: list[list[int]] | None  # [[user_frame_i, reference_frame_j], ...]
