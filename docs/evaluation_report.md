# Evaluation Report (task 131)

**Status: preliminary, not the final V1/V2 dataset evaluation.** This is a
real run of `eval/run_evaluation.py` against whatever real reference data
exists in this session's Postgres as of 2026-09-25 -- 4 usable real
reference clips across 3 QBs (a 4th clip, `lamar_jackson`'s
`clip2_nfl_everythrow_full`, is excluded per its documented
`pass-with-caveat` status; see below). This is not the "final dataset"
tasks 29/99 describe, which needs a much larger reference set this
environment has not yet been able to source and curate. Every number below
is real (not synthetic, not fabricated to look better), and every one of
them is honestly too small a sample to draw a real conclusion from -- that
is itself the finding.

## What was run, and what wasn't

| Metric | Script | Run? |
|---|---|---|
| Leave-one-out retrieval accuracy | `eval/retrieval_accuracy.py` | Yes |
| Self-consistency | `eval/self_consistency.py` | Yes |
| Discriminative validity | `eval/discriminative_validity.py` | Yes |
| Pose-extraction PCK | `eval/pck.py` | **No** -- needs hand-labeled ground-truth keypoints, which don't exist. No gold-labeling pass (task 19) has been done against real footage. Fully implemented and unit-tested against synthetic predicted/ground-truth pairs (`tests/test_pck.py`), just never run against anything real. |

## Dataset used

4 clip-level (whole-clip, `phase_name=None`) feature vectors, the same
`pipeline/similarity.py::compare_features()` V0 layer the live API actually
uses to match a real upload today:

| Clip | QB |
|---|---|
| `josh_allen__clip2_combine_slowmo` | josh_allen |
| `lamar_jackson__clip1_ravens_combine_full` | lamar_jackson |
| `patrick_mahomes__clip1_qbperformancelab_62mph` | patrick_mahomes |
| `patrick_mahomes__clip2_nfl_2017combine_full` | patrick_mahomes |

`lamar_jackson__clip2_nfl_everythrow_full` is excluded: `data/provenance.csv`
already documented (2026-09-24) that its release/follow-through phases were
never actually visible on camera (the broadcast cuts away first). Its
extracted feature vector still has all 17 keys populated -- `segment_heuristic`
assigns *some* boundary to every phase regardless of whether the real motion
is in frame -- so the values for those phases aren't missing, just not
meaningfully comparable to a clip where release/follow-through really
happened. Including it would silently corrupt the comparison; the exclusion
was already decided, this script just enforces it.

**Only `patrick_mahomes` has more than one clip in this filtered set.**
That means retrieval accuracy and discriminative validity are only
*possible* to get right for the two Mahomes clips -- `josh_allen` and
`lamar_jackson` each have exactly one clip, so there is no correct answer
they could retrieve even in principle. This is the single biggest reason
these numbers can't be treated as a real accuracy measurement yet.

## Results

```json
{
  "n_items": 4,
  "labels": ["josh_allen", "lamar_jackson", "patrick_mahomes"],
  "retrieval_accuracy": {"1": 0.0},
  "self_consistency_mean": 0.584,
  "discriminative_validity": {
    "mean_intra_label_distance": 0.960,
    "mean_inter_label_distance": 0.961,
    "ratio": 1.0006
  }
}
```

**Retrieval accuracy@1 = 0.0.** Both Mahomes clips retrieved a *different*
QB's clip as their nearest match under the current, untuned, equal-weighted
`compare_features()` distance. At n=4 with only one same-label pair to even
attempt, one wrong retrieval already produces 0%; this is not evidence the
approach doesn't work, it's evidence there isn't remotely enough data yet
to tell.

**Discriminative validity ratio ≈ 1.0006 (essentially exactly chance).**
Same-QB clips are, on average, no closer together than different-QB clips
in this feature space, at this sample size, with these untuned per-feature
weights. `docs/similarity_methodology.md` and `docs/embedding_methodology.md`
already flagged every weight in `similarity.py`/`similarity_dtw.py` as an
unvalidated placeholder pending exactly this kind of check (tasks 52-53) --
this run confirms that caveat was not just theoretical hedging: with real
data, the untuned weights genuinely produce no measurable discriminative
signal yet.

**Self-consistency mean ≈ 0.584.** Moderate stability under simulated small
measurement noise (5% perturbation, 20 trials per item) -- lower than ideal,
but with only 4 items this is more a rough sanity check than a validated
number.

## Honest interpretation

This is **not** a result that says "the approach doesn't work." It's a
result that says: 4 clips across 3 QBs, one of which has only a single
clip each, is nowhere near enough data to validate (or invalidate) a
similarity metric, tuned or not -- exactly the state `docs/research_log.md`
has described all along, now backed by an actual number instead of only a
prediction. The real next step (task 29/99: expand the reference dataset;
task 52-53: tune weights against real retrieval accuracy once there's
enough data to tune against) is unchanged by this report -- this report
just replaces "we haven't been able to check" with "we checked, and
confirmed there isn't enough data yet to conclude anything either way."

## Reproducing this report

```bash
source .venv/bin/activate
python -m eval.run_evaluation
```

Re-run any time `data/features_raw/` and the seeded Postgres reference set
change -- the script always reflects whatever real clean-`pass` reference
data currently exists, not a fixed snapshot.
