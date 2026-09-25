# QB Motion Atlas

A pose-based biomechanics system that decomposes a user's football throwing motion into interpretable phases (load, stride, arm cock, acceleration, release, follow-through) and compares it, phase by phase, against a curated database of NFL quarterback throwing mechanics.

This is a long-term personal AI/ML portfolio project, built in stages (V0 proof of concept → V1 functional MVP → V2 strong portfolio piece → V3 research-grade). See `full_context.md`, `product_spec.md`, and `engineering_spec.md` for the full design, and `implementation_checklist.md` for the 160-task build plan this repo is being built against. **`docs/technical_report.md`** is the consolidated methodology + evaluation + honest-limitations writeup; **`docs/evaluation_report.md`** has the real (if still small-sample) numbers behind it.

**Live demo:** not yet deployed -- see `docs/deployment.md` for exactly what's left and why (it needs real third-party accounts, not more code).

## What works right now (V2)

- **Pose extraction** (MediaPipe) → **phase segmentation** (velocity/angle heuristics) → **per-phase feature extraction** (joint angles, timing, rotation velocity, all body-scale- and tempo-normalized) → **similarity scoring** (V0 weighted feature distance + V1 DTW whole-motion-shape layer + V2 learned per-phase embedding, `pgvector`-indexed) → **confidence scoring** (pose completeness + boundary confidence + similarity margin) → **coaching notes** (structured deltas, LLM-ready with a rule-based fallback since no LLM key is configured yet).
- **Per-phase breakdown**: match/score/confidence for each individual phase, not just an overall score.
- **Skeleton overlay + synced comparison**: a canvas-drawn skeleton over your own uploaded video, and a DTW-aligned side-by-side view against the matched QB's motion (rendered skeleton-only on their side, not their source video -- see `docs/research_log.md`'s note on why).
- **Live webcam capture**: record directly in-browser (`MediaRecorder`), not just file upload.
- **Shareable results card**: one-click PNG export of your match/percentage/confidence.
- **Upload validation**: camera-angle, full-body-visibility, and single-throw checks with specific rejection reasons -- explicit, honest rejection rather than a forced guess on bad input.
- **Robustness**: multi-person primary-thrower selection, left-handed mirroring, low-confidence-joint interpolation and jitter smoothing.
- **A real FastAPI backend** (uploads, status, results, per-phase comparison, landmark/video serving, share-card export, reference-QB listing) backed by Postgres (SQLAlchemy + Alembic + `pgvector`), running the full pipeline as a background job.
- **A real Next.js frontend**: upload or record a video, watch it process, see your match, per-phase breakdown, skeleton overlay, coaching notes, and a `/qbs` reference-database browser page.
- **A real reference dataset with real computed pose/feature data**: 3 QBs (Josh Allen, Patrick Mahomes, Lamar Jackson), 4-6 sourced clips with full provenance (`data/provenance.csv`, `docs/data_criteria.md`) -- pose extraction, phase segmentation, and feature extraction have actually been run on the real footage, not just recorded as metadata.

**Known limitation, stated plainly:** that reference dataset is still far too small to validate a similarity metric against -- most QBs have only one or two usable clips. `docs/evaluation_report.md` runs the real evaluation scripts against it anyway and shows exactly why the result is inconclusive rather than skipping the check. Expanding the dataset (tasks 29/99) is the highest-leverage next step; every placeholder weight/threshold in this codebase is waiting on it.

## Local setup

### Backend
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# System dependencies MediaPipe/OpenCV need (Ubuntu/Debian):
sudo apt-get install -y ffmpeg libegl1 libgl1 libgles2

# Postgres -- see docs/database_setup.md for full detail
sudo apt-get install -y postgresql postgresql-contrib
sudo service postgresql start
sudo -u postgres psql -c "CREATE USER qb_motion_atlas WITH PASSWORD '<pick one>';"
sudo -u postgres psql -c "CREATE DATABASE qb_motion_atlas OWNER qb_motion_atlas;"
cp .env.example .env  # fill in your DATABASE_URL (note the +psycopg2 driver suffix)

alembic upgrade head
python -m db.seed   # loads data/provenance.csv's reference clips (real data)

uvicorn api.main:app --reload   # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # points at the backend above
npm run dev   # http://localhost:3000
```

### Tests
```bash
source .venv/bin/activate
python -m pytest tests/   # pipeline unit tests (synthetic data) + API integration tests (real local Postgres)
```

### Reproducing the reference dataset pipeline (V0-V2)
Once new source clips are trimmed into `data/trimmed/<qb_name>/<clip_name>.mp4` (see `docs/data_criteria.md` for what qualifies), this regenerates everything derived from them:
```bash
source .venv/bin/activate
python -m pipeline.run_pose_extraction      # data/pose_raw/
python -m pipeline.run_phase_segmentation   # data/phase_boundaries_raw/
python -m pipeline.run_features             # data/features_raw/
python -m pipeline.run_landmark_export      # data/landmarks_raw/ (task 123, skeleton overlay)
python -m db.seed                            # loads all of the above into Postgres
```

### Training the V2 embedding model
```bash
source .venv/bin/activate
jupyter notebook notebooks/01_train_embedding.ipynb   # Colab/Kaggle-ready; see docs/embedding_methodology.md for the objective/architecture
# or, to only backfill embeddings for reference clips using existing checkpoints:
python -m db.backfill_embeddings <checkpoints_dir>   # one subdirectory per phase name; see the module docstring
```

### Running the evaluation
```bash
source .venv/bin/activate
python -m eval.run_evaluation   # prints real retrieval-accuracy/self-consistency/discriminative-validity numbers -- see docs/evaluation_report.md
```

## Project layout
- `pipeline/` — pose extraction, validation, phase segmentation, features, similarity, confidence, coaching, landmark storage, share-card rendering (pure Python, unit-tested).
- `eval/` — evaluation metrics (retrieval accuracy, self-consistency, discriminative validity, PCK) and the runner script.
- `models/` — the V2 embedding network, training notebook, ONNX export.
- `api/` — FastAPI app.
- `db/` — SQLAlchemy models, seed script.
- `alembic/` — migrations.
- `frontend/` — Next.js app.
- `data/` — reference clip provenance and (locally, gitignored) raw/derived video and pose artifacts.
- `docs/` — design docs, methodology, evaluation results, and the running research log.
- `tests/` — pytest suite.

## Docs worth reading
- `docs/technical_report.md` — the consolidated V2 methodology + evaluation + limitations writeup.
- `docs/evaluation_report.md` — real evaluation numbers against the current reference dataset, honestly interpreted.
- `docs/research_log.md` — the actual build history: findings, dead ends, and every blocker encountered, in order.
- `docs/feature_definitions.md`, `docs/phase_definitions.md`, `docs/similarity_methodology.md`, `docs/embedding_methodology.md`, `docs/confidence_scoring.md`, `docs/coaching_schema.md`, `docs/coaching_prompt.md`, `docs/share_card_design.md` — the technical methodology behind each pipeline stage.
- `docs/deployment.md` — what's left to actually put this on the internet.
