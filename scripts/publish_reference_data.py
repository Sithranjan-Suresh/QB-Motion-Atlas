"""Publish the reference dataset to production. Run on the machine that has
the (gitignored) data/ directories -- the Windows sourcing machine.

1. Seeds the production database from data/provenance.csv plus
   data/features_raw, data/phase_boundaries_raw and data/landmarks_raw
   (the same idempotent db/seed.py used locally).
2. Trims every overlay-eligible reference clip in data/trimmed/ to the
   frame range its phase boundaries cover and uploads it to the production
   bucket as reference_clips/<clip_id>.mp4 -- what
   GET /reference-clips/{clip_id}/video serves.

Usage (repo root, with production settings in the environment or .env):
    python -m scripts.publish_reference_data             # seed + upload new clips
    python -m scripts.publish_reference_data --force     # re-upload every clip
    python -m scripts.publish_reference_data --skip-seed # clips only

Needs: DATABASE_URL, and S3_BUCKET / S3_ENDPOINT_URL / S3_REGION /
S3_ACCESS_KEY_ID / S3_SECRET_ACCESS_KEY for the upload step. ffmpeg on PATH.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / ".env")

from api.storage import S3Storage, get_storage, reference_clip_key  # noqa: E402
from db import seed  # noqa: E402
from db.base import get_session_factory  # noqa: E402
from db.models import QBReferenceClip  # noqa: E402
from pipeline.reference_video import served_range_sec, trim_video  # noqa: E402
from pipeline.video_licensing import is_video_overlay_eligible  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
TRIMMED_DIR = DATA_DIR / "trimmed"
BOUNDARIES_DIR = DATA_DIR / "phase_boundaries_raw"
LANDMARKS_DIR = DATA_DIR / "landmarks_raw"


def publish_clips(force: bool) -> tuple[int, int, list[str]]:
    storage = get_storage()
    if not isinstance(storage, S3Storage):
        sys.exit("S3_BUCKET is not set -- refusing to 'publish' to local disk")
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found on PATH")

    uploaded, skipped, problems = 0, 0, []
    with get_session_factory()() as session:
        clips = session.query(QBReferenceClip).filter(QBReferenceClip.validation_status != "fail").all()
        for clip in sorted(clips, key=lambda c: c.clip_id):
            if not is_video_overlay_eligible(clip.license_note):
                skipped += 1
                continue
            key = reference_clip_key(clip.clip_id)
            if not force and storage.exists(key):
                skipped += 1
                continue

            qb_name, clip_name = clip.clip_id.split("__", 1)
            source = TRIMMED_DIR / qb_name / f"{clip_name}.mp4"
            boundaries_path = BOUNDARIES_DIR / f"{clip.clip_id}.json"
            landmarks_path = LANDMARKS_DIR / f"{clip.clip_id}.json"
            missing = [p.name for p in (source, boundaries_path, landmarks_path) if not p.exists()]
            if missing:
                problems.append(f"{clip.clip_id}: missing {', '.join(missing)}")
                continue

            boundaries = json.loads(boundaries_path.read_text(encoding="utf-8"))
            fps = json.loads(landmarks_path.read_text(encoding="utf-8"))["fps"]
            start_sec, end_sec = served_range_sec([(b["start_frame"], b["end_frame"]) for b in boundaries], fps)

            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / f"{clip.clip_id}.mp4"
                if not trim_video(source, start_sec, end_sec, out):
                    problems.append(f"{clip.clip_id}: ffmpeg trim failed")
                    continue
                storage.put_file(key, out)
            uploaded += 1
            print(f"uploaded {key} ({end_sec - start_sec:.2f}s)")
    return uploaded, skipped, problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", action="store_true", help="re-upload clips that already exist")
    parser.add_argument("--skip-seed", action="store_true", help="don't touch the database")
    parser.add_argument("--skip-clips", action="store_true", help="don't upload video")
    args = parser.parse_args()

    if not args.skip_seed:
        seed.main()
    if not args.skip_clips:
        uploaded, skipped, problems = publish_clips(args.force)
        print(f"clips: {uploaded} uploaded, {skipped} skipped (already there or not eligible)")
        for problem in problems:
            print(f"  ! {problem}")


if __name__ == "__main__":
    main()
