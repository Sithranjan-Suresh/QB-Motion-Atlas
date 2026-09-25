"""Local file storage for uploaded videos (task 69). V1 scope only -- a
managed object store (S3-alike) is a deployment concern, not needed for
local dev or the V1 target (a single small Render/droplet instance per
engineering_spec.md).
"""

from __future__ import annotations

from pathlib import Path

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"


def save_upload(upload_id: str, filename: str, contents: bytes) -> Path:
    """Writes `contents` to data/uploads/<upload_id><ext>, where <ext> comes
    from the original filename (defaulting to .mp4 if it has none)."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or ".mp4"
    dest = UPLOADS_DIR / f"{upload_id}{ext}"
    dest.write_bytes(contents)
    return dest
