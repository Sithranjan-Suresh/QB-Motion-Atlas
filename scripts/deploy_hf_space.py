"""Deploy the backend to a Hugging Face Space (Docker SDK).

Stages only what the container needs (see Dockerfile), adds the Space
README front matter Hugging Face requires, creates the Space if it doesn't
exist, optionally pushes runtime secrets, and uploads everything as one
commit -- which triggers the Space to rebuild. Uses the huggingface_hub API
rather than `git push`, so binary files (fonts) go through LFS
automatically.

Usage (from the repo root, any OS):
    pip install huggingface_hub
    python scripts/deploy_hf_space.py --space <hf-username>/qb-motion-atlas-api
    python scripts/deploy_hf_space.py --space <...> --secrets-from-env

HF_TOKEN (environment or .env) must hold a Hugging Face token with write access
(https://huggingface.co/settings/tokens). --secrets-from-env copies every
variable in SECRET_NAMES / VARIABLE_NAMES that's set in the current
environment into the Space's settings, so a local .env can be the single
source of truth.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

try:  # a local .env counts as "the environment" for --secrets-from-env
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

INCLUDE = [
    "Dockerfile",
    ".dockerignore",
    "requirements-prod.txt",
    "alembic.ini",
    "alembic",
    "api",
    "db",
    "models",
    "pipeline",
    "assets",
    "data/provenance.csv",
    "scripts/start.sh",
]
EXCLUDE_NAMES = {"__pycache__", ".ipynb_checkpoints", "checkpoints"}
EXCLUDE_SUFFIXES = {".pyc", ".onnx", ".pt", ".pth", ".ckpt", ".task"}

# Private values: stored as Space *secrets* (hidden after saving).
SECRET_NAMES = [
    "DATABASE_URL",
    "GROQ_API_KEY",
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "SENTRY_DSN",
]
# Non-sensitive configuration: stored as Space *variables* (visible).
VARIABLE_NAMES = [
    "CORS_ALLOWED_ORIGINS",
    "S3_BUCKET",
    "S3_ENDPOINT_URL",
    "S3_REGION",
    "S3_SERVE_MODE",
    "GROQ_MODEL",
    "UPLOAD_RETENTION_DAYS",
    "UPLOAD_RATE_LIMIT_COUNT",
    "UPLOAD_RATE_LIMIT_WINDOW_SEC",
    "MAX_QUEUED_UPLOADS",
    "WORKER_CONCURRENCY",
    "JOB_TIMEOUT_SEC",
    "JOB_MAX_ATTEMPTS",
    "REFERENCE_VIDEO_OVERLAY_ENABLED",
    "REFERENCE_VIDEO_ALLOW_OFFICIAL",
]

SPACE_README = """---
title: QB Motion Atlas API
emoji: 🏈
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

Backend API for QB Motion Atlas: upload a throwing video, get a
phase-by-phase comparison against NFL quarterback mechanics. Deployed from
the project repository with `scripts/deploy_hf_space.py`; edit there, not here.
"""


def _copy(src: Path, dest: Path) -> None:
    if src.is_dir():
        for child in src.iterdir():
            if child.name in EXCLUDE_NAMES or child.suffix in EXCLUDE_SUFFIXES:
                continue
            _copy(child, dest / child.name)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def stage(out_dir: Path) -> None:
    for rel in INCLUDE:
        src = REPO_ROOT / rel
        if not src.exists():
            raise SystemExit(f"missing {rel} -- run from a full checkout")
        _copy(src, out_dir / rel)
    # Windows checkouts may have CRLF line endings; bash in the container
    # would choke on them.
    start = out_dir / "scripts" / "start.sh"
    start.write_bytes(start.read_bytes().replace(b"\r\n", b"\n"))
    (out_dir / "README.md").write_text(SPACE_README, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--space", required=True, help="<hf-username>/<space-name>")
    parser.add_argument("--secrets-from-env", action="store_true", help="copy set env vars into Space settings")
    parser.add_argument("--private", action="store_true", help="create the Space as private (API won't be public)")
    parser.add_argument("--dry-run", action="store_true", help="stage files and list them, upload nothing")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp)
        stage(staged)
        files = sorted(p.relative_to(staged).as_posix() for p in staged.rglob("*") if p.is_file())
        print(f"staged {len(files)} files")
        if args.dry_run:
            print("\n".join(files))
            return

        from huggingface_hub import HfApi

        token = os.environ.get("HF_TOKEN")
        if not token:
            sys.exit("HF_TOKEN is not set")
        api = HfApi(token=token)
        api.create_repo(args.space, repo_type="space", space_sdk="docker", private=args.private, exist_ok=True)

        if args.secrets_from_env:
            for name in SECRET_NAMES:
                if os.environ.get(name):
                    api.add_space_secret(args.space, name, os.environ[name])
                    print(f"secret set: {name}")
            for name in VARIABLE_NAMES:
                if os.environ.get(name):
                    api.add_space_variable(args.space, name, os.environ[name])
                    print(f"variable set: {name}")

        api.upload_folder(
            repo_id=args.space,
            repo_type="space",
            folder_path=str(staged),
            commit_message="Deploy from QB Motion Atlas repo",
            delete_patterns=["*"],  # files removed from the repo disappear from the Space too
        )

    owner, name = args.space.split("/", 1)
    print(f"deployed: https://huggingface.co/spaces/{args.space}")
    print(f"API URL (once built): https://{owner.lower()}-{name.lower().replace('_', '-')}.hf.space")


if __name__ == "__main__":
    main()
