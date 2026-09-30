#!/usr/bin/env bash
# Container entrypoint: apply migrations, then serve. Migrations are
# idempotent, so every boot running them is safe.
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is not set" >&2
  exit 1
fi

alembic upgrade head
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-7860}" --proxy-headers --forwarded-allow-ips='*'
