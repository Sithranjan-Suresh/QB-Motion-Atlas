"""Object storage for uploaded videos and served reference clips (task 137).

Two backends behind one small interface, picked by environment:

- `LocalStorage` (default): files under data/ on this machine's disk. Fine
  for local dev; on a PaaS whose disk is wiped on every deploy it loses
  every upload, which is why production uses:
- `S3Storage`: any S3-compatible bucket -- Supabase Storage, Cloudflare R2,
  AWS S3. Enabled by setting S3_BUCKET (plus S3_ENDPOINT_URL, S3_REGION,
  S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY).

Everything is addressed by a storage *key* ("uploads/<id>.mp4",
"reference_clips/<clip_id>.mp4"), never a machine path, so the value stored
in `uploads.video_path` survives moving between machines. MediaPipe/OpenCV
need a real file, so `local_copy()` hands out a path (downloading to a
temp file first on S3).
"""

from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterator

from fastapi import Request
from fastapi.responses import FileResponse, RedirectResponse, Response, StreamingResponse

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
UPLOADS_PREFIX = "uploads"
REFERENCE_CLIPS_PREFIX = "reference_clips"
PRESIGNED_URL_TTL_SEC = 3600
_STREAM_CHUNK_BYTES = 1024 * 1024

MEDIA_TYPES = {".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}


def upload_key(upload_id: str, ext: str) -> str:
    return f"{UPLOADS_PREFIX}/{upload_id}{ext}"


def reference_clip_key(clip_id: str) -> str:
    return f"{REFERENCE_CLIPS_PREFIX}/{clip_id}.mp4"


def media_type_for(key: str) -> str:
    return MEDIA_TYPES.get(Path(key).suffix.lower(), "application/octet-stream")


class LocalStorage:
    def __init__(self, root: Path = DATA_DIR):
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        # Rows written before storage keys existed hold an absolute path.
        path = Path(key)
        return path if path.is_absolute() else self.root / key

    def put_file(self, key: str, source: Path) -> None:
        dest = self._path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    @contextlib.contextmanager
    def local_copy(self, key: str) -> Iterator[Path]:
        path = self._path(key)
        if not path.exists():
            raise FileNotFoundError(key)
        yield path

    def response(self, key: str, request: Request | None = None) -> Response:
        return FileResponse(self._path(key), media_type=media_type_for(key))


class S3Storage:
    """`S3_SERVE_MODE=redirect` (default) answers video requests with a 302
    to a short-lived presigned URL, so video bytes never pass through the
    API. `proxy` streams through the API instead (Range requests passed
    through, so seeking and Safari playback still work) for providers
    without presigned-URL support."""

    def __init__(self, bucket: str, client=None, serve_mode: str | None = None):
        self.bucket = bucket
        self.serve_mode = serve_mode or os.environ.get("S3_SERVE_MODE", "redirect")
        if client is None:
            import boto3
            from botocore.config import Config

            client = boto3.client(
                "s3",
                endpoint_url=os.environ.get("S3_ENDPOINT_URL") or None,
                region_name=os.environ.get("S3_REGION") or "auto",
                aws_access_key_id=os.environ.get("S3_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("S3_SECRET_ACCESS_KEY"),
                # Supabase Storage and R2 both need path-style addressing.
                config=Config(s3={"addressing_style": "path"}, signature_version="s3v4"),
            )
        self.client = client

    def put_file(self, key: str, source: Path) -> None:
        self.client.upload_file(str(source), self.bucket, key, ExtraArgs={"ContentType": media_type_for(key)})

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    @contextlib.contextmanager
    def local_copy(self, key: str) -> Iterator[Path]:
        suffix = Path(key).suffix or ".mp4"
        fd, tmp_name = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            self.client.download_file(self.bucket, key, str(tmp_path))
            yield tmp_path
        finally:
            tmp_path.unlink(missing_ok=True)

    def response(self, key: str, request: Request | None = None) -> Response:
        if self.serve_mode != "proxy":
            url = self.client.generate_presigned_url(
                "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=PRESIGNED_URL_TTL_SEC
            )
            return RedirectResponse(url, status_code=302)

        params = {"Bucket": self.bucket, "Key": key}
        range_header = request.headers.get("range") if request is not None else None
        if range_header:
            params["Range"] = range_header
        obj = self.client.get_object(**params)
        headers = {"Accept-Ranges": "bytes", "Content-Length": str(obj["ContentLength"])}
        if "ContentRange" in obj:
            headers["Content-Range"] = obj["ContentRange"]
        body = obj["Body"]
        return StreamingResponse(
            iter(lambda: body.read(_STREAM_CHUNK_BYTES), b""),
            status_code=206 if range_header else 200,
            media_type=media_type_for(key),
            headers=headers,
        )


_storage: LocalStorage | S3Storage | None = None


def get_storage() -> LocalStorage | S3Storage:
    global _storage
    if _storage is None:
        bucket = os.environ.get("S3_BUCKET")
        _storage = S3Storage(bucket) if bucket else LocalStorage()
    return _storage


def set_storage(storage: LocalStorage | S3Storage | None) -> None:
    """Test hook: swap the backend (None resets to the env-configured one)."""
    global _storage
    _storage = storage
