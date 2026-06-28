"""A single, consistent error envelope for every API error response.

CONTRACT (backward compatible): error responses keep the FastAPI-native `detail` field
(so existing clients/tests are unaffected) AND add a structured `error` object:

    {
      "success": false,
      "detail": "Job not found",                 # unchanged, human string
      "error": {
        "code": "not_found",                     # stable, machine-readable
        "message": "Job not found",
        "request_id": "1f9c..."                  # correlate with server logs
      }
    }

This lets the web/mobile clients branch on a stable `code` and surface the `request_id` in a
"contact support" path, without us having to rewrite every `raise HTTPException(...)` site.
"""
from __future__ import annotations

from typing import Any, Optional

# Map HTTP status -> stable error code. Anything unmapped falls back by class (4xx/5xx).
_STATUS_CODE = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    501: "not_implemented",
    502: "upstream_error",
    503: "unavailable",
}


def code_for_status(status_code: int) -> str:
    if status_code in _STATUS_CODE:
        return _STATUS_CODE[status_code]
    if 400 <= status_code < 500:
        return "client_error"
    return "server_error"


def _message_from_detail(detail: Any, status_code: int) -> str:
    """A short human message for the `error.message` field.

    HTTPException.detail is usually a string but can be a dict/list (e.g. validation errors).
    In that case we use a generic message and leave the structured detail in `detail`.
    """
    if isinstance(detail, str) and detail:
        return detail
    return {
        401: "Authentication required.",
        403: "You don't have access to that.",
        404: "Not found.",
        422: "The request was invalid.",
        429: "Too many requests.",
    }.get(status_code, "Request failed.")


def error_body(
    status_code: int,
    detail: Any,
    request_id: Optional[str] = None,
) -> dict:
    """Build the response body shared by every error handler."""
    body: dict = {
        "success": False,
        "detail": detail,
        "error": {
            "code": code_for_status(status_code),
            "message": _message_from_detail(detail, status_code),
        },
    }
    if request_id:
        body["error"]["request_id"] = request_id
    return body
