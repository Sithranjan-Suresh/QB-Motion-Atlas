"""Per-client upload rate limit. Every upload costs real CPU time, so a
public URL without this lets one script exhaust the server.

In-memory sliding window: correct for the single API instance this project
deploys as. Running several instances behind a load balancer would need a
shared store (e.g. a Postgres table) instead.
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

from fastapi import Request


def client_ip(request: Request) -> str:
    """Behind Render / Hugging Face / Vercel the socket peer is the proxy, so
    the real client comes from X-Forwarded-For. TRUST_PROXY_HEADERS=false
    ignores it (when the API is exposed directly, the header is forgeable)."""
    if os.environ.get("TRUST_PROXY_HEADERS", "true").lower() != "false":
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_sec: float):
        self.max_events = max_events
        self.window_sec = window_sec
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, now: float | None = None) -> float | None:
        """Records an event for `key` and returns None if allowed, or the
        seconds until the next event would be allowed if over the limit
        (rejected events aren't recorded)."""
        now = time.monotonic() if now is None else now
        with self._lock:
            events = self._events[key]
            while events and events[0] <= now - self.window_sec:
                events.popleft()
            if len(events) >= self.max_events:
                return (events[0] + self.window_sec - now) if events else self.window_sec
            events.append(now)
            if len(self._events) > 10_000:  # bound memory under a spray of IPs
                for stale_key in [k for k, v in self._events.items() if not v]:
                    del self._events[stale_key]
            return None


upload_limiter = SlidingWindowLimiter(
    max_events=int(os.environ.get("UPLOAD_RATE_LIMIT_COUNT", "10")),
    window_sec=float(os.environ.get("UPLOAD_RATE_LIMIT_WINDOW_SEC", "3600")),
)
