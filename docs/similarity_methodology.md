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

## What the live upload path actually runs (`pipeline/matching.py`)
Until 2026-09-30 the upload pipeline only used Layer 1; DTW and the embedding existed but were never called for a real upload. `score_reference_clips()` now scores every reference clip whose provenance QC didn't fail, using whichever layers that clip has data for:

| Layer | Used when | Source |
|---|---|---|
| Feature distance | always | the clip's clip-level feature vector |
| DTW | the clip has a stored landmark sequence | `landmark_sequences` (seeded from `data/landmarks_raw`) |
| Embedding | `EMBEDDING_CHECKPOINTS_DIR` has a checkpoint for a phase, and the clip's phase rows have backfilled `embedding_vector`s | `models/embedding_inference.py`, `db/backfill_embeddings.py` |

A clip's score is the weighted mean of its available layers, with the weights (equal thirds, `LAYER_WEIGHTS`) renormalized over them. Two details that matter for correctness:
- **Handedness:** reference landmark sequences are stored un-mirrored (they're drawn over the real video), so they're canonicalized to right-handed before the trajectory is built. Without that, a left-handed QB's trajectory would be compared on the wrong arm.
- **DTW cost:** both trajectories are resampled to at most 60 frames first, which keeps ~40 reference clips well under a second in pure Python.

Known limitation: a clip scored with one extra layer isn't strictly comparable with a clip scored on fewer, because each layer has its own score distribution. Once every reference clip has landmark data (after the next `db.seed` with `data/landmarks_raw`), all clips are scored on the same layers. The per-layer scores for each match are logged (`"upload matched"`) so the weighting can be tuned against real uploads.

## V2 preview
`full_context.md` describes a third layer — a learned embedding space trained via metric learning (triplet loss) — layered on top of these two interpretable layers, not replacing them. That's out of scope until the V1 exit criteria (a deployed app with validated retrieval accuracy) are met.
