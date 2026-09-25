# QB Motion Atlas — Technical Report (V2)

A standalone summary of what this project is, how it works, what's been
validated, and what hasn't -- task 142's "full written technical report
(methodology + evaluation + honest limitations)." Every methodology
section below links back to the detailed doc it summarizes; nothing here
is new content, this is the consolidated read.

## What it does

Given a short (5-15s) side-view video of a person throwing a football,
QB Motion Atlas: extracts 2D body pose per frame (MediaPipe), segments the
throw into six biomechanical phases (load, stride, arm cock, acceleration,
release, follow-through), extracts interpretable per-phase features (joint
angles, timing, velocity), compares those features and the whole-motion
trajectory shape against a curated database of real NFL quarterbacks'
throwing mechanics, and returns a match, a similarity score, a confidence
level, and coaching notes -- overall and, in V2, per phase ("your stride
resembles Herbert, your release resembles Stafford").

## Pipeline methodology

1. **Pose extraction** -- MediaPipe `PoseLandmarker` (VIDEO mode), 33
   landmarks/frame. Multi-person frames resolve to the largest,
   most-central bounding box, or are rejected as ambiguous rather than
   guessing wrong.
2. **Robustness hardening** -- short gaps in per-joint detection are
   interpolated (bounded both sides by a real detection, never
   extrapolated off a clip edge); light jitter smoothing; left-handed
   throws are detected and mirrored onto the same canonical orientation
   the rest of the pipeline assumes.
3. **Validation** -- camera-angle, full-body-visibility, and
   single-throw checks reject bad input with a specific, user-facing
   reason instead of silently scoring it. See `docs/validation_rules.md`.
4. **Phase segmentation** -- a velocity/angle-threshold heuristic over
   lead-ankle and throwing-wrist trajectories, each boundary carrying its
   own confidence (inflection sharpness, degraded under joint occlusion).
   See `docs/phase_definitions.md`.
5. **Feature extraction** -- 17 features per clip (5 core biomechanical
   signals + per-phase timing/rate features), body-scale-normalized
   (shoulder width) and tempo-normalized (fraction of total throw
   duration) so they're comparable across camera distances and playback
   speeds. See `docs/feature_definitions.md`.
6. **Similarity** -- three layers, combined:
   - **V0**: scale-normalized weighted Euclidean distance over the
     per-phase feature snapshots.
   - **V1**: dynamic time warping over each clip's full per-frame
     trajectory (elbow angle, shoulder rotation, wrist speed), handling
     different throwing tempos.
   - **V2**: a learned per-phase embedding (triplet-loss MLP, 8-dim,
     `pgvector`-indexed for nearest-neighbor search), layered on top of,
     not replacing, the interpretable layers.
   See `docs/similarity_methodology.md` and `docs/embedding_methodology.md`.
7. **Confidence scoring** -- pose completeness + average boundary
   confidence + top1-vs-top2 similarity margin, averaged into
   high/medium/low. See `docs/confidence_scoring.md`.
8. **Coaching notes** -- structured per-phase deltas against the matched
   clip, LLM-ready (schema + prompt defined) with a rule-based fallback
   since no LLM API key is configured in this environment. See
   `docs/coaching_schema.md`, `docs/coaching_prompt.md`.
9. **Per-phase breakdown, skeleton overlay, synced comparison (V2)** --
   the phase-level match/score/confidence above are computed per phase,
   not just overall; a canvas-drawn skeleton overlays the user's own
   video, and a DTW-aligned side-by-side view compares it to the matched
   QB's motion -- rendered skeleton-only on the reference side, not
   streaming its source video, since reference clips are licensed for
   internal research use, not redistribution to end users (see
   `docs/research_log.md`'s 2026-09-25 "skeleton overlay" entry).

## System architecture

FastAPI backend (Postgres via SQLAlchemy/Alembic, background-job
processing) + Next.js frontend (file upload or live `MediaRecorder`
webcam capture, processing/results pages). See the README for the full
endpoint list and local setup.

## Evaluation

Full results, methodology, and honest interpretation: **`docs/evaluation_report.md`**.

Short version: with the real reference data this environment has been
able to source and process so far (4 usable clips across 3 QBs -- one QB
with only a single clip each), leave-one-out retrieval accuracy and
discriminative validity both come back at essentially chance level. This
is not evidence the approach is wrong; it's confirmation of what every
methodology doc has flagged all along -- every similarity weight and
confidence threshold in this codebase is an unvalidated placeholder,
because there has not yet been enough real, curated reference data to tune
or validate them against. Pose-extraction accuracy (PCK) hasn't been run
at all, since it needs hand-labeled ground-truth keypoints that don't
exist yet.

## Known limitations, stated plainly

1. **The reference dataset is far too small to validate against.** 4-6
   usable real clips across 3 QBs, most with only one or two clips each.
   Expanding it (tasks 29/99) is the single highest-leverage next step;
   everything downstream of it (weight tuning, a meaningful evaluation
   report, a trained embedding worth trusting) is blocked on it, not on
   more engineering.
2. **Every similarity/confidence weight is a placeholder.** Documented as
   such everywhere they're defined; `docs/evaluation_report.md` now shows
   *why* that caveat matters in practice, not just in theory.
3. **No LLM-generated coaching notes.** The schema and prompt are built
   and tested; every note a user actually sees comes from the rule-based
   fallback, since no project LLM API key is configured here.
4. **Not deployed.** Runs correctly locally (backend, frontend, real
   Postgres, all verified via real HTTP requests and a real Chromium
   browser throughout this project's build); nothing is live on the
   internet. Blocked on the user provisioning their own cloud accounts
   (`docs/deployment.md`), not on code.
5. **No hand-labeled gold phase boundaries or ground-truth keypoints
   exist.** The heuristic phase segmenter and pose-extraction accuracy
   have never been checked against real human-annotated ground truth --
   only against each other and against the pipeline's own internal
   consistency.
6. **Two edge cases (genuine multi-person footage, low-light footage)
   remain untested against real video** for the same reference-data
   reason as everywhere else -- covered at the unit level with synthetic
   data, not through a live end-to-end request with real footage.

None of this is new information hidden until now -- every item above has
its own dated entry in `docs/research_log.md`, the project's running,
honest build history. This report is the consolidated summary of that
log, not a replacement for it.
