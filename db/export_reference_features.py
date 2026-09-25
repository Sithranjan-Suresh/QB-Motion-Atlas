"""Exports qb_reference_features (joined with qb_reference_clips for
qb_name) to a portable JSON file -- one record per (clip, phase) row, in
the shape pipeline/embedding/sampling.py::PhaseRecord expects. Used to hand
reference data to a Colab/Kaggle notebook (task 104), which won't have
direct access to this environment's local Postgres.

Usage: python -m db.export_reference_features [output_path]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from db.base import get_session_factory
from db.models import QBReferenceClip, QBReferenceFeature

DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "reference_features_export.json"


def export_reference_features(output_path: str | Path = DEFAULT_OUTPUT_PATH) -> int:
    session_factory = get_session_factory()
    with session_factory() as session:
        rows = (
            session.query(QBReferenceFeature, QBReferenceClip.qb_name)
            .join(QBReferenceClip, QBReferenceFeature.clip_id == QBReferenceClip.clip_id)
            .filter(QBReferenceFeature.phase_name.isnot(None))
            .all()
        )

    records = [
        {
            "qb_name": qb_name,
            "clip_id": feature.clip_id,
            "phase_name": feature.phase_name,
            "feature_vector": feature.feature_vector,
        }
        for feature, qb_name in rows
    ]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2))
    return len(records)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT_PATH
    count = export_reference_features(path)
    print(f"Exported {count} per-phase feature records to {path}")
    if count == 0:
        print(
            "Note: 0 records means qb_reference_features has no phase_name-populated rows yet "
            "-- V1 only wrote clip-level rows (phase_name=None). Nothing to export until V2's "
            "per-phase feature extraction (task 116) or per-phase reference features are seeded."
        )
