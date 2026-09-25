# QB Motion Atlas — Candidate Clip Research (Agent 1)

**Status: unverified candidates, NOT gold clips.** Everything below was found by web/YouTube search and judged only from titles, descriptions, channel names, upload dates, and (where the search tool surfaced it) short textual summaries. I did not download or frame-scrub any video. Per this project's own `docs/research_log.md` (see the 2026-09-25 "gold-label prep" entry), title/thumbnail screening has repeatedly missed real disqualifiers — a showman full-arm-circle windup that isn't a real mechanics rep, a Short that loops the same throw twice, slow-motion capture that looks like a freeze-frame stall — and those were only caught by full frame-by-frame / contact-sheet review after download. **Every clip here still needs that same frame-by-frame pass (per `docs/data_criteria.md`) before it goes anywhere near `data/raw/`.** Treat "high confidence" as "good title/channel/length signal," not "verified."

Confidence tiers used below:
- **High** — dedicated QB-mechanics breakdown channel (e.g., a "Performance Lab of California" / "QB Performance Lab"-style channel, or an official NFL/team combine-workout video), title strongly implies a single clean near-side throw, and duration looks short.
- **Medium** — plausible source type (combine/pro-day footage, a mechanics-breakdown title) but the video is longer/compilation-style, has commentary voiceover/cuts, or the channel isn't one with a track record on this project, so the useful window still needs to be found and checked.
- **Low** — game-broadcast highlight compilations, "every throw vs. Team X" cut-ups, or interview/press-conference footage. These are included only when nothing better turned up for that QB; broadcast camera angles are usually high/wide rather than true near-side, and compilations cut between plays, both of which are likely disqualifiers per `data_criteria.md`. Flagged explicitly as needing real scrutiny.

Clip-type notes: **"short"** = already a short single video (a Short, or a dedicated <1 min breakdown clip) — still needs the full-body/angle/occlusion checks, but no timestamp-hunting. **"long, needs isolation"** = a multi-minute or full-workout video where a specific throw's timestamp range still needs to be found.

I could not watch these videos, verify exact channel names/handles beyond what appeared in search snippets, or confirm resolution/fps. Where a search result's synthesized summary named a channel (e.g. "Performance Lab of California"), I've passed that along as reported, but it is unverified and may not exactly match the "QB Performance Lab" channel already used elsewhere in this project's dataset (per `research_log.md`, that channel is `@qbperformancelab`) — these could be a different, similarly-named channel. Flagged where relevant.

---

## Current starters used, and sourcing notes

Verified via web search on 2026-09-25 (current NFL season, roughly Week 3–4). Two general starter-tracker pages (nbc.com/nbc-insider and si.com's weekly-updated list) gave partly conflicting info versus more specific per-team searches; the per-team searches (cited under each division) were treated as authoritative since they were more recent/specific.

**Ambiguous / contested starters, flagged explicitly:**
- **Washington Commanders:** Jayden Daniels is the normal starter but suffered a dislocated elbow in Week 3 (loss to Dallas); **Marcus Mariota** was named the starter "this weekend" as of Sept 21, 2026, with no clear return timeline for Daniels as of the source dates found. I used Mariota as the *current* starter and sourced Mariota clips, but flag that Daniels is the long-term starter and may return soon.
- **Atlanta Falcons:** Tua Tagovailoa signed as a free agent and started Weeks 1–2; **Michael Penix Jr.** (recovering from a season-ending ACL/knee injury) took over the starting job from Week 3 onward per multiple sources. I used Penix Jr. as current starter and sourced Penix clips (plus this is also who the Falcons are building around long-term).
- **Cleveland Browns:** Deshaun Watson won a training-camp competition over rookie Shedeur Sanders and was named Week 1 starter; some sources note this remains a competition. Used Watson.
- **Las Vegas Raiders:** Kirk Cousins was named the Week 1 starter over rookie #1-overall-pick Fernando Mendoza; some coverage suggested a "possible rookie takeover" later in the season, but no confirmed switch was found as of the search date. Used Cousins.
- **Kansas City Chiefs:** Patrick Mahomes tore his ACL/LCL in Week 15 of the 2025 season, had surgery, and per late-Sept-2026 reporting was cleared and took all first-team reps for the Week 1 2026 opener. Used Mahomes as the current/expected starter.

All other 27 teams' starters were corroborated by at least one dedicated per-team or per-division search and did not show meaningful ambiguity at research time.

---

## Buffalo Bills — Josh Allen

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=9HaDjrmdQOg | Mechanics-breakdown channel (title style matches "QB Performance Lab"-type content) | "Josh Allen Throwing Mechanics — Explains Foot Hop To Get Hips Open," #quarterbackmechanics tag | High | short |
| https://www.youtube.com/watch?v=G6Cfoz5X0Bw | Same style/tag family | "Josh Allen Throwing Mechanics That Every Great Quarterback Replicates" | Medium-high | short |
| https://www.youtube.com/watch?v=100rQl0IRQU | Mechanics-breakdown channel | "Josh Allen Throwing Mechanics Breakdown" | Medium | short |
| https://www.youtube.com/watch?v=tE2GYS7wkeo | Unconfirmed breakdown channel | "Josh Allen Throwing Mechanics at the Combine" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=s38NnMlS8EQ | NFL Combine broadcast footage | "Josh Allen throws huge passes — 2018 NFL Combine" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=SI41Vxv38pk | Unclear (possibly interview/self-analysis) | "Allen breaks down his own mechanics" — may be talking-head with inserted clips rather than one continuous throw | Low-medium | long, needs isolation |
| https://www.youtube.com/watch?v=Jq3OXR45TWk | College-era footage | "Josh Allen Throwing Motion At Wyoming" | Low-medium | long, needs isolation |

Note: this project's `research_log.md` already documents 2 Josh Allen seed clips (one excluded as a showman non-standard throw); these are additional untried candidates.

## Miami Dolphins — Malik Willis

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=B3vpcx3Sv20 | Draft-media pro-day compilation | "Malik Willis FULL Pro Day Highlights: Every Throw" (Liberty, 2022) | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=nP-WVYkoU1E | NFL/draft-media combine footage | "Malik Willis' FULL 2022 NFL Scouting Combine Workout" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=npbNe8-0Ndo | Combine footage | "Malik Willis Throwing the ball at 2022 NFL Combine" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=f-uNTPneq48 | Pro day footage | "Malik Willis Pro Day" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=YVCA7NCeqPo | Pro day footage | "Malik Willis throws to Tre Turner at Liberty's pro day" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=64h5wYb2RR0 | Draft-analysis channel | "Malik Willis Combine Breakdown — Best Quarterback At NFL Combine" | Low-medium | long, needs isolation |
| https://www.youtube.com/watch?v=wzV9Ip2vLAU | Game-highlight clip | "Malik Willis impressive arm angle on TD throw" | Low | short |

No dedicated mechanics-breakdown-channel clip surfaced for Willis (weaker source pool than average — flagged honestly).

## New England Patriots — Drake Maye

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=ee2vSqgOjsc | Mechanics-breakdown channel | "Drake Maye Throwing Mechanics Breakdown," #quarterbackmechanics tag | Medium-high | short |
| https://www.youtube.com/watch?v=ioZB1zOachs | Draft-media pro-day compilation | "Drake Maye FULL Pro Day Highlights: Every Throw" (UNC) | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=vdZxWifuNrQ | Pro-day footage | "Drake Maye TOSS'N BOMBS At Pro Day" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=A4KHFzarH_E | Pro-day footage | "Drake Maye's pro day at UNC Chapel Hill" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=X6Wr_rJIq2w | Film-analysis channel | "Drake Maye's Throwing Mechanics vs. the Raiders — Biomechanical Analysis" (in-game, likely broadcast angle + commentary) | Low-medium | long, needs isolation |
| https://www.youtube.com/watch?v=Htc7n-yYFsA | NFL podcast/analysis | "Kurt Warner Evaluates Drake Maye's Throwing Mechanics" — likely talking-head with inserted clips | Low | long, needs isolation |

Note: Maye did not throw at the NFL Combine (per search results), so no combine-workout footage exists — pro day is the main pre-NFL source.

## New York Jets — Geno Smith

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=oz-0-Qx_1c0 | Combine footage | "Geno Smith NFL Combine" (2013) | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=rsZXijY69mg | Team/OTA footage | "Drew Lock, Geno Smith Throwing On First Day Of Seahawks OTAs" | Low-medium | long, needs isolation |
| https://www.youtube.com/watch?v=caZrEN4MY8Q | Game-highlight compilation | "Geno Smith Throwing Dimes 2024" | Low | long, needs isolation |
| https://www.youtube.com/watch?v=Ova20guHZRc | Game-highlight compilation | "Geno Smith Every Throw — Preseason — Jets vs Steelers" | Low | long, needs isolation |
| https://www.youtube.com/watch?v=w40Ld0FfyLg | Game-highlight clip | "Geno Smith AMAZING TD throw in between 3 defenders" | Low | short |

Weakest source pool found so far — no dedicated mechanics-breakdown channel content turned up for Smith. This QB likely needs a second, more targeted sourcing pass (e.g. searching Seahawks-era practice footage) before the dataset relies on him.

## Baltimore Ravens — Lamar Jackson

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=YIlqMpKFhds | NFL Combine broadcast footage | "Every Lamar Jackson Throw During Workout! — NFL Combine Highlights" — likely the same/similar source already used for this project's existing Lamar seed clips per `research_log.md` | Medium-high | long, needs isolation |
| https://www.youtube.com/watch?v=fMb7nRtwtL0 | "Performance Lab of California" (per search summary) | "Lamar Jackson Throwing Mechanics — Performance Lab of California" | Medium-high | short |
| https://www.youtube.com/watch?v=0BfSNlRmWM4 | Mechanics-breakdown channel | "Lamar Jackson Updated Throwing Mechanics Breakdown" | Medium | short |
| https://www.youtube.com/watch?v=rVrM2dZBNDU | Mechanics-breakdown channel | "Lamar Jackson Throwing Motion Breakdown" | Medium | short |
| https://www.youtube.com/watch?v=CfPNXAxTXu8 | Mechanics-breakdown channel | "Lamar Jackson Throwing Mechanics" | Medium | short |
| https://www.youtube.com/watch?v=M_yxB-ZjmAA | Mechanics-breakdown channel | "Lamar Jackson Deep Ball Breakdown" | Medium | short |
| https://www.youtube.com/shorts/q13h2_zdh2o | Shorts, mechanics-focused | "Lamar Jackson's Perfect Throw: Breaking Down the Mechanics!" | Medium | short |

Note: `research_log.md` documents this project already found Lamar's available footage skews wide/broadcast and that the two existing seed clips came from mining NFL/Ravens combine broadcast video — consistent with what turned up here. The "Performance Lab of California" clip is worth prioritizing for verification since it may be a genuinely clean near-side breakdown, distinct from the broadcast-angle problem already documented.

## Cincinnati Bengals — Joe Burrow

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=get6ZMlb7y4 | "Performance Lab of California" (per search summary) | "Joe Burrow Throwing Mechanics — Performance Lab of California" (LSU-era) | High | short |
| https://www.youtube.com/watch?v=LwiNJ_nVzVA | Mechanics-breakdown channel | "Joe Burrow Throwing Mechanics Complete Breakdown," #quarterbackmechanics tag | Medium-high | short |
| https://www.youtube.com/watch?v=bNrJlSkr2dk | Mechanics-breakdown channel | "Joe Burrow Throwing Mechanics Breakdown" (college-era) | Medium | short |
| https://www.youtube.com/watch?v=pyGsPLtHD0Y | Mechanics-breakdown channel | "Joe Burrow Throwing Mechanics" | Medium | short |
| https://www.youtube.com/watch?v=osYNHgUyPgM | Mechanics-breakdown channel | "Joe Burrow 2020 Throwing Mechanics Breakdown" | Medium | short |
| https://www.youtube.com/watch?v=qz1Xq-kIsE8 | Mechanics-breakdown channel | "Joe Burrow Throwing Mechanics And What Makes Him A Great Quarterback" | Medium | short |
| https://www.youtube.com/watch?v=IGU5P9RYf88 | Shorts | "Burrow with a slowmo throw #shorts" | Medium | short |

Good source pool — multiple independent mechanics-breakdown uploads plus one likely on the same "Performance Lab of California" channel already used well elsewhere.

## Cleveland Browns — Deshaun Watson

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=Lo-ZMwm_Plo | "Performance Lab" (per search summary) | "Performance Lab: Deshaun Watson Throw Mechanics Breakdown" (Clemson-era, 2017) | High | short |
| https://www.youtube.com/watch?v=_np2yxIF9U0 | Mechanics-breakdown channel | "Deshaun Watson Throwing Mechanics Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=LuJ1gI1XwoY | Mechanics-breakdown channel | "The All Purpose Quarterback Deshaun Watson — QB Throwing Mechanics" | Medium | short |
| https://www.youtube.com/watch?v=GSifAJNyX6Y | NFL/draft-media pro-day footage | "Clemson Pro Day: Deshaun Watson and Mike Williams Highlights & Mike Mayock's Analysis" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=axg2XQyFe50 | Practice/drill footage | "Deshaun Watson puts on a show during throwing drills" | Low-medium | long, needs isolation |
| https://www.youtube.com/watch?v=lCJoDGWdKew | Team practice footage | "DESHAUN WATSON IS BACK THROWING AT PRACTICE" | Low | long, needs isolation |

## Pittsburgh Steelers — Aaron Rodgers

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=-jhElzcgGOc | "Performance Lab of California" (per search summary) | "Aaron Rodgers Throw Breakdown — Maximize Throw Power — Performance Lab of California" | High | short |
| https://www.youtube.com/watch?v=u3tRz5-Hsuo | "Performance Lab" (per search summary) | "Before and After with Aaron Rodgers — College vs. NFL Throwing Breakdown — Performance Lab" | High | short |
| https://www.youtube.com/watch?v=pNZNHn1OUn8 | Mechanics-breakdown channel | "Aaron Rodgers Throwing Mechanics Breakdown Pt. 2" | Medium-high | short |
| https://www.youtube.com/watch?v=3h-G0Xgg71o | Mechanics-breakdown channel | "Aaron Rodgers Throw Breakdown To Improve Your Wrist Flick" | Medium | short |
| https://www.youtube.com/shorts/8qdatlWXjOw | Shorts | "AARON RODGERS Throwing Motion" | Medium | short |
| https://www.youtube.com/watch?v=krj08Y-AgQQ | Analysis channel | "Aaron Rodgers has A Superior Throwing Motion" | Medium | short |
| https://www.youtube.com/watch?v=YD9vBoL_lA0 | "Performance Lab of California" | "ULTIMATE QB Mechanics Video — Performance Lab of California" — multi-QB compilation (Brady/Brees/Rodgers/Mahomes), so Rodgers' segment needs isolating within it | Medium | long, needs isolation |

Strong source pool — the "Performance Lab" family shows up repeatedly for Rodgers.

## Houston Texans — C.J. Stroud

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=WpfYNvADzSo | "Performance Lab of California" (per search summary) | "CJ Stroud Throwing Mechanics — Elite 11 MVP — Performance Lab of California" | High | short |
| https://www.youtube.com/watch?v=oO0bRzWlO6A | Mechanics-breakdown channel | "CJ Stroud Slow Motion Throwing Mechanics NFL Combine" | High | short |
| https://www.youtube.com/watch?v=63-AT09voHc | Mechanics-breakdown channel | "CJ Stroud Throwing Mechanics Breakdown From NFL Combine" | Medium-high | short |
| https://www.youtube.com/watch?v=VjNh1n_qKYo | Mechanics-breakdown channel | "CJ Stroud Throwing Mechanics Breakdown" | Medium | short |
| https://www.youtube.com/watch?v=LxUYitHvdWw | Mechanics-breakdown channel | "CJ Stroud's Insanely Quick Throwing Motion: The Breakdown" | Medium | short |
| https://www.youtube.com/watch?v=41WFI-ivcCQ | NFL Combine official footage | "C.J. Stroud's FULL 2023 NFL Scouting Combine On Field Workout" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=iOAdShfljtQ | Pro-day footage | "Ohio State's C.J. Stroud throwing drills at Pro Day" | Medium | long, needs isolation |

## Indianapolis Colts — Daniel Jones

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=KiyL8i0-KyA | Mechanics-breakdown channel | "Daniel Jones Throwing Mechanics" | Medium | short |
| https://www.youtube.com/watch?v=Ii2opg5hvJw | Slow-motion clip channel | "Daniel Jones Slow Motion Pass Throw — New York Giants Quarterback" | Medium | short |
| https://www.youtube.com/watch?v=ialF9xWbKww | Mechanics-breakdown channel | "Daniel Jones Throwing Breakdown — Top College Quarterback from Duke" | Medium | short |
| https://www.youtube.com/watch?v=8symuaLxNPo | NFL Combine footage | "Daniel Jones' 2019 Combine Workout" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=hhnS0TuDw-E | Game-highlight clip | "Daniel Jones makes an incredible throw" | Low | short |
| https://www.youtube.com/watch?v=tkjOnKMGN-k | Game-highlight compilation | "Every Daniel Jones Throw vs The Bengals" | Low | long, needs isolation |

## Jacksonville Jaguars — Trevor Lawrence

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=2CoqSIdQ8jk | "Performance Lab" (per search summary) | "Performance Lab: Trevor Lawrence Mechanics Breakdown" | High | short |
| https://www.youtube.com/watch?v=ymiFKkhmx3k | Mechanics-breakdown channel | "Trevor Lawrence Throwing Mechanics Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=7d75xE2HGG4 | Mechanics-breakdown channel | "Trevor Lawrence 2023 Throwing Mechanics Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=NDVJHPRF-fE | Mechanics-breakdown channel | "Trevor Lawrence Throwing Mechanics — Clemson Quarterback" | Medium | short |
| https://www.youtube.com/watch?v=VdNTCVF4qNI | Slow-motion clip channel | "Trevor Lawrence Slow Motion Pass" | Medium | short |
| https://www.youtube.com/watch?v=w9MYx3QUBGM | Draft-media pro-day coverage | "Trevor Lawrence Pro Day Highlights and Analysis [WATCH 65-YARD DIME] — CBS Sports HQ" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=t298eGa3o38 | Draft-media pro-day compilation | "Trevor Lawrence FULL Pro Day Highlights: Every Throw" | Medium | long, needs isolation |

## Tennessee Titans — Cam Ward

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=pCer54U6CSE | "Quarterback Mechanics" channel | "Cam Ward Pro Day Throwing Mechanics Breakdown — Quarterback Mechanics" | Medium-high | short |
| https://www.youtube.com/watch?v=6yHLI7Uv3ss | "Quarterback Mechanics" channel | "Cam Ward NFL Debut Throwing Mechanics — Quarterback Mechanics" | Medium | short |
| https://www.youtube.com/watch?v=QIZduLtmUws | Draft-media (Pro Football Talk) | "Cam Ward shines with 'effortless' throws at his Miami Pro Day" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=nzYq2Gd8AI0 | Draft-media pro-day compilation | "Cam Ward 'FULL' Miami Pro Day Highlights + INSANE Throws" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=wcgrkxtey3o | Local sports coverage | "Cam Ward puts on show at University of Miami pro day" | Medium | long, needs isolation |
| https://www.youtube.com/shorts/dmyYeVq5wHM | Shorts, pro-day footage | "Cam Ward has got an arm (Miami Hurricanes Pro Day)" | Medium | short |

## Kansas City Chiefs — Patrick Mahomes

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/shorts/DgyXQKTiUoQ | Mechanics-breakdown Shorts | "Patrick Mahomes Slow Motion 62mph Throw (The Fastest In History) #quarterbackmechanics" — likely the same/similar clip already used as a Mahomes seed clip per `research_log.md` (`clip1_qbperformancelab_62mph`) | High | short |
| https://www.youtube.com/shorts/ZiHlwHXj-24 | Mechanics-breakdown Shorts | "Patrick Mahomes 80 Yard Throw From Pro Day (BEST VIEW) #patrickmahomes #quarterbackmechanics" | High | short |
| https://www.youtube.com/watch?v=hZdpR93uggw | Pro-day footage | "Pat Mahomes: 80 Yard Throw at Pro Day (BEST VIEW)" — non-Shorts, likely same source material as above | Medium-high | short |
| https://www.youtube.com/watch?v=7KzR2q6qA9c | Mechanics-breakdown channel | "Patrick Mahomes Throwing Mechanics Breakdown" | Medium | short |
| https://www.youtube.com/watch?v=MjYuxyT21zY | Mechanics-breakdown channel | "Patrick Mahomes Throwing Mechanics — How To Drive Off The Back Leg To Increase Throw Power" | Medium | short |
| https://www.youtube.com/watch?v=6KrTPRDfnGs | Mechanics-breakdown channel | "Patrick Mahomes 2020 Throwing Mechanics Breakdown" | Medium | short |
| https://www.youtube.com/watch?v=Ppeu6Mm4cT8 | NFL Combine official footage | "Patrick Mahomes' 2017 Combine Workout" | Medium | long, needs isolation |

Note: this project already has two seed Mahomes clips per `research_log.md` (`clip1_qbperformancelab_62mph`, `clip2_nfl_2017combine`) with 100% pose-detection rates — the first two rows above likely overlap with the already-used clip1; worth checking against `data/provenance.csv` before re-downloading.

## Las Vegas Raiders — Kirk Cousins

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=lUfg1n_qGAo | Mechanics-breakdown channel | "Kirk Cousins Throwing Breakdown — Future Minnesota Vikings Quarterback" (2018) | Medium | short |
| https://www.youtube.com/watch?v=ALa3Zm8d4rA | Slow-motion clip channel | "Kirk Cousins & Atlanta Falcons 4K SUPER SLOW MOTION..." | Medium | short |
| https://www.youtube.com/watch?v=Ou2E0ND4UI4 | Highlight/mechanics hybrid | "Kirk Cousins Throwing Mechanics 500+ Passing Yards — Falcons Highlights" — likely a highlight compilation despite the "mechanics" title | Low-medium | long, needs isolation |
| https://www.youtube.com/watch?v=z_MeJA_Bnpo | Analysis channel ("The QB School") | "The Best Throw Of Kirk Cousins Career" | Low-medium | short |

Weak source pool for a clean near-side single-throw clip — most results are either old (2018 pre-draft-style breakdown) or highlight-reel style. This QB likely needs a follow-up search pass focused on Vikings/Falcons practice-day or OTA footage.

## Los Angeles Chargers — Justin Herbert

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=nO4J-WMQ8VI | "Performance Lab of California" (per search summary) | "Dual-Threat Quarterback Justin Herbert — Throwing Breakdown — Performance Lab of California" | High | short |
| https://www.youtube.com/watch?v=aXv6jKSDcHg | Mechanics-breakdown channel | "Justin Herbert Throwing Mechanics Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=cx1OU5HAPUg | "Quarterback Mechanics" channel | "Justin Herbert Throwing Mechanics Breakdown — Quarterback Mechanics" (2025) | Medium-high | short |
| https://www.youtube.com/watch?v=6AAgkVtatUc | Mechanics-breakdown channel | "Justin Herbert Throwing Mechanics 2021" | Medium | short |
| https://www.youtube.com/watch?v=q0fZePnYHr0 | "Gurusfilmroom" channel | "JUSTIN HERBERT THROWING MOTION — Gurusfilmroom" | Medium | short |
| https://www.youtube.com/watch?v=Hr5dMZgNj4g | Draft-media pro-day compilation | "Justin Herbert's FULL Pro Day Highlights" (Oregon) | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=TPVOP9fvHkU | Slow-motion compilation | "8 Minutes Of Relaxing Justin Herbert Throws — LA Chargers" (2025 training camp, reportedly slowed to 120fps per search summary) | Medium | long, needs isolation |

## Denver Broncos — Bo Nix

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=Rvi4hOx5JNM | Draft-media pro-day compilation | "Bo Nix's FULL Pro Day Highlights: Every Throw" (Oregon) | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=lmp4PdN8H40 | NFL Combine official footage | "Bo Nix's FULL 2024 NFL Scouting Combine On Field Workout" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=PajflHkoLBE | Draft-media combine footage | "EVERY THROW: Bo Nix vs JJ Mccarthy GOING BOMB FOR BOMB — 2024 NFL Combine QB's Highlights" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=1Duu5vTcdtM | Draft-media (Pro Football Talk) | "Examining JJ McCarthy, Bo Nix, Michael Penix Jr. throws at Combine" | Low-medium | long, needs isolation |
| https://www.youtube.com/watch?v=Xt4g_V9eq3M | Local/fan coverage | "Bo Nix - Oregon Pro Day Reactions" | Low | long, needs isolation |

No dedicated slow-motion mechanics-breakdown-channel clip surfaced for Nix — the QB film-breakdown channels that did turn up ("QB Film Breakdown" style) analyze in-game tape with commentary/graphics rather than a clean single throw, so I excluded those as likely disqualifying (overlays/cuts). Flagged as a weaker source pool.

## Dallas Cowboys — Dak Prescott

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=SAenOXqDzlQ | Mechanics-breakdown channel | "Dak Prescott Throwing Mechanics Breakdown" (2020) | Medium-high | short |
| https://www.youtube.com/watch?v=jdJqvoKCHLo | "Performance Lab" (per search summary, 2017) | "Dak Prescott Throw Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=OKIJNAJC0-E | Slow-motion clip | "#Cowboys Dak Prescott with the slow motion" | Medium | short |
| https://www.youtube.com/watch?v=hAIYs6tDcbA | NFL Combine footage | "Dak Prescott (Mississippi State, QB) — 2016 NFL Combine..." | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=eoGJDebZtA0 | Combine footage | "Dak Prescott 2016 Throwback NFL Scouting Combine Highlights" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=7518jybfYOQ | Analysis channel | "Does Dak Prescott Have New Throwing Mechanics? — Blogging the Boys" | Low-medium | long, needs isolation |

## New York Giants — Jaxson Dart

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=U45tFkwR_Jc | Mechanics-breakdown channel | "Jaxson Dart Throwing Mechanics Breakdown — How To Increase Your Throwing Power #quarterbackmechanics" | High | short |
| https://www.youtube.com/watch?v=kzcvB6Am_-M | Local/draft-media pro-day coverage | "Jaxson Dart's throwing session highlights Ole Miss Pro Day" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=n3YC73w1mQs | Combine footage | "Jaxson Dart Throwing DARTS At The Combine" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=XYSpio7qRpU | NFL Network analysis | "Inside Ole Miss QB Jaxson Dart's session at 2025 NFL Combine — Chris Simms Unbuttoned" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=MnqKcOPAloc | Local/draft-media coverage | "Former Ole Miss QB Jaxson Dart on Pro Day in Oxford" | Medium | long, needs isolation |

## Philadelphia Eagles — Jalen Hurts

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/shorts/0mSaVgxdHMI | Mechanics-breakdown Shorts | "Jalen Hurts Slow Motion Throwing Mechanics 4 Different Angles #quarterbackmechanics" | High | short |
| https://www.youtube.com/watch?v=iGVp-4ZzkOg | Mechanics-breakdown channel | "Jalen Hurts Throwing Mechanics Breakdown #quarterbackmechanics" | Medium-high | short |
| https://www.youtube.com/watch?v=LwzsfFyD5tM | Mechanics-breakdown channel | "Jalen Hurts Throwing Mechanics Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=NW9iNAOiWXQ | Mechanics-breakdown channel | "Jalen Hurts Deep Ball Throwing Mechanics — How To Throw A Football #quarterbackmechanics" | Medium | short |
| https://www.youtube.com/watch?v=F7C2ygAbLPs | Film-study channel | "Jalen Hurts throwing mechanics 2022 vs 2021 direct comparison — Film Study with Eye Test Eastwood" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=S1ZyvNzrezo | Draft-media pro-day compilation | "Jalen Hurts & CeeDee Lamb FULL Pro Day Highlights at Oklahoma" | Medium | long, needs isolation |

## Washington Commanders — Marcus Mariota (current starter; see ambiguity note above — Jayden Daniels is the normal starter)

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=praimUqT6PE | "Performance Lab" (per search summary, 2017) | "Marcus Mariota Throw Breakdown — Performance Lab" | High | short |
| https://www.youtube.com/watch?v=LGkJ55nNq_A | NFL Combine footage | "Marcus Mariota Combine Throws" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=sWCL0czoo2A | Pro-day footage | "Marcus Mariota Oregon Pro Day highlights" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=eevqOtGxAjM | Combine footage | "Marcus Mariota (Oregon, QB) 2015 NFL Combine highlights" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=D9MNVZHBxTs | Combine footage | "Marcus Mariota NFL Combine" | Low-medium | long, needs isolation |

Sparse pool overall (mostly a decade-old combine/pro-day cycle plus one older Performance Lab breakdown); no recent NFL-career mechanics content turned up. If Jayden Daniels returns as starter before this clip is used, he likely has a stronger/more recent source pool and should be re-checked.

## Chicago Bears — Caleb Williams

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=V40HqlsVhCQ | Mechanics-breakdown channel | "Caleb Williams Pro Day Throwing Mechanics Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=fAwsvWgN5MU | "Quarterback Mechanics" channel | "Caleb Williams Throw Mechanics Breakdown — Quarterback Mechanics" | Medium-high | short |
| https://www.youtube.com/watch?v=9t9apY4_g6U | Mechanics-breakdown channel | "New Caleb Williams Updated Throwing Motion Breakdown — Heisman Trophy Season" | Medium | short |
| https://www.youtube.com/watch?v=OI3WTTC-r90 | Mechanics-breakdown channel | "Caleb Williams Throwing Mechanics Breakdown From Week 6 Highlights" | Medium | short |
| https://www.youtube.com/watch?v=PhnAX0PVHmU | Draft-media pro-day compilation | "Caleb Williams 'FULL' USC Pro Day Highlights (Future #1 Overall Pick)" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=q-_8TSFpz0I | Local/draft-media coverage | "HIGHLIGHTS: USC QB Caleb Williams Pro Day throwing session" | Medium | long, needs isolation |

## Detroit Lions — Jared Goff

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=--xjU0Zatvc | Mechanics-breakdown channel | "Jared Goff Throwing Mechanics Breakdown" (2020) | Medium-high | short |
| https://www.youtube.com/watch?v=DalbsyK59K8 | Mechanics-breakdown channel | "Jared Goff Throwing Mechanics" (2017) | Medium | short |
| https://www.youtube.com/watch?v=-u7GMHPatmo | Slow-motion clip channel | "Jared Goff Slow Motion Pass Throw Quarterback NFL Rams" | Medium | short |
| https://www.youtube.com/watch?v=oagfYhvOB6I | NFL Combine footage | "Jared Goff (California, QB) — 2016 NFL Combine Highlights" | Medium | long, needs isolation |

Weaker pool for Goff — no recognizable "Performance Lab"-style clip turned up, and most other results are game-highlight compilations that were excluded as likely disqualifying.

## Green Bay Packers — Jordan Love

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=vvfHUabPl6w | Mechanics-breakdown channel | "Jordan Love Throwing Mechanics Breakdown" (2020) | Medium-high | short |
| https://www.youtube.com/watch?v=FVT4DQnbJWs | Mechanics-breakdown channel | "Jordan Love Throwing Mechanics" | Medium | short |
| https://www.youtube.com/watch?v=G9zd92rH6I8 | Mechanics-breakdown channel | "Jordan Love Throwing Mechanics 2024 In Packers..." | Medium | short |
| https://www.youtube.com/watch?v=iONQVisM9kE | NFL Combine footage | "QB Jordan Love's Full NFL Combine Highlights - Green Bay Packers" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=Ab609DJcO-4 | Team practice footage | "Jordan Love Throwing At Packers OTA's" | Low-medium | long, needs isolation |

## Minnesota Vikings — Kyler Murray

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=j5fyOG2xptY | Mechanics-breakdown channel | "Kyler Murray Throwing Mechanics Breakdown" (2019) | Medium-high | short |
| https://www.youtube.com/watch?v=WhTg0KHmYNw | Mechanics-breakdown channel | "Kyler Murray 2020 Throwing Mechanics Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=5QMetMuDA_Q | Mechanics-breakdown channel | "Kyler Murray Deep Throw Breakdown" | Medium | short |
| https://www.youtube.com/watch?v=W5Ne_6wpGeI | "Performance Lab" (per search summary) | "Russell Wilson vs. Kyler Murray Analysis — QB Throwing Comparison — Performance Lab" — comparison video, Murray's segment needs isolating | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=ukpqbSXtVLU | Pro-day footage | "Every Throw from Kyler Murray's Pro Day" (Oklahoma) | Medium | long, needs isolation |

Note: Murray did not throw at the NFL Combine (per search results), so pro day is the only pre-NFL workout source.

## Atlanta Falcons — Michael Penix Jr. (current starter; see ambiguity note above — Tua Tagovailoa started Weeks 1–2)

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=SMoWqRrmZf0 | Mechanics-breakdown channel | "Michael Penix Highlights Throwing Motion Breakdown And Analysis #quarterbackmechanics" | Medium-high | short |
| https://www.youtube.com/watch?v=yKqeHSY9NW0 | Mechanics-breakdown channel | "Michael Penix Jr. Throwing Motion — 3 Keys to Throw with Force" | Medium-high | short |
| https://www.youtube.com/watch?v=Ln_vGtU-HEI | Draft-media pro-day compilation | "Michael Penix Jr. Full Pro Day Highlights: Every Throw" (Washington) | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=IuXZmH_C_JU | Draft-media pro-day compilation | "EVERY THROW: Michael Penix INSANE FULL NFL Pro Day Debut" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=1Duu5vTcdtM | Draft-media (Pro Football Talk) | "Examining JJ McCarthy, Bo Nix, Michael Penix Jr. throws at Combine" | Low-medium | long, needs isolation |

## Carolina Panthers — Bryce Young

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=BCa8JiPwSzE | "Performance Lab of California" (per search summary) | "Bryce Young Throwing Mechanics — Quarterback Breakdown — Performance Lab of CA" | High | short |
| https://www.youtube.com/watch?v=DKFPYAEH1Fc | "Performance Lab" (per search summary) | "Bryce Young Throwing Breakdown - Performance Lab" | High | short |
| https://www.youtube.com/watch?v=PaN7HM3O5JQ | Mechanics-breakdown channel | "Bryce Young Pro Day Throwing Mechanics Breakdown #bryceyoung #proday" | Medium-high | short |
| https://www.youtube.com/watch?v=553L524J4Ac | Mechanics-breakdown channel | "BRYCE YOUNG Throwing Mechanics" | Medium | short |
| https://www.youtube.com/watch?v=TkjvZ3KNQgI | Local/draft-media coverage | "Watch Bryce Young throw 43 times at Alabama Pro Day 2023" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=6xcvGMnUho8 | Slow-motion clip channel | "Bryce Young Slow Motion Pass" | Medium | short |

Note: Young did not throw at the NFL Combine (per search results) — Alabama pro day is the pre-NFL source.

## New Orleans Saints — Tyler Shough

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=eMf5Y_i00F0 | Fan/clip channel | "A clip of Louisville QB Tyler Shough from the combine has gone viral" | Low-medium | short |
| https://www.youtube.com/watch?v=HnDD9buJdVU | Combine footage | "Louisville QB Tyler Shough at the 2025 NFL Scouting Combine" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=OYfDPOPeYhQ | Pro-day footage | "Tyler Shough and U of L football players go through Pro Day" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=s6qae0rlfKc | Training-camp footage | "Every Tyler Shough Throw from Day 8 of Saints Training Camp" | Low | long, needs isolation |
| https://www.youtube.com/watch?v=o0L4MUCOJqU | Game-highlight clip | "This Throw By Tyler Shough" | Low | short |

Weak pool — no dedicated slow-motion mechanics-breakdown clip found at all for Shough; only 5 candidates, honestly listed, and even those lean toward medium/low confidence. This QB should be prioritized for a follow-up sourcing pass.

## Tampa Bay Buccaneers — Baker Mayfield

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=VGOWhfv4tNc | "Performance Lab of California" (per search summary) | "A Deep Look Into Baker Mayfield's Throwing Mechanics — Performance Lab of California" | High | short |
| https://www.youtube.com/watch?v=UDEIYZGGiII | "Performance Lab of CA" (per search summary) | "Philip Rivers & Baker Mayfield Throwing Mechanics — Performance Lab of CA" — comparison video, needs isolating Mayfield's segment | Medium-high | long, needs isolation |
| https://www.youtube.com/watch?v=pZPxY7SJPlI | Mechanics-breakdown channel | "Baker Mayfield Throwing Mechanics Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=9AiYYUY9mls | Mechanics-breakdown channel | "Baker Mayfield Throwing Mechanics" (2017) | Medium | short |
| https://www.youtube.com/watch?v=wXKbSYuB0L8 | Mechanics-breakdown channel | "Baker Mayfield Throwing Mechanics Breakdown #quarterbackmechanics" | Medium | short |
| https://www.youtube.com/watch?v=0YsfPz2E26M | Pro-day footage | "OU Pro Day 2018: Baker Mayfield" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=sJMmXE6n02o | Training-camp footage | "Baker Mayfield Training Camp Throws Breakdown" | Low-medium | long, needs isolation |

## Arizona Cardinals — Jacoby Brissett

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=Xi5aj0MWSzQ | Slow-motion clip channel | "Jacoby Brissett Slow Motion Pass Throw Quarterback NFL Colts" | Medium | short |
| https://www.youtube.com/watch?v=yi6GOLYMv7I | Coaching-analysis channel | "Jacoby Brissett Film Breakdown With Patriots QB Coach T.C...." | Low-medium | long, needs isolation |

Weakest source pool of all 32 QBs. No dedicated mechanics-breakdown-channel content, no combine/pro-day workout compilation, and no obvious "Performance Lab"-style clip turned up in two search passes (I ran a third, NC-State-specific search and it returned only college game highlights, no pro-day/combine workout footage). Only 2 usable candidates found — listed honestly rather than padded. This QB needs a dedicated follow-up sourcing effort (e.g., searching his 2016 pro day at NC State directly by date, or Patriots/Colts/Browns-era practice footage) before he can be treated as adequately sourced.

## Los Angeles Rams — Matthew Stafford

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=14wXhy5ECEE | Mechanics-breakdown channel | "Matthew Stafford Throwing Mechanics Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=BIMWzyD343o | Mechanics-breakdown channel | "Matthew Stafford Throwing Mechanics Breakdown" (2021) | Medium-high | short |
| https://www.youtube.com/watch?v=SsEN3FCV7fU | Mechanics-breakdown channel | "Matthew Stafford Throwing Motion Breakdown" (2022) | Medium | short |
| https://www.youtube.com/watch?v=Om1y9IvGFbQ | Mechanics-breakdown channel | "Matthew Stafford Throwing Mechanics On Deep Ball" (2017) | Medium | short |
| https://www.youtube.com/watch?v=ys3z4S1Nbpk | Mechanics-breakdown channel | "Breaking Down Matthew Stafford's Throwing Mechanics" | Medium | short |
| https://www.youtube.com/watch?v=hBFN6oNSae8 | Combine footage | "Matthew Stafford 2009 combine clip" — note: search summary says Stafford warmed up but did not participate in several throwing drills at his actual combine, so verify this clip actually shows throws | Low-medium | long, needs isolation |

## San Francisco 49ers — Brock Purdy

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=fNvYgXF6guU | Mechanics-breakdown channel | "Brock Purdy Throwing Motion Breakdown #quarterback" | Medium-high | short |
| https://www.youtube.com/watch?v=m9yXJROJBL8 | Mechanics-breakdown channel | "Brock Purdy Throwing Mechanics — How To Be An NFL Quarterback #quarterbackmechanics" | Medium-high | short |
| https://www.youtube.com/watch?v=fJkcuXU4RKI | Team practice footage | "#49ers Brock Purdy throwing in slow motion at practice" | Medium | short |
| https://www.youtube.com/watch?v=hFZemDBXhJg | Analysis channel | "BIG Throw Brock: How Brock Purdy EXCELS In Throwing..." | Medium | short |
| https://www.youtube.com/watch?v=IQXfU3EGz_s | NFL Combine footage | "Brock Purdy (Iowa State, QB) 2022 NFL Combine Highlights" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=W6uNo4QcU6w | Feature/analysis piece | "Brock Purdy's offseason training uses motion capture data analysis to improve his throwing motion" — potentially very relevant to this project's methodology, worth watching even if not clip-worthy | Low-medium | long, needs isolation |

## Seattle Seahawks — Sam Darnold

| URL | Source / Channel | Description | Confidence | Clip type |
|---|---|---|---|---|
| https://www.youtube.com/watch?v=oehb8dzrQBg | "Performance Lab" (per search summary) | "USC QB Sam Darnold's Throwing Mechanics — Heisman Favorite — Performance Lab" | High | short |
| https://www.youtube.com/watch?v=-N6Kmim4kl0 | Mechanics-breakdown channel | "Sam Darnold Throwing Mechanics Breakdown" | Medium-high | short |
| https://www.youtube.com/watch?v=y9Zf3HedNlY | Slow-motion clip channel | "Sam Darnold Slow Motion Pass Throw Quarterback Jets NFL" | Medium | short |
| https://www.youtube.com/watch?v=hRcVAU-zJQU | Local/draft-media coverage | "Sam Darnold shows off throws in the rain at USC Pro Day" (note: rain — may affect footage quality/visibility, verify) | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=I_qM-Dtb51k | NFL-produced pro-day coverage | "Sam Darnold's Pro Day Highlights in the Rain & Analysis — NFL" | Medium | long, needs isolation |
| https://www.youtube.com/watch?v=QQm2IWDLfO4 | Combine footage | "Sam Darnold NFL Combine" | Medium | long, needs isolation |

---

## Summary of source-pool quality (for the human doing verification)

**Strong pools (multiple high/medium-high confidence dedicated mechanics-breakdown clips found):** Josh Allen, Joe Burrow, Deshaun Watson, Aaron Rodgers, C.J. Stroud, Trevor Lawrence, Justin Herbert, Jalen Hurts, Bryce Young, Baker Mayfield, Sam Darnold, Jaxson Dart, Patrick Mahomes (though check for overlap with clips already in this project's dataset).

**Adequate pools (some good candidates, more reliance on pro-day/combine long-form video needing timestamp isolation):** Lamar Jackson, Cam Ward, Daniel Jones, Dak Prescott, Caleb Williams, Jordan Love, Kyler Murray, Michael Penix Jr., Matthew Stafford, Brock Purdy, Drake Maye.

**Weak pools — flagged for follow-up sourcing before relying on them:** Malik Willis (no dedicated breakdown-channel clip), Geno Smith (no dedicated breakdown-channel clip at all, mostly game highlights), Kirk Cousins (mostly old pre-draft content or highlight reels), Bo Nix (no clean slow-motion breakdown clip found), Marcus Mariota (only one recent-ish breakdown, rest is decade-old combine content — also may be a temporary starter, see ambiguity note), Jared Goff (no "Performance Lab"-style clip found), Tyler Shough (only 5 candidates total, none high confidence), **Jacoby Brissett (only 2 candidates found — weakest of all 32; needs a dedicated follow-up search)**.

## Explicit reminders for whoever verifies these next
1. Nothing here has been watched. Titles/channel names can be wrong, misleading, or (per this project's own research log) technically compliant while still hiding a loop, a showman edit, or a broadcast cut mid-throw.
2. "Performance Lab of California" / "Performance Lab" / "QB Performance Lab" appeared repeatedly across many QBs' search results but I could not confirm whether these are all the same channel, and whether any of them is the exact `@qbperformancelab` channel this project has already used successfully for Allen, Mahomes, and Lamar clips. Confirm channel identity before treating "same channel as before" as a quality signal.
3. Long-form combine/pro-day videos need the exact usable throw window isolated — and per `research_log.md`'s ad-insertion finding, browser-noted timestamps should not be trusted; re-locate the window from the downloaded file itself.
4. Every clip that survives verification still needs a `data/provenance.csv` entry with source URL and license/usage note per `data_criteria.md` before use.
