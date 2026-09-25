# Coaching LLM: Fixed Prompt & Output Schema

The single, narrow LLM integration point in the whole system (`engineering_spec.md`): one call, after all numeric analysis is complete, that turns `Delta` rows (`docs/coaching_schema.md`) into short coaching sentences. The LLM never sees raw video, never re-derives or second-guesses the similarity match, and never invents a number that isn't already in its input.

## System prompt (fixed, verbatim)
```
You are a football throwing-mechanics coach. You will be given a JSON list of
measured differences ("deltas") between a user's throwing motion and a matched
NFL quarterback's, one delta per biomechanical metric. Each delta has already
been computed by a separate measurement system -- you are not measuring
anything yourself, and you must not state or imply any number that isn't
already present in the input.

For each distinct "phase" value in the input, write exactly one short coaching
sentence (max ~25 words) that:
- names the phase,
- references the specific numeric delta and unit for at least one metric in
  that phase,
- gives one concrete, actionable coaching cue tied to that number.

Do not comment on phases that aren't in the input. Do not rank or score the
user overall -- that's not your job. Do not mention the matched QB's name if
it isn't given to you. Output nothing except the JSON described below.
```

## Input (from `build_deltas()`, task 58)
```json
[
  {"phase": "release", "metric_name": "elbow_angle_deg", "user_value": 141.4, "reference_value": 144.5, "delta": -3.1, "unit": "deg"},
  {"phase": "stride", "metric_name": "stride_length", "user_value": 0.95, "reference_value": 1.10, "delta": -0.15, "unit": "shoulder_widths"}
]
```
(One entry per shared metric, as `Delta` dataclass instances serialized to dicts -- not filtered or summarized before being handed to the LLM, since which deltas matter enough to mention is itself part of what the LLM is asked to decide within its per-phase sentence limit.)

## Output schema (fixed)
```json
[
  {"phase": "release", "note": "Your elbow angle at release is 3° tighter than the reference -- work on getting slightly more extension before you let go."},
  {"phase": "stride", "note": "Your stride is about 15% shorter (in body-widths) than the reference -- try driving further toward the target before planting."}
]
```
A JSON array of objects, each with exactly two string keys, `phase` and `note`. `pipeline/coaching.py::generate_coaching_notes()` (task 60) validates every returned object against this schema before accepting it:
- valid JSON, a list, non-empty (if the input had at least one phase);
- each item is a dict with exactly the keys `{"phase", "note"}`;
- `phase` is one of the six valid phase names from `phase_definitions.md`, and was actually present in the input deltas (the LLM can't invent commentary on a phase it wasn't given data for);
- `note` is a non-empty string, at most `MAX_NOTE_LENGTH` (200) characters;
- `note` contains at least one digit -- a cheap structural proxy for "actually references the numeric delta," not a semantic guarantee (verifying the note cites the *correct* number would need another LLM call or fragile regex-matching against formatted values, out of scope for V1).

Any validation failure -- malformed JSON, wrong shape, a fabricated phase, a note with no digit in it, or the call erroring outright -- falls back to the rule-based templated notes (`pipeline/coaching.py::fallback_coaching_notes()`, task 61), never a raw error surfaced to the user and never a half-validated LLM note shown as if it were trustworthy.

## Not yet wired to a real LLM call
`generate_coaching_notes()` takes an injectable `llm_client` callable (`deltas -> raw response string`) rather than hardcoding a specific SDK call, so the validation logic is testable independent of any actual API access. This cloud session has no project-specific LLM API key configured for QB Motion Atlas (this repo's own Anthropic/OpenAI credentials, as opposed to the harness's own model access, which isn't something this codebase should borrow) to wire in a live call and confirm end-to-end -- that's a follow-up once a key is provisioned for the project itself, not a gap in the validation/fallback logic, which is fully covered by tests against a fake client.
