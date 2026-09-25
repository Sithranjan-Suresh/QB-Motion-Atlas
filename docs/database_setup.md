# Local Database Setup (task 63)

V1 uses Postgres (`engineering_spec.md`'s deployment target is a managed Postgres instance -- Supabase or Neon, task 90 -- but local development runs against a native local instance). Docker wasn't available in the cloud session this was first set up in (no `docker.sock`), so this uses a native install instead of the more common `docker run postgres` approach; either works for local dev, and `engineering_spec.md` doesn't mandate one over the other.

## Install and start
```bash
sudo apt-get install -y postgresql postgresql-contrib postgresql-16-pgvector
sudo service postgresql start
```
`postgresql-16-pgvector` is needed from V2 onward (tasks 112-115's vector search) -- enable the extension once per database:
```bash
sudo -u postgres psql -d qb_motion_atlas -c "CREATE EXTENSION IF NOT EXISTS vector;"
```
(`alembic upgrade head` also runs `CREATE EXTENSION IF NOT EXISTS vector` itself as part of its migration, so this manual step is only needed if you want the extension active before running migrations for some reason -- it's idempotent either way.)

## Create the dev database and user
```bash
sudo -u postgres psql -c "CREATE USER qb_motion_atlas WITH PASSWORD '<pick-a-local-dev-password>';"
sudo -u postgres psql -c "CREATE DATABASE qb_motion_atlas OWNER qb_motion_atlas;"
```

## Configure the app
Copy `.env.example` to `.env` and fill in the password you picked above:
```
DATABASE_URL=postgresql+psycopg2://qb_motion_atlas:<password>@localhost:5432/qb_motion_atlas
```
(The `+psycopg2` driver suffix is required with SQLAlchemy 2.1 -- a bare `postgresql://` URL defaults to the psycopg3 dialect, which isn't installed here; `psycopg2-binary` is what's pinned in `requirements.txt`.)
`.env` is gitignored (per `.gitignore`'s existing `.env` / `.env.*` rules) -- never commit real credentials, even local-dev-only ones.

## Verify
```bash
psql "$DATABASE_URL" -c "SELECT current_database(), current_user;"
```

## Migrations
```bash
alembic upgrade head    # apply all migrations
alembic downgrade base  # drop everything back to just alembic_version (verified in task 65)
```

## Seeding / re-seeding reference data (tasks 66-67)
```bash
python -m db.seed
```
Safe to run any time and as many times as you like -- `db/seed.py` upserts by `clip_id` (reference clips, features) or deletes-then-reinserts per clip (phase boundaries), so re-running never duplicates rows. Concretely, re-run it whenever:
- `data/provenance.csv` gains a new reference clip or an existing row's metadata changes (V1 task 29's dataset expansion will do this repeatedly).
- `data/features_raw/` or `data/phase_boundaries_raw/` get new or updated files for a clip already in `provenance.csv` (a clip's `.json` file with no matching `qb_reference_clips` row is skipped with a printed warning, not silently dropped or turned into an orphan row).

**Verified (task 67):** ran `python -m db.seed` twice in a row against the real local Postgres with the real 6-row `data/provenance.csv` -- row count stayed at 6 both times, no duplicates. Also verified the features/phase-boundaries upsert and delete-then-reinsert paths the same way, using temporary fixture files for one clip (removed afterward, since `data/features_raw`/`data/phase_boundaries_raw` are otherwise empty in this session -- see the YouTube network-access blocker in `docs/research_log.md`): row counts were identical after a second run in both tables.
