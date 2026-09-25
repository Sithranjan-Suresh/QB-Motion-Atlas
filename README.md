# QB Motion Atlas

A pose-based biomechanics system that decomposes a user's football throwing motion into interpretable phases (load, stride, arm cock, acceleration, release, follow-through) and compares it, phase by phase, against a curated database of NFL quarterback throwing mechanics.

This is a long-term personal AI/ML portfolio project, built in stages (V0 proof of concept → V1 functional MVP → V2 strong portfolio piece → V3 research-grade). See `full_context.md`, `product_spec.md`, and `engineering_spec.md` for the full design, and `implementation_checklist.md` for the 160-task build plan this repo is being built against.

**Live demo:** not yet deployed -- see `docs/deployment.md` for exactly what's left and why (it needs real third-party accounts, not more code).

## What works right now (V1)

- **Pose extraction** (MediaPipe) → **phase segmentation** (velocity/angle heuristics) → **per-phase feature extraction** (joint angles, timing, rotation velocity, all body-scale- and tempo-normalized) → **similarity scoring** (weighted feature distance + a DTW whole-motion-shape layer) → **confidence scoring** (pose completeness + boundary confidence + similarity margin) → **coaching notes** (structured deltas, LLM-ready with a rule-based fallback since no LLM key is configured yet).
- **Upload validation**: camera-angle, full-body-visibility, and single-throw checks with specific rejection reasons -- explicit, honest rejection rather than a forced guess on bad input.
- **Robustness**: multi-person primary-thrower selection, left-handed mirroring, low-confidence-joint interpolation and jitter smoothing.
- **A real FastAPI backend** (`POST /uploads`, `GET /uploads/{id}/status`, `GET /results/{id}`, `GET /qbs`) backed by Postgres (SQLAlchemy + Alembic), running the full pipeline as a background job.
- **A real Next.js frontend**: upload a video, watch it process, see your match, similarity score, confidence level, and coaching notes.
- **A real reference dataset**: 3 QBs (Josh Allen, Patrick Mahomes, Lamar Jackson), 6 sourced clips with full provenance (`data/provenance.csv`), documented sourcing criteria (`docs/data_criteria.md`).

**Known limitation, stated plainly:** the reference *feature* database (the actual computed pose/phase/feature data for those 6 clips, as opposed to their provenance metadata) isn't populated in this environment -- re-downloading the source clips is blocked by this environment's network policy (YouTube isn't reachable here; see `docs/research_log.md`'s 2026-09-25 entry). The full pipeline, API, and frontend all work correctly end-to-end regardless -- verified throughout this session with synthetic data and mocked pose extraction at exactly that one boundary -- but a fresh upload today has nothing real to match against until that's unblocked and the pipeline is re-run on the actual footage.

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

## Project layout
- `pipeline/` — pose extraction, validation, phase segmentation, features, similarity, confidence, coaching (pure Python, unit-tested).
- `api/` — FastAPI app.
- `db/` — SQLAlchemy models, seed script.
- `alembic/` — migrations.
- `frontend/` — Next.js app.
- `data/` — reference clip provenance and (locally, gitignored) raw/derived video and pose artifacts.
- `docs/` — design docs, methodology, and the running research log.
- `tests/` — pytest suite.

## Docs worth reading
- `docs/research_log.md` — the actual build history: findings, dead ends, and every blocker encountered, in order.
- `docs/feature_definitions.md`, `docs/phase_definitions.md`, `docs/similarity_methodology.md`, `docs/confidence_scoring.md`, `docs/coaching_schema.md`, `docs/coaching_prompt.md` — the technical methodology behind each pipeline stage.
- `docs/deployment.md` — what's left to actually put this on the internet.
