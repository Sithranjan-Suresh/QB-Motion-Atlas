# Deployment (V1 Target, tasks 90-95)

**Status: blocked on the user, not on missing code.** Provisioning a managed Postgres instance (Supabase/Neon), deploying the backend (Render or a droplet), and deploying the frontend (Vercel) all require creating and authenticating into third-party accounts -- something this session cannot and should not do autonomously (unlike the earlier YouTube network-access blocker, this isn't an environment setting, it's the user's own accounts/credentials/billing). What follows is everything prepared in advance so the actual deploy, once someone with those accounts runs it, is a short mechanical process rather than a from-scratch investigation.

## What's ready
- `requirements.txt` — pinned, installs cleanly (verified this session).
- `alembic/` — migrations apply cleanly to a fresh Postgres (verified against the local instance, task 65).
- `db/seed.py` — idempotent, safe to run against any Postgres instance including a freshly-provisioned one (task 66-67).
- `api/main.py` — reads `DATABASE_URL` and `CORS_ALLOWED_ORIGINS` from the environment already (no hardcoded local-only config).
- `frontend/` — reads `NEXT_PUBLIC_API_BASE_URL` from the environment already; builds cleanly (`next build`, verified this session).

## Task 90: managed Postgres (Supabase or Neon free tier)
1. Create a free-tier project on either.
2. Copy its connection string, and rewrite it to use the psycopg2 driver explicitly (SQLAlchemy 2.1 default is psycopg3, not installed here): `postgresql+psycopg2://...` -- same fix `docs/database_setup.md` already needed locally.
3. Run migrations against it: `DATABASE_URL=<connection string> alembic upgrade head`.

## Task 91: backend to Render (or a small droplet)
1. New Web Service from this repo, root `/`, start command `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
2. Env vars: `DATABASE_URL` (from task 90), `CORS_ALLOWED_ORIGINS` (the Vercel URL from task 92, once known), and an LLM API key when the project has one provisioned (`docs/coaching_prompt.md`'s "no key configured" caveat -- `generate_coaching_notes()` already falls back to the rule-based notes without one, so this isn't blocking, just an enhancement).

## Task 92: frontend to Vercel
1. Import this repo, root directory `frontend/`.
2. Env var: `NEXT_PUBLIC_API_BASE_URL` = the Render backend's URL from task 91.

## Task 93: seed the deployed Postgres
`DATABASE_URL=<connection string> python -m db.seed` -- loads `data/provenance.csv`'s 6 real reference clips (same idempotent script as local dev).

## Task 94: manual end-to-end walkthrough
Once 90-93 are live: open the Vercel URL as a stranger would, upload a real throw video, confirm it reaches a result or an honest rejection. (This is also the point where the V1 "submitted and running" bar from `product_spec.md` gets checked for real, against real infrastructure rather than this session's local Postgres/uvicorn/next-dev stack.)

## Task 95: structured error logging on the deployed backend
Not yet implemented -- reasonable to add alongside task 91 (e.g. Python's `logging` module configured for structured/JSON output, or a lightweight APM if Render's free tier's own log viewer isn't sufficient). Deferred until there's a deployed backend to actually configure logging *for*.
