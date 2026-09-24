# Engineering Spec — QB Motion Atlas ("NFL QB DNA")

No code — design only. Written so implementation requires minimal further design decisions.

## Overall Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  Frontend    │────▶│   Backend API     │────▶│  ML Pipeline         │
│ (Next.js/    │     │  (FastAPI)        │     │  (Python module,     │
│  React)      │◀────│                   │◀────│  in-process V1,      │
└─────────────┘     └──────────────────┘     │  separate service V2+)│
       │                     │                └────────────────────┘
       │              ┌──────▼──────┐                   │
       │              │  Job Queue    │          ┌────────▼────────┐
       │              │ (BackgroundTasks│          │  Model Serving    │
       │              │  V1 → Celery/  │          │  (pose model +     │
       │              │  Redis V2+)    │          │  embedding model)   │
       │              └──────┬──────┘          └────────┬────────┘
       │                     │                           │
       │              ┌──────▼──────┐          ┌────────▼────────┐
       │              │  Object       │          │  Reference DB      │
       │              │  Storage      │          │  (Postgres +        │
       │              │ (local V0/V1, │          │  pgvector, or        │
       │              │  S3/R2 later) │          │  FAISS index)        │
       │              └──────────────┘          └────────────────────┘
       └───────────────────────────────────────────────────────┘
```

**Processing sequence:** upload → validation (angle/quality) → pose extraction → phase segmentation → feature extraction + normalization → similarity computation (feature-distance + embedding) → result assembly → coaching-note generation → response.

## Database / Data Model

**Core tables (Postgres):**

- `users` — id, email/auth identifier (only if adding accounts; not required for V1 anonymous use), created_at.
- `uploads` — id, user_id (nullable), storage_path, upload_timestamp, validation_status (pending/valid/rejected), rejection_reason (nullable), detected_angle, confidence_flag.
- `qb_reference_clips` — id, qb_name, clip_source_url, timestamp_range, storage_path, added_at.
- `qb_reference_features` — clip_id (FK), phase_name, feature_vector (JSON or array column), embedding_vector (pgvector column), extracted_at.
- `analysis_results` — id, upload_id (FK), overall_match_qb, overall_similarity_score, confidence_level, phase_results (JSON: per-phase match + score), coaching_notes (JSON array), created_at.
- `phase_boundaries` — clip_id or upload_id (FK), phase_name, start_frame, end_frame, detection_method (heuristic/learned).

**Vector search:** `qb_reference_features.embedding_vector` indexed via pgvector's IVFFlat or HNSW index for nearest-neighbor lookup at query time. FAISS is a viable alternative if the reference set grows large enough that in-database vector search becomes a bottleneck — not needed at the dataset sizes described in this project.

## API Design

- `POST /uploads` — accepts video file (multipart), returns `{upload_id, status: "processing"}`.
- `GET /uploads/{upload_id}/status` — returns `{status: "processing" | "valid" | "rejected", rejection_reason?}`. Polled by frontend, or upgraded to a WebSocket push at V2+.
- `GET /results/{upload_id}` — returns full `analysis_results` payload once processing completes.
- `POST /results/{upload_id}/export` — generates and returns a shareable image asset.
- `GET /qbs` — returns the list of reference QBs and their archetype labels, for display purposes (e.g., populating a "who's in the database" page).

**Auth strategy:** Not required for V1 (anonymous, ephemeral results keyed by upload_id). If persistent user history is added later, standard session-token auth (e.g., JWT) is sufficient — no need for anything more complex given the scope.

## Frontend Architecture

- **Pages/routes:** `/` (landing + upload/record), `/processing/[uploadId]` (status polling view), `/results/[uploadId]` (main results page), `/qbs` (reference database browser, optional).
- **Component hierarchy:** `UploadRecorder` (handles both file upload and MediaRecorder-based webcam capture) → `ProcessingStatus` → `ResultsPage` composed of `OverallMatchCard`, `PhaseBreakdownPanel`, `SkeletonOverlayPlayer` (canvas-based, renders landmarks over video), `CoachingNotesList`, `ShareExportButton`.
- **State management:** For this scope, React's built-in state + a lightweight fetch/polling hook is sufficient — no need for Redux/Zustand given the linear, single-flow nature of the app. A simple context provider for the current upload/result state across the processing → results transition is enough.

## Backend Architecture

- **Service structure (V1):** Single FastAPI app with modules: `api/` (route handlers), `pipeline/` (pose extraction, phase segmentation, feature extraction — pure Python functions, easily unit-testable), `models/` (embedding model loading/inference), `db/` (SQLAlchemy models + queries).
- **Service structure (V2+):** Split `pipeline/` and `models/` into a separate inference service (own process, potentially own container) communicating with the main API via internal HTTP or a message queue, so the ML component can be scaled/versioned independently of the request-handling API.
- **Key algorithms:** heuristic phase segmentation (velocity/angle threshold-based, V1) upgraded to a trained temporal classifier (V2); DTW-based sequence similarity as the interpretable layer; triplet-loss embedding model as the learned similarity layer; weighted combination or separate display of both for the "why" explanation.
- **LLM integration point:** A single, narrow call after all numeric analysis is complete — input is a structured JSON of computed deltas per phase, output is constrained to a fixed schema (one short coaching sentence per phase, referencing the specific numeric delta provided). The LLM never receives raw video or makes any numeric/matching decision.

## External Integrations

- Pose estimation library (MediaPipe, later RTMPose) — local inference, no external API dependency.
- LLM API (for coaching-note phrasing only) — any standard provider, called with a strict system prompt and structured input/output schema.
- Object storage (local disk V0/V1 → S3 or Cloudflare R2 for deployed V2+).

## Deployment Strategy

- **V0/V1:** Frontend on Vercel (free tier), backend on Render or a small DigitalOcean droplet, Postgres via Render's managed offering or a free-tier hosted Postgres (e.g., Supabase/Neon), local or R2 storage for video files.
- **"Submitted and running" for V1:** a public URL where a stranger can upload a video and receive a result without any manual intervention, with the reference database pre-loaded and the validation/rejection path fully functional.
- **V2+:** Add Celery/Redis for real background job handling if synchronous processing time becomes a UX problem; separate the model-serving component if inference load or model iteration speed warrants it; move model training runs to Colab/Kaggle, exporting trained weights (ONNX where practical) for lightweight production inference.
