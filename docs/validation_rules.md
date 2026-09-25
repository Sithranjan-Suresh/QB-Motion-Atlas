# Upload Validation Rules

Computable, automated counterparts to the by-eye criteria in `docs/data_criteria.md` (which govern what goes *into* the reference database) — these run against a user's uploaded video at inference time, so `pipeline/validation.py::validate_upload()` (task 36) has an unambiguous target to implement against. All three rules must pass for an upload to proceed to phase segmentation; the first one that fails determines the `rejection_reason`, checked in the order below (camera angle → full body → single throw), since a bad angle or missing body makes the throw-detection check meaningless.

**Precondition:** same as `phase_segmentation.py`/`features.py` — every frame must already have landmarks (gaps filled by `filter_low_confidence_landmarks` first). Landmark indices per the existing canonical-orientation convention (throwing arm = right side, lead leg = left side); left-handed mirroring (V1 task 41) happens upstream of validation too, so validation always sees the canonical orientation.

## 1. Camera angle
**Signal:** for each frame, `shoulder_span_x = |shoulder_R.x - shoulder_L.x|` (landmarks 12, 11) and `torso_length = distance(shoulder_midpoint, hip_midpoint)` (midpoints of landmarks 11/12 and 23/24). The ratio `shoulder_span_x / torso_length` is small for a true side-on view (the two shoulders nearly overlap in the image's x-axis when viewed edge-on) and large for a frontal/rear view (the full shoulder width is visible).
**Rule:** average the per-frame ratio across all frames; **pass** if `mean_ratio <= CAMERA_ANGLE_MAX_RATIO` (V0/V1 placeholder: `0.5`, un-tuned against real uploads — same caveat as `pipeline/similarity.py`'s placeholder weights).
**Rejection reason:** `bad_camera_angle` — "Camera angle looks frontal/behind rather than to your throwing side. Move the camera to your throwing-arm side, roughly perpendicular to your body."
**Known limitation:** this is a 2D heuristic and doesn't disambiguate every viewing angle perfectly (per `full_context.md`'s framing, real camera-angle robustness needs 3D lifting, which is explicitly V3 scope) — it's meant to catch the clearly-wrong cases (fully frontal, fully behind), not to be a precise angle estimator.

## 2. Full body visible
**Signal:** a required joint set — nose (0), both shoulders (11, 12), both hips (23, 24), both knees (25, 26) — covers "head to at least mid-thigh" per `data_criteria.md`. A frame counts as "body visible" if every required joint's `visibility >= JOINT_VISIBILITY_THRESHOLD` (0.5, matching the threshold already used by `landmark_filter.py`).
**Rule:** **pass** if the fraction of frames counted as "body visible" is `>= FULL_BODY_MIN_FRAME_FRACTION` (0.9) of all frames in the clip.
**Rejection reason:** `body_not_fully_visible` — "Can't see your full body (head to mid-thigh) through the whole throw. Back up or reframe so your legs and throwing arm stay in frame."

## 3. Single throw detected
**Signal:** the throwing wrist's (landmark 16) per-frame linear speed series, same finite-difference definition as `phase_definitions.md` (`sqrt(vx^2 + vy^2)`, units/sec). Peaks are detected with a minimum height (`SINGLE_THROW_PEAK_HEIGHT`, a placeholder velocity threshold distinguishing a real throwing motion from incidental arm movement) and a minimum frame separation (`SINGLE_THROW_MIN_PEAK_DISTANCE_FRAMES`) so jitter around one true peak isn't double-counted as two throws.
**Rule:** **pass** if exactly one peak is found.
**Rejection reasons:**
- `no_throw_detected` (zero peaks) — "Didn't detect a throwing motion in this clip. Make sure the full load-through-release motion is visible."
- `multiple_throws_detected` (more than one peak) — "Detected more than one throwing motion in this clip. Upload a single throw per video."

## `ValidationResult`
```
ValidationResult(status: "pass" | "reject", rejection_reason: str | None)
```
`rejection_reason` is one of the four string codes above (`None` when `status == "pass"`), used as a lookup key into the shared rejection-copy constants (task 38) rather than the copy itself, so API and frontend can both render the same message (or localize it later) from one source of truth.
