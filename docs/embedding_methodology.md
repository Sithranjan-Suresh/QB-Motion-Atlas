# V2 Learned Embedding Methodology

`full_context.md`'s stated differentiator: "a learned embedding space trained via metric learning, not just hand-tuned distance metrics." This documents the training objective (task 98) and network architecture (task 102) for that embedding.

## Why per-phase, not per-clip

`full_context.md`'s whole framing is per-phase comparison ("your stride phase resembles Herbert, your release resembles Stafford"), not a single whole-throw embedding. So the embedding is trained and applied **per (clip, phase) pair**, not per clip — one embedding vector per phase per reference clip, matching `qb_reference_features`'s existing `phase_name` column (V1 leaves this `None` for the whole-clip feature set; V2 populates one row per phase instead/in addition).

## Triplet definition (task 98)

Given the reference set only has QB-identity labels right now (no independently-verified "phase archetype" labels — those would have to come from clustering a *trained* embedding, which doesn't exist yet), the initial objective bootstraps off identity, with phase-archetype grouping as a stated future refinement once an initial embedding produces clusters worth inspecting:

- **Anchor:** `(clip_i, phase_p)`'s feature vector -- one specific phase of one specific reference clip.
- **Positive:** `(clip_j, phase_p)` where `clip_j != clip_i` belongs to the **same QB** as `clip_i`, same phase `p`. The intent: a QB's stride mechanics should look like *that QB's* stride mechanics across their different clips, regardless of which specific rep it is.
- **Negative:** `(clip_k, phase_p)` where `clip_k` belongs to a **different QB**, same phase `p` (never a different phase -- comparing a stride embedding to a release embedding would conflate "different phase" with "different mechanics," which isn't the signal being learned).

**Loss:** standard margin-based triplet loss, `L = max(0, d(anchor, positive) - d(anchor, negative) + margin)`, `d` = Euclidean distance in embedding space, encouraging same-QB-same-phase pairs closer together than different-QB-same-phase pairs by at least `margin`.

**Refinement once clusters exist:** after an initial embedding is trained and evaluated (tasks 105-107), inspect whether same-phase clips cluster by something more specific than QB identity (e.g. "over-the-top vs. three-quarter release" cutting across QBs) -- if so, re-derive positive/negative pairs from those clusters instead of raw QB identity for a second training pass. Not attempted in the initial pass since it requires a trained embedding to even discover candidate archetypes from.

## Network architecture (task 102)

Input: one phase's feature vector from `extract_phase_features()` -- a small, fixed-size vector (the per-phase subset of the 17 keys in `docs/feature_definitions.md`, typically 2-5 numbers per phase plus its duration/fraction). This is deliberately **not** a sequence model over raw per-frame trajectories (that's what the V1 DTW layer already does, per `docs/similarity_methodology.md`) -- the embedding operates on the same interpretable per-phase feature space the V0/V1 layers already use, so a small MLP is the appropriate architecture, not a 1D-conv/RNN encoder that would need much more reference data than this project's realistic clip counts to train without overfitting.

```
EmbeddingNet:
  Linear(input_dim -> 32) -> ReLU
  Linear(32 -> 16) -> ReLU
  Linear(16 -> EMBEDDING_DIM)   # EMBEDDING_DIM = 8, a deliberately small
                                 # space given how little reference data
                                 # this project realistically has
  L2-normalize output           # so embedding distance is comparable
                                 # across phases/runs regardless of raw
                                 # feature-vector scale
```

`input_dim` varies by phase (different phases have different feature counts in `feature_definitions.md`) -- one `EmbeddingNet` instance is trained per phase, not one shared network across all six, since mixing e.g. `release`'s 3-feature vector with `stride`'s 3-feature vector into one input space would need padding/masking machinery that isn't justified at this project's scale.

## Train/validation/held-out-test split (task 101)

Split **at the clip level, stratified by QB**, via `pipeline/embedding/dataset_split.py::split_clips()` -- never at the phase or feature-vector level, since a clip's six phases all came from the same physical throw and splitting them across train/test would leak information about that specific throw into "held-out" evaluation.

**Target ratios: 70% train / 15% validation / 15% test**, standard for a small-data metric-learning setup where validation is used for early-stopping/hyperparameter choices (task 107) and the test split is only touched for the final reported retrieval accuracy (task 106) -- keeping those two separate is what makes the final number honest rather than a number that was implicitly tuned against.

**Small-N handling:** at the reference set's realistic current/near-term size (single digits of clips per QB before task 99's expansion), a strict 70/15/15 split per QB often rounds to zero clips in validation/test for that QB. `split_clips()` handles this explicitly rather than silently producing an empty split: a QB with fewer than `MIN_CLIPS_FOR_SPLIT` (3) clips has all of its clips placed in train, and is documented as absent from validation/test until it has enough clips to split meaningfully. This means validation/test coverage will be sparse and QB-lopsided until task 99 actually grows the dataset -- an accepted, logged limitation, not a bug to work around with a fake split.

## Known limitation

Every number above (network width, embedding dimension, margin) is a placeholder sized for "this should train without immediately overfitting on a handful of reference clips," not empirically tuned -- there's no real reference dataset large enough to tune against yet (task 99, blocked on the same YouTube network-access issue as the rest of this project's real-data work; see `docs/research_log.md`). Revisit once real data exists.
