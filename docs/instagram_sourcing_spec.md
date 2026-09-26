# Instagram Sourcing Spec (Task: Instagram data-collection agents)

Written after a night of real, hands-on failure and correction (see
`docs/research_log.md`'s 2026-09-26 entries and `docs/candidate_review_log.md`
in full). Read those two files first if anything here is unclear -- they
show the actual mistakes this spec exists to prevent, with real screenshots
described in the text.

## Why Instagram, and why this spec exists

Tonight's 42-clip YouTube batch passed 0/42: YouTube search results for
"[QB] throwing mechanics" are structurally dominated by reaction-channel
picture-in-picture content and highlight compilations. YouTube also
requires an authenticated cookies.txt to download actual video bytes
(confirmed directly: `yt-dlp --list-formats` works with no cookies, but
downloading the actual stream 403s without one).

Instagram is different: confirmed by direct test that `yt-dlp` downloads
real video bytes from Instagram reels/posts with **zero cookies required**.
That's the whole reason this is worth doing. But Instagram has the *same*
content-shape problem as YouTube (reaction/duet reposts are everywhere) --
so the verification discipline below is not optional. Two real clips were
checked by hand tonight: one was a duet/stitch reaction format (rejected),
one was a genuinely clean single continuous throw reposted from
`@patrickmahomes` via NFL's own "NFL on Prime Video" account (accepted).
Both looked promising at a glance; only real per-frame verification told
them apart.

## Your job

You are assigned a batch of QBs (given in your task prompt). For **each**
QB in your batch:

1. Search for candidate videos.
2. Download the most promising 1-3 candidates.
3. Verify each one for real, at true frame rate -- not by eyeballing a
   coarse sample.
4. Report back structured findings (do NOT edit git, do NOT touch
   `data/provenance.csv`, do NOT commit anything -- a human/orchestrator
   spot-checks and promotes after you report).

Aim for **at least one verified-clean candidate per QB** if one exists in
a reasonable number of search attempts (try ~5-8 distinct search queries
and their top results before giving up on a QB). It is completely fine
and expected to come back empty-handed for some QBs -- report that
honestly, the same way tonight's YouTube review reported 0/42 honestly.
Do not stretch a marginal clip into a "pass" to have something to show.

## Step 1: Search

Use `WebSearch` (not a browser) with queries like:
- `site:instagram.com "<QB name>" throwing training`
- `site:instagram.com/reel "<QB name>" throwing`
- `site:instagram.com "<QB name>" back to work` (post-injury/offseason
  training clips are often genuinely raw, single-camera, personal-account
  content -- these turned out to be a good signal tonight)
- `site:instagram.com "<QB name>" pro day` / `"<QB name>" combine`

**Prefer, in this order:**
1. **QB trainer/coach accounts** -- private QB coaches post clean,
   deliberately-filmed training throws constantly, often already from a
   good side/three-quarter angle since that's literally what they're
   selling. Examples: 3DQB, Jordan Palmer, QB Country, Will Hewlett,
   Performance Lab of California ("qbperformancelab" -- already the
   source of 2 of this project's 3 currently-accepted clips). Search
   `site:instagram.com "<coach/account name>" "<QB name>"` -- these
   accounts train many QBs, so you need the QB's name in the query too.
2. The QB's own personal account, or a close family/teammate account.
3. A beat reporter / local-news / team-adjacent account posting raw
   sideline or practice footage (not a produced highlight package).
4. A repost of (1)-(3) by a larger account (even an official one, e.g.
   "NFL on Prime Video") -- still fine, see the licensing note below.

**Other platforms:** X (Twitter) and TikTok host the same kind of training
reels and `yt-dlp` supports both, but confirm cookie-free byte-level
download works there before relying on it -- Instagram turned out to
allow it with zero cookies, YouTube did not (confirmed by direct test,
not assumed). Test on one real candidate URL per new platform
(`yt-dlp --list-formats` then an actual download) before searching that
platform broadly. If a platform 403s or demands login for the actual
video file the same way YouTube did, drop it and say so in your report
rather than burning time on candidates you can't download.

**Deprioritize or skip entirely:**
- Any title/caption suggesting "breakdown," "mechanics analysis,"
  "reacts to," or a coach/analyst persona -- these are almost always
  duet/stitch or picture-in-picture reaction format.
- Highlight-compilation-style captions ("Top Plays," "Every Throw," "Best
  Moments").

## Step 2: Download

```
yt-dlp --js-runtimes node --remote-components ejs:github \
  --list-formats "https://www.instagram.com/reel/<ID>/"
```
No cookies flag needed. Pick the highest-resolution video-only DASH format
(prefer 720x1280 or better) plus the audio-only format (audio doesn't
matter for pose extraction, but the merge needs it), e.g.:
```
yt-dlp --js-runtimes node --remote-components ejs:github \
  -f "<video-format-id>+<audio-format-id>" \
  -o "data/candidates_staging/<qb_name>/<ID>.%(ext)s" \
  "https://www.instagram.com/reel/<ID>/"
```
(`<qb_name>` is the same slug convention as existing folders --
lowercase, underscores, matching `docs/qb_candidate_clips.md`'s headings.)

Also fetch and record the uploader info for the licensing note:
```
yt-dlp --js-runtimes node --remote-components ejs:github \
  --dump-json --no-download "https://www.instagram.com/reel/<ID>/" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('uploader'), d.get('uploader_id'), d.get('description'), d.get('upload_date'))"
```

If you get a 429 or rate-limit error: wait 30-60 seconds and retry once
or twice before moving on. Don't hammer it.

## Step 3: Verify -- the part that matters most

**The single biggest lesson from tonight: a coarse contact sheet (one
sampled frame per several seconds) is only reliable for *rejecting* a
clip. It is not reliable for *confirming* one is clean.** Two real
failures tonight, both caught only by resampling at a true (non-decimated)
frame rate:

- A clip that looked like a changing combine-throw sequence on a coarse
  6x6 grid turned out to be a **frozen still image** with an animated
  logo playing over it -- literally zero real motion for 35+ seconds,
  confirmed only once every sampled frame at true 8-10fps came back
  pixel-identical.
- A clip that looked like a near-side angle on a coarse grid turned out,
  at true 1fps sampling across the full window, to be a **directly-behind**
  camera angle (the thrower's back and number face the camera) -- the
  coarse sampling just didn't have enough temporal resolution to reveal it.

**So: for your final candidate window (after you've roughly located where
in the source video the real throw is), always verify with `ffmpeg` at a
true, non-decimating frame rate before reporting a pass.** Concretely:

```bash
# 1. Get duration
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 <file>.mp4

# 2. Get native fps
ffprobe -v error -show_entries stream=r_frame_rate -select_streams v -of default=noprint_wrappers=1:nokey=1 <file>.mp4

# 3. Extract your candidate window (adjust -ss/-t)
ffmpeg -y -ss <start> -i <file>.mp4 -t <duration> -c copy <window>.mp4

# 4. Sample the WHOLE window at true fps (8-15fps is usually enough to see
#    real per-frame progression without missing anything; for a window
#    under ~10s you can often just use the native fps). Pick a tile grid
#    that covers every sampled frame (e.g. 10x10 for ~100 samples).
ffmpeg -y -i <window>.mp4 -vf "fps=<N>,tile=<cols>x<rows>" -frames:v 1 -vsync vfr -update 1 <sheet>.jpg

# 5. View <sheet>.jpg with the Read tool and actually look at every tile.
```

**Checklist to apply while looking at that true-fps sheet** (this is
`docs/data_criteria.md`, restated with the specific failure modes found
tonight):

- [ ] **Real motion, not a frozen image.** The pose must visibly and
  continuously change tile-to-tile. If most/all tiles are pixel-identical,
  reject -- it's a static image with a bumper/caption animating on top.
- [ ] **One single continuous throw**, not a repeated drill. Walk through
  the tiles in order: you should see approach/set -> load -> cock ->
  release -> follow-through as ONE progression, not the same phase
  repeating over and over (a rapid catch-and-toss drill re-aliases onto
  a coarse sample and can look like continuous motion when it isn't --
  this is exactly what a true-fps check catches). If the window contains
  multiple reps, either trim to isolate exactly one cycle and re-verify
  the trimmed clip the same way, or reject if you can't cleanly isolate one.
- [ ] **Near-side, three-quarter, or three-quarter-behind camera angle.**
  You must be able to see the side profile of the thrower's torso and the
  arm's path through the throw. **Verified against this project's own
  accepted clips**: pure lateral (near-side) is ideal and is what the
  Josh Allen clip uses, but three-quarter-*behind* (camera sitting behind
  and to one side, not dead-center behind) is also already accepted and
  working -- both the Patrick Mahomes and Lamar Jackson accepted clips use
  this angle, not pure lateral. Accept that range.
  **Still reject: directly behind** (the thrower's back and jersey number
  face the camera flat/square-on, no side profile of the torso visible at
  all) **and directly head-on** (facing the camera, no side view of the
  arm). This isn't pickiness -- the pipeline's shoulder/elbow angle math
  is 2D-projection-based and cannot reliably extract those angles from a
  dead-on rear or front view. A clip 30-45 degrees off dead-behind is
  fine; a clip that's square-on behind is not.
- [ ] **Full body visible**, head to at least mid-thigh, for the whole
  throwing motion. Reject tight upper-body-only crops.
- [ ] **No heavy overlay on the body.** A caption bar confined to the top
  or bottom edge of frame (not overlapping the thrower) is fine. Circles/
  arrows/telestrator lines drawn over the arm, shoulder, or torso are not.
- [ ] **No picture-in-picture / duet / stitch split-screen.** If a
  reactor's face or a second video occupies part of the frame throughout,
  reject -- regardless of how large or small that region is.
- [ ] **No occlusion.** No other person overlapping the thrower during the
  load-through-release window.
- [ ] **Plausible identity.** Cross-check the uploader account name,
  caption text, and any visible jersey/context clues against the QB
  you're sourcing for. If you're not reasonably confident it's actually
  them, reject rather than guess -- mislabeling a different person under
  a QB's name is worse than having no clip at all.

## Step 4: Licensing note (for the report, not for you to write to provenance.csv)

Based on `pipeline/video_licensing.py`'s existing eligibility rule
(`"official" in license_note.lower()` -> skeleton-only, otherwise real
video-overlay eligible):

- Personal account, family/friend account, beat reporter, or a small fan
  account -> **not "official"** -- note this in your report so the human
  can grant video-overlay eligibility.
- A repost by an official league/team/broadcast-partner account (NFL,
  a team's own account, "NFL on Prime Video," ESPN, etc.) -> treat as
  **"official"** for this purpose even if the original creator was the
  player themselves (this is the conservative call already made tonight
  for exactly this situation) -- still fine to promote as reference
  biomechanics data, just skeleton-only for the video-overlay feature.

Either way, the clip is valuable **reference data** regardless of video-
overlay eligibility -- that's the primary thing this whole effort is for.
Don't downgrade or skip a clip just because it'll end up in the "official"
/skeleton-only bucket.

## Step 5: Report format

For each QB in your batch, report one of:

**FOUND:**
```
QB: <qb_name>
Video ID: <id>
Source URL: https://www.instagram.com/reel/<id>/
Uploader account: <uploader> (<uploader_id>)
Original creator (if different, e.g. "(via @x)" in caption): <...>
License tier: official | individual/fan
Local file: data/candidates_staging/<qb_name>/<id>.mp4
Isolated throw window: <start>s to <end>s (if the full file needed trimming)
Camera angle: near-side | three-quarter
Verification: [describe what the true-fps sheet showed -- e.g. "confirmed
  continuous single motion across N frames at Mfps, no aliasing, no PIP"]
Notes: <anything else relevant>
```

**NOT FOUND:**
```
QB: <qb_name>
Searched: <queries tried>
Candidates checked: <video IDs tried and why each failed -- be specific,
  e.g. "duet/reaction format", "directly-behind angle", "frozen still",
  "couldn't confirm identity">
```

Report all QBs in your batch in one final message, even the not-found
ones -- an honest empty result is useful information, not a failure to
hide.

## Do NOT

- Do not edit `data/provenance.csv`, `data/raw/`, or any tracked file.
- Do not `git add`/`git commit`/`git push` anything.
- Do not reseed the database or run the pipeline scripts.
- Do not report a clip as verified unless you personally viewed a
  true-fps contact sheet of it and walked the checklist above.

The human orchestrator will spot-check your reported "FOUND" clips before
promoting any of them, so accuracy matters more than volume.
