"""Backfill embedding_vector for existing qb_reference_features rows (task
113), using one trained checkpoint per phase
(models/export_onnx.py::save_checkpoint / models/embedding_inference.py).

Usage: python -m db.backfill_embeddings <checkpoints_dir>
  <checkpoints_dir> must contain one subdirectory per phase name, each a
  checkpoint dir (model.onnx + metadata.json), e.g.:
    checkpoints_dir/release/model.onnx
    checkpoints_dir/release/metadata.json
    checkpoints_dir/stride/model.onnx
    ...

Note (2026-09-25): no trained checkpoints exist yet -- no real per-phase
reference feature data exists to train on (docs/research_log.md's YouTube
blocker). Validated in tests/test_backfill_embeddings.py against a
synthetic checkpoint and seeded rows.
"""

from __future__ import annotations

import sys
from pathlib import Path

from db.base import get_session_factory
from db.models import QBReferenceFeature
from models.embedding_inference import EmbeddingInference


def backfill_embeddings(checkpoints_dir: str | Path) -> int:
    """Fills in embedding_vector for every row that has a phase_name, has no
    embedding_vector yet, and whose phase has a checkpoint available under
    `checkpoints_dir`. Rows for a phase with no checkpoint yet are left
    alone (not an error) -- expected until every phase has been trained.
    Returns the number of rows updated.
    """
    checkpoints_dir = Path(checkpoints_dir)
    session_factory = get_session_factory()
    inference_by_phase: dict[str, EmbeddingInference] = {}
    updated = 0

    with session_factory() as session:
        rows = (
            session.query(QBReferenceFeature)
            .filter(QBReferenceFeature.phase_name.isnot(None))
            .filter(QBReferenceFeature.embedding_vector.is_(None))
            .all()
        )

        for row in rows:
            phase = row.phase_name
            if phase not in inference_by_phase:
                checkpoint_dir = checkpoints_dir / phase
                if not checkpoint_dir.exists():
                    continue
                inference_by_phase[phase] = EmbeddingInference(checkpoint_dir)

            row.embedding_vector = inference_by_phase[phase].embed(row.feature_vector)
            updated += 1

        session.commit()

    return updated


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m db.backfill_embeddings <checkpoints_dir>")
        sys.exit(1)

    count = backfill_embeddings(sys.argv[1])
    print(f"Backfilled embedding_vector for {count} rows")
