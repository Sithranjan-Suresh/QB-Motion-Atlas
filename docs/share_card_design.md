# Shareable Results Card (task 133)

A single 1200x630px PNG (the standard social-preview/OG-image aspect ratio,
so it renders cleanly if pasted into iMessage/Slack/Twitter without
cropping), rendered server-side with Pillow -- no headless browser needed,
since the layout is simple typography + basic shapes over a solid
background, no video frames or copyrighted imagery.

## Layout (top to bottom)

1. **Header**, small caps, top-left: `QB MOTION ATLAS` -- the product name,
   not a logo/wordmark image.
2. **"Your closest match"** label, centered, small/muted.
3. **QB name**, centered, large bold -- the single biggest element on the
   card, since it's the headline result.
4. **Similarity percentage**, centered, even larger -- the number people
   actually screenshot this for.
5. **Confidence badge**, centered, a small pill (colored per
   `PhaseBreakdownPanel`'s existing high/medium/low convention, for visual
   consistency with the web results page).
6. **Key stats row**, near the bottom: up to 3 per-phase results (phase
   name + matched QB), if `phase_results` has any -- the "your stride
   resembles X, your release resembles Y" hook, condensed. Omitted
   entirely (not left blank) when there's no per-phase data yet, same
   honest-gap convention as the web UI.
7. **Footer**, small, bottom-right: the product name -- not a fabricated
   URL, since this project isn't deployed yet (tasks 90-95 are blocked on
   the user's own cloud accounts); swap in the real deployed URL once one
   exists.

## Colors

Dark background (`#111827`, matching the web UI's `bg-gray-900` buttons)
with white/light-gray text -- consistent with the rest of the app's
minimal black-on-white-and-gray palette, just inverted for a card that's
meant to stand out against a chat thread's white background.

## What this doesn't do

No video frame, skeleton overlay, or reference-clip imagery on the card --
keeping it text/stat-only sidesteps any question about redistributing
copyrighted reference footage in a shareable image (the same reasoning
behind SyncedComparisonView rendering the matched QB as skeleton-only, not
video), and keeps the card fast to generate (no video decode needed).
