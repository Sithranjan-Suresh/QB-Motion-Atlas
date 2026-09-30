"""Trimming reference clips down to what the analysis actually used (task
A3), shared by the API's on-demand path (api/main.py) and the bulk upload
script (scripts/publish_reference_data.py)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def served_range_sec(boundary_frames: list[tuple[int, int]], fps: float) -> tuple[float, float]:
    """(start, end) seconds spanning every phase boundary -- never more of the
    source clip than was compared."""
    start = min(start for start, _end in boundary_frames)
    end = max(end for _start, end in boundary_frames)
    return start / fps, end / fps


def trim_video(source_path: Path, start_sec: float, end_sec: float, out_path: Path) -> bool:
    """Re-encodes `source_path` between the two timestamps into `out_path`
    (H.264 + faststart, so browsers can start playback before the whole file
    arrives). Returns whether it succeeded."""
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source_path), "-ss", f"{start_sec:.3f}",
            "-to", f"{end_sec:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", str(out_path),
        ],
        capture_output=True, text=True, timeout=120,
    )
    return result.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0
