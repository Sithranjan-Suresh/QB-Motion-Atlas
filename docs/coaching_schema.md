# Coaching Delta Schema

The single structured input the LLM coaching step (`docs/coaching_prompt.md`, task 59) is allowed to see — per `engineering_spec.md`'s narrow integration point: "input is a structured JSON of computed deltas per phase... The LLM never receives raw video or makes any numeric/matching decision."

## `Delta`
```
Delta(
    phase: str,             # one of the six phase names from phase_definitions.md
    metric_name: str,       # a key from extract_phase_features()'s output, e.g. "elbow_angle_deg"
    user_value: float,      # the uploaded user's value for this metric
    reference_value: float, # the matched reference QB's value for the same metric
    delta: float,           # user_value - reference_value (signed; positive = user's value is higher)
    unit: str,              # "deg", "sec", "fraction", "shoulder_widths", or "shoulder_widths/sec[^2]"
)
```

## Feature -> (phase, unit) mapping
`pipeline/coaching.py::build_deltas()` (task 58) needs to know which phase and unit each of `extract_phase_features()`'s flat keys belongs to, since the feature dict itself doesn't carry that metadata:

| Feature key | Phase | Unit |
|---|---|---|
| `shoulder_rotation_angle_deg` | release | deg |
| `elbow_angle_deg` | release | deg |
| `release_arm_velocity` | release | shoulder_widths/sec |
| `stride_length` | stride | shoulder_widths |
| `hip_shoulder_separation_deg` | arm_cock | deg |
| `acceleration_rate` | acceleration | shoulder_widths/sec^2 |
| `follow_through_deceleration_rate` | follow_through | shoulder_widths/sec^2 |
| `{phase}_duration_sec` (load/stride/arm_cock/acceleration/follow_through) | that phase | sec |
| `{phase}_duration_frac` (same five phases) | that phase | fraction |

`build_deltas()` only emits a `Delta` for a metric present in *both* the user's and the matched QB's feature dicts (a metric one side is missing shouldn't silently compare against a stale or zero value) and raises if it encounters a metric key it has no mapping for, rather than guessing a phase/unit -- this keeps the schema honest as `features.py` evolves.

## Why this schema, and why it's the LLM's only input
Every number the LLM ever phrases into a sentence traces back to one of these `Delta` rows -- so a coaching note like "your release-arm velocity is 12% below Mahomes'" is always backed by an actual computed value, not an invented-sounding generality. This is what `product_spec.md`'s acceptance criterion ("references a specific measured value or delta... rather than a generic sentence with no numbers behind it") and `full_context.md`'s "back every claim with a number" both require structurally, not just as a prompt instruction.
