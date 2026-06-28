"""Structured (JSON) logging for the Career Operator API.

WHY: production debugging needs machine-greppable logs with a request id that ties a
client-visible error (we return the same id in the body) back to the exact server log line.
Vercel/most platforms ingest stdout line-by-line, so one JSON object per line is the
lowest-friction format that downstream tools (Datadog, Logtail, `jq`) can parse.

DESIGN: standard-library only (no new dependency — keeps the Vercel function under its size
limit). A `contextvar` carries the per-request id so every log record emitted while handling
a request is automatically stamped with it, without threading the id through every call.
"""
from __future__ import annotations

import json
import logging
import os
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

# Per-request correlation id. Set by the request-id middleware in asgi.py; read by the
# formatter below. Defaults to None outside a request (e.g. startup logs).
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Keys that are always present on a LogRecord — everything else a caller passes via
# `logger.info(..., extra={...})` is treated as structured context and merged into the line.
_RESERVED = set(
    logging.makeLogRecord({}).__dict__.keys()
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    """Render each log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        # Merge caller-supplied `extra=` context FIRST, then stamp the fixed fields on top, so
        # a stray extra key (e.g. extra={"level": ...} or {"exc": ...}) can never overwrite a
        # reserved field or silently drop the traceback.
        payload = {}
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        payload.update(
            {
                "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
        )
        rid = request_id_var.get()
        if rid:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_CONFIGURED = False


def setup_logging() -> None:
    """Install the JSON formatter on the root logger (idempotent).

    Honors LOG_LEVEL (default INFO). Skipped when LOG_FORMAT=plain so local runs / pytest -s
    stay human-readable. Replaces existing handlers so we don't double-emit under uvicorn.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    if os.getenv("LOG_FORMAT", "json").lower() == "plain":
        return

    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
