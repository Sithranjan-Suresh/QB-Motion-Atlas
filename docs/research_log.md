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

---

## 2026-09-25 — Automating candidate-clip download: still IP-reputation-blocked, cookies.txt path chosen

Re-confirmed live (not just from memory of the earlier session) that `yt-dlp` from this container still hits the same wall: `HTTP Error 429` followed by `"Sign in to confirm you're not a bot"` on a real candidate URL. This is YouTube's bot-detection acting on request/IP reputation, not a fixable flag or retry-logic problem -- the earlier session's workaround attempts (`--js-runtimes node`, `player_client=android`, delayed retries) already ruled those out, and this session's fresh attempt reproduced the identical failure.

Discussed automation options with the user for scaling from 6 seed clips to the 32-QB candidate list (`docs/qb_candidate_clips.md`): running the download locally (residential IP), sending a `cookies.txt` from a real logged-in YouTube session, or a paid residential-proxy service. **User chose to send a `cookies.txt`.**

Built `pipeline/run_candidate_download.py` ahead of the file arriving, so the batch job is ready to run the moment it does:
- Parses `docs/qb_candidate_clips.md`'s per-QB tables into structured candidates (regex-based; 6 unit tests in `tests/test_candidate_download.py`, including a live sanity check against the real document).
- **Prioritizes quality over volume by default** -- selects only `High`/`Medium-high` confidence, `short` clip-type (no timestamp isolation needed) candidates, capped at 2 per QB (43 candidates by default, out of 186 total rows), consistent with this session's standing view that a bad/unverified clip actively hurts triplet-loss training more than a missing one helps it. All three filters are CLI flags, so a broader pass is one command away if 2/QB proves too thin after review.
- Downloads via `yt-dlp --cookies <file>`, writes into `data/candidates_staging/<qb_name>/`, generates an `ffmpeg` tiled-frame contact-sheet montage per clip (the same technique that caught the showman-windup and looped-Short problems on 2026-09-24) for fast eyeball QC, and logs every attempt (success or failure, with the error) to a resumable manifest CSV.
- **Deliberately does not touch `data/raw/` or `data/provenance.csv`** -- per `docs/data_criteria.md`, clip acceptance is "applied by eye," and this project has already been burned twice by trusting title/thumbnail screening over full frame-by-frame review. This script gets candidates into a reviewable staging area; the accept/reject/trim call and the provenance entry stay a separate, deliberate step.

Not yet run for real (waiting on the user's `cookies.txt`) -- `--dry-run` confirmed the parsing/selection logic against the real document (43/186 candidates selected, spanning most of the 32 QBs; the QBs already flagged as weak source pools in `qb_candidate_clips.md` -- Malik Willis, Geno Smith, Kirk Cousins, Bo Nix, Tyler Shough, Jacoby Brissett -- correctly drop out of this High/Medium-high-only selection entirely, which is expected and matches that document's own findings).

---

## 2026-09-25 — Candidate-clip cookies handling: two accounts rejected before a real one arrived

Before running the batch download, two `cookies.txt` files the user sent were checked byte-for-byte against each other and against a later one: the first and second were **the same Google account session** (identical `SID`/`SAPISID`/`APISID`/`HSID`/`SSID`/`__Secure-1PSID`/`__Secure-3PSID` values), despite being described as a secondary account -- flagged to the user rather than used, and both files were deleted from disk immediately (`shred -u`, falling back to `rm -f`) without ever being referenced in a download or committed anywhere. A third file's core session cookies were confirmed to differ entirely from the first two, and only that one was used. General principle applied here for any future credential file a user sends this session: verify identity claims against the file's actual contents before use, never assume a re-export is a different account just because it was resent, and delete anything not used or no longer needed rather than letting it accumulate on disk.

## 2026-09-25 — Batch candidate-clip download: real run, two real bugs found and fixed

Ran `pipeline/run_candidate_download.py` for real against the verified cookies file. Two genuine technical blockers surfaced and were fixed on the spot, both confirmed via a real download rather than guessed at:

1. **YouTube's JS signature/n-parameter challenge.** Getting past the cookie-based bot check (see above) wasn't sufficient by itself -- yt-dlp then needed a JS runtime (`--js-runtimes node`, Node 22 is present in this container) plus its own remote EJS challenge-solver component (`--remote-components ejs:github`) to decode current-format YouTube URLs. That component download itself failed TLS verification, because yt-dlp's bundled `certifi` store doesn't trust this container's local egress-proxy CA (`/root/.ccr/README.md`) -- fixed by appending the proxy CA into that certifi bundle in place (verification stays on; this just adds the trusted issuer, not a bypass) via `setup_environment()`. Confirmed with a real single-clip download before running the batch.
2. **Contact-sheet generation was silently broken for all 42 downloaded clips.** The original `ffmpeg -vf select='not(mod(n,ceil(n_frames/N)))'` expression referenced `n_frames` as if it were a filter-exposed constant -- it isn't (ffmpeg's `select` filter only exposes per-frame values like `n`, not a total frame count), so every invocation failed to parse and `generate_contact_sheet()` returned `False` silently, with no manifest error logged for it (a real gap -- the manifest only tracks download success/failure, not this step). Fixed by switching to `ffprobe`-based duration lookup + an `fps=(cols*rows)/duration,tile=RxC` filter (the same technique already used ad hoc earlier this session, just made robust and reusable), verified against a real downloaded clip, then re-run over all already-downloaded clips to backfill the missing contact sheets.

**Result: 42/43 candidates downloaded successfully** (one `jalen_hurts` Short 403'd -- a single-clip failure, not a systemic block, most likely a since-privated/region-locked video rather than the earlier bot-detection issue, since 42 other requests on the same session succeeded around it), covering 25 of the 32 QBs, ~760MB staged under `data/candidates_staging/` (gitignored -- unreviewed copyrighted source video, same treatment as `data/raw/`). All 42 now have a contact-sheet montage for fast eyeball QC. **Nothing here has been reviewed for `data_criteria.md` compliance yet** -- frame-by-frame review, trimming, and promotion into `data/raw/` + `provenance.csv` remains a separate, deliberate next step, same as always.

---

## 2026-09-25 — Tasks 119-122: live webcam capture

Built while the candidate-clip download ran in the background. Extended `UploadRecorder` (task 79) with a mode toggle between the existing file-upload flow and a new `MediaRecorder`-based webcam path: live preview with a framing-guide overlay (dashed side-on silhouette + instructional text) while positioning, a 15-second-capped recording with a visible countdown, then a retake/use-this-recording preview step before the recorded blob is wrapped into a `File` and sent through the exact same `createUpload()` call a picked file uses.

**Real bug found and fixed via real browser testing, not assumed away:** `MediaRecorder`'s actual blob MIME type includes a codecs parameter (`video/webm;codecs=vp9`), which `api/main.py`'s content-type check compared with exact-match against `ALLOWED_CONTENT_TYPES` -- every real webcam recording was rejected with `400 unsupported file type` until this was caught. Fixed by comparing only the base MIME type (splitting off everything after `;`). Never would have surfaced from a unit test alone; only showed up sending an actual recorded blob through an actual browser fetch.

**Also verified, not assumed:** whether `video/webm` needs server-side transcoding before pose extraction can run on it (the checklist's own "format conversion if needed" phrasing). It doesn't -- OpenCV's `cv2.VideoCapture` (used by both `api/main.py`'s duration probe and `pipeline/pose_extraction.py`) opens a real `ffmpeg`-generated webm file and reads frames from it with no special handling, confirmed directly before touching any code. `ALLOWED_CONTENT_TYPES` just needed `video/webm` added.

**Testing (task 122), real infrastructure throughout:**
- `tsc --noEmit` and `eslint` clean on the changed frontend files.
- Backend: `tests/test_api.py::test_webcam_recorded_webm_flow_produces_a_match`, a full real-Postgres integration test using an actual `ffmpeg`-generated webm file and the exact `video/webm;codecs=vp9` content-type string a real browser sends (added specifically to cover the bug above as a regression, not just to reach the fix).
- **Real Chromium browser via Playwright**, using `--use-fake-device-for-media-stream`/`--use-fake-ui-for-media-stream` so `getUserMedia`/`MediaRecorder` run against a real (synthetic) camera feed with no actual webcam needed: clicked through start-camera -> live preview with framing guide -> start recording -> visible countdown -> stop -> preview -> "Use this recording", confirmed a real `201` from `POST /uploads`, confirmed status polling, and confirmed the pipeline correctly rejected the clip with `no_pose_detected` (the fake device's test pattern has no person in it -- this is the *correct* outcome, and exercises the real background pipeline running real `MediaPipe` pose extraction against a real recorded browser blob end-to-end). Screenshots reviewed at each stage.
- **Not verified: cross-browser.** This container only has Chromium's Playwright binary installed (no Firefox/WebKit) -- task 122 asks for "at least two browsers," which isn't achievable from this environment. `pickSupportedMimeType()` defensively falls back through codec options and surfaces a clear error rather than crashing if `MediaRecorder` isn't usable at all (accounting for Safari's narrower support), but this is written-to-spec defensive code, not something verified against an actual non-Chromium browser. Disclosed rather than silently skipped; real cross-browser testing needs a different environment or the user's own machine.

---

## 2026-09-25 — The original 6 seed clips finally have real pose/feature data

With the YouTube download pipeline now actually working (cookies + JS-challenge-solver fix, above), went back and re-fetched the 6 original V0 seed clips this session could never download before -- the single biggest standing blocker logged throughout this whole build (2026-09-25's earlier "cloud session handoff" entry, and every "blocked pending real footage" note since). One (`patrick_mahomes/clip1_qbperformancelab_62mph`) was already sitting in `data/candidates_staging/` from the 42-clip candidate batch, since it happened to also appear in Agent 1's research; the other 4 needed a fresh download, using the exact `source_url` + `timestamp_range` already recorded in `provenance.csv` from the original 2026-09-24 sourcing pass -- no new judgment calls, just mechanically re-fetching and re-trimming what was already vetted.

**One real discrepancy found and fixed:** `lamar_jackson/clip1_ravens_combine_full`'s original 23.3-25.15s window, which the 2026-09-24 entry documented as 56/56 (100%) pose detection, left a 3-frame trailing gap this time (the same "camera pans to the jumbotron" tail described back then). This isn't a bug -- it's this re-download landing at a slightly different frame alignment than the original one (different CDN edge, different exact bytes for the same nominal quality tier) -- but it meant the previously-documented 100% figure didn't reproduce exactly. Retrimmed to 23.3-25.0s using the same iterate-until-clean approach as the original session; down to two isolated 1-frame gaps, both cleanly interpolated. `provenance.csv` updated with the new window and an honest note explaining why it changed rather than silently overwriting the old number.

**Two real bugs found in the reference-clip batch scripts, both from running them against real data for the first time ever:** `pipeline/run_phase_segmentation.py` and `pipeline/run_features.py` were written back in V0 (before jitter smoothing / handedness canonicalization existed) and never exercised end-to-end since -- every run before now used pre-computed synthetic fixtures or was never run at all. Real footage immediately exposed that neither script applied `smooth_jitter`, and `run_features.py` didn't even apply `filter_low_confidence_landmarks` before loading raw `pose_raw/` JSON directly -- both would crash outright (`ValueError: ... requires landmarks on every frame`) on any real clip with an unfillable gap, which is a normal, expected outcome for real broadcast footage (a camera pan, a moment of occlusion), not a bug in the footage. Fixed both to filter+smooth consistently with `pipeline/orchestrator.py`'s real-upload path, and to skip (with a logged reason) rather than crash on a clip that still has a gap after that -- exactly the same defensive pattern already proven in production, just missing from these two older scripts because they'd never had real data to fail on before.

**Result:** `data/features_raw/` and `data/phase_boundaries_raw/` are real for the first time this session, for 5 of the 6 seed clips (all except the excluded `josh_allen/clip1_sideline_slowmo` showman-windup clip, per the original 2026-09-24 disqualification -- correctly still excluded). `python -m db.seed` loaded them for real: **6 reference clips, 5 real feature sets, 5 real phase-boundary sets**, now live in the local Postgres this session has been testing against all along. Full pytest suite (129 tests) still green with this real data in place. This means a real upload run through the live API today would be compared against real Josh Allen / Mahomes / Lamar Jackson mechanics, not just clip metadata with no features behind it -- the V0 core technical bet (real phase segmentation + real features + real similarity, per the 2026-09-24 kickoff entry's exit criteria) can finally start being checked for real, though a rigorous check still needs hand-labeled gold boundaries (task 19-20) and a larger sample than 5 clips across 3 QBs -- this is real data flowing end-to-end, not yet a validated system.

---

## 2026-09-25 — Tasks 123-126: skeleton overlay + synced comparison

Built on top of the real reference landmark data above. Design decisions worth recording:

**Storage (task 123):** new `landmark_sequences` table (dual-use nullable FK, same pattern as `phase_boundaries`), storing only (x, y) per landmark -- z/visibility/presence are dropped since nothing downstream needs them (confirmed by reading `pipeline/features.py`'s and `pipeline/similarity_dtw.py`'s actual angle/velocity math before assuming otherwise). Stored *pre*-handedness-canonicalization, since mirroring only serves the internal feature-comparison math and would render backwards over the real (un-mirrored) video; frame count/order is unaffected by mirroring so indices still line up with the boundaries computed on the canonicalized copy. Scoped to the boundary-covered frame range via a new `scope_to_boundary_range()` helper. `pipeline/run_landmark_export.py` (new batch script, mirroring `run_features.py`'s structure) populated real sequences for all 5 usable seed clips; `db/seed.py::seed_landmark_sequences()` loads them.

**A real product/legal decision, not just an engineering one:** task 125 asks for a "synced side-by-side view against the matched QB's clip." This project's reference video files are downloaded under a "non-commercial research/portfolio use" license note for *internal analysis* -- streaming that actual copyrighted video back to every visitor of a deployed app is a materially different, riskier use than what's been done with it so far, and there's no existing serving infrastructure for it anyway. Decided to render the matched QB's side as a **skeleton-only canvas animation** (just the extracted joint coordinates, drawn as lines/dots on a plain background) instead of streaming its source video -- it delivers the actual comparison value (motion mechanics, not pixels) without the licensing exposure. The user's own side plays their real uploaded video (a new `GET /uploads/{id}/video` endpoint, added since no such playback endpoint existed at all before this) with the skeleton drawn on top, since that's the user's own footage with no licensing question.

**Alignment:** `GET /results/{upload_id}/comparison` reconstructs both sequences' frame trajectories and calls the existing V1 `pipeline/similarity_dtw.py::dtw_align()` -- the first real production use of that module, which until now only fed into `combined_similarity()` (unused in the live match path per the V1 status entry's known limitations). Returns `reference: null` / `alignment: null` (not a 404) when the match exists but has no landmark data yet -- same honest-gap convention as every other nullable field in this project, since the user's own overlay is still fully usable on its own.

**Frontend:** `SkeletonOverlayPlayer` (task 124) draws a `POSE_CONNECTIONS` stick-figure on a canvas, either over a `<video>` or standalone; `useFrameScrubber` + `ScrubBar` (task 126) provide shared play/pause/seek state reusable by both the standalone player and the two-sided `SyncedComparisonView` (task 125), which maps the shared frame position through the DTW alignment path to keep both sides on equivalent motion phases despite different clip lengths.

**Two real bugs found via real testing, not assumed away:**
1. A CSS layout bug: the two side-by-side panels only render correctly because of a definite width; with a percentage-based width (`w-full`) inside a shrink-to-fit flex column, a panel's actual size was determined by whichever *sibling* label text was widest ("Patrick Mahomes" vs. "You"), since the video/canvas inside are `position: absolute` and don't contribute intrinsic size. Only visible by actually rendering it in a browser and comparing the two boxes -- fixed with a definite `w-80`.
2. My own test video (OpenCV's `mp4v` fourcc, the same one already used throughout the existing pytest suite) turned out to not be browser-playable at all (`readyState: 0`) -- MPEG-4 Part 2 isn't decodable by Chromium's `<video>` element. Not a bug in the shipped app (real uploads are phone/webcam H.264 or MediaRecorder's VP8/VP9), but a genuine gap in what the existing synthetic-video test helper can be trusted to validate for anything involving actual playback -- worth remembering if a future test needs real video rendering, not just pipeline processing.

**Validation:** the strongest real-data test this project has run yet -- rather than synthetic fixtures, used the *actual* real Josh Allen landmark sequence (189 real MediaPipe-extracted frames) as a stand-in upload, matched against the *actual* real Patrick Mahomes reference sequence (396 real frames), and called the real `/results/{id}/comparison` endpoint: real `dtw_align()` produced a 469-step alignment from real trajectory data on both sides. Confirmed via real Chromium/Playwright: both skeletons render correctly and distinctly at frame 1, both update to different correctly-posed frames when scrubbed to frame 91/189, no console errors. (The stand-in upload's own video file was a synthetic placeholder, deliberately -- not the real downloaded Josh Allen clip -- to avoid ever routing a copyrighted reference clip through the "user's own video" serving path, even in a throwaway local test.) Backend: 6 new API/integration tests (landmark endpoint, video endpoint, comparison endpoint with and without reference landmark data) plus 11 new unit/integration tests for the storage/serialization layer, all against real Postgres. Full suite: 138/138 passing.

---

## 2026-09-25 — Tasks 133-135: shareable results card export

Server-side PNG generation via Pillow (`pipeline/share_card.py`, layout decisions in `docs/share_card_design.md`) -- plain typography and shapes over a solid background, no headless browser needed. Deliberately text/stat-only, no video frame or skeleton imagery on the card, for the same reason `SyncedComparisonView` renders the matched QB as skeleton-only rather than video: keeps the card free of any reference-footage redistribution question. `POST /results/{upload_id}/export` returns the PNG directly; `ShareExportButton` fetches it as a blob and triggers a same-origin object-URL download -- a real single-click download, not a redirect to a separate page.

**Caught before it shipped:** the card's footer originally had a placeholder URL (`qbmotionatlas.app`) as a "try it here" call to action. Removed it -- this project isn't deployed anywhere yet (tasks 90-95 are blocked on the user's own cloud accounts), so putting a fake-looking live domain on an artifact meant to be shared around would be actively misleading. Footer just says "QB Motion Atlas" for now; swap in the real URL once one exists.

**Validated for real:** `render_share_card()` produces a correctly-sized real PNG (checked via Pillow re-opening the bytes, not just a byte-count check) across the matched/no-match/unknown-confidence/with-phase-stats cases (4 unit tests). Real Postgres API tests confirm `/export` returns real PNG magic bytes and 404s correctly when there's no result yet (2 tests). Real Chromium/Playwright: seeded a real result row, clicked the button, captured the actual triggered browser download via Playwright's `expect_download()`, verified the saved file's magic bytes and confirmed it visually matches the seeded data (QB name, percentage, confidence badge, phase stat all correct). Full suite: 143/143 passing.

---

## 2026-09-25 — Tasks 139-141: frontend polish

**Task 140** (`/qbs` reference-database browser page): a straightforward `GET /qbs`-backed page, linked from the home page. Verified against the real seeded data (Josh Allen, Lamar Jackson, Patrick Mahomes, 2 clips each) in a real browser, no console errors.

**Task 139** (loading-state polish): added a plain CSS fade-in (`prefers-reduced-motion`-respecting) so the processing and results pages' content doesn't pop in abruptly when a spinner is replaced by its result. Deliberately small -- the actual loading *states* (spinners, `aria-label`s) were already built in tasks 81/85; this is the transition between them.

**Task 141** (accessibility/responsive pass) -- **a real contrast bug found and fixed, not just checked off:** `globals.css` auto-switched to a dark background/foreground via `prefers-color-scheme: dark`, but not one component in this app has a `dark:` Tailwind variant -- every color is a fixed light-theme value. Rendering the home page with a real Chromium `color-scheme: dark` context showed exactly the predicted failure: "Upload a 5-15 second..." and the file-picker control both became barely legible, since a light-styled component was now sitting on a dark page background. Rather than half-support a dark theme (real further work, out of scope for a polish pass), forced light consistently by removing the media query, and confirmed via a second real dark-mode render that everything is legible again.

Also verified for real rather than assumed: keyboard `Tab` navigation reaches every interactive control on the upload page in a sane order with the browser's default focus ring intact (no `outline-none` anywhere suppressing it), and the results page (including the two-column `SyncedComparisonView`) reflows to a single column with no horizontal overflow at a 375px mobile viewport. Full suite: 143/143 passing (no backend changes this round, styling/markup only).

---

## 2026-09-25 — Task 131: a real (if tiny) evaluation run, and tasks 142-143: V2 documentation

With real reference feature data now existing (the seed-clip re-download entry above), ran the actual evaluation scripts for the first time this session rather than leaving task 131 purely theoretical. `eval/run_evaluation.py` (new) loads the real clean-`pass` reference clips' whole-clip feature vectors from Postgres and runs `eval/retrieval_accuracy.py`, `eval/self_consistency.py`, and `eval/discriminative_validity.py` against them -- `eval/pck.py` is explicitly not run, since it needs hand-labeled ground-truth keypoints that don't exist (no gold-labeling pass has ever been done against real footage).

**Deliberately excluded `lamar_jackson/clip2_nfl_everythrow_full`** from the eval set: its `pass-with-caveat` provenance already documented (2026-09-24) that release/follow-through were never actually visible on camera. Checked the actual extracted feature JSON before assuming this mattered -- the vector still has all 17 keys populated (segment_heuristic assigns *some* boundary regardless of whether the real motion is in frame), so the exclusion is about the *values* not being comparable, not about missing keys. This is the exact exclusion `research_log.md` already decided on 2026-09-24 for the V0 similarity check; `run_evaluation.py` just enforces it in code instead of leaving it as a rule a future script could forget.

**Real result, honestly reported: retrieval accuracy@1 = 0.0, discriminative validity ratio ≈ 1.0006 (chance level).** With only 4 usable clips across 3 QBs (only `patrick_mahomes` has more than one), this isn't evidence the similarity approach is broken -- it's the first real confirmation that every placeholder weight this codebase has documented all along genuinely has no measurable signal to tune yet, because there still isn't enough real data. Full writeup with the reasoning, not just the numbers: `docs/evaluation_report.md`.

**Task 142-143**: `docs/technical_report.md` consolidates the pipeline methodology, architecture, evaluation summary, and known limitations into one standalone document (task 142). README updated for V2 capabilities, linking both new docs, plus real reproduction steps for the reference-data pipeline, V2 embedding training, and running the evaluation (task 143) -- checked each referenced file path actually exists (`notebooks/01_train_embedding.ipynb`, not the guessed `models/training_notebook.ipynb`; `db.backfill_embeddings`'s actual CLI usage, not a guessed one-liner) rather than writing plausible-looking commands that don't run. Full suite: 143/143 passing (documentation + one new eval script; no pipeline/API changes).

---

## 2026-09-26 — Tasks A1-A8: real reference-clip video overlay, with risk mitigations

Revisits the 2026-09-25 decision (above) to render the matched QB's side as skeleton-only. The user's stated deploy plan changed the calculus: this is going up as an unmarketed personal/portfolio deployment (linked from a resume, not promoted or indexed for public discovery), not a product being pushed to an audience -- meaningfully lower exposure than the "every visitor of a deployed app" framing that motivated the original skeleton-only call. Decided this justifies streaming real reference footage back, but only for the lower-risk subset of clips, with three concrete mitigations rather than just reversing the old decision wholesale.

**Eligibility split (A2):** `pipeline/video_licensing.py::is_video_overlay_eligible(license_note)` -- clips whose `license_note` contains "official" (the existing convention for NFL/team broadcast-channel sourcing, e.g. `"NFL official YouTube channel; non-commercial research/portfolio use"`) stay skeleton-only; individual-creator/fan-reupload clips (the "test fixture" / non-"official" notes) become video-eligible. Rationale: official league/team broadcast content is the material realistically covered by automated content-fingerprinting (YouTube Content ID and similar), while an individual creator's reupload is a materially different risk profile -- lower audience, no known automated enforcement layer, and arguably closer to fair-use commentary/analysis given the pose overlay adds transformative annotation. Also gated behind a `REFERENCE_VIDEO_OVERLAY_ENABLED` env var as a global kill-switch, independent of any per-clip judgment, in case this assessment needs to be revisited after deployment.

**Serving (A1, A3):** new `GET /reference-clips/{clip_id}/video` -- 404s immediately for an ineligible or unknown clip (`api/main.py::get_reference_clip_video`), otherwise serves a **boundary-trimmed** copy: `_boundary_trimmed_reference_video()` reads the clip's already-seeded `PhaseBoundaryRow`s to compute the actual compared frame range (min start to max end across phases), trims via `ffmpeg -ss/-to` into `data/served_clips/{clip_id}.mp4`, and caches it there so repeat requests skip re-encoding. Trimming rather than serving the full source file matters for the same reason as the eligibility split: it caps what's exposed to exactly the segment the app's own analysis actually used, not an arbitrary-length clip that could include unrelated broadcast content before/after the throw. `data/served_clips/*` added to `.gitignore` alongside the other derived-video directories -- these are ffmpeg outputs from copyrighted source video and must never be committed.

**Wiring (A4-A5):** `ComparisonResponse` gained `reference_video_eligible: bool` (computed once in `get_comparison()` from the matched clip's `license_note`) so the frontend never has to guess or rely on a 404 to find out; `SyncedComparisonView` passes `videoUrl={getReferenceClipVideoUrl(matchedClipId)}` to the reference-side `SkeletonOverlayPlayer` only when that flag is true, falling back to the pre-existing skeleton-only rendering otherwise -- the exact same component now serves both cases, since `SkeletonOverlayPlayer` already supported an optional `videoUrl` from the task 124 user-video work.

**Mitigation: reduced discoverability (A6).** Site-wide `robots: { index: false, follow: false }` metadata (`frontend/src/app/layout.tsx`) plus a `robots.txt` (`frontend/src/app/robots.ts`, Next.js's static-route convention) disallowing all crawlers. Matches the "unmarketed, resume-linked" deployment framing directly -- there's no reason a page embedding real reference footage should be sitting in a search index at all, independent of the licensing risk itself.

**Mitigation: attribution (A7).** `ComparisonResponse.reference_clip_source_url` is populated (from the already-stored `QBReferenceClip.source_url`) only alongside `reference_video_eligible=true` -- never leaked for a skeleton-only match. `SyncedComparisonView` renders it as a small "Footage source" link under the video. Doesn't change the legal risk calculus, but costs nothing and is the right thing to do when redistributing someone else's footage at all, eligible or not.

**Tests (A8):** `tests/test_video_licensing.py` (7 tests: eligible/ineligible, case-insensitivity, both kill-switch states) plus 6 new `tests/test_api.py` cases covering the video endpoint (serves an eligible clip, 404s for an official-broadcast clip, 404s for an unknown clip) and the comparison endpoint (`reference_video_eligible` + `reference_clip_source_url` both set together for an eligible match, both correctly absent/null for an ineligible one). Full suite: 155/155 passing. Frontend: `tsc --noEmit` and `eslint` both clean, `next build` succeeds and confirms `/robots.txt` is generated as a real static route.

**What this does not change:** the share-card export (`pipeline/share_card.py`, 2026-09-25 entry above) stays text/stat-only by deliberate design, not oversight -- a downloadable, freely re-shareable artifact is a different and less controllable distribution surface than footage streamed only to that user's own results page, so the same risk-reduction logic that justifies in-app video for creator-sourced clips does not extend to baking that footage into an export.

**Real end-to-end QA against real Postgres + a real running stack, with an honest limitation surfaced rather than glossed over:** against the actual seeded reference clips (not fixtures), hit the real `GET /reference-clips/josh_allen__clip2_combine_slowmo/video` endpoint on a live `uvicorn` process -- confirmed the real `ffmpeg -ss/-to` trim runs against the real downloaded source file, produces a real playable 6.27s H.264 `.mp4` (`ffprobe`-verified), returns it with correct `video/mp4` / `Accept-Ranges: bytes` / CORS headers, and that a second request hits the on-disk cache (unchanged mtime, no re-encode). Confirmed `patrick_mahomes__clip2_nfl_2017combine_full` (an "official" clip) and an unknown clip both correctly 404. Then seeded two throwaway real-Postgres uploads (cleaned up after) -- one matched to the eligible Josh Allen clip, one to the official Mahomes clip -- and drove the actual Next.js dev server against the actual FastAPI server in real Chromium via Playwright: confirmed via `currentSrc`/DOM inspection that the eligible case renders exactly 2 `<video>` elements pointed at the correct URLs plus a "Footage source" attribution link with the correct `href` (the clip's real `source_url`), while the ineligible case renders exactly 1 `<video>` (the user's own) + 2 canvases and *no* attribution link -- i.e. the eligibility branch and the A7 attribution gating both work correctly in a real browser against real data, not just in the unit tests.

**What this QA could not confirm, and why:** actual visual video *playback* (frames rendering inside the `<video>` element). `element.canPlayType('video/mp4; codecs="avc1.64001f")` returns `''` in this sandbox's bundled Chromium (`vp9`/`vp8` both report `"probably"`) -- this specific headless browser build has no H.264 decoder at all, so every `<video src>` in this environment stays at `readyState=0` regardless of whether the server-side bytes are valid, including the user's-own-video path that was already shipped and working before tonight. Confirmed this is a browser-build gap, not a regression, by checking `canPlayType` directly rather than assuming: the served bytes are independently verified valid H.264 via `ffprobe` (`codec_name=h264`, `profile=High`, standard `avc1`/yuv420p), and real users' browsers (Chrome, Safari, mobile) support H.264 broadly. Same class of gap as the 2026-09-25 entry's `mp4v`-fourcc finding -- worth remembering for any future QA that needs to confirm actual decoded video frames, not just DOM wiring, in this sandbox.

Two stale comments caught and fixed while doing this pass (not new behavior, just docs that had drifted): `SkeletonOverlayPlayer`'s `videoUrl` prop comment and `GET /uploads/{id}/video`'s docstring both still said the matched QB's video is "never streamed back" / always skeleton-only, which was true as of the 2026-09-25 decision but is no longer the full picture after tonight's eligibility split.

Full suite: 155/155 passing. `tsc --noEmit`, `eslint`, and `next build` all clean.

---

## 2026-09-26 — Task #68: reviewed all 42 downloaded candidate clips; 0 passed

Manually reviewed every clip in `data/candidates_staging/` (42 downloaded,
1 recorded download failure) against `docs/data_criteria.md`'s checklist,
via each clip's ffmpeg contact sheet, conservatively (reject on real
doubt). Full per-clip reasoning: `docs/candidate_review_log.md`.

**Honest result: 0 of 42 passed.** This isn't a review-process failure --
it reflects something real about where these clips actually came from.
The earlier download pass (`pipeline/run_candidate_download.py`, prior
session) pulled from YouTube search results matching each QB's name, and
search results for "[QB name] throwing mechanics" are dominated by exactly
the content that fails this project's criteria: reaction/breakdown
channels built around picture-in-picture commentary and telestrator
overlays (one channel, "PLC", accounted for roughly a third of all 42
candidates by itself), and highlight compilations, both of which are
fundamentally the wrong *shape* of source video regardless of how good the
underlying game footage might be. The 6 already-accepted reference clips
in `data/provenance.csv` came from more targeted, deliberate searching in
the original sourcing pass (task 7), not a bulk keyword-search download --
this batch was explicitly framed as a broader/faster sourcing attempt, and
the 0% pass rate is the real, measured cost of that trade-off, not
something to paper over.

A handful of clips had a genuinely promising single-throw *segment*
buried inside an otherwise-disqualifying multi-scene download (noted
per-clip in the review log) -- worth a manual re-clip attempt someday, but
guessing at trim points from a contact sheet alone isn't something this
review pass should do.

**No changes to `data/raw/` or `data/provenance.csv`** -- there's nothing
from this batch that passed to promote (task #69 is a no-op this round).
Moving to task #71: sourcing new candidates for the 7 QBs with zero
accepted reference clips (Malik Willis, Geno Smith, Kirk Cousins, Bo Nix,
Jared Goff, Tyler Shough, Jacoby Brissett), applying this same checklist
*during* search this time -- filtering out picture-in-picture reaction
channels and highlight-compilation titles up front -- rather than
discovering the mismatch after a bulk download.

---

## 2026-09-26 — Task #71: blocked again on YouTube cookies (same root cause as before)

Before researching *new* candidates, checked `docs/qb_candidate_clips.md`
directly: all 7 of the QBs named in tonight's task list (Malik Willis,
Geno Smith, Kirk Cousins, Bo Nix, Jared Goff, Tyler Shough, Jacoby
Brissett) already have candidate URLs listed there from the original
research pass -- they just weren't in the earlier download batch because
that batch defaulted to the "High confidence + short clip" filter, and
these 7 QBs' pools are honestly documented as weak (mostly `Medium`
confidence, `long, needs isolation` Combine/Pro-Day footage). So the real
next step wasn't fresh web research, it was downloading the
already-identified `Medium`-tier candidates for review -- broadening
`run_candidate_download.py`'s selection, not re-searching from scratch.

That's blocked again on the same root cause as the very first entry in
this log: YouTube requires an authenticated cookies.txt to serve actual
video bytes to this container's datacenter IP, even though metadata
extraction now works without one. Confirmed this directly rather than
assuming it still applies: `yt-dlp --list-formats` succeeds with no
cookies at all (gets a full format list, including 1080p), but the actual
byte download of any format gets `HTTP Error 403: Forbidden` with no
cookies. This session's container is fresh (a new session since the
cookies.txt from the earlier sourcing pass was used and, per that pass's
own policy, never persisted or reused across accounts), so there is no
valid cookies file available right now and I have no way to produce one
myself -- it requires the user's own authenticated YouTube session.

**Not attempting a workaround** (no `--cookies-from-browser` on a
container with no logged-in browser, no scraping around the 403, no
alternate video host) -- this is exactly the kind of external-credential
dependency flagged as a real blocker rather than papered over, same as the
original 2026-09-24 entry. Marking task #71 blocked pending the user
supplying a fresh cookies.txt; moving to task #73 (overnight Postgres
watchdog), the one remaining task that doesn't depend on new video data.

---

## 2026-09-26 — Task #73: overnight Postgres watchdog

Confirmed Postgres is healthy right now (`pg_isready` -> accepting
connections; `service postgresql status` -> `16/main (port 5432): online`).
Recovery command for this environment if it's ever found down:
`pg_ctlcluster 16 main start` (this container has no systemd, so
`systemctl`/`service` control don't apply the way they would elsewhere --
confirmed by testing `service postgresql status` directly rather than
assuming, which is how the "16/main: online" line above was produced).

Scheduled a self check-in (`send_later`, survives container restarts per
its own description) to verify Postgres is still up, restart it if not,
and note anything found. All other tonight-scope tasks (#67-#72) are
either done or genuinely blocked on external input (YouTube cookies) that
no amount of polling fixes, so this watchdog's job is narrow: catch and
recover from the idle-suspend risk flagged earlier in the session, not
manufacture busywork.

---

## 2026-09-26 — Follow-up: manual re-clip attempt found nothing usable either

Went back to the 4 candidates from the 42-clip review that had a
"promising sub-segment, worth a manual re-clip" note and actually did that
work -- extracted each flagged window and resampled at a true (non-
decimating) frame rate instead of trusting the original coarse contact
sheet. **All 4 failed real verification**, each for a different and more
fundamental reason than what the original note said: `baker_mayfield`'s
"combine drill" turned out to be a frozen still image with an animated
logo on top (zero real motion across 35 real-sampled seconds); both
`bryce_young` segments turned out to be rapid-fire multi-rep drills (not
a single throw) and, for the first one, a directly-behind camera angle I
had misread as near-side; `cj_stroud`'s angle-doubt note was confirmed,
not resolved. Full writeup: `docs/candidate_review_log.md`'s follow-up
section.

**No new promotions.** The real, reusable finding here is about method,
not these 4 clips: this project's fast contact-sheet review (established
2026-09-24) is reliable for rejecting a clip -- any real problem shows up
even sparsely sampled -- but is not reliable for confirming one is clean.
Sparse even-spaced sampling can alias onto a repeated pose in a rapid
drill and look like a single continuous throw, and can even fail to
reveal that a "clip" never has any motion at all. Any future promotion
attempt needs a true-fps check of the exact candidate window before
counting it as a pass, not just a coarse grid.

**Where this leaves the dataset, stated plainly:** 3 QBs with any accepted
reference data (Josh Allen, Lamar Jackson, Patrick Mahomes), only 4 of
those 6 clips usable for evaluation, and the two bulk-sourcing attempts
tonight (the 42-clip batch and this re-clip follow-up) both came back
empty. Closing the coverage gap needs either a fresh, authenticated
cookies.txt to source new candidates (task #71, still blocked) or a
fundamentally different acquisition strategy (e.g. deliberately searching
for raw/unedited practice-feed or local-broadcast-affiliate footage
instead of QB-name keyword search, which this session's evidence
suggests is structurally dominated by reaction/highlight content) --
not more review effort against the same already-downloaded pool.

---

## 2026-09-26 — Watchdog validated: the container actually did restart overnight

The idle-suspend risk flagged earlier in the session (evidenced then only
by an unexplained multi-hour gap in Postgres's own logs) happened for
real: the harness reported an explicit container restart, and Postgres
was confirmed down (`pg_isready` -> no response) immediately after.
Restarted it with the documented recovery command
(`pg_ctlcluster 16 main start`) and verified both that it came back up
and that the data survived intact -- `qb_reference_clips` still has all 6
rows, matching what was there before the restart. No commits were lost
either (`git status` was clean and `git log` showed all of tonight's
commits still present), since everything was committed and pushed as it
was finished rather than left staged locally.

This validates the task #73 watchdog setup was worth doing, not
precautionary busywork: without a scheduled check-in surviving container
restarts, this exact failure mode (Postgres silently down, indistinguishable
from "just idle" until someone tries to use it) would have gone
unnoticed until the user's morning session hit a real error. Still no
cookies.txt available, so task #71 remains blocked.
