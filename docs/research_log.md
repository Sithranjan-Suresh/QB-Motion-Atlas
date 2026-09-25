# Research Log

Running log of findings, decisions, and dead ends across the build. Newest entries at the bottom.

---

## 2026-09-24 — Project kickoff / V0 scope

**Goal:** QB Motion Atlas — decompose a throwing motion into phases (load, stride, arm cock, acceleration, release, follow-through), extract per-phase biomechanical features, and compute similarity against a curated NFL QB reference database, using both interpretable hand-engineered features and (later) a learned embedding.

**V0 exit criteria (proof of concept):** On a small seed set of 3 QBs' publicly available coaching-breakdown clips —
1. MediaPipe pose extraction produces usable landmark tracking.
2. A heuristic (velocity/angle-threshold) phase segmenter produces boundaries reasonably close to hand-labeled ground truth.
3. A hand-engineered weighted-distance similarity score puts same-QB throws closer together than cross-QB throws.

If all three hold on the seed set, the core technical bet has legs and V1 (full 8–10 QB dataset, validation, DB, API, frontend, deployment) is worth building. If not, the phase taxonomy, feature set, or pose-extraction approach needs rework before scaling up.

**Environment:** Python 3.11.9, dependencies pinned in `requirements.txt` (mediapipe 1.0.1, opencv-python 5.0.0.93, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, matplotlib 3.11.2), installed cleanly into `.venv` with no conflicts.

---

## 2026-09-24 — Seed clip sourcing (tasks 7-9)

**Sourced:** 2 clips each for Josh Allen, Patrick Mahomes, Lamar Jackson (6 total), trimmed to single-throw windows. Full provenance in `data/provenance.csv`.

**Finding — browser playback time ≠ downloaded file time for long videos:** While scouting clean throw segments by scrubbing YouTube in-browser, timestamps noted from the live player did not reliably match the same timestamp in the yt-dlp-downloaded file for long-form videos (mid-roll ads shift the player's reported `currentTime` relative to the ad-free downloaded stream). This cost significant rework on the Mahomes and Lamar combine-video clips — segments that looked clean live were at a different offset once downloaded. Fix: after downloading, re-locate the usable window by extracting frames directly from the downloaded file (`ffmpeg -vf fps=1`) and visually confirming, rather than trusting browser-noted timestamps. This did not affect the YouTube Shorts sources (Allen clip1/2, Mahomes clip1) — Shorts don't appear to carry the same ad-insertion behavior.

**Finding — available Lamar Jackson footage skews toward wide/broadcast camera angles:** Unlike Allen and Mahomes, who both have clean near-side-view Shorts from a dedicated QB-mechanics coaching channel (@qbperformancelab), no equivalent clean short-form clip was found for Lamar Jackson within reasonable search effort — the shorts available were either broadcast game footage (cluttered, wide), fan phone-camera footage (obstructed), or had heavy graphic-overlay text covering the frame. Usable Lamar footage came from mining official NFL/Ravens combine broadcast videos for the brief moments their camera cuts to a close near-side shot; one of the two resulting clips (`clip2_nfl_everythrow`) only captures load+stride, not the full throw, because the broadcast cuts away before release. This is a real, worth-tracking asymmetry in data availability across QBs — flagged for revisiting during the V1 dataset expansion (task 29).

---

## 2026-09-24 — Pose extraction on seed set (tasks 11-12)

Implemented `pipeline/pose_extraction.py` using MediaPipe's newer Tasks API (`mediapipe.tasks.python.vision.PoseLandmarker`, VIDEO running mode) — the installed mediapipe version (1.0.1) no longer ships the older `mp.solutions.pose` API that most existing tutorials reference. Model: `pose_landmarker_lite.task` (downloaded from Google's MediaPipe model bundle storage, kept out of git via `.gitignore`, ~5.6MB).

Ran `pipeline/run_pose_extraction.py` over all 6 trimmed seed clips. Per-frame detection rate:

| Clip | Frames | Detected | Rate |
|---|---|---|---|
| josh_allen / clip1_sideline_slowmo | 318 | 316 | 99.4% |
| josh_allen / clip2_combine_slowmo | 462 | 462 | 100% |
| patrick_mahomes / clip1_qbperformancelab_62mph | 396 | 396 | 100% |
| patrick_mahomes / clip2_nfl_2017combine | 120 | 120 | 100% |
| lamar_jackson / clip1_ravens_combine | 75 | 65 | 86.7% |
| lamar_jackson / clip2_nfl_everythrow | 135 | 135 | 100% |

Only `lamar_jackson/clip1_ravens_combine` shows a meaningfully lower detection rate (86.7%) — consistent with it being the shortest, most action-heavy segment (the camera is mid-pan as it captures this throw, per the sourcing note above). Not disqualifying for V0, but worth a closer look (task 14) at which specific frames failed.

---

## 2026-09-24 — Overlay inspection (task 14)

Generated skeleton-overlay debug videos for all 6 seed clips (`pipeline/debug_overlay.py`) and reviewed frames from each. Overlay tracking looked correct and stable across all clips — skeleton follows the correct person even when a second player is in frame (e.g. Josh Allen clip1, where a teammate walks through the background).

Investigated the 10 missing-pose frames in `lamar_jackson/clip1_ravens_combine` (frame indices 60-67, 73-74 of 75): these are not a tracking failure at all — they're the tail end of the clip where the broadcast camera pans up and away from the field to the jumbotron, so there is no person in frame for MediaPipe to detect. Retrimmed the clip to 23.3-25.15s (was 23.3-25.8s) to end right before the pan starts, and re-ran pose extraction: **56/56 frames (100%) detected.** `data/provenance.csv` updated accordingly. All 6 seed clips now have 100% frame-level pose detection.

---

## 2026-09-24 — Landmark confidence filter (task 15)

Implemented `pipeline/landmark_filter.py::filter_low_confidence_landmarks()`: per-joint (not per-frame) interpolation across short low-visibility runs (default threshold 0.5, max gap 5 frames), bounded on both sides by a real detection so it never extrapolates off a clip edge. Runs that are too long, or missing a good frame on either side, are left untouched rather than fabricated.

Ran it across all 6 seed clips: the two fully-missing frames in `josh_allen/clip1_sideline_slowmo` (indices 195, 308) were both fully interpolated (76 joint-entries total, including a handful of other individually low-visibility joints elsewhere in the same clip); the remaining 5 clips needed 0-3 joint-entry interpolations each. No clip had a gap long enough or at a boundary such that it couldn't be filled — expected, given all 6 clips already sit at 100% frame-level pose detection.

---

## 2026-09-24 — Gold-label prep: two more sourcing problems found by frame-by-frame review (task 19)

Before hand-labeling phase boundaries, reviewed every clip via ffmpeg contact-sheet montages (tiled grids of overlay frames) rather than spot-checking a few frames — this caught two problems the earlier single-frame spot-checks missed entirely:

**`josh_allen/clip1_sideline_slowmo` is not a standard throw.** Full frame-by-frame review shows an exaggerated, theatrical full-arm-circle showman windup (consistent with content made for a slow-mo highlight reel, not game/practice mechanics), and the back half of the 10.6s clip cuts to unrelated sideline moments (a teammate interaction, talking to a reporter) that have nothing to do with the throw. This clip passed every criterion in `data_criteria.md` when checked by eye in the browser at normal speed — the issue only became visible scrubbing frame-by-frame. **Decision: excluded from phase-segmentation gold-labeling, feature extraction, and the V0 similarity check.** Kept in `data/raw/` and documented in `provenance.csv` as a worked example of a disqualifying case for future sourcing (task 29). Net effect: Josh Allen now has only 1 usable clip for V0, same constraint already flagged for Lamar Jackson.

**`josh_allen/clip2_combine_slowmo` and `patrick_mahomes/clip1_qbperformancelab_62mph` needed the same frame-by-frame check to tell loop from slow-motion.** Both are YouTube Shorts with a long apparent "stillness" early in the clip. Contact-sheet review confirmed:
- `josh_allen/clip2_combine_slowmo` (originally 15.4s) **does loop** the same throw twice back-to-back. Retrimmed to 0:00-6.3s to isolate the first cycle; re-ran pose extraction (189/189 frames, 100%) and phase segmentation.
- `patrick_mahomes/clip1_qbperformancelab_62mph` (13.2s) does **not** loop — the apparent stillness is a real high-frame-rate slow-motion capture of the load phase (a fraction of a real-time second stretched across several playback seconds), and the motion runs continuously through release and follow-through. No change needed.

**Takeaway for V1 dataset expansion (task 29):** don't trust a single frame or even a handful of spot-checked screenshots to validate "single continuous throw, no cuts" — build a full contact-sheet montage (`ffmpeg -vf "fps=N,tile=RxC"`) and scan the whole clip before accepting it into the dataset. This is now the standard verification step, not an optional extra.

Corrected `provenance.csv` for all three affected clips.

---

## 2026-09-25 — Cloud session handoff: environment reconstruction, YouTube network block (task 19 blocked)

Work continued in a fresh cloud container (no local state carried over — raw video, pose JSON, phase boundaries, and the MediaPipe model are all gitignored by design, per `.gitignore`). Reconstructed the environment from scratch:

- `ffmpeg` installed via `apt-get` (not preinstalled in this container).
- Python 3.11 venv created; `requirements.txt` installed cleanly (mediapipe 1.0.1, opencv-python 5.0.0.93, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, matplotlib 3.11.2) plus `yt-dlp` — added `yt-dlp` to `requirements.txt` since it's a real pipeline dependency (clip sourcing) that was missing from it.
- `models/pose_landmarker_lite.task` re-downloaded from Google's MediaPipe model storage (`storage.googleapis.com`) — succeeded, ~5.6MB, matches the file used previously.

**Blocker: this cloud environment's network policy denies `youtube.com`.** `yt-dlp` and a raw `curl` to `https://www.youtube.com` both fail with a `403 Forbidden` at the proxy layer (not a YouTube-side error — the tunnel/CONNECT itself is rejected). `pypi.org` and `storage.googleapis.com` are reachable, so this is a host-allowlist policy, not a general outage. Net effect: the 6 seed clips in `data/provenance.csv` cannot be re-downloaded from this session, so anything requiring the actual video frames is blocked here:

- **Task 19** (hand-label gold phase boundaries) — needs the real footage to label against; cannot be done on synthetic data without defeating the point of "ground truth."
- **Task 20** (heuristic-vs-gold frame-offset error) — depends on task 19's output.
- **Task 23** (run feature extraction on the seed clips) — needs real pose landmarks, not just the code.
- **Tasks 26–27** (pairwise similarity sanity check + V0 exit-criterion writeup) — need real per-clip features to compare.

**What this session did instead, to keep making real forward progress rather than stalling:** implemented the remaining V0 code that doesn't require the actual seed footage to write or unit-test — `docs/feature_definitions.md` (task 21), `pipeline/features.py` (task 22) with body-scale normalization (task 24), and `pipeline/similarity.py` (task 25) — validated against synthetic landmark sequences (hand-constructed, not real throws) the same way a unit test would, clearly distinct from the real gold-labeling/validation work in tasks 19/20/23/26/27, which remain genuinely blocked and unstarted pending either (a) broader network access for this environment (YouTube added to the allowed domains, or a "full internet access" policy, changeable in the environment's settings), or (b) the clips being made available to the session another way (e.g. committed as small proxy/derivative artifacts, or a future session run where the container does have YouTube access).

**Fix needed to unblock 19/20/23/26/27:** widen this environment's network access to include `youtube.com` (and likely `googlevideo.com`, which serves the actual video stream) via the cloud environment's settings, then re-run this same reconstruction (ffmpeg/yt-dlp already scripted above, informally) to pull the 6 clips back down using the exact `source_url` + `timestamp_range` already recorded in `provenance.csv`.

**Additional reconstruction step found while building the API (task 70):** `extract_pose()`'s first real invocation this session (previously only exercised indirectly via unit tests on synthetic landmarks, never MediaPipe itself) failed with `OSError: libEGL.so.1: cannot open shared object file` -- this container's base image doesn't ship the Mesa EGL/GLES libraries MediaPipe's native pose-landmarker library dynamically links against. Fixed with `sudo apt-get install -y libegl1 libgl1 libgles2`. Add this to the reconstruction checklist alongside ffmpeg/the venv/the model download for any future fresh container.

---

## 2026-09-25 — Manual edge-case testing against the running stack (task 89)

Went through `product_spec.md`'s edge-case list (no throw, multi-person, occluded arm, left-handed, too-short/long, low-light) against the actual running API (`uvicorn api.main:app`) and, where relevant, the actual running frontend (`next dev`) in a real Chromium browser via Playwright -- not just the pipeline-level unit tests those modules already have. Real human footage still isn't available in this session (YouTube blocker above), so "against the running stack" here means: real HTTP requests, a real Postgres row round-trip, and a real rendered page, with the pose-extraction boundary substituted by synthetic/mocked landmarks where an actual person needs to be in frame -- consistent with this session's approach throughout.

| Edge case | Expected | Actual | How verified |
|---|---|---|---|
| No throw / no person | Rejected with a specific reason, not silently scored | `no_pose_detected` rejection, surfaced correctly on `/processing/[id]` in a real browser | Full stack: real synthetic no-person video → real `POST /uploads` → real background pipeline → real DB row → real rendered rejection UI (task 77, task 81) |
| Too long | Rejected before processing starts | `400`, `"video is 20.0s, longer than the 15.5s limit"` | Real `POST /uploads` call with a real 20s synthetic video (task 76) |
| Too short | Rejected before processing starts | **Gap found: no minimum existed at all.** Fixed by adding `MIN_DURATION_SEC = 2.0` to `api/main.py` (a conservative technical floor below which no real load-through-follow-through motion could fit, distinct from `full_context.md`'s 5s *recommended* floor, which is sourcing guidance, not a hard cutoff) | Real `POST /uploads` call with a real 0.5s synthetic video, confirmed `400`/`"shorter than"` after the fix; added `test_upload_request_validation_rejects_too_short_video` to `tests/test_api.py` |
| Occluded throwing arm | Doesn't crash; confidence degrades rather than reporting false certainty | Pipeline completed (`validation_status: passed`), `confidence_level: medium` (vs. `high` for the same clip unoccluded) | Real `POST /uploads` → real background pipeline, with `extract_pose` mocked to synthetic landmarks whose right-wrist visibility drops to 0.1 across the release/follow-through window; real DB round-trip |
| Left-handed | Detected and mirrored transparently; pipeline still completes | Pipeline completed (`validation_status: passed`) on a fully mirrored synthetic left-handed clip -- `canonicalize_handedness()` correctly normalized it before segmentation/features ran | Real `POST /uploads` → real background pipeline, with `extract_pose` mocked to `mirror_landmarks()`-transformed synthetic landmarks; real DB round-trip |
| Multiple people in frame | Primary thrower selected if clear, rejected if ambiguous | **Not verifiable against the running stack in this session.** `_select_primary_pose()`'s bounding-box selection logic runs *inside* `extract_pose()`, before the mock boundary used above -- exercising it for real needs an actual multi-person video frame for MediaPipe to detect two real people in, which requires real footage. Already covered at the unit level (`tests/test_pose_extraction.py`: clear-primary selection, ambiguous-pair rejection, empty-detections), just not through a live HTTP round-trip | N/A -- documented gap |
| Low light | Pose extraction degrades gracefully (lower detection rate) rather than failing opaquely | **Not verifiable at all in this session**, unit-level or otherwise -- this is specifically about MediaPipe's real-world robustness to sensor noise/poor lighting, which synthetic frames can't approximate; there's no code path to unit-test around, only real footage to evaluate against | N/A -- documented gap, revisit once real footage is available |

**Bug found and fixed:** the missing minimum-duration check above -- a genuine gap this review exists to catch, not a hypothetical one.

**Two edge cases remain genuinely untested** (multi-person's bbox-selection logic through a live request, and low-light entirely) pending the same real-footage blocker as tasks 19/20/23/26-29/48/52-53. Both have a clear, cheap path to real verification once that's unblocked: upload an actual multi-person clip and an actual dim/low-light clip through the running stack and confirm the already-implemented logic behaves as expected.

---

## 2026-09-25 — Deployment (tasks 90-95): blocked on user accounts, not code

Unlike every other blocker logged in this session, this one isn't an environment setting or missing data -- it's that provisioning a managed Postgres (Supabase/Neon), deploying the backend (Render), and deploying the frontend (Vercel) all require creating and authenticating into third-party accounts on the user's behalf, with real billing/identity implications even on free tiers. This session does not have, and should not create, those accounts autonomously.

Everything that *can* be prepared without those accounts has been: `docs/deployment.md` documents exact, mechanical steps for each of tasks 90-95, referencing already-verified pieces (migrations apply cleanly to a fresh Postgres per task 65, `db/seed.py` is idempotent per task 66-67, both the API and frontend already read their config -- `DATABASE_URL`/`CORS_ALLOWED_ORIGINS`, `NEXT_PUBLIC_API_BASE_URL` -- from the environment rather than hardcoding local-only values). Once the user provisions the actual accounts, deployment should be a short mechanical process rather than a fresh investigation. Proceeding to tasks 96-97 (documentation), which don't require external accounts.

---

## 2026-09-25 — V1 status: implementation complete, deployment pending (task 97)

Every V1 task in `implementation_checklist.md` that doesn't require either (a) real reference-clip footage or (b) a third-party cloud account is done, real, and verified -- not stubbed. Summary by section:

- **Data Expansion (29-34):** blocked -- needs the real YouTube footage this environment can't reach.
- **Upload Validation (35-38):** done. Computable camera-angle/full-body/single-throw checks, `validate_upload()`, 6 unit tests, centralized rejection copy shared (in spirit) between the API and frontend.
- **Pose Extraction Hardening (39-42):** done. Jitter smoothing, multi-person primary-thrower selection, left-handed detection/mirroring, 11 unit tests.
- **Phase Segmentation Hardening (43-45):** 43 blocked (needs a larger real gold-labeled set); 44-45 done -- per-boundary confidence from inflection sharpness, degraded by joint occlusion.
- **Feature Engineering + Normalization (46-49):** 46-47, 49 done -- full per-phase feature set with timing normalization, a data-quality outlier report. 48 blocked (needs the real reference dataset to populate).
- **Similarity Engine — DTW (50-53):** 50-51 done -- DTW alignment layer combined with the V0 feature-distance layer. 52-53 blocked (need real reference data for a real retrieval-accuracy check).
- **Confidence Scoring (54-56):** done, with unit tests confirming actual degradation under simulated bad input.
- **Coaching Notes (57-62):** done -- structured delta schema, fixed LLM prompt/schema, schema-validating generator with a rule-based fallback (no LLM key configured in this environment, so the fallback is what's actually live), 13 unit tests.
- **Database (63-67):** done against a real local Postgres -- models, migrations (verified both directions), an idempotent seed script that loaded the real 6-clip reference set for real.
- **Backend API (68-77):** done. Every endpoint verified against the real API + real database, including two genuine bugs found and fixed along the way (a missing system library blocking MediaPipe entirely, an orchestrator ordering bug). 8 real integration tests plus the rest of the pipeline's unit tests.
- **Frontend (78-86):** done. Every page verified in a real Chromium browser via Playwright, not just built/linted -- including two more real bugs found this way (missing CORS headers, a mobile-viewport overflow).
- **Testing (87-89):** done. Full pipeline pytest coverage, an end-to-end local smoke test, and a manual edge-case sweep against the running stack that caught a real missing-minimum-duration bug.
- **Deployment (90-95):** blocked on the user's own cloud accounts, not on code -- `docs/deployment.md` has the exact steps ready.
- **Documentation (96-97):** this entry, plus `README.md`.

### Known limitations, stated plainly
1. **No real reference feature data.** The 6 seed clips' provenance is real and seeded; their actual pose/feature data isn't, because this environment can't reach YouTube to re-download them. A fresh upload today has nothing real to match against.
2. **Not deployed.** Everything runs locally (verified extensively); nothing is live on the internet yet.
3. **No LLM-generated coaching notes.** `generate_coaching_notes()` is fully built and schema-validated, but with no project LLM API key configured, every note in practice comes from the rule-based fallback, not an actual LLM call.
4. **Live API matching uses only the V0 feature-distance layer**, not the V1 DTW layer -- `qb_reference_features` stores per-phase feature vectors, not each clip's raw per-frame trajectory DTW needs. Both layers exist and are tested independently; wiring DTW into the live match path is future work.
5. **Two edge cases (multi-person, low-light) are untested against real footage** for the same reason as (1) -- see the 2026-09-25 edge-case entry above.
6. **All weights and thresholds are documented placeholders** (`similarity.py`, `similarity_dtw.py`, `confidence.py`, `validation.py`) -- none have been empirically tuned, because tuning needs the real reference/retrieval data that's blocked.

None of these are hidden or glossed over -- each is logged at the point it was found, with why it's blocked and what unblocks it. The V0 core technical bet (phase segmentation + interpretable features + similarity, per the 2026-09-24 kickoff entry's exit criteria) still hasn't actually been validated against real throws, because that validation needs the same real footage every other blocker above needs. Everything built on top of it is real, tested engineering -- it just hasn't yet been proven against the real world it's meant to work in.

---

## 2026-09-25 — Tasks 116-118: per-phase breakdown end-to-end

Wired V2's "Per-Phase Breakdown" feature (`full_context.md`: "your stride phase resembles Herbert, your release resembles Stafford") all the way through, on top of the per-phase grouping/comparison helpers already built (`pipeline/per_phase_similarity.py`, `pipeline/feature_scale.py`):

- **`pipeline/orchestrator.py`**: added `_compute_phase_results()`, called from `run_pipeline_for_upload()` right after the existing V0/V1 overall-match logic. For each phase the current upload has features for, it finds the best-matching `QBReferenceFeature` row scoped to that `phase_name`, using the same top1-vs-top2 similarity-margin confidence bucketing as the clip-level confidence formula. A phase with no reference data yet is simply omitted from the result dict -- same honest-gap convention as `matched_qb_name` being nullable overall -- rather than fabricating a match.
- **`db/models.py` / migration `6c48217bf46f`**: added `AnalysisResult.phase_results` (JSON), verified against the real local Postgres in both directions. Autogenerate incorrectly proposed dropping the pgvector HNSW index in this same diff (a false positive from task 114's index being raw-SQL rather than an `sa.Index` on the model) -- removed manually, documented in the migration's own docstring.
- **`api/schemas.py` / `api/main.py`**: `AnalysisResultResponse` now includes `phase_results: dict[str, PhaseResultResponse]`; `/results/{upload_id}` returns it.
- **Frontend**: `PhaseBreakdownPanel.tsx` (new), rendering one row per phase present in `phase_results` in canonical throw order (load → stride → arm_cock → acceleration → release → follow_through), reusing the same confidence-badge styling as `OverallMatchCard`. Wired into `/results/[uploadId]` below the overall match card and above coaching notes.

**Validation, real infrastructure throughout:**
- `tests/test_per_phase_similarity.py` (6 tests) already covered the grouping/scoring math in isolation.
- Extended `tests/test_api.py`'s real-Postgres `test_good_video_flow_produces_a_match` to also seed a `release`-phase `QBReferenceFeature` row and assert the live `/results/{id}` response's `phase_results.release` is correct end-to-end (real HTTP request, real background pipeline run, real DB round-trip) -- not just a unit test of the helper in isolation.
- Full suite: 122/122 passing.
- Frontend: `tsc --noEmit` and `eslint` clean; then a **real Chromium browser check via Playwright** against the actual running `uvicorn` + `next dev` stack (seeded a real `AnalysisResult` row with three phases across all three confidence tiers directly in Postgres, navigated to `/results/{id}`, confirmed the panel renders in the correct phase order with no console errors and CORS working) -- screenshot reviewed, test row cleaned up afterward.

No real reference data exists yet for phases beyond what a future real dataset would provide (same blocker as everywhere else in this log), so today the per-phase panel will show "no per-phase reference data available yet" for a fresh upload against the real (empty-of-phase-rows) seeded dataset -- the code path itself is fully built, tested, and proven correct against synthetic/seeded data, consistent with this project's standing practice of not faking results just to make a feature look complete.

---

## 2026-09-25 — Agent 1 (parallel QB video research) completed

Per the user's request to split into two parallel workstreams, a background agent ("Agent 1: QB Video Research & Collection," research-only, no downloading) was spawned to identify all 32 current NFL starting quarterbacks and source 5-10 candidate YouTube clip links each, useful for future reference-dataset expansion (task 29). It completed and produced `qb_research_agent1_output.md` in an isolated git worktree, while this session ("Agent 2") continued the checklist (tasks 116-118 above) in parallel.

**Reviewed and pulled into `docs/qb_candidate_clips.md`.** Content quality: appropriately honest and well-calibrated -- confidence-tiered (high/medium/low) by source-type signal only (dedicated mechanics-breakdown channel vs. combine/pro-day long-form vs. game-highlight compilation), explicitly flags which clips still need timestamp isolation vs. are already short, explicitly names weak-source-pool QBs for follow-up (Malik Willis, Geno Smith, Kirk Cousins, Bo Nix, Jared Goff, Tyler Shough, Jacoby Brissett -- the last with only 2 candidates, honestly reported rather than padded to a quota), and explicitly flags starter ambiguity for 5 teams (injury/competition situations at research time: Commanders/Mariota-Daniels, Falcons/Penix-Tagovailoa, Browns/Watson-Sanders, Raiders/Cousins-Mendoza, Chiefs/Mahomes' ACL recovery). Critically, it opens with the same lesson this project's own `research_log.md` already learned the hard way (2026-09-24 "gold-label prep" entry) -- that a title/channel/duration screen alone has repeatedly missed real disqualifiers (showman non-throws, looped Shorts, slow-motion mistaken for a stall) -- and states plainly that nothing was watched frame-by-frame, so none of this is gold yet.

**Independent verification not possible from this session:** attempted to spot-check 3 of the listed video IDs via `WebFetch` to confirm they resolve to real, non-removed videos, but this session's network egress currently blocks `www.youtube.com` entirely (`EGRESS_BLOCKED`) -- a recurrence of the same class of blocker logged on 2026-09-25 above, though this container's specific policy state may differ from that session's post-fix state. Could not confirm link validity beyond trusting the search tool's own results as reported. This is disclosed rather than glossed over: the document's own confidence tiers and "nothing has been watched" framing already account for this, and the next real step (per the document's own closing reminders) is unchanged -- frame-by-frame contact-sheet review after an actual download, whenever YouTube access is next available from a session.
