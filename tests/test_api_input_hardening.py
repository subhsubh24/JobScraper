"""Track F: API input-bounds + rate-limit consistency hardening.

Completes the input-bounds work (unbounded client-supplied ids on the coach endpoint) and
proves the two endpoints that previously lacked a rate limit now enforce one. The limiter is
LIVE in the unit-test env (only the CI E2E server sets E2E_DISABLE_RATE_LIMIT), so these are
real behavioural assertions, not just "the decorator is present".
"""

import asgi
from src.db.models import User, UserTier


def _register(client, email="hardening@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_chat_request_rejects_overlong_ids(client, db_session):
    """An over-long session_id / job_id is rejected at the boundary (422), never passed to
    the query layer. A within-bounds id is NOT a validation error."""
    token = _register(client, "chat-bounds@example.com")
    db_session.query(User).update({User.tier: UserTier.PREMIUM})
    db_session.commit()

    # job_id bound is 64; session_id is tighter (36) because it is INSERTED into a
    # String(36) column — a 37..64-char value must be rejected at the boundary, not raise a
    # DB truncation 502 downstream.
    r = client.post(
        "/api/coach/chat",
        headers=_auth(token),
        json={"message": "hi", "job_id": "x" * 65},
    )
    assert r.status_code == 422, r.text

    r = client.post(
        "/api/coach/chat",
        headers=_auth(token),
        json={"message": "hi", "session_id": "x" * 65},
    )
    assert r.status_code == 422, r.text

    # A 40-char session_id is within the old 64 bound but over the DB column width — it must
    # 422 (locks the tightened 36-char bound so it can't silently regress to 64).
    r = client.post(
        "/api/coach/chat",
        headers=_auth(token),
        json={"message": "hi", "session_id": "x" * 40},
    )
    assert r.status_code == 422, r.text

    # A real UUID-length id passes validation (it may then 503 for no LLM key — the point is
    # it is NOT a 422). Proves the bound accepts legitimate ids.
    r = client.post(
        "/api/coach/chat",
        headers=_auth(token),
        json={"message": "hi", "session_id": "b3f1c2d4-0000-1111-2222-333344445555"},
    )
    assert r.status_code != 422, r.text


def test_coach_suggestions_is_rate_limited(client, monkeypatch):
    """The suggestions endpoint (a per-user context query) now enforces a limit, so an authed
    client can't hammer it unbounded — it was the only coach endpoint without one.

    Determinism: freeze `time.time` so all 35 requests share ONE 60s limiter window
    (`window_key = int(time.time() // 60)`); a burst straddling a boundary otherwise splits
    across two windows and never trips the 30/60s limit (the CI-flake class fixed 2026-07-13).
    """
    monkeypatch.setattr(asgi.time, "time", lambda: 1_700_000_000.0)
    token = _register(client, "suggest-limit@example.com")
    saw_429 = False
    for _ in range(35):  # limit is 30/60s
        r = client.get("/api/coach/suggestions", headers=_auth(token))
        if r.status_code == 429:
            saw_429 = True
            assert "Too many requests" in r.json()["detail"]
            break
        assert r.status_code == 200, r.text
    assert saw_429, "coach/suggestions should throttle within 35 rapid calls"


def test_verify_purchase_is_rate_limited(client, monkeypatch):
    """The verify-purchase write endpoint now shares the auth limiter. It still refuses
    honestly (501, no fake grant) AND throttles under a burst.

    Determinism: freeze `time.time` so all 15 requests share ONE 60s limiter window — a burst
    straddling a boundary otherwise splits across two windows and never trips the 10/60s limit.
    """
    monkeypatch.setattr(asgi.time, "time", lambda: 1_700_000_000.0)
    token = _register(client, "verify-limit@example.com")
    body = {"receipt_data": "r", "platform": "ios"}
    statuses = []
    for _ in range(15):  # auth bucket limit is 10/60s (register already consumed one)
        r = client.post("/api/auth/verify-purchase", headers=_auth(token), json=body)
        statuses.append(r.status_code)
        if r.status_code == 429:
            break
    # Early calls refuse honestly (never grant), and a burst is eventually throttled.
    assert 501 in statuses, statuses
    assert 429 in statuses, statuses


def test_rate_limit_live_in_unit_env():
    """Guard: the limiter must be active in this env (bypass only for the CI E2E server)."""
    assert asgi._RATE_LIMIT_DISABLED is False
