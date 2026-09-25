# Local Database Setup (task 63)

V1 uses Postgres (`engineering_spec.md`'s deployment target is a managed Postgres instance -- Supabase or Neon, task 90 -- but local development runs against a native local instance). Docker wasn't available in the cloud session this was first set up in (no `docker.sock`), so this uses a native install instead of the more common `docker run postgres` approach; either works for local dev, and `engineering_spec.md` doesn't mandate one over the other.

## Install and start
```bash
sudo apt-get install -y postgresql postgresql-contrib
sudo service postgresql start
```

## Create the dev database and user
```bash
sudo -u postgres psql -c "CREATE USER qb_motion_atlas WITH PASSWORD '<pick-a-local-dev-password>';"
sudo -u postgres psql -c "CREATE DATABASE qb_motion_atlas OWNER qb_motion_atlas;"
```

## Configure the app
Copy `.env.example` to `.env` and fill in the password you picked above:
```
DATABASE_URL=postgresql://qb_motion_atlas:<password>@localhost:5432/qb_motion_atlas
```
`.env` is gitignored (per `.gitignore`'s existing `.env` / `.env.*` rules) -- never commit real credentials, even local-dev-only ones.

## Verify
```bash
psql "$DATABASE_URL" -c "SELECT current_database(), current_user;"
```

## Next steps
- Task 64: SQLAlchemy models for the five tables.
- Task 65: initial Alembic migration.
- Task 66-67: seed script + idempotency.
