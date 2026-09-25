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
