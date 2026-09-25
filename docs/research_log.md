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
