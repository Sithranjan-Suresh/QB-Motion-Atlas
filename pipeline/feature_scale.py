"""Shared per-feature scale constants (task 116), covering all 17 keys
extract_phase_features() can return -- an extension of
pipeline/similarity.py's SCALE (which only covers the original 5 V0
features) so the V2 per-phase comparison
(pipeline/per_phase_similarity.py) can normalize any subset of features
consistently. Values for the 5 original keys match similarity.py's SCALE
exactly; that module's own SCALE dict is left as-is rather than refactored
to import from here, since it's already tested and shipped.

All values are placeholders (typical-range guesses, not empirically
measured) -- same caveat as similarity.py's SCALE and every other
placeholder constant in this codebase, pending real reference data.
"""

from __future__ import annotations

SCALE_ALL: dict[str, float] = {
    "shoulder_rotation_angle_deg": 180.0,
    "elbow_angle_deg": 180.0,
    "stride_length": 1.5,
    "hip_shoulder_separation_deg": 90.0,
    "release_arm_velocity": 2.0,
    "acceleration_rate": 150.0,
    "follow_through_deceleration_rate": 100.0,
}
for _phase in ("load", "stride", "arm_cock", "acceleration", "follow_through"):
    SCALE_ALL[f"{_phase}_duration_sec"] = 0.3
    SCALE_ALL[f"{_phase}_duration_frac"] = 1.0
