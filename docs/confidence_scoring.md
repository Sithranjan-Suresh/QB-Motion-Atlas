# Confidence Scoring

A single high/medium/low confidence level per analysis result, so the product can show an explicit low-confidence state instead of a forced, potentially-wrong-looking answer (`full_context.md`'s "Confidence-aware results" feature, `product_spec.md`'s acceptance criteria on flagging bad input rather than silently scoring it). `pipeline/confidence.py::compute_confidence()` (task 55) implements this against three inputs, each already computed elsewhere in the pipeline:

## 1. Pose-extraction completeness
**Signal:** the fraction of frames whose landmarks are entirely non-interpolated -- i.e. every joint on that frame came from a real MediaPipe detection, none of it was filled in by `landmark_filter.py::filter_low_confidence_landmarks()` (task 15). A frame with even one interpolated joint counts against completeness, since it means the raw signal had a gap there.
**Range:** `[0, 1]`, where `1.0` means every frame was fully, genuinely detected.

## 2. Average phase-boundary confidence
**Signal:** the mean of the six `PhaseBoundary.confidence` values from `phase_segmentation.py::segment_heuristic()` (tasks 44-45) -- each boundary's confidence already reflects both inflection sharpness and joint visibility (occlusion) at that frame. `load`'s confidence is definitionally `1.0` (it's the clip's start, not a detected inflection), so it always contributes a "free" high value; this is a known simplification, not a bug -- five of the six boundaries are genuinely detected and drag the average down when they're unreliable.
**Range:** `[0, 1]`.

## 3. Similarity-score margin
**Signal:** given a ranked list of similarity scores against the reference set (highest first), the gap between the top-1 and top-2 scores: `similarity_scores[0] - similarity_scores[1]`. A large margin means the top match clearly beats the runner-up -- a confident match, not a coin flip between two similar-looking QBs. With only one candidate score (or none), there's no runner-up to compare against; the raw top score itself is used as a (weaker) stand-in for margin in that case.
**Range:** approximately `[0, 1]` (similarity scores themselves are `(0, 1]` per `pipeline/similarity.py`, so the largest possible margin approaches 1).

## Combining into a level
```
overall = (pose_completeness + avg_boundary_confidence + similarity_margin) / 3

level = "high"   if overall >= HIGH_THRESHOLD   (0.7)
        "medium" if overall >= MEDIUM_THRESHOLD (0.4)
        "low"    otherwise
```
Equal weighting and the two thresholds (`0.7`, `0.4`) are V1 placeholders -- same caveat as `similarity.py`'s feature weights and `similarity_dtw.py`'s layer-combination weights: there's no labeled data yet to justify weighting one signal over another or picking different cutoffs. Revisit once there's real usage data to check whether "high" confidence actually correlates with results a user would agree with.
