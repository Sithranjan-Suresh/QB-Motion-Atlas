"""Batch-download the candidate clips listed in docs/qb_candidate_clips.md
(Agent 1's research pass) using a real YouTube session's cookies, to get
around the datacenter-IP bot-detection block documented in
docs/research_log.md (2026-09-25 entries).

This does NOT add anything to data/raw/ or data/provenance.csv directly --
per docs/data_criteria.md, clip selection is "applied by eye," and this
project has already been burned twice (research_log.md's 2026-09-24
"gold-label prep" entry) by trusting a title/thumbnail screen instead of a
full frame-by-frame review. This script's job is narrower: download a
curated, prioritized subset into a staging area and generate a contact-
sheet montage per clip so that review is fast, not to make the accept/
reject call itself.

Usage:
    python -m pipeline.run_candidate_download --cookies /path/to/cookies.txt
    python -m pipeline.run_candidate_download --cookies cookies.txt --dry-run
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

CANDIDATES_DOC = Path(__file__).resolve().parent.parent / "docs" / "qb_candidate_clips.md"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "candidates_staging"

# This container's outbound HTTPS goes through a re-terminating proxy (see
# /root/.ccr/README.md); yt-dlp's bundled `certifi` store doesn't trust that
# proxy's CA by default, which breaks its own challenge-solver-script
# download (not the video download itself). setup_environment() below
# appends the proxy's CA to certifi's bundle once, in place, rather than
# disabling verification.
_PROXY_CA_BUNDLE = Path("/root/.ccr/ca-bundle.crt")


def setup_environment() -> dict:
    """Returns a subprocess environment with the proxy CA trusted (Node) and
    patches yt-dlp's own certifi bundle in place if this container's proxy
    CA bundle is present and not already trusted (idempotent -- checks
    before appending, safe to call every run)."""
    env = dict(os.environ)
    if _PROXY_CA_BUNDLE.exists():
        env["NODE_EXTRA_CA_CERTS"] = str(_PROXY_CA_BUNDLE)
        env["SSL_CERT_FILE"] = str(_PROXY_CA_BUNDLE)
        env["REQUESTS_CA_BUNDLE"] = str(_PROXY_CA_BUNDLE)

        try:
            import certifi

            certifi_path = Path(certifi.where())
            proxy_ca_text = _PROXY_CA_BUNDLE.read_text()
            if proxy_ca_text.strip() not in certifi_path.read_text():
                with certifi_path.open("a") as f:
                    f.write("\n" + proxy_ca_text)
        except ImportError:
            pass
    return env

# Matches "## <Team> — <QB Name>" or "## <Team> — <QB Name> (current starter; ...)"
_HEADING_RE = re.compile(r"^## .+? — (.+?)(?:\s*\(.*\))?$")
_ROW_RE = re.compile(
    r"^\|\s*(https://www\.youtube\.com/(?:watch\?v=|shorts/)\S+?)\s*\|"
    r"\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(High|Medium-high|Medium|Low-medium|Low)\s*\|"
    r"\s*(short|long, needs isolation)\s*\|$"
)


@dataclass
class Candidate:
    qb_name: str
    url: str
    source: str
    description: str
    confidence: str
    clip_type: str


def _slugify(name: str) -> str:
    name = name.lower().replace(".", "").replace("'", "")
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    return name


def parse_candidates(doc_path: Path = CANDIDATES_DOC) -> list[Candidate]:
    """Parses docs/qb_candidate_clips.md's per-QB tables into Candidate rows.
    Skips the summary section at the bottom (no table rows there matching
    _ROW_RE, so nothing extra to special-case)."""
    candidates: list[Candidate] = []
    current_qb: str | None = None

    for line in doc_path.read_text().splitlines():
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            current_qb = _slugify(heading_match.group(1))
            continue

        row_match = _ROW_RE.match(line)
        if row_match and current_qb:
            url, source, description, confidence, clip_type = row_match.groups()
            candidates.append(Candidate(current_qb, url, source, description, confidence, clip_type))

    return candidates


def select_candidates(
    candidates: list[Candidate],
    confidence_tiers: set[str],
    clip_types: set[str],
    limit_per_qb: int,
) -> list[Candidate]:
    """Prioritizes clean, high-signal candidates over raw volume -- a
    prioritized 2-per-QB "short" + "High"/"Medium-high" subset, by default,
    rather than every row in the document. See this module's docstring on
    why quantity isn't the goal here."""
    selected: list[Candidate] = []
    per_qb_count: dict[str, int] = {}

    for candidate in candidates:
        if candidate.confidence not in confidence_tiers:
            continue
        if candidate.clip_type not in clip_types:
            continue
        if per_qb_count.get(candidate.qb_name, 0) >= limit_per_qb:
            continue
        selected.append(candidate)
        per_qb_count[candidate.qb_name] = per_qb_count.get(candidate.qb_name, 0) + 1

    return selected


def _clip_slug(url: str) -> str:
    video_id = url.rstrip("/").split("/")[-1].split("=")[-1]
    return video_id


def download_clip(candidate: Candidate, cookies_path: Path, out_dir: Path) -> tuple[bool, str, Path | None]:
    """Downloads one candidate via yt-dlp. Returns (success, message, video_path)."""
    qb_dir = out_dir / candidate.qb_name
    qb_dir.mkdir(parents=True, exist_ok=True)
    slug = _clip_slug(candidate.url)
    output_template = str(qb_dir / f"{slug}.%(ext)s")

    result = subprocess.run(
        [
            "yt-dlp",
            "--js-runtimes",
            "node",
            "--remote-components",
            "ejs:github",
            "--cookies",
            str(cookies_path),
            "--no-playlist",
            "-f",
            "best[height<=720][ext=mp4]/best[height<=720]/best",
            "-o",
            output_template,
            candidate.url,
        ],
        capture_output=True,
        text=True,
        timeout=180,
        env=setup_environment(),
    )

    if result.returncode != 0:
        return False, result.stderr.strip().splitlines()[-1] if result.stderr else "unknown yt-dlp failure", None

    downloaded = list(qb_dir.glob(f"{slug}.*"))
    downloaded = [p for p in downloaded if p.suffix != ".jpg"]
    if not downloaded:
        return False, "yt-dlp reported success but no output file found", None
    return True, "ok", downloaded[0]


def generate_contact_sheet(video_path: Path, out_path: Path, cols: int = 6, rows: int = 6) -> bool:
    """ffmpeg tiled-frame montage for fast eyeball QC (the same technique
    that caught the showman-windup and looped-Short problems in
    research_log.md's 2026-09-24 entry) -- one image instead of scrubbing
    the full video."""
    n_frames = cols * rows
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"select='not(mod(n\\,ceil(n_frames/{n_frames})))',tile={cols}x{rows}",
            "-frames:v",
            "1",
            "-vsync",
            "vfr",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode == 0 and out_path.exists()


def run(
    cookies_path: Path,
    confidence_tiers: set[str],
    clip_types: set[str],
    limit_per_qb: int,
    sleep_seconds: float,
    out_dir: Path,
    dry_run: bool,
) -> None:
    all_candidates = parse_candidates()
    selected = select_candidates(all_candidates, confidence_tiers, clip_types, limit_per_qb)

    print(f"Parsed {len(all_candidates)} total candidates from {CANDIDATES_DOC.name}")
    print(f"Selected {len(selected)} for download (tiers={sorted(confidence_tiers)}, "
          f"types={sorted(clip_types)}, limit_per_qb={limit_per_qb})")

    if dry_run:
        for c in selected:
            print(f"  [dry-run] {c.qb_name}: {c.url} ({c.confidence}, {c.clip_type})")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "download_manifest.csv"
    already_done = set()
    if manifest_path.exists():
        with manifest_path.open() as f:
            already_done = {row["url"] for row in csv.DictReader(f)}

    write_header = not manifest_path.exists()
    with manifest_path.open("a", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["qb_name", "url", "confidence", "clip_type", "status", "message", "local_path", "contact_sheet_path"]
        )
        if write_header:
            writer.writeheader()

        for i, candidate in enumerate(selected):
            if candidate.url in already_done:
                print(f"[{i+1}/{len(selected)}] {candidate.qb_name}: already in manifest, skipping")
                continue

            print(f"[{i+1}/{len(selected)}] {candidate.qb_name}: downloading {candidate.url} ...")
            success, message, video_path = download_clip(candidate, cookies_path, out_dir)

            contact_sheet_path = ""
            if success and video_path:
                sheet_path = video_path.with_suffix(".contact_sheet.jpg")
                if generate_contact_sheet(video_path, sheet_path):
                    contact_sheet_path = str(sheet_path)
                print(f"    ok -> {video_path}")
            else:
                print(f"    FAILED: {message}")

            writer.writerow(
                {
                    "qb_name": candidate.qb_name,
                    "url": candidate.url,
                    "confidence": candidate.confidence,
                    "clip_type": candidate.clip_type,
                    "status": "downloaded" if success else "failed",
                    "message": message,
                    "local_path": str(video_path) if video_path else "",
                    "contact_sheet_path": contact_sheet_path,
                }
            )
            f.flush()

            if i < len(selected) - 1:
                time.sleep(sleep_seconds)

    print(f"\nManifest written to {manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cookies", type=Path, required=True, help="Path to a Netscape-format cookies.txt")
    parser.add_argument(
        "--confidence-tiers", default="High,Medium-high",
        help="Comma-separated confidence tiers to include (default: High,Medium-high)",
    )
    parser.add_argument(
        "--clip-types", default="short",
        help="Comma-separated clip types to include: short, 'long, needs isolation' (default: short)",
    )
    parser.add_argument("--limit-per-qb", type=int, default=2, help="Max clips to download per QB (default: 2)")
    parser.add_argument("--sleep-seconds", type=float, default=8.0, help="Delay between downloads (default: 8s)")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded without downloading")
    args = parser.parse_args()

    run(
        cookies_path=args.cookies,
        confidence_tiers=set(args.confidence_tiers.split(",")),
        clip_types=set(args.clip_types.split(",")),
        limit_per_qb=args.limit_per_qb,
        sleep_seconds=args.sleep_seconds,
        out_dir=args.out_dir,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
