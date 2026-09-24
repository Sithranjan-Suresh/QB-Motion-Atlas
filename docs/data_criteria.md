# Clip Selection Criteria

Rules a candidate clip must satisfy before it's added to `data/raw/`. Applied by eye during sourcing (task 7) and re-checked after trimming (task 10).

## Required
- **Camera angle:** near-side-view of the thrower (camera roughly perpendicular to the throwing-arm side, not head-on and not directly behind). This is the angle the whole pipeline is designed around for V0–V2; frontal/behind angles get excluded until 3D lifting (V3).
- **Single visible throw:** exactly one full throwing motion per clip, from load through follow-through, with no cuts or replays mid-motion.
- **Full body visible:** head to at least mid-thigh visible for the entire throwing motion — no crops that cut off the legs/stride or the throwing arm.
- **Resolution:** at least 720p source (can be re-encoded lower, but shouldn't originate below this — pose tracking degrades fast on blurry/low-res footage).
- **Duration:** the source clip should be short enough that isolating the single throw is unambiguous — under ~30 seconds of source footage per throw is a reasonable working ceiling before trimming.
- **Frame rate:** 24fps or higher, no obvious frame drops/stutter (coaching-breakdown slow-mo is fine and often ideal — it just needs a documented playback-speed note in provenance so timing features can be corrected later).

## Disqualifying
- Multiple people overlapping the thrower during the throw window.
- Heavy graphic overlays (telestrator lines, scoreboard bugs, picture-in-picture) covering the thrower's body.
- Thrower partially occluded by another player, ref, or camera obstruction during the release window.
- Clips where the "throw" is a handoff, pump-fake, or scramble rather than a full mechanics rep.

## Provenance requirement
Every clip that passes must have a traceable source URL and license/usage note recorded in `data/provenance.csv` (task 8) before it's used — no untracked footage.
