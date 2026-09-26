# Candidate Clip Review Log (Task #68)

Manual review of the 42 clips in `data/candidates_staging/` against
`docs/data_criteria.md`'s checklist, done via each clip's ffmpeg-generated
contact sheet (a tiled grid of sampled frames across the whole downloaded
source, not just the isolated throw). Conservative by design: reject on any
real doubt rather than promote and find out later during pose extraction.
Clips that pass go to `data/raw/` + `data/provenance.csv` (task #69); this
log exists so the reasoning survives even for rejects, which never get a
provenance entry.

Format per clip: `qb_name/video_id` — **PASS** / **REJECT** (reason).

---

## aaron_rodgers

- `-jhElzcgGOc` — **REJECT**. Contact sheet shows a wide elevated broadcast
  angle (full-field view, both end zones' worth of context) cycling through
  many different plays, not one throw — this is a highlight-compilation
  video, not a single-throw source. Disqualifying on multiple counts:
  wrong camera angle (broadcast-wide, not near-side), not a single visible
  throw, heavy scoreboard/down-distance graphic overlays on every frame,
  thrower is a tiny distant figure (well below any usable resolution for
  pose tracking on the body).
- `u3tRz5-Hsuo` — **REJECT**. A QB-mechanics breakdown video (same channel
  style as the already-accepted `qbperformancelab` reference clips) showing
  one throw analyzed repeatedly, near-side angle, good resolution. But the
  contact sheet shows real ambiguity that's disqualifying under a
  conservative read: (1) at least one sampled frame cuts to an unrelated
  wide stadium/scoreboard shot ("QTR 4 3:38") mid-grid, meaning the source
  isn't a clean single continuous throw -- there's a cut to different
  footage somewhere in the runtime; (2) the later third of the grid shows
  progressively heavier hand-drawn joint-tracking overlays (green circles +
  angle numbers) directly over the throwing arm/shoulder, which is exactly
  the "heavy graphic overlay covering the thrower's body" disqualifier.
  The early frames alone look promising, but I can't tell from the contact
  sheet alone whether a clean, overlay-free, single-throw sub-range exists
  that's also on the correct side of that mid-video cut -- rejecting rather
  than guessing at trim points that task #69 would have to guess right.

## baker_mayfield

- `VGOWhfv4tNc` — **REJECT**. The downloaded source is actually two
  unrelated segments spliced together: an empty-stadium Combine throwing
  drill (near-side view, single person, full body visible, only a
  lower-third "2017 Heisman Trophy winner" banner that doesn't cover the
  body -- this portion alone looks promising) followed by a long run of
  elevated "coaches film" all-22 pre-snap formation shots from what looks
  like unrelated game footage (tiny distant players, no throw visible at
  all, wrong camera angle). Fails "duration should be short enough that
  isolating the single throw is unambiguous" and "single visible throw"
  for the file as downloaded -- this isn't a single-throw source, it's a
  multi-segment compilation. The combine-drill portion might be worth a
  manual re-clip in a future pass, but not promoting the full download.
- `pZPxY7SJPlI` — **REJECT**. A multi-scene compilation: sideline
  warmup/crowd shots, then a close-up torso/head shot of a player wearing
  "GORDON #12" (not Baker Mayfield -- wrong player, and framed too tight
  to show below the chest, failing "full body visible" outright even if it
  were him), then a wide FOX-broadcast shot of what looks like a scramble/
  run play, not a throw. Fails single-visible-throw, full-body-visible, and
  arguably isn't even footage of the right QB for the segments that do show
  a throwing motion.

## brock_purdy

- `fNvYgXF6guU` — **REJECT**. A "PLC" breakdown video, but unlike the
  Rodgers one above this is unambiguous: it cycles through several
  different broadcast plays/games (different opponents' jerseys across
  the grid), each from a standard wide broadcast angle with heavy yellow
  telestrator arrows drawn across the offensive line and other players
  constantly in frame, then transitions into straight talking-head coach
  commentary and paid "Quarterback University" ad testimonial slides for
  the back half of the runtime. Fails single-visible-throw, camera angle,
  and overlay criteria simultaneously, and a large fraction of the source
  isn't even football footage.
- `m9yXJROJBL8` — **REJECT**. Same "PLC" channel, same problems in a
  different form: a talking-head reaction video with the actual game
  footage shown as a small picture-in-picture inset (never full-frame),
  cycling through multiple different plays/games, with large animated
  caption text ("PURDY HOLDS HIS EYES", "TO THE LEFT") overlaid on the
  inset itself. Picture-in-picture is explicitly disqualifying, the inset
  resolution is far below the 720p floor even if the source file is
  higher-res, and it's multiple plays, not one throw.

## bryce_young

- `BCa8JiPwSzE` — **REJECT**. A recruiting-camp/7-on-7 video with several
  spliced-together scenes: a canopy-tent interview/podium setup, a
  mid-video frame that's clearly a phone screenshot of a Photos-app-style
  gallery UI (not football footage at all -- a strong signal this source
  is an edited vlog, not a clean single-throw recording), then a genuinely
  promising 7v7-tournament throwing segment (near-side angle, single
  player visible, full body, only a small non-body-covering "TROJAN
  INSIDER" watermark). Rejecting the download as a whole for the same
  reason as the other multi-scene compilations above -- the throwing
  segment alone looks like a good candidate for a future manual re-clip
  attempt, but isolating it isn't a call this review pass should guess at.
- `DKFPYAEH1Fc` — **REJECT**. Same shape of problem again: opens on a
  different 7v7-camp scene (crowd/canopy tents, distant thrower), cuts to
  a separate showcase/training session with a "#5" jersey player doing
  repeated rollout throws (this middle segment looks genuinely good --
  three-quarter/near-side view, full body, single player, other players
  visible but not overlapping the thrower), then ends with an unmistakable
  screen-recording artifact (a literal browser window showing YouTube and
  the PLC website) spliced into the last frames -- confirming the whole
  download is an edited compilation, not raw footage. Reject the file as a
  whole for the same reason as the other compilations; the middle segment
  is a good re-clip candidate for later.

## caleb_williams

- `V40HqlsVhCQ` — **REJECT**. Another "PLC" talking-head reaction video,
  picture-in-picture inset for essentially the whole runtime, tiny inset
  further crowded with many people (can't reliably identify a single
  thrower in most frames), plus the same ad-testimonial slides at the end.
  Fails picture-in-picture, resolution, and single-visible-throw all at
  once, same as the other PLC-reaction-format rejects above.
- `fAwsvWgN5MU` — **REJECT**. Same PLC picture-in-picture reaction format,
  inset shows a standard wide broadcast angle with a scoreboard bug
  ("OKLAHOMA 24") and a full crowd of players at every snap, cycling
  through multiple different plays of a game. Same disqualifiers as the
  other PLC rejects: picture-in-picture, camera angle, multiple plays,
  scoreboard overlay.

## cam_ward

- `pCer54U6CSE` — **REJECT**. Same PLC picture-in-picture reaction format
  (pro-day showcase footage of Cam Ward as the inset), plus persistent
  "CAM WARD SHOWCASES ARM, ATHLETICISM" news-ticker/lower-third graphics
  and hand-drawn cyan circles/angle numbers over the thrower in later
  frames, and unrelated basketball-scores ticker bugs bleeding in from the
  channel's stream overlay. Same picture-in-picture/overlay disqualifiers
  as the other PLC rejects.

## cj_stroud

- `WpfYNvADzSo` — **REJECT**. The first ~24 frames are a genuinely
  promising continuous single-throw sequence at a practice facility
  (single player, #16 maroon practice gear, full body head-to-feet, only
  a small logo watermark and a couple of thin angle-guide lines late in
  the motion) -- but the camera is positioned diagonally behind the
  thrower looking downfield, which reads closer to "directly behind" than
  the required "near-side, roughly perpendicular to the throwing-arm side"
  angle; genuinely borderline rather than clean. On top of that, the
  second half of the source cuts to completely unrelated aerial drone
  footage of an empty field with a Cowboys star logo (tiny distant
  figures, wrong context entirely), confirming this is again a
  multi-scene compilation, not a single clean source. Rejecting on the
  combination of camera-angle doubt + compilation structure; conservative
  per the review brief given the angle question alone is a real doubt.
- `oO0bRzWlO6A` — **REJECT**. Same PLC picture-in-picture reaction format
  with the talking head permanently in the bottom-right corner and a
  persistent "C.J. Stroud -- 2-time Big Ten Offensive Player" lower-third
  bug plus a "VERTICAL" combine-drill graphic across the top; cycles
  through multiple different combine reps and ends in the same ad-slide
  sequence as the other PLC videos. Same disqualifiers as the rest of this
  channel's clips reviewed above.

## dak_prescott

- `SAenOXqDzlQ` — **REJECT**. A self-filmed training clip (single person,
  empty field, no scoreboard) with heavy blue-circle + green-arrow
  joint/angle annotations drawn directly over the shoulder/elbow/hip for
  most of the runtime -- exactly the "heavy graphic overlay covering the
  thrower's body" disqualifier, not just a thin guide line. The back third
  of the source also cuts to unrelated wide-broadcast NFL game footage
  (different scene, different camera angle, multiple players), confirming
  this is a spliced compilation on top of the overlay problem.
- `jdJqvoKCHLo` — **REJECT**. "Dak Prescott Rookie Highlights" broadcast
  compilation -- wide elevated camera angle, persistent scoreboard bugs,
  multiple different games/opponents across the grid (score changes from
  DAL 14-LA 7 to CHI 0-DAL 7 to PHI 10-DAL 10), and every frame is a
  pre-snap or in-the-pocket formation shot with the full offensive/
  defensive lines in frame, not an isolated throw. Fails camera angle,
  single-visible-throw, and scoreboard-overlay criteria outright.

## deshaun_watson

- `Lo-ZMwm_Plo` — **REJECT**. "Deshaun Watson Redemption -- Ultimate
  Clemson Highlights" compilation with a persistent "THZ" watermark --
  wide elevated broadcast angle across multiple different games
  (down/distance and scoreboard bugs change: "3rd & 11" vs. "2nd & 19" vs.
  "Syracuse 0 / Clemson 10"), full offensive/defensive lines in every
  frame, no isolated throw visible anywhere in the sampled grid. Same
  compilation/camera-angle disqualifiers as the other highlight reels.
- `_np2yxIF9U0` — **REJECT**. Opens with a Texans practice-field warmup
  segment (single player, near-side view, full body) but with blue-circle
  + green-arrow joint annotations drawn over the body in most frames, then
  cuts to wide FOX-broadcast game footage with scoreboard bugs across
  multiple different games ("CIN 10 LAR 24 FINAL", "NY Jets 15 Jacksonville
  Final"). Multi-scene compilation plus body-covering overlay on the one
  segment that otherwise had a usable angle.

## drake_maye

- `ee2vSqgOjsc` — **REJECT**. Same PLC picture-in-picture reaction format,
  inset cycles through Draft-broadcast game footage and Pro Day workout
  clips with a persistent "2024 NFL Draft" / "QB Drake Maye" lower-third,
  plus the usual ad-slide ending. Same disqualifiers as the rest of this
  channel's clips.

## jalen_hurts

- (`0mSaVgxdHMI` — download failed, no file to review.)
- `iGVp-4ZzkOg` — **REJECT**. Same PLC picture-in-picture reaction format
  with a persistent talking-head coach in the corner, "Throw: 54 mph"
  broadcast graphic burned into the inset, and a scoreboard bug ("LAC 24
  PHI"). Same disqualifiers as the rest of this channel's clips.

## jared_goff

- `--xjU0Zatvc` — **REJECT**. Multi-scene compilation: opens on a
  close-up torso-only shot (empty stadium, cropped at the chest -- fails
  "full body visible" outright, no legs/stride visible at all) with heavy
  blue-circle/green-arrow overlays on the arm, then cuts to wide broadcast
  game footage against the Bears (scoreboard bug "CHICAGO BEARS 7",
  multiple linemen in every frame), then cuts again to a distant pregame
  warmup wide shot. Fails full-body-visible, camera angle, overlay, and
  single-visible-throw simultaneously across its different segments.

## jaxson_dart

- `U45tFkwR_Jc` — **REJECT**. Same PLC picture-in-picture reaction format,
  NFL Combine footage as the inset, heavy cyan circle/box overlays drawn
  over the thrower and cyan drop-step markers on the turf, plus stat-card
  lower-thirds ("PFF: Led FBS with 1,517 pass yds..."), ending in the usual
  ad slides. Same disqualifiers as the rest of this channel's clips.

## joe_burrow

- `LwiNJ_nVzVA` — **REJECT**. Same PLC picture-in-picture reaction format
  (Pro Bowl skills-competition footage as the inset), cyan drawn arrows/
  circles over the thrower in several frames, ending in the usual ad
  slide. Same disqualifiers as the rest of this channel's clips.
- `get6ZMlb7y4` — **REJECT**. A stats-focused highlight compilation
  ("JustBombsProductions"/"JBP_Official" watermark) with green telestrator
  numbers/arrows over receivers, persistent scoreboard bugs across multiple
  different games (LSU-Texas, LSU-Utah St), full offensive/defensive lines
  in every frame, wide broadcast angle throughout. Fails camera angle,
  single-visible-throw, and overlay criteria.

## jordan_love

- `vvfHUabPl6w` — **REJECT**. A Senior-Bowl/all-star-week workout clip
  shot from the stadium upper deck -- the thrower is a tiny distant figure
  in the middle of the field (far below usable resolution for pose
  tracking on the body even though the source file itself may be HD),
  with a persistent draft-info lower-third ("Jordan Love QB 6'3 3/4" 224
  USU") and heavy green-arrow/blue-circle telestrator overlays drawn over
  him throughout. Fails effective resolution and overlay criteria.

## josh_allen

(Note: these are two new candidates found beyond the two already-promoted
Josh Allen reference clips in `data/provenance.csv` -- different video IDs,
reviewed independently.)

- `9HaDjrmdQOg` — **REJECT**. A vertical-format promotional short at
  Highmark Stadium -- Josh Allen mostly just standing, talking, and
  gesturing casually while holding a ball, interspersed with "STAY TUNED
  FOR MORE VIDEOS" and "QUARTERBACK UNIVERSITY" / "QB MECHANICS PROGRAM"
  ad-bumper interstitials. No actual throwing motion is visible in any
  sampled frame -- fails "single visible throw" because there isn't one to
  find, on top of being ad content for a large fraction of the runtime.
- `G6Cfoz5X0Bw` — **REJECT**. Same PLC picture-in-picture reaction format,
  Combine/scouting-footage inset with a "SCOUTING" graphic and "ALLEN #2"
  lower-third, cyan overlay circles/arrows drawn over the thrower, cycling
  between two different source clips (stadium combine + separate outdoor
  practice field), ending in the usual ad slides. Same disqualifiers as
  the rest of this channel's clips.

## justin_herbert

- `aXv6jKSDcHg` — **REJECT**. Opens with a wide stadium-level Combine shot
  where the thrower is a small distant figure (persistent draft-stat
  lower-third "3,471 pass yds, 32 TD..." plus blue-circle/green-arrow
  overlays), then cuts entirely to a different scene -- Oregon (green
  jersey) broadcast game footage with multiple players in the pocket.
  Fails effective resolution, camera angle, overlay, and is a multi-scene
  compilation on top of that.
- `nO4J-WMQ8VI` — **REJECT**. A "SkyDesignsGFX" broadcast-graphics reel
  with a persistent FS1 scoreboard/ticker bug and down-and-distance
  graphic across a full Oregon-Cal game (score and clock visibly change
  throughout), wide broadcast angle, full offensive/defensive lines in
  every frame. No isolated throw, wrong camera angle, heavy overlays.

## kyler_murray

- `WhTg0KHmYNw` — **REJECT**. A breakdown-style compilation of at least two
  different plays (first play alone in the pocket with heavy red/green
  circle-and-arrow overlays covering the whole torso; second play a
  49ers-defense pass rush with multiple defenders directly overlapping
  Murray during the throw window). Fails single-visible-throw, overlay,
  and "no occlusion during release" simultaneously.
- `j5fyOG2xptY` — **REJECT**. A multi-play, multi-scene compilation: a
  broadcast angle with the State Farm Stadium jumbotron visible in frame
  and overlays on the thrower, then several different snap/pocket
  formations from a low sideline angle, then a completely different
  scene of Murray celebrating in the end zone. No single isolated throw,
  multiple overlays, multiple unrelated moments spliced together.

## lamar_jackson

- `fMb7nRtwtL0` — **REJECT**. PLC-branded FOX broadcast footage, wide
  angle with a persistent down/distance graphic and scoreboard bug across
  at least two different plays (score changes from "CARDINALS 3 RAVENS 7"
  to "CARDINALS 6 RAVENS 10"), full offensive/defensive lines in frame
  throughout, no isolated throw. Fails camera angle, single-visible-throw,
  and overlay criteria.

## marcus_mariota

- `praimUqT6PE` — **REJECT**. "Marcus Mariota Breakdown" (PLC) highlight
  compilation spanning many different games and even different players'
  plays (scoreboard/caption text at various points names "B. ROETHLISBERGER
  LEFT GAME 2ND & 1, KNEE!" and "D. CARR: 6/8, 41 YDS, TD" -- unrelated
  plays mixed in), wide broadcast angle throughout, full lines in every
  frame, no isolated Mariota throw visible. Fails single-visible-throw and
  camera-angle criteria outright, and part of the footage isn't even him.

## matthew_stafford

- `14wXhy5ECEE` — **REJECT**. Multi-play breakdown across at least two
  different games (Chiefs defense, then Patriots/Meijer-branded broadcast),
  heavy blue/red/green telestrator boxes and arrows over the thrower in
  nearly every frame, defenders directly draped on/around him during
  several throw windows. Fails single-visible-throw, overlay, and
  no-occlusion-during-release criteria.
- `BIMWzyD343o` — **REJECT**. Another multi-play/multi-scene breakdown with
  "IMPROVE YOUR ARM STRENGTH IN 10 DAYS" ad-bumper interstitials, heavy
  red/blue/green telestrator arrows and circles covering the thrower in
  nearly every frame, a coach/trainer standing directly against the
  thrower during several reps, and standard broadcast wide-angle game
  footage with a fantasy-stats ticker bug for other segments. Fails
  overlay, no-occlusion, camera-angle, and single-visible-throw criteria.

## michael_penix_jr

- `SMoWqRrmZf0` — **REJECT**. Same PLC picture-in-picture reaction format,
  cycling through multiple different plays/games (Big Ten broadcast
  footage, wide angle), talking head permanently in frame, ending in the
  usual ad slides. Same disqualifiers as the rest of this channel's clips.
- `yKqeHSY9NW0` — **REJECT**. Another picture-in-picture reaction video
  (different channel, same format) with a circular webcam bug covering
  part of the play, cycling through multiple different games/scoreboards
  (Pac-12 Championship, then a separate "W 38" game with an ESPN ticker
  for unrelated NFL games underneath), plus an unrelated baseball-pitcher
  photo spliced in as an analogy slide. Fails picture-in-picture,
  single-visible-throw, and camera-angle criteria.

## patrick_mahomes

(Note: two new candidates beyond the two already-promoted Mahomes
reference clips in `data/provenance.csv` -- different video IDs.)

- `DgyXQKTiUoQ` — **REJECT**. A vertical-format short: genuinely promising
  on camera angle, single continuous throw, and full body visibility (no
  crowding, only a non-body-covering "QB MECHANICS PROGRAM" ad banner
  along the top edge) -- but I cannot actually confirm this is Patrick
  Mahomes from the contact sheet. The thrower wears a plain black practice
  shirt with no visible team branding, number, or clear face shot in any
  sampled frame; the only background detail (a wall graphic with a large
  "12" in what looks like Patriots navy/silver) is circumstantial at best
  and doesn't confirm identity either way. Given the instruction to reject
  on real doubt, mislabeling a different QB's mechanics as Mahomes would
  corrupt the reference dataset more seriously than just losing this
  candidate, so rejecting on identity uncertainty despite the otherwise
  clean footage.
- `ZiHlwHXj-24` — **REJECT**. A wide shot of a Big 12 field (Texas Tech's
  "Fearless" end zone visible -- plausibly college-era Mahomes given his
  Texas Tech background, but far too distant to confirm), showing a tiny
  figure running what looks like a route, not a throwing motion, at any
  point in the sampled frames. Interspersed with "STAY TUNED FOR MORE
  VIDEOS" / "QUARTERBACK UNIVERSITY" ad bumpers for a large fraction of
  the runtime. Fails single-visible-throw (there isn't one) and effective
  resolution.

## sam_darnold

- `-N6Kmim4kl0` — **REJECT**. A multi-scene compilation: USC Pro Day
  footage with a persistent "Sam Darnold participating in USC Pro Day"
  lower-third and heavy blue-circle/green-arrow overlays, spliced with
  what looks like separate Jets practice/game footage (different jerseys,
  numbers, background) with linemen directly occluding the thrower during
  several snaps. Fails single-visible-throw, overlay, and no-occlusion
  criteria.
- `oehb8dzrQBg` — **REJECT**. "USC QB Sam Darnold 2016 Highlights"
  (JustBombsProductions/PLC) compilation, wide broadcast angle across
  multiple plays with a persistent "2nd & 1 / USC 27 Penn St 42" scoreboard
  bug, full offensive/defensive lines and frequent occlusion by linemen
  during snaps. Same disqualifiers as the other highlight-reel rejects.

## trevor_lawrence

- `2CoqSIdQ8jk` — **REJECT**. A "Rivals" recruiting-camp clip (high-school
  #21) shot from directly behind the thrower looking downfield -- exactly
  the "directly behind" angle the criteria explicitly excludes, not just
  borderline -- with a coach standing immediately next to/overlapping him
  in several frames. Fails camera angle outright.
- `ymiFKkhmx3k` — **REJECT**. A multi-game broadcast highlight compilation
  (scoreboard changes from "Coast Car 21 Texas St 7" to "Texas Tech 44
  Oklahoma St 50 FINAL"), heavy red-circle/green-arrow telestrator overlays
  drawn over receivers and defenders on nearly every frame, wide angle
  with full offensive/defensive lines visible throughout, no isolated
  throw. Same disqualifiers as the other highlight-reel rejects.

---

## Summary

All 42 downloaded candidates reviewed (plus 1 recorded download failure,
`jalen_hurts/0mSaVgxdHMI`). **Result: 0 passed, 42 rejected.**

Rejection reasons broke down into a small number of recurring patterns,
none of them subtle:

1. **PLC-channel picture-in-picture reaction videos** (~15 of 42) — a
   talking-head coach permanently on screen reacting to a small inset of
   the actual footage. Disqualifying on picture-in-picture alone, before
   even considering the persistent overlays and ad-slide endings these
   all shared.
2. **Wide-broadcast highlight/breakdown compilations** (~15 of 42) —
   standard TV camera angle (not near-side), scoreboard/down-distance
   bugs, multiple plays or even multiple different games spliced together,
   often with hand-drawn telestrator arrows/circles directly over the
   thrower.
3. **Multi-scene personal/recruiting compilations** (~8 of 42) — vlog-style
   or camp videos mixing a promising-looking single-throw segment with
   completely unrelated footage (screen recordings, aerial drone shots,
   other plays), or shot from directly behind rather than the required
   near-side angle.
4. **Identity/content mismatches** (2 of 42) — footage of a different
   player than the folder's QB name, or a `patrick_mahomes`-labeled clip
   where the thrower's identity couldn't actually be confirmed.

None of the 42 source files are being deleted -- they stay in
`data/candidates_staging/` (gitignored, not committed) in case a future
pass wants to hand-trim one of the promising sub-segments called out
above (baker_mayfield's Combine drill, both bryce_young 7v7 segments,
cj_stroud's practice-facility throw, deshaun_watson's Texans-practice
segment, and the patrick_mahomes vertical short all got an explicit
"good sub-segment, but not this download as-is" note above). That kind of
manual re-clipping is real future work, not something this review pass
should attempt by guessing at timestamps from a contact sheet alone.

**Task #69 (promote passing clips) has nothing to promote from this
batch** -- `data/raw/` and `data/provenance.csv` are unchanged. Moving on
to task #71 (source new candidates for the QBs with zero clips at all:
Malik Willis, Geno Smith, Kirk Cousins, Bo Nix, Jared Goff, Tyler Shough,
Jacoby Brissett) with this same checklist applied up front during search,
rather than after a bulk download.
