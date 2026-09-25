"""Seed script (task 66): loads reference clips/features/phase boundaries
into the DB. Idempotent (task 67) -- safe to re-run any time provenance.csv
or the data/*_raw directories change, e.g. after adding new reference clips.

Usage: python -m db.seed

Note (2026-09-25): data/provenance.csv is real, checked-in data (it's just
clip metadata, not video), so reference-clip seeding is fully functional
right now. data/features_raw and data/phase_boundaries_raw are still empty
in this cloud session -- see docs/research_log.md's YouTube network-access
blocker -- so those two seed steps are no-ops until that data exists, but
the loading code is ready for when it does.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from db.base import get_session_factory
from db.models import PhaseBoundaryRow, QBReferenceClip, QBReferenceFeature

PROVENANCE_CSV = Path(__file__).resolve().parent.parent / "data" / "provenance.csv"
FEATURES_DIR = Path(__file__).resolve().parent.parent / "data" / "features_raw"
BOUNDARIES_DIR = Path(__file__).resolve().parent.parent / "data" / "phase_boundaries_raw"


def seed_reference_clips(session) -> int:
    """Upsert every data/provenance.csv row into qb_reference_clips, keyed by
    clip_id -- re-running updates existing rows in place instead of
    duplicating them."""
    if not PROVENANCE_CSV.exists():
        return 0

    count = 0
    with PROVENANCE_CSV.open(newline="") as f:
        for row in csv.DictReader(f):
            clip_id = f"{row['qb_name']}__{row['clip_id']}"
            clip = session.query(QBReferenceClip).filter_by(clip_id=clip_id).one_or_none()
            if clip is None:
                clip = QBReferenceClip(clip_id=clip_id)
                session.add(clip)

            clip.qb_name = row["qb_name"]
            clip.source_url = row["source_url"]
            clip.license_note = row["license_note"]
            clip.timestamp_range = row["timestamp_range"]
            clip.camera_angle = row["camera_angle"]
            clip.notes = row.get("notes")
            clip.validation_status = row["validation_status"]
            count += 1

    return count


def seed_reference_features(session) -> int:
    """Upsert each data/features_raw/<clip_id>.json into qb_reference_features
    (one clip-level row, phase_name=None -- see feature_definitions.md).
    Skips a features file whose clip_id isn't in qb_reference_clips yet,
    rather than creating an orphan row."""
    if not FEATURES_DIR.exists():
        return 0

    count = 0
    for path in sorted(FEATURES_DIR.glob("*.json")):
        clip_id = path.stem
        clip = session.query(QBReferenceClip).filter_by(clip_id=clip_id).one_or_none()
        if clip is None:
            print(f"seed_reference_features: skipping {clip_id}, no matching qb_reference_clips row")
            continue

        feature_row = (
            session.query(QBReferenceFeature).filter_by(clip_id=clip_id, phase_name=None).one_or_none()
        )
        if feature_row is None:
            feature_row = QBReferenceFeature(clip_id=clip_id, phase_name=None)
            session.add(feature_row)
        feature_row.feature_vector = json.loads(path.read_text())
        count += 1

    return count


def seed_phase_boundaries(session) -> int:
    """Replace each clip's phase_boundaries rows from
    data/phase_boundaries_raw/<clip_id>.json -- delete-then-reinsert per
    clip is the simplest idempotent strategy for a list-shaped child table
    with no natural single-row upsert key."""
    if not BOUNDARIES_DIR.exists():
        return 0

    count = 0
    for path in sorted(BOUNDARIES_DIR.glob("*.json")):
        clip_id = path.stem
        clip = session.query(QBReferenceClip).filter_by(clip_id=clip_id).one_or_none()
        if clip is None:
            print(f"seed_phase_boundaries: skipping {clip_id}, no matching qb_reference_clips row")
            continue

        session.query(PhaseBoundaryRow).filter_by(reference_clip_id=clip_id).delete()
        for boundary in json.loads(path.read_text()):
            session.add(PhaseBoundaryRow(reference_clip_id=clip_id, **boundary))
        count += 1

    return count


def main() -> None:
    Session = get_session_factory()
    with Session() as session:
        n_clips = seed_reference_clips(session)
        n_features = seed_reference_features(session)
        n_boundaries = seed_phase_boundaries(session)
        session.commit()

    print(f"Seeded {n_clips} reference clips, {n_features} feature sets, {n_boundaries} clips' phase boundaries")


if __name__ == "__main__":
    main()
