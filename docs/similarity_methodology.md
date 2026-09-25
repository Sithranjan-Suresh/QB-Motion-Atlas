# Similarity Methodology

Two complementary similarity layers, per `engineering_spec.md`'s "interpretable features (DTW/weighted distance)" framing — combined into one overall score at V1, with a third learned-embedding layer added at V2 (`full_context.md`'s "hand-engineered feature distance + DTW + learned metric-learning embedding").

## Layer 1: V0 per-phase feature distance (`pipeline/similarity.py`)
`compare_features()` compares two clips' five-features-per-clip snapshots (`docs/feature_definitions.md`) via scale-normalized weighted Euclidean distance, mapped to a `(0, 1]` similarity score. This captures *what the key numbers were* at specific meaningful instants (release angle, peak velocity, etc.) but throws away everything about the shape of the motion in between those instants — two throws with an identical release angle and stride length could still look completely different through the load and arm-cock phases, and this layer can't tell.

## Layer 2: V1 DTW whole-motion shape (`pipeline/similarity_dtw.py`)
`dtw_align()` runs classic dynamic time warping over each clip's full per-frame trajectory (`build_frame_trajectory()`: elbow angle, shoulder rotation angle, normalized wrist speed, one triple per frame) rather than a handful of per-phase snapshots. DTW handles the fact that two people don't throw at exactly the same tempo — it finds the lowest-cost alignment between the two sequences even when one runs faster or slower through parts of the motion, which a frame-by-frame or per-phase-only comparison can't do. This is what actually captures "the *shape* of the whole motion resembles X," not just "the numbers at these five checkpoints happen to match."

**Normalization:** raw DTW cost grows with the warping path's length (longer clips accumulate more per-frame cost even for a perfect match), so `dtw_similarity()` divides the raw distance by the alignment length before converting to a `(0, 1]` similarity score — the same `1 / (1 + distance)` transform Layer 1 uses, so both layers are on a comparable scale before combining.

## Combining the two layers (task 51)
`similarity_dtw.py::combined_similarity()`:

```
combined = feature_weight * feature_similarity + dtw_weight * trajectory_similarity
```

**Current weighting: equal (0.5 / 0.5) — a placeholder, not a tuned value.** There's no labeled retrieval data yet to justify weighting one layer over the other (same caveat as Layer 1's per-feature weights in `similarity.py`). Task 52 (leave-one-out retrieval accuracy check) and task 53 (tune weighting/thresholds until same-QB retrieval clearly beats chance) are the steps that would actually justify a different split — both are currently blocked on the same YouTube network-access issue documented in `docs/research_log.md`'s 2026-09-25 entry, since they need the real reference set's features and trajectories to run against, not synthetic data. Revisit this constant once those tasks actually run.

## V2 preview
`full_context.md` describes a third layer — a learned embedding space trained via metric learning (triplet loss) — layered on top of these two interpretable layers, not replacing them. That's out of scope until the V1 exit criteria (a deployed app with validated retrieval accuracy) are met.
