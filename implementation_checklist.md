# QB Motion Atlas — Implementation Checklist

Sequenced by the V0 → V1 → V2 → V3 roadmap from `product_spec.md` / `engineering_spec.md`. Single global numbering for linear progress tracking across the full multi-month build. Each task is tagged with its target stage.

---

## STAGE V0 — Proof of Concept
*Goal: prove the core technical bets (pose extraction, phase splitting, distance-based similarity) hold up on a handful of real clips before investing in infrastructure.*

### Environment & Project Setup
1. [V0] Create project root repo structure: `/pipeline`, `/data`, `/notebooks`, `/api` (placeholder), `/frontend` (placeholder), `/docs`.
2. [V0] Initialize git repo and `.gitignore` (venv, raw video data, model weights, `.env`).
3. [V0] Set up Python 3.11 environment with a dependency manager (poetry or pip + requirements.txt); pin `mediapipe`, `opencv-python`, `numpy`, `scipy`, `pandas`, `matplotlib`.
4. [V0] Establish a `notebooks/` sandbox convention for exploratory pose-extraction experiments.
5. [V0] Create `docs/research_log.md` and commit the first entry describing the project goal and V0 exit criteria.

### Data Collection & Curation (Seed Set)
6. [V0] Define clip-selection criteria (near-side-view angle, single visible throw, minimum resolution/duration) in `docs/data_criteria.md`.
7. [V0] Manually source 3 QBs' publicly available coaching-breakdown clips (2–3 throws each) meeting the criteria; save under `data/raw/<qb_name>/`.
8. [V0] Define `data/provenance.csv` schema (qb_name, clip_id, source_url, retrieval_date, license_note, timestamp_range) and populate it for the seed set.
9. [V0] Trim each seed clip to its single-throw window (ffmpeg or video editor) into `data/trimmed/`.
10. [V0] Visually verify each trimmed clip against the selection criteria; log pass/fail in `provenance.csv`.

### Pose Extraction Pipeline
11. [V0] Write `pipeline/pose_extraction.py::extract_pose(video_path) -> list[frame_landmarks]` using MediaPipe Pose (video mode).
12. [V0] Run pose extraction on all seed clips; save raw landmarks to `data/pose_raw/<clip_id>.json`.
13. [V0] Write a debug overlay script that draws extracted landmarks back onto source frames for visual sanity-checking.
14. [V0] Inspect overlay output for all seed clips; log clips with poor tracking (occlusion, dropped frames) in `docs/research_log.md`.
15. [V0] Write a landmark-confidence filter that flags/interpolates low-visibility joints per frame.

### Phase Segmentation — Heuristic v0
16. [V0] Define the throw phase taxonomy (load, stride, arm cock, acceleration, release, follow-through) with the kinematic signal marking each boundary, in `docs/phase_definitions.md`.
17. [V0] Write `pipeline/phase_segmentation.py::segment_heuristic(landmarks) -> phase_boundaries` using velocity/angle thresholds on wrist and shoulder trajectories.
18. [V0] Run heuristic segmentation on all seed clips; store output to `data/phase_boundaries_raw/<clip_id>.json`.
19. [V0] Hand-label true phase boundaries for the seed clips into `data/phase_boundaries_gold/<clip_id>.json`.
20. [V0] Compare heuristic vs. hand-labeled boundaries per clip; log frame-offset error per boundary in `docs/research_log.md`.

### Feature Engineering
21. [V0] Define the initial per-phase feature set (shoulder rotation angle, elbow angle, stride length, hip-shoulder separation, release-arm velocity) in `docs/feature_definitions.md`.
22. [V0] Write `pipeline/features.py::extract_phase_features(landmarks, phase_boundaries) -> dict`.
23. [V0] Run feature extraction on all seed clips; store to `data/features_raw/<clip_id>.json`.
24. [V0] Add body-scale normalization (shoulder width or torso length as reference unit) to remove camera-distance bias.

### Similarity Engine — Hand-Engineered v0
25. [V0] Write `pipeline/similarity.py::compare_features(vec_a, vec_b) -> float` using weighted Euclidean or cosine distance.
26. [V0] Run pairwise similarity across all seed clips; sanity-check same-QB throws score closer than cross-QB throws.
27. [V0] Log the pairwise similarity matrix and interpretation in `docs/research_log.md` — this is the V0 exit criterion.

### V0 Wrap-up
28. [V0] Write a "V0 findings" summary in `docs/research_log.md`: what worked, failure modes observed, what must change before scaling to V1.

---

## STAGE V1 — Functional MVP
*Goal: an end-to-end deployed app — upload a video, get an overall match + one data-backed coaching note within ~30s, with explicit rejection on bad input.*

### Data Expansion & Provenance
29. [V1] Expand the reference database to 8–10 QBs with 10+ clips each, following the V0 sourcing/provenance workflow.
30. [V1] Extend `provenance.csv` to cover the full reference set.
31. [V1] Batch-trim all new clips to single-throw windows into `data/trimmed/`.
32. [V1] Run pose extraction + overlay check across the full reference set; exclude/re-source clips with unusable tracking.
33. [V1] Run heuristic phase segmentation across the full set; spot-check a sample against hand labels to confirm generalization beyond the 3-QB seed set.
34. [V1] Batch-extract features for the full reference set into `data/features_raw/`.

### Video Quality / Camera-Angle Validation (P0)
35. [V1] Define checkable validation rules: camera-angle range (shoulder-to-hip orientation), full-body-visible (joint visibility threshold over a frame fraction), single-throw-detected (one clear wrist-velocity peak).
36. [V1] Write `pipeline/validation.py::validate_upload(landmarks) -> ValidationResult` returning status + specific rejection_reason.
37. [V1] Write unit tests for `validate_upload` using synthetic edge cases (no throw, wrong angle, partial occlusion).
38. [V1] Centralize rejection-message copy in a shared constants file for reuse across API and frontend.

### Pose Extraction Pipeline Hardening
39. [V1] Add low-confidence-joint interpolation/smoothing across short gaps.
40. [V1] Handle multiple people in frame: select primary thrower via largest/most-central bounding box; reject if ambiguous.
41. [V1] Detect left-handed throwers and mirror landmarks so normalization works against the reference set.
42. [V1] Write unit tests: single-person happy path, multi-person rejection, left-handed mirroring correctness.

### Phase Segmentation Hardening
43. [V1] Expand hand-labeled gold boundaries to 15–20 clips; retune heuristic thresholds to reduce V0's frame-offset error.
44. [V1] Add a boundary-confidence signal (sharpness of the detected inflection) for later use in overall confidence scoring.
45. [V1] Handle partial occlusion of the throwing arm during release: degrade to lower confidence rather than failing segmentation.

### Feature Engineering + Normalization
46. [V1] Expand the per-phase feature set to cover stride, arm-cock/acceleration, release, and follow-through.
47. [V1] Add timing normalization (relative to total throw duration) alongside body-scale normalization.
48. [V1] Store finalized reference-set feature vectors as the canonical `qb_reference_features` dataset with a documented schema.
49. [V1] Write a data-quality report script flagging reference clips whose features are statistical outliers vs. their own QB's other clips.

### Similarity Engine — DTW Layer
50. [V1] Write `pipeline/similarity_dtw.py::dtw_align(seq_a, seq_b) -> (alignment, distance)` over per-frame feature trajectories.
51. [V1] Combine the V0 weighted-distance score with the DTW distance into one overall score; document the weighting in `docs/similarity_methodology.md`.
52. [V1] Run a leave-one-out retrieval check across the reference set; log top-1 accuracy in `docs/research_log.md`.
53. [V1] Tune weighting/thresholds until same-QB retrieval clearly beats chance.

### Confidence Scoring
54. [V1] Define a confidence formula (high/medium/low) from pose-extraction completeness, phase-boundary confidence, and similarity-score margin.
55. [V1] Write `pipeline/confidence.py::compute_confidence(...) -> level`.
56. [V1] Write unit tests confirming confidence degrades correctly under simulated low-quality inputs.

### Coaching Notes (LLM Integration Point)
57. [V1] Define the structured JSON delta schema (`phase`, `metric_name`, `user_value`, `reference_value`, `delta`, `unit`).
58. [V1] Write `pipeline/coaching.py::build_deltas(user_features, matched_qb_features) -> list[Delta]`.
59. [V1] Write the fixed LLM system prompt + output schema (one short coaching sentence per phase, referencing the numeric delta; no raw video, no matching decisions given to the LLM).
60. [V1] Implement `generate_coaching_notes(deltas) -> list[str]`, validating LLM output conforms to schema.
61. [V1] Implement a rule-based templated fallback (referencing the same delta) if the LLM call fails or returns malformed output.
62. [V1] Write unit tests for `build_deltas` and output-schema validation.

### Database Schema & Models
63. [V1] Stand up a local Postgres instance (Docker or native).
64. [V1] Write SQLAlchemy models for `uploads`, `qb_reference_clips`, `qb_reference_features`, `analysis_results`, `phase_boundaries`.
65. [V1] Write and run the initial Alembic migration creating all five tables.
66. [V1] Write a seed script loading finalized reference clips/features/boundaries into the DB.
67. [V1] Verify the seed script is idempotent; document the re-seed procedure for new reference clips.

### Backend API (FastAPI)
68. [V1] Scaffold the FastAPI app: `api/`, `pipeline/`, `models/`, `db/` modules.
69. [V1] Implement `POST /uploads`: accept multipart video, save to local storage, create `uploads` row, return `{upload_id, status: "processing"}`.
70. [V1] Trigger the full pipeline as a `BackgroundTasks` job from `POST /uploads`.
71. [V1] On validation failure, update `uploads.validation_status = "rejected"` with the specific reason.
72. [V1] On success, write the full result payload into `analysis_results`.
73. [V1] Implement `GET /uploads/{upload_id}/status`.
74. [V1] Implement `GET /results/{upload_id}`.
75. [V1] Implement `GET /qbs` (reference QB list + archetype labels).
76. [V1] Add request validation at `POST /uploads` (file type/size, duration ≤15s) with clear 4xx errors.
77. [V1] Write integration tests: full good-video flow, and full bad-video rejection flow.

### Frontend — Core Flow
78. [V1] Scaffold Next.js app with routes `/`, `/processing/[uploadId]`, `/results/[uploadId]`.
79. [V1] Build `UploadRecorder` (file upload only for V1), posting to `POST /uploads`.
80. [V1] Build a `useUploadStatus` polling hook against `GET /uploads/{upload_id}/status`.
81. [V1] Build `/processing/[uploadId]` with a processing indicator and explicit rejection-reason display.
82. [V1] Build a lightweight context provider carrying upload/result state across the processing → results transition.
83. [V1] Build `OverallMatchCard` (match, similarity %, confidence level).
84. [V1] Build `CoachingNotesList`.
85. [V1] Wire `/results/[uploadId]` to `GET /results/{upload_id}`, handling the "not ready yet" case.
86. [V1] Basic responsive styling pass across the three core pages (usable, not polished).

### Testing
87. [V1] Unit-test coverage across `pipeline/` (pose_extraction, validation, phase_segmentation, features, similarity, confidence, coaching) for happy paths and documented edge cases.
88. [V1] End-to-end local smoke test: run a known test video through the full pipeline (not via API), assert all output fields populate.
89. [V1] Manually test every product-spec edge case (no throw, multi-person, occluded arm, left-handed, too-short/long, low-light) against the running stack; log actual vs. expected in `docs/research_log.md`.

### Deployment (V1 Target)
90. [V1] Provision a managed Postgres instance (Supabase or Neon free tier); migrate schema.
91. [V1] Deploy FastAPI backend to Render (or a small droplet) with env vars for DB, LLM key, storage path.
92. [V1] Deploy Next.js frontend to Vercel, pointed at the deployed backend.
93. [V1] Run the seed script against the deployed Postgres instance.
94. [V1] Manually walk the public URL end-to-end as a stranger would; confirm the "submitted and running" bar is met.
95. [V1] Set up basic structured error logging on the deployed backend.

### Documentation (V1)
96. [V1] Write the project README: what it is, V1 capabilities, local run instructions, link to the deployed demo.
97. [V1] Update `docs/research_log.md` with a "V1 shipped" entry and known limitations.

---

## STAGE V2 — Strong Portfolio Project
*Goal: a learned embedding component, full per-phase breakdown, live webcam capture, and a real evaluation report with numbers.*

### Learned Embedding Model — Data Prep
98. [V2] Define the triplet-loss training objective (anchor/positive = same QB or same phase-archetype, negative = different) in `docs/embedding_methodology.md`.
99. [V2] Expand the reference dataset per QB as needed to support triplet sampling; document target clip counts.
100. [V2] Write `pipeline/embedding/sampling.py` generating (anchor, positive, negative) triples per phase.
101. [V2] Split the reference dataset into train/validation/held-out-test at the clip level; document ratios and rationale.

### Learned Embedding Model — Training
102. [V2] Design the embedding network architecture (small MLP or 1D-conv encoder over per-phase feature sequences → fixed-size embedding) in `docs/embedding_methodology.md`.
103. [V2] Implement `models/embedding_net.py` and a triplet-loss training loop in `models/train_embedding.py`.
104. [V2] Set up a Colab/Kaggle notebook for training runs, exporting checkpoints back to the repo/storage.
105. [V2] Train an initial embedding model on the train split; log loss curves in `docs/research_log.md`.
106. [V2] Evaluate on the held-out test split via top-1/top-3 retrieval accuracy; log the number.
107. [V2] Iterate on architecture/hyperparameters to improve held-out retrieval accuracy; log each iteration.
108. [V2] Export the final model to ONNX for lightweight production inference.
109. [V2] Write `models/embedding_inference.py::embed(features) -> vector` loading the ONNX model.

### Similarity Engine — Embedding Integration
110. [V2] Combine the DTW/hand-engineered score with the embedding nearest-neighbor score into the final similarity computation; document the combination strategy.
111. [V2] Re-run the leave-one-out retrieval check with the combined V2 engine; confirm and log improvement over the V1-only baseline.

### Database — Vector Search
112. [V2] Add the pgvector extension; add `embedding_vector` column to `qb_reference_features`.
113. [V2] Backfill `embedding_vector` for every existing reference clip/phase row.
114. [V2] Add an IVFFlat or HNSW index on `embedding_vector`.
115. [V2] Update the similarity step to query the DB vector index instead of a flat-file brute-force scan.

### Per-Phase Breakdown (End-to-End)
116. [V2] Extend `analysis_results.phase_results` to include per-phase match, score, and confidence.
117. [V2] Build `PhaseBreakdownPanel` rendering each phase's match/score/confidence.
118. [V2] Wire `PhaseBreakdownPanel` into `/results/[uploadId]` below `OverallMatchCard`.

### Live Webcam Capture
119. [V2] Extend `UploadRecorder` with MediaRecorder-based webcam capture, capped at 15s with a visible timer.
120. [V2] Add a client-side framing guide/overlay hinting correct side-on positioning before recording.
121. [V2] Wire the recorded webcam blob through the existing `POST /uploads` flow (format conversion if needed).
122. [V2] Manually test the live webcam flow end-to-end on the deployed app across at least two browsers.

### Skeleton Overlay + Synced Comparison
123. [V2] Store per-frame landmark coordinates for both the user upload and the matched reference clip (scoped to compared phases).
124. [V2] Build `SkeletonOverlayPlayer` (canvas) rendering landmarks over the user's video.
125. [V2] Add a synced side-by-side view against the matched QB's clip, aligned via the V1 DTW alignment.
126. [V2] Add frame-by-frame scrub controls to the overlay player.

### Evaluation Report
127. [V2] Formalize leave-one-out retrieval accuracy as `eval/retrieval_accuracy.py`.
128. [V2] Implement a self-consistency metric (`eval/self_consistency.py`): stability of match/embedding under repeat runs or small augmentation.
129. [V2] Implement a discriminative-validity metric (`eval/discriminative_validity.py`): inter-QB vs. intra-QB embedding distance.
130. [V2] Implement a pose-extraction PCK metric (`eval/pck.py`) against any available hand-labeled/high-confidence frames.
131. [V2] Run all four evaluation scripts against the final dataset/model; write up numbers and honest caveats in `docs/evaluation_report.md`.
132. [V2] Add charts visualizing retrieval accuracy and inter/intra-QB distance distributions.

### Shareable Results Card Export
133. [V2] Design the shareable card layout (match, percentage, key stats).
134. [V2] Implement `POST /results/{upload_id}/export` generating a rendered card image.
135. [V2] Wire `ShareExportButton` to call the export endpoint and trigger a single-click download.

### Backend Scaling
136. [V2] Introduce Celery + Redis for background jobs if synchronous processing time has become a UX problem.
137. [V2] Move object storage from local disk to S3 or Cloudflare R2.
138. [V2] (If inference load warrants it) split `pipeline/` + `models/` into a separate inference service behind internal HTTP.

### Frontend Polish
139. [V2] Add loading-state/transition polish across processing/results pages.
140. [V2] Build the optional `/qbs` reference-database browser page via `GET /qbs`.
141. [V2] Accessibility/responsive pass across all pages (keyboard nav, contrast, mobile).

### Documentation (V2)
142. [V2] Write the full written technical report (methodology + evaluation + honest limitations) as a standalone artifact.
143. [V2] Update the README with V2 capabilities, the evaluation report link, and model-training reproduction steps.

---

## STAGE V3 — Sophisticated / Research Version
*Goal: measurable camera-angle robustness via 3D lifting, plus at least one documented research experiment — including honest negative results if applicable.*

### Camera-Angle Robustness — 3D Lifting
144. [V3] Research and select a monocular 2D-to-3D pose-lifting approach fitting the project's compute budget; document the choice in `docs/3d_lifting_methodology.md`.
145. [V3] Implement `pipeline/pose_3d.py::lift_to_3d(landmarks_2d) -> landmarks_3d`.
146. [V3] Re-derive phase-segmentation/feature-extraction to optionally consume 3D landmarks, keeping 2D as a low-confidence-angle fallback.
147. [V3] Collect/approximate a small camera-angle-variation test set (same motion from multiple angles).
148. [V3] Run a before/after comparison (2D-only vs. 2D+3D-lifted) on the angle-variation set; log measurable robustness numbers.
149. [V3] Update `docs/evaluation_report.md` with the camera-angle robustness before/after section.

### Research Experiments
150. [V3] Select one research experiment (cross-sport contrastive pretraining or multi-position generalization) based on feasibility; document the choice.
151. [V3] *(If cross-sport pretraining)* Source a small unlabeled cross-sport clip pool (e.g., baseball pitching, javelin) with documented provenance.
152. [V3] Implement a contrastive pretraining step on the pooled data before fine-tuning the embedding model on the QB-specific set.
153. [V3] Compare pretrained-then-fine-tuned retrieval accuracy against the V2 QB-only baseline; log the result honestly, including if negative or mediocre.
154. [V3] *(If multi-position generalization instead)* Select a second position (WR routes, DB backpedal, RB running style) and define its phase taxonomy analogous to `docs/phase_definitions.md`.
155. [V3] Source a small curated reference dataset for the second position via the existing provenance workflow.
156. [V3] Run the existing pipeline against the new position's dataset, adapting only phase taxonomy and feature definitions.
157. [V3] Document how much of the pipeline generalized unchanged vs. required position-specific rework.
158. [V3] Write up the research experiment(s) run — including honest negative/mediocre findings — in `docs/evaluation_report.md`.

### Final Documentation / Writeup Polish
159. [V3] Consolidate the research log, evaluation report, and V3 research writeup into a single polished technical report for external portfolio sharing.
160. [V3] Final README pass reflecting the full V0→V3 journey, current capabilities, and links to the live demo and full report.
