# Product Spec — QB Motion Atlas ("NFL QB DNA")

## Product Requirements (what must be true at each stage)

**Must be true at V1 (functional MVP):**
- User can upload a video and receive a results page within a reasonable processing time (target: under 30 seconds).
- System rejects or clearly flags videos that fail quality checks (bad angle, no full body, no detected throw) instead of silently producing a result.
- Results page shows an overall QB match with a similarity percentage and at least one specific, data-derived coaching note (not a generic template with no numbers behind it).
- Reference database (8–10 QBs minimum) has documented provenance for every clip used.

**Must be true at V2 (strong portfolio project):**
- Similarity engine includes a trained embedding component, not only hand-engineered feature distance.
- Per-phase breakdown is available, not just an overall score.
- Live webcam capture works end-to-end, not upload-only.
- A written evaluation report exists with real numbers (retrieval accuracy, self-consistency).
- Shareable results card can be exported as an image.

**Must be true at V3:**
- Camera-angle robustness has been measurably improved via 3D lifting or an equivalent technique, with before/after numbers.
- At least one of the research experiments (Section 6 of the technical breakdown) has been run and documented with results, including honest negative/mediocre findings if applicable.

## User Stories

1. **As a user**, I want to upload or record a throwing video **so that** I can see which NFL QB my mechanics most resemble.
   - *Acceptance criteria:* Upload/record UI accepts video ≤15 seconds; system provides visible processing status; result appears without requiring a page reload.

2. **As a user**, I want the system to tell me if my video isn't usable **so that** I don't get a misleading or garbage result.
   - *Acceptance criteria:* Videos with insufficient body visibility, wrong camera angle, or no detected throw are explicitly flagged with a specific, actionable message (e.g., "move your camera to your throwing side") rather than silently scored.

3. **As a user**, I want to see which specific part of my throw resembles which QB **so that** the feedback feels precise rather than a single vague label.
   - *Acceptance criteria:* Results page shows separate similarity scores for at least stride, arm-cock/acceleration, release, and follow-through phases, each with its own top match.

4. **As a user**, I want a concrete coaching suggestion tied to an actual measurement from my throw **so that** the feedback is useful, not just entertainment.
   - *Acceptance criteria:* At least one coaching note per result references a specific measured value or delta (e.g., timing gap, angle difference) rather than a generic sentence with no numbers behind it.

5. **As a user**, I want to export or share my result **so that** I can show it to friends.
   - *Acceptance criteria:* A single-click export produces a shareable image containing the match, percentage, and key stats.

6. **As a returning user**, I want to know how confident the system is in my result **so that** I know whether to trust it or re-record.
   - *Acceptance criteria:* Every result displays an explicit confidence level (high/medium/low) derived from actual pipeline signal quality (pose extraction completeness, angle validity), not a hardcoded value.

## Edge Cases to Handle

- Video with no throw detected at all (empty upload, wrong content).
- Multiple people in frame — system must identify the primary thrower or reject ambiguous input.
- Partial occlusion of the throwing arm during the critical release window.
- Left-handed throwers — normalization must handle mirrored mechanics, not silently misclassify them against a right-handed-only reference set.
- Extremely short or extremely long videos outside the expected duration range.
- Low-light or low-resolution video degrading pose extraction quality — must lower confidence rather than fail silently.
- A throw that genuinely doesn't resemble any reference QB well — system should surface a "no strong match" result with the closest available options and low confidence, not force a misleadingly high percentage.

## Feature Priority

| Priority | Feature | Notes |
|---|---|---|
| P0 (V1-blocking) | Video upload + pose extraction pipeline | Nothing works without this |
| P0 | Camera-angle/quality validation with explicit rejection | Prevents garbage-in-garbage-out from undermining the whole system's credibility |
| P0 | Overall similarity match + basic coaching note | Minimum viable output |
| P0 | Reference database with documented provenance (8–10 QBs) | Foundation for everything downstream |
| P1 (V2-blocking) | Per-phase breakdown | The core differentiator vs. shallow single-score tools |
| P1 | Learned embedding model (metric learning) | The core ML depth signal |
| P1 | Live webcam capture | Major demo/UX upgrade |
| P1 | Evaluation report with real metrics | The single biggest portfolio-credibility item |
| P2 (V3 / stretch) | Shareable card export | Nice-to-have, not core to the technical narrative |
| P2 | 3D pose lifting for angle invariance | High-effort, high-research-value, not required for a strong V2 |
| P2 | Cross-sport contrastive pretraining experiment | Highest research ceiling, most optional given time constraints |
| P2 | Multi-position generalization (WR/DB) | Only pursue once the QB pipeline is fully validated |
