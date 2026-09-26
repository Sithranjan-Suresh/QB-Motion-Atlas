"""Reference-clip video-overlay eligibility (task A2, see docs/research_log.md's
2026-09-26 "real video vs. skeleton-only" entry for the full reasoning).

Reference clips are downloaded YouTube footage under a "non-commercial
research/portfolio use" understanding for internal pose-analysis, not for
redistributing the source video to visitors of a deployed app. Streaming
the actual clip back is only done for clips sourced from an individual
creator's coaching-breakdown channel or a fan re-upload -- lower-profile,
not the kind of content rightsholders run automated fingerprinting against.
Clips sourced from an official league/team broadcast channel (the kind of
content automated content-ID systems are specifically built to catch,
regardless of a deployment's traffic) stay skeleton-only, no exception.

This is a text classifier over data/provenance.csv's already-written
license_note, not a new field to keep in sync by hand -- "official" in a
license note ("NFL official YouTube channel", "Baltimore Ravens official
YouTube channel") is exactly the phrasing already used for broadcast-
sourced clips throughout provenance.csv.
"""

from __future__ import annotations

import os

# Global kill-switch (task A5): set to "false" to force skeleton-only for
# every reference clip regardless of source, e.g. after a takedown notice,
# without a code change.
_ENV_FLAG = "REFERENCE_VIDEO_OVERLAY_ENABLED"


def is_video_overlay_eligible(license_note: str) -> bool:
    if os.environ.get(_ENV_FLAG, "true").lower() == "false":
        return False
    return "official" not in license_note.lower()
