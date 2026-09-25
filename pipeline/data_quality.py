"""Data-quality outlier report (task 49): flags reference clips whose
features are statistical outliers relative to their own QB's other clips --
catches a bad trim, a mislabeled clip, or a pose-extraction glitch that
slipped past the by-eye checks in data_criteria.md.
"""

from __future__ import annotations

OUTLIER_Z_THRESHOLD = 2.0
# Need at least this many *other* clips to establish what's "normal" for a QB
# before flagging one of their clips as an outlier -- with fewer, a single
# clip's mean/std isn't meaningful.
MIN_OTHER_CLIPS = 2


def find_outlier_clips(qb_features: dict[str, dict[str, dict[str, float]]]) -> list[dict]:
    """qb_features: qb_name -> clip_id -> feature_dict (from extract_phase_features).

    For each clip and each feature, compares that clip's value against the
    leave-one-out mean/std of the *same QB's other clips* for that feature
    (not the whole reference set -- a QB with naturally high release velocity
    shouldn't be flagged just for differing from the rest of the database).
    Returns one report entry per (clip, feature) pair whose z-score exceeds
    OUTLIER_Z_THRESHOLD, sorted by |z_score| descending (most anomalous first).
    """
    outliers = []

    for qb_name, clips in qb_features.items():
        clip_ids = list(clips.keys())
        feature_names: set[str] = set()
        for feature_dict in clips.values():
            feature_names.update(feature_dict.keys())

        for feature_name in feature_names:
            for clip_id in clip_ids:
                if feature_name not in clips[clip_id]:
                    continue

                other_values = [
                    clips[other_id][feature_name]
                    for other_id in clip_ids
                    if other_id != clip_id and feature_name in clips[other_id]
                ]
                if len(other_values) < MIN_OTHER_CLIPS:
                    continue

                mean = sum(other_values) / len(other_values)
                variance = sum((v - mean) ** 2 for v in other_values) / len(other_values)
                std = variance**0.5
                if std == 0:
                    continue

                value = clips[clip_id][feature_name]
                z_score = (value - mean) / std
                if abs(z_score) > OUTLIER_Z_THRESHOLD:
                    outliers.append(
                        {
                            "qb_name": qb_name,
                            "clip_id": clip_id,
                            "feature": feature_name,
                            "value": value,
                            "other_clips_mean": mean,
                            "other_clips_std": std,
                            "z_score": z_score,
                        }
                    )

    outliers.sort(key=lambda o: abs(o["z_score"]), reverse=True)
    return outliers
