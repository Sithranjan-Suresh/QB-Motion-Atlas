# V0 Feature Set

The initial per-phase biomechanical feature set, computed from the six phase boundaries in `docs/phase_definitions.md` plus the underlying per-frame MediaPipe landmarks. Each feature below is a single scalar per clip (V0 scope) — `pipeline/features.py::extract_phase_features()` (task 22) has an unambiguous target to implement against.

**Convention:** same as `phase_definitions.md` — canonical right-handed-thrower orientation (throwing arm = right side: shoulder 12, elbow 14, wrist 16; lead leg = left side: hip 23, knee 25, ankle 27; trailing hip = right hip 24; trailing/non-lead shoulder-hip pairing as needed below). Left-handed mirroring happens upstream (V1 task 41). All landmark positions are MediaPipe normalized image coordinates `(x, y) ∈ [0,1]` unless a feature is explicitly marked as body-scale-normalized (task 24).

## 1. Shoulder rotation angle
**Phase:** measured at the Release frame (the single frame marking the Arm Cock → Acceleration boundary in `phase_definitions.md`).
**Definition:** the angle, in degrees, of the line between the two shoulders (landmark 11 → landmark 12) relative to the image's horizontal axis: `atan2(shoulder_R.y - shoulder_L.y, shoulder_R.x - shoulder_L.x)`, normalized to `[-180, 180]`. This approximates how "open" the shoulders are to the target at release — a shoulder line near 0° (parallel to the horizontal, i.e. perpendicular to the throw direction) indicates a square, fully-rotated release; a larger magnitude indicates the shoulders haven't fully opened up.
**Why at Release:** this is the single most diagnostic instant for shoulder rotation across QBs — comparing it earlier (e.g. mid-Arm-Cock) would conflate "rotation speed" with "rotation completeness," which `release-arm velocity` (feature 5) already captures separately.

## 2. Elbow angle
**Phase:** measured at the Release frame.
**Definition:** the interior angle at the throwing elbow (landmark 14), formed by the shoulder (12), elbow (14), and wrist (16): `angle = arccos( (v1 · v2) / (|v1| |v2|) )` where `v1 = shoulder - elbow` and `v2 = wrist - elbow`, in degrees, range `[0, 180]`. A common coaching signal (e.g. "throwing from a 90°-ish bent elbow at release vs. a locked-out arm") tracked as a single release-instant value in V0.

## 3. Stride length
**Phase:** measured across Stride (Load→Stride boundary frame to Stride→Arm-Cock boundary frame, i.e. the plant).
**Definition:** the straight-line displacement of the lead ankle (landmark 27) between those two frames: `sqrt((ankle_end.x - ankle_start.x)^2 + (ankle_end.y - ankle_start.y)^2)`, in normalized image units at this stage (body-scale-normalized in task 24 so it's comparable across clips shot at different camera distances).

## 4. Hip-shoulder separation
**Phase:** measured at the frame of maximum separation within the Arm Cock phase (the window between the Stride→Arm-Cock boundary and the Arm-Cock→Acceleration boundary) — this is the classic "X-factor" biomechanics signal, and it peaks during arm-cocking by construction (hips have started rotating toward the target while shoulders are still cocked back).
**Definition:** the absolute angular difference, in degrees, between the hip-line angle and the shoulder-line angle at each candidate frame — `hip_angle = atan2(hip_R.y - hip_L.y, hip_R.x - hip_L.x)` (landmarks 24 → 23), `shoulder_angle` as in feature 1 — and the feature value is `max(|shoulder_angle(t) - hip_angle(t)|)` over `t` in the Arm Cock window.

## 5. Release-arm velocity
**Phase:** measured at the Release frame (reuses the same peak-speed computation `phase_segmentation.py::segment_heuristic()` already performs to *locate* the Release boundary — feature extraction does not recompute it independently, it reads the value off the same wrist-speed series).
**Definition:** the throwing wrist's (landmark 16) linear speed at the Release frame: `sqrt(vx^2 + vy^2)` where `(vx, vy)` is the per-frame finite-difference velocity defined in `phase_definitions.md`, in normalized-units/sec (body-scale-normalized in task 24). This is the single strongest available proxy for arm speed without ball-tracking.

## Output shape
`extract_phase_features()` returns a flat `dict[str, float]` with keys `shoulder_rotation_angle_deg`, `elbow_angle_deg`, `stride_length`, `hip_shoulder_separation_deg`, `release_arm_velocity` — one scalar per feature per clip, matching the five named features above. Per-phase breakdown (multiple values per phase, one feature set per phase rather than one per clip) is a V2 concern (`implementation_checklist.md` task 78, "Per-Phase Breakdown").

## Normalization
Two of the five features (`stride_length`, `release_arm_velocity`) are in image-space units and are therefore biased by how close the camera is to the thrower. Task 24 (`pipeline/features.py`) divides both by a body-scale reference measured on the same frame(s) they're computed from — shoulder width (`|shoulder_R - shoulder_L|`) as the reference unit, since it's visible and stable across the whole throw in every V0 seed clip (torso length was considered as an alternative but is more sensitive to camera pitch angle). The three angle-based features (`shoulder_rotation_angle_deg`, `elbow_angle_deg`, `hip_shoulder_separation_deg`) are already scale-invariant by construction and are left unnormalized.
