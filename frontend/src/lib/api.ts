// Typed client for the FastAPI backend (api/main.py, api/schemas.py).
// Base URL comes from NEXT_PUBLIC_API_BASE_URL so it can point at a local
// `uvicorn api.main:app` during dev and the deployed backend in prod
// (task 91 -- Render/droplet URL there instead).

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type UploadCreatedResponse = {
  upload_id: string;
  status: string;
};

export type UploadStatusResponse = {
  upload_id: string;
  status: string;
  rejection_reason: string | null;
};

export type CoachingNote = {
  phase: string;
  note: string;
};

export type PhaseResult = {
  matched_qb_name: string;
  score: number;
  confidence: string;
};

export type AnalysisResultResponse = {
  upload_id: string;
  matched_qb_name: string | null;
  matched_clip_id: string | null;
  overall_similarity_score: number;
  confidence_level: string;
  coaching_notes: CoachingNote[];
  phase_results: Record<string, PhaseResult>;
};

export type QBSummary = {
  qb_name: string;
  clip_count: number;
};

export type LandmarkFrame = {
  frame_index: number;
  timestamp_ms: number;
  landmarks: [number, number][]; // 33 [x, y] pairs, normalized 0-1
};

export type LandmarkSequenceResponse = {
  fps: number;
  frames: LandmarkFrame[];
};

export type ComparisonResponse = {
  user: LandmarkSequenceResponse;
  reference: LandmarkSequenceResponse | null;
  reference_qb_name: string | null;
  alignment: [number, number][] | null;
  reference_video_eligible: boolean;
  reference_clip_source_url: string | null;
};

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API error ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return typeof body?.detail === "string" ? body.detail : response.statusText;
  } catch {
    return response.statusText;
  }
}

export async function createUpload(file: File): Promise<UploadCreatedResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/uploads`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return response.json();
}

export async function getUploadStatus(uploadId: string): Promise<UploadStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/uploads/${uploadId}/status`);
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return response.json();
}

// Returns null for the "not ready yet" case (backend 404s until the
// AnalysisResult exists) rather than throwing, so callers can distinguish
// "still processing" from a real error.
export async function getResults(uploadId: string): Promise<AnalysisResultResponse | null> {
  const response = await fetch(`${API_BASE_URL}/results/${uploadId}`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return response.json();
}

export async function listQbs(): Promise<QBSummary[]> {
  const response = await fetch(`${API_BASE_URL}/qbs`);
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return response.json();
}

// Task 124: a <video src> URL, not a fetch -- the browser streams it directly.
export function getUploadVideoUrl(uploadId: string): string {
  return `${API_BASE_URL}/uploads/${uploadId}/video`;
}

// Task A1: only actually serves video when ComparisonResponse.reference_video_eligible
// is true -- callers should check that first rather than relying on a 404 here.
export function getReferenceClipVideoUrl(clipId: string): string {
  return `${API_BASE_URL}/reference-clips/${clipId}/video`;
}

export async function getUploadLandmarks(uploadId: string): Promise<LandmarkSequenceResponse | null> {
  const response = await fetch(`${API_BASE_URL}/uploads/${uploadId}/landmarks`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return response.json();
}

// Task 125. Returns null for "not ready yet" (same convention as
// getResults) rather than throwing -- the caller already knows from
// getResults() whether a match exists at all.
export async function getComparison(uploadId: string): Promise<ComparisonResponse | null> {
  const response = await fetch(`${API_BASE_URL}/results/${uploadId}/comparison`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return response.json();
}

// Task 134: the rendered share-card PNG, as a Blob for ShareExportButton to
// turn into a download.
export async function exportShareCard(uploadId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/results/${uploadId}/export`, { method: "POST" });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return response.blob();
}
