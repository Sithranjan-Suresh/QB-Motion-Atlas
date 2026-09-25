# Throw Phase Taxonomy

Six phases per `full_context.md`. Each boundary below is defined as a concrete, computable signal over MediaPipe Pose's 33 landmarks, so `pipeline/phase_segmentation.py::segment_heuristic()` (task 17) has an unambiguous target to implement against.

**Convention:** landmark indices below assume a right-handed thrower in the canonical (post-normalization) orientation — throwing arm = right side (shoulder 12, elbow 14, wrist 16), lead/stride leg = left side (hip 23, knee 25, ankle 27). Left-handed throwers are mirrored onto this convention during preprocessing (V1 task 41) before phase segmentation runs, so the segmenter itself only ever has to handle one handedness.

All positions are in MediaPipe's normalized image coordinates (x, y in [0, 1] relative to frame width/height) unless otherwise noted. "Velocity" of a landmark at frame *i* means `(position[i] - position[i-1]) * fps` — a per-frame finite difference, not a smoothed signal, at the heuristic-segmenter stage (V0). Sign convention: +x is toward the target/downfield direction the thrower is facing, +y is downward (image coordinates).

## 1. Load
**Description:** Initial set-up — ball held near the chest/torso, weight balanced, before any forward motion begins.
**Start:** start of the analyzed clip window (the clip is already trimmed to begin at or before the throw's initiation, per `data_criteria.md`).
**End (→ Stride):** the frame where the lead ankle's (landmark 27) forward (x) velocity first exceeds a small positive threshold and stays above it for several consecutive frames — the moment the front foot begins its forward step. This is the single most reliable, low-noise boundary in the whole taxonomy, since the lead leg is nearly stationary during Load and moves distinctly during Stride.

## 2. Stride
**Description:** The lead leg steps forward toward the target; the throwing arm begins drawing back but hasn't yet reached max external rotation.
**Start:** end of Load (above).
**End (→ Arm Cock):** lead-foot plant — the frame where the lead ankle's (landmark 27) vertical (y) velocity returns to near zero after the stride's downward swing, sustained for several consecutive frames (a local-minimum-then-flat pattern in `|velocity_y|`). This is the classic "front foot down" biomechanical marker used to separate stride from arm-cocking in throwing-motion analysis generally.

## 3. Arm Cock
**Description:** From front-foot plant to maximum external rotation of the throwing shoulder — the ball is drawn back, elbow near 90°, throwing hand at its rearmost point relative to the torso.
**Start:** end of Stride (above).
**End (→ Acceleration):** the frame of maximum external rotation, approximated as the local extremum where the throwing wrist's (landmark 16) horizontal position relative to the throwing shoulder (landmark 12) — i.e. `wrist.x - shoulder.x` — reaches its most negative (rearmost) value and begins increasing. This is the reversal point where the arm stops cocking backward and starts driving forward.

## 4. Acceleration
**Description:** Rapid internal rotation of the shoulder, trunk/hip rotation toward the target, elbow extension — the arm whips forward toward release.
**Start:** end of Arm Cock (above).
**End (→ Release):** the frame of peak forward linear speed of the throwing wrist (landmark 16), i.e. `argmax(|velocity(wrist)|)` over the window between the Arm Cock boundary and the end of the clip. Ball release happens at or immediately after peak hand speed in essentially all overhand throwing motions, making this the standard proxy for release timing when the ball itself isn't separately tracked.

## 5. Release
**Description:** The instant the ball leaves the hand.
**Definition:** a single frame, not a duration — the same frame identified as the Acceleration→Release boundary above (peak throwing-wrist speed). Downstream feature extraction treats Release as a point-in-time marker (for timing features) rather than a phase with its own duration.

## 6. Follow-through
**Description:** Deceleration — the arm continues across the body, trunk keeps rotating, back leg may drag through. Ends when the motion visibly settles.
**Start:** the Release frame (above).
**End:** end of the analyzed clip window (the clip is trimmed to end at or shortly after the throw's completion, per `data_criteria.md`), or, if the clip runs longer, the frame where the throwing wrist's speed decays back below the same small threshold used for the Load→Stride boundary and stays there — the motion has visibly stopped.

## Implementation notes for `segment_heuristic()`
- Compute all six boundary frame indices in one pass per clip: Load→Stride, Stride→ArmCock, ArmCock→Acceleration (=Release), then Follow-through end.
- Each `PhaseBoundary` (except Load, whose start=0 is the clip boundary rather than a detected inflection) also carries a `confidence` score in `[0, 1]` (V1 task 44) — the discrete-curvature sharpness of the detected inflection in whatever signal located it, normalized against the sharpest curvature elsewhere in that same signal. A boundary found at a sharp, unambiguous inflection scores near 1.0; one found on a flat or noisy stretch scores low. This feeds the overall confidence-scoring system later (V1 "Confidence Scoring" section), not just phase segmentation in isolation.
- That confidence is further weighted by the visibility, at the detected frame, of the joint whose trajectory located the boundary (V1 task 45) -- so a boundary correctly located on a partially-occluded joint (e.g. the throwing arm occluded right at release) degrades confidence proportionally rather than `segment_heuristic` either failing outright or reporting unwarranted full confidence.
- Thresholds (forward-velocity-onset, near-zero-vertical-velocity) are not fixed in this document — they get tuned empirically against the V0 hand-labeled gold boundaries (task 19-20) and re-tuned against a larger labeled set in V1 (task 43).
- This heuristic is velocity/angle-threshold based by design (per `engineering_spec.md`'s V1 heuristic-segmentation approach) and is expected to be replaced by a trained temporal classifier in V2.
