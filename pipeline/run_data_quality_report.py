"""Task 49 CLI: run the data-quality outlier report (pipeline/data_quality.py)
against every clip's feature vector in data/features_raw/.

Usage: python -m pipeline.run_data_quality_report

Note (2026-09-25): not runnable against real data yet -- data/features_raw
is empty in this cloud session (see docs/research_log.md's YouTube
network-access blocker; task 23's batch feature extraction hasn't run).
The seed set only has 1-2 clips per QB regardless (see provenance.csv),
below MIN_OTHER_CLIPS, so this report is only meaningful once the V1
dataset expansion (task 29: 8-10 QBs, 10+ clips each) is done.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.data_quality import find_outlier_clips

FEATURES_DIR = Path(__file__).resolve().parent.parent / "data" / "features_raw"


def _load_qb_features() -> dict[str, dict[str, dict[str, float]]]:
    qb_features: dict[str, dict[str, dict[str, float]]] = {}
    for features_path in sorted(FEATURES_DIR.glob("*.json")):
        clip_id = features_path.stem
        qb_name, _clip_name = clip_id.split("__", 1)
        qb_features.setdefault(qb_name, {})[clip_id] = json.loads(features_path.read_text())
    return qb_features


def main() -> None:
    qb_features = _load_qb_features()
    if not qb_features:
        print(f"No feature files found in {FEATURES_DIR} -- nothing to check.")
        return

    outliers = find_outlier_clips(qb_features)
    if not outliers:
        print("No outliers found.")
        return

    for outlier in outliers:
        print(
            f"{outlier['qb_name']} / {outlier['clip_id']}: {outlier['feature']} = "
            f"{outlier['value']:.4f} (other clips' mean {outlier['other_clips_mean']:.4f}, "
            f"z={outlier['z_score']:.2f})"
        )


if __name__ == "__main__":
    main()
