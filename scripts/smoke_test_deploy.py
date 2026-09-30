"""Post-deploy smoke test for a live backend (and optionally frontend).

Checks readiness, pushes a real (synthetic, person-free) video through the
whole queue -> worker -> storage path, expects the honest "no_pose_detected"
rejection, confirms the stored video is served back, then deletes the upload.
Also fetches the frontend's pages when --frontend is given.

Usage:
    python scripts/smoke_test_deploy.py --api https://<user>-qb-motion-atlas-api.hf.space \\
        [--frontend https://<project>.vercel.app]

Needs ffmpeg on PATH (to generate the test clip) and httpx.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

TERMINAL_STATUSES = {"passed", "rejected", "failed"}


def check(ok: bool, label: str, detail: str = "") -> bool:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}{(' -- ' + detail) if detail else ''}")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api", required=True)
    parser.add_argument("--frontend")
    parser.add_argument("--timeout", type=float, default=240, help="seconds to wait for processing")
    args = parser.parse_args()
    api = args.api.rstrip("/")
    results = []

    with httpx.Client(timeout=60, follow_redirects=False) as client:
        ready = client.get(f"{api}/health/ready")
        body = ready.json() if ready.headers.get("content-type", "").startswith("application/json") else {}
        results.append(check(ready.status_code == 200, "backend ready", str(body)))
        results.append(check(body.get("storage") == "S3Storage", "using object storage", body.get("storage", "?")))

        qbs = client.get(f"{api}/qbs").json()
        results.append(check(len(qbs) > 0, "reference QBs seeded", f"{len(qbs)} QBs"))

        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "smoke.mp4"
            subprocess.run(
                ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc=duration=4:size=640x480:rate=30",
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
                check=True,
            )
            with video.open("rb") as f:
                created = client.post(f"{api}/uploads", files={"file": ("smoke.mp4", f, "video/mp4")})
        if not check(created.status_code == 201, "upload accepted", f"HTTP {created.status_code} {created.text[:200]}"):
            sys.exit(1)
        upload_id = created.json()["upload_id"]

        deadline = time.monotonic() + args.timeout
        status = {}
        while time.monotonic() < deadline:
            status = client.get(f"{api}/uploads/{upload_id}/status").json()
            if status.get("status") in TERMINAL_STATUSES:
                break
            time.sleep(3)
        results.append(
            check(
                status.get("status") == "rejected" and status.get("rejection_reason") == "no_pose_detected",
                "worker processed the upload",
                str(status),
            )
        )

        video_resp = client.get(f"{api}/uploads/{upload_id}/video")
        if video_resp.status_code in (301, 302, 307):
            video_resp = httpx.get(video_resp.headers["location"], timeout=60)
        results.append(
            check(video_resp.status_code in (200, 206) and len(video_resp.content) > 0, "stored video served back")
        )

        deleted = client.delete(f"{api}/uploads/{upload_id}")
        gone = client.get(f"{api}/uploads/{upload_id}/status")
        results.append(check(deleted.status_code == 204 and gone.status_code == 404, "upload deleted"))

        if args.frontend:
            site = args.frontend.rstrip("/")
            for path in ("/", "/how-to-film", "/privacy", "/terms", "/qbs"):
                page = client.get(f"{site}{path}", follow_redirects=True)
                results.append(check(page.status_code == 200, f"frontend {path}"))
            preflight = client.options(
                f"{api}/uploads",
                headers={"Origin": site, "Access-Control-Request-Method": "POST"},
            )
            allowed = preflight.headers.get("access-control-allow-origin")
            results.append(check(allowed == site, "CORS allows the frontend", f"allow-origin={allowed}"))

    print(f"\n{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
