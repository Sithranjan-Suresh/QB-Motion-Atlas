"""Task 131: runs the evaluation scripts against whatever real reference
data currently exists in Postgres, and prints results as JSON for
docs/evaluation_report.md to quote directly (not retyped by hand, so the
report can't silently drift from what was actually run).

PCK (eval/pck.py) is deliberately not run here -- it needs hand-labeled
ground-truth keypoints, which don't exist (no gold-labeling pass has been
done; see docs/research_log.md).

Usage: python -m eval.run_evaluation
"""

from __future__ import annotations

import json
import random

from db.base import get_session_factory
from db.models import QBReferenceClip, QBReferenceFeature
from eval.discriminative_validity import compute_discriminative_validity
from eval.retrieval_accuracy import LabeledVector, leave_one_out_retrieval_accuracy
from eval.self_consistency import self_consistency_score
from pipeline.similarity import compare_features


def _distance_fn(a: dict[str, float], b: dict[str, float]) -> float:
    return 1.0 - compare_features(a, b)


def load_whole_clip_features() -> list[LabeledVector]:
    """The clip-level (phase_name=None) feature rows -- the same feature
    set the live V0/V1 matching path (pipeline/orchestrator.py) actually
    compares against. Excludes clips whose validation_status isn't a clean
    "pass" -- "pass-with-caveat" clips (e.g. lamar_jackson's clip2, whose
    release/follow-through phases were never actually visible on camera per
    data/provenance.csv) still produce a full 17-key feature vector, since
    segment_heuristic still assigns *some* boundary to those phases
    regardless of whether real release/follow-through motion is in frame --
    the values aren't missing, they're just not meaningfully comparable to
    a clip where release/follow-through really happened. This is the exact
    exclusion research_log.md's 2026-09-24 entry already decided on; this
    script just enforces it instead of re-deciding it ad hoc.
    """
    session_factory = get_session_factory()
    with session_factory() as session:
        rows = (
            session.query(QBReferenceFeature)
            .join(QBReferenceClip, QBReferenceFeature.clip_id == QBReferenceClip.clip_id)
            .filter(QBReferenceFeature.phase_name.is_(None), QBReferenceClip.validation_status == "pass")
            .all()
        )
        return [LabeledVector(label=row.clip_id.split("__")[0], item_id=row.clip_id, vector=row.feature_vector) for row in rows]


def main() -> None:
    items = load_whole_clip_features()
    result = {
        "n_items": len(items),
        "labels": sorted({item.label for item in items}),
        "item_ids": [item.item_id for item in items],
    }

    if len(items) >= 2:
        result["retrieval_accuracy"] = leave_one_out_retrieval_accuracy(items, compare_features, k_values=(1,))

    if len(items) >= 2:
        rng = random.Random(0)
        result["self_consistency_mean"] = sum(
            self_consistency_score(item.vector, compare_features, rng=rng) for item in items
        ) / len(items)

    label_counts = {label: sum(1 for i in items if i.label == label) for label in result["labels"]}
    has_intra_pair = any(count >= 2 for count in label_counts.values())
    has_inter_pair = len(result["labels"]) >= 2
    if has_intra_pair and has_inter_pair:
        dv = compute_discriminative_validity(items, _distance_fn)
        result["discriminative_validity"] = {
            "mean_intra_label_distance": dv.mean_intra_label_distance,
            "mean_inter_label_distance": dv.mean_inter_label_distance,
            "ratio": dv.ratio,
        }
    else:
        result["discriminative_validity"] = None

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
