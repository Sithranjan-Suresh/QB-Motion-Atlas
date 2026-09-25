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
**Definition:** the absolute angular difference, in degrees, between the hip-line angle and the shoulder-line angle at each candidate frame — `hip_angle = atan2(hip_R.y - hip_L.y, hip_R.x - hip_L.x)` (landmarks 23 → 24, same left-to-right direction as the shoulder line), `shoulder_angle` as in feature 1 — and the feature value is `max(|shoulder_angle(t) - hip_angle(t)|)` over `t` in the Arm Cock window.

## 5. Release-arm velocity
**Phase:** measured at the Release frame (reuses the same peak-speed computation `phase_segmentation.py::segment_heuristic()` already performs to *locate* the Release boundary — feature extraction does not recompute it independently, it reads the value off the same wrist-speed series).
**Definition:** the throwing wrist's (landmark 16) linear speed at the Release frame: `sqrt(vx^2 + vy^2)` where `(vx, vy)` is the per-frame finite-difference velocity defined in `phase_definitions.md`, in normalized-units/sec (body-scale-normalized in task 24). This is the single strongest available proxy for arm speed without ball-tracking.

## Output shape
`extract_phase_features()` returns a flat `dict[str, float]` with keys `shoulder_rotation_angle_deg`, `elbow_angle_deg`, `stride_length`, `hip_shoulder_separation_deg`, `release_arm_velocity` — one scalar per feature per clip, matching the five named features above. Per-phase breakdown (multiple values per phase, one feature set per phase rather than one per clip) is a V2 concern (`implementation_checklist.md` task 78, "Per-Phase Breakdown").

## V1 additions: per-phase timing (tasks 46-47)

V0's five features are single-instant or single-window snapshots that don't, on their own, give every one of the six phases a feature. V1 adds a duration for every phase, plus two rate-of-change signals that are distinct from the existing peak/instant features rather than duplicates of them:

- **`{phase}_duration_sec`** for all six phases (`load`, `stride`, `arm_cock`, `acceleration`, `release`, `follow_through`) — `(end_frame - start_frame) / fps`. `release` is a single frame by definition (`phase_definitions.md`), so its duration is always 0 and isn't included as a feature.
- **`acceleration_rate`** — the average rate of increase of throwing-wrist speed across the Acceleration phase: `(wrist_speed[release_frame] - wrist_speed[acceleration.start_frame]) / acceleration_duration_sec`, body-scale-normalized (divided by mean shoulder width over the Acceleration window). Deliberately not the same thing as `release_arm_velocity` (peak speed) — two throws can reach the same peak speed via very different acceleration rates, which is itself a meaningful mechanical difference.
- **`follow_through_deceleration_rate`** — the average rate of decrease of throwing-wrist speed across Follow-through: `(wrist_speed[release_frame] - wrist_speed[n-1]) / follow_through_duration_sec`, same normalization. Expected positive (decelerating from the release-instant peak).

**Timing normalization (task 47):** absolute per-phase duration in seconds isn't comparable across clips shot at different effective throw speed (e.g. high-frame-rate slow-motion vs. real-time — see `provenance.csv`'s playback-speed notes). Alongside each `{phase}_duration_sec`, `extract_phase_features()` also returns **`{phase}_duration_frac`** = `{phase}_duration_sec / total_duration_sec` (total = sum of all six phase durations, i.e. `(n - 1) / fps`), which is scale-invariant to overall throw tempo the same way the task-24 body-scale normalization is scale-invariant to camera distance.

## Normalization
Two of the five features (`stride_length`, `release_arm_velocity`) are in image-space units and are therefore biased by how close the camera is to the thrower. Task 24 (`pipeline/features.py`) divides both by a body-scale reference — shoulder width `|shoulder_R - shoulder_L|` (landmarks 12, 11) as the reference unit, since it's visible and stable across the whole throw in every V0 seed clip (torso length was considered as an alternative but is more sensitive to camera pitch angle). To avoid the reference itself being noisy at a single frame, it's averaged over every frame the un-normalized feature spans: the Stride window (`stride.start_frame`..`stride.end_frame`) for `stride_length`, and just the Release frame for `release_arm_velocity`. The three angle-based features (`shoulder_rotation_angle_deg`, `elbow_angle_deg`, `hip_shoulder_separation_deg`) are already scale-invariant by construction and are left unnormalized.
