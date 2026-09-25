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
