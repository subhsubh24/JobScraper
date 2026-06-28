"""Tests for the consistent error envelope + request-id correlation (PR: API hardening).

The envelope is ADDITIVE: every error response keeps the native `detail` AND gains a
structured `error` object with a stable `code`, a `message`, and the `request_id` that also
appears in the `X-Request-ID` response header (so a client can quote it to support and we
can grep the server logs for it).
"""
from fastapi.testclient import TestClient

import asgi
from src.api.errors import code_for_status, error_body


client = TestClient(asgi.app, raise_server_exceptions=False)


def test_404_has_envelope_and_keeps_detail():
    # Unauthenticated request to a protected route -> 401 via HTTPException.
    r = client.get("/api/jobs/does-not-exist")
    assert r.status_code == 401
    body = r.json()
    assert body["detail"]  # native field preserved (back-compat)
    assert body["success"] is False
    assert body["error"]["code"] == "unauthorized"
    assert body["error"]["message"]
    # request id is echoed both in the body and the header, and they match.
    assert body["error"]["request_id"]
    assert r.headers["X-Request-ID"] == body["error"]["request_id"]


def test_validation_error_uses_envelope():
    # Missing required fields -> RequestValidationError -> 422 in the same envelope.
    r = client.post("/api/auth/register", json={"email": "x@example.com"})
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["detail"], list)  # field-level errors preserved
    assert r.headers["X-Request-ID"]


def test_inbound_request_id_is_honored():
    r = client.get("/api/auth/me", headers={"X-Request-ID": "trace-abc-123"})
    assert r.status_code == 401
    assert r.headers["X-Request-ID"] == "trace-abc-123"
    assert r.json()["error"]["request_id"] == "trace-abc-123"


def test_success_response_has_request_id_header():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.headers["X-Request-ID"]


def test_extra_keys_cannot_overwrite_fixed_fields():
    # A stray extra={"level":...} must NOT corrupt reserved fields — fixed fields are
    # stamped last and always win, while genuine extra context is still merged.
    import json
    import logging
    from src.api.logging_config import JsonFormatter

    rec = logging.makeLogRecord(
        {"name": "t", "levelno": logging.INFO, "levelname": "INFO", "msg": "hi"}
    )
    rec.level = "HACKED"  # collides with a fixed field name
    rec.user_id = "u1"  # legitimate structured context
    out = json.loads(JsonFormatter().format(rec))
    assert out["level"] == "INFO"  # fixed field preserved, not "HACKED"
    assert out["user_id"] == "u1"  # genuine extra merged
    assert out["message"] == "hi"


def test_code_for_status_mapping():
    assert code_for_status(404) == "not_found"
    assert code_for_status(429) == "rate_limited"
    assert code_for_status(418) == "client_error"  # unmapped 4xx
    assert code_for_status(599) == "server_error"  # unmapped 5xx


def test_error_body_shape():
    body = error_body(403, "nope", request_id="rid1")
    assert body == {
        "success": False,
        "detail": "nope",
        "error": {"code": "forbidden", "message": "nope", "request_id": "rid1"},
    }
    # non-string detail (e.g. validation list) -> generic message, detail preserved.
    body2 = error_body(422, [{"loc": ["body"]}])
    assert body2["error"]["code"] == "validation_error"
    assert body2["detail"] == [{"loc": ["body"]}]
    assert "request_id" not in body2["error"]
