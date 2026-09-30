"""Unit tests for api/storage.py's S3 backend against an in-memory fake
client (no network), plus LocalStorage basics."""

from __future__ import annotations

import io

from botocore.exceptions import ClientError
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse

from api.storage import LocalStorage, S3Storage, media_type_for


class FakeS3:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def upload_file(self, filename, bucket, key, ExtraArgs=None):
        with open(filename, "rb") as f:
            self.objects[key] = f.read()

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return {}

    def delete_object(self, Bucket, Key):
        self.objects.pop(Key, None)

    def download_file(self, bucket, key, filename):
        with open(filename, "wb") as f:
            f.write(self.objects[key])

    def generate_presigned_url(self, op, Params, ExpiresIn):
        return f"https://signed.example/{Params['Key']}?ttl={ExpiresIn}"

    def get_object(self, Bucket, Key, Range=None):
        data = self.objects[Key]
        if Range:
            start, end = Range.removeprefix("bytes=").split("-")
            part = data[int(start) : int(end) + 1]
            return {
                "Body": io.BytesIO(part),
                "ContentLength": len(part),
                "ContentRange": f"bytes {start}-{end}/{len(data)}",
            }
        return {"Body": io.BytesIO(data), "ContentLength": len(data)}


class FakeRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}


def test_s3_roundtrip_and_local_copy(tmp_path):
    fake = FakeS3()
    storage = S3Storage("bucket", client=fake)
    src = tmp_path / "in.mp4"
    src.write_bytes(b"video-bytes")

    storage.put_file("uploads/a.mp4", src)
    assert storage.exists("uploads/a.mp4")
    with storage.local_copy("uploads/a.mp4") as path:
        assert path.read_bytes() == b"video-bytes"
        copied = path
    assert not copied.exists()  # temp copy cleaned up

    storage.delete("uploads/a.mp4")
    assert not storage.exists("uploads/a.mp4")


def test_s3_redirect_mode_returns_presigned_redirect():
    storage = S3Storage("bucket", client=FakeS3(), serve_mode="redirect")
    response = storage.response("uploads/a.mp4", FakeRequest())
    assert isinstance(response, RedirectResponse)
    assert response.headers["location"].startswith("https://signed.example/uploads/a.mp4")


def test_s3_proxy_mode_passes_range_through(tmp_path):
    fake = FakeS3()
    fake.objects["uploads/a.mp4"] = b"0123456789"
    storage = S3Storage("bucket", client=fake, serve_mode="proxy")

    response = storage.response("uploads/a.mp4", FakeRequest({"range": "bytes=2-5"}))
    assert isinstance(response, StreamingResponse)
    assert response.status_code == 206
    assert response.headers["content-range"] == "bytes 2-5/10"

    full = storage.response("uploads/a.mp4", FakeRequest())
    assert full.status_code == 200


def test_local_storage_handles_legacy_absolute_paths(tmp_path):
    legacy = tmp_path / "old_upload.mp4"
    legacy.write_bytes(b"x")
    storage = LocalStorage(tmp_path / "root")
    assert storage.exists(str(legacy))
    with storage.local_copy(str(legacy)) as path:
        assert path == legacy
    assert isinstance(storage.response(str(legacy)), FileResponse)


def test_media_types():
    assert media_type_for("a/b.webm") == "video/webm"
    assert media_type_for("a/b.MOV") == "video/quicktime"


def test_database_url_normalization():
    from db.base import normalize_database_url

    assert normalize_database_url("postgres://u:p@h/db") == "postgresql+psycopg2://u:p@h/db"
    assert normalize_database_url("postgresql://u:p%40x@h/db?sslmode=require") == (
        "postgresql+psycopg2://u:p%40x@h/db?sslmode=require"
    )
    assert normalize_database_url("postgresql+psycopg2://u@h/db") == "postgresql+psycopg2://u@h/db"
    assert normalize_database_url(None) is None
