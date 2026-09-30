"""Structured logging (task 95): one JSON object per line on stdout, which
Render / Hugging Face / any container log viewer can search. LOG_FORMAT=text
switches to plain lines for local dev. Anything passed via `extra=` shows up
as top-level JSON keys. Also turns on Sentry when SENTRY_DSN is set and
sentry-sdk is installed."""

from __future__ import annotations

import datetime
import json
import logging
import os

# Attributes every LogRecord has; anything else came from `extra=`.
_STANDARD_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in vars(record).items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_configured = False


def configure_logging() -> None:
    global _configured
    if _configured:
        return
    _configured = True

    handler = logging.StreamHandler()
    if os.environ.get("LOG_FORMAT", "json") == "text":
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    else:
        handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

    dsn = os.environ.get("SENTRY_DSN")
    if dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=dsn, traces_sample_rate=0.0, send_default_pii=False)
        except ImportError:
            logging.getLogger(__name__).warning("SENTRY_DSN set but sentry-sdk is not installed")
