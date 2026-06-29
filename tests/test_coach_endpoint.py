"""Track C/E/F: outcome contract for the AI coach endpoint.

Asserts the paths NOT already covered by the journey suite / coach-safety tests: a
Premium user with no key degrades honestly (503, no fake reply); the success response
carries the model reply; and the per-user/day LLM ceiling actually blocks (429) — the
wallet-drain defense. (The Free-user 403 gate and the key-free crisis-moderation
round-trip are already covered in tests/journeys + tests/test_coach_safety.py.)
"""

import asgi
from src.db.models import User, UserTier


def _register(client, email="coach@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _make_premium(db_session):
    db_session.query(User).update({User.tier: UserTier.PREMIUM})
    db_session.commit()


def test_coach_honest_degradation_without_key(client, db_session):
    """Premium user, no LLM key → honest 503 (no fake reply)."""
    token = _register(client, "premium-nokey@example.com")
    _make_premium(db_session)
    r = client.post("/api/coach/chat", headers=_auth(token), json={"message": "Hi"})
    assert r.status_code == 503
    assert "GEMINI_API_KEY" in r.json()["detail"]


def test_coach_success_contract(client, db_session, monkeypatch):
    token = _register(client, "premium-ok@example.com")
    _make_premium(db_session)

    class _FakeCoach:
        def __init__(self, db):
            pass

        @staticmethod
        def available():
            return True

        def chat(self, user, message, session_id=None, job_context=None):
            return "Here is some concrete career advice."

    monkeypatch.setattr(asgi, "CareerCoach", _FakeCoach)
    r = client.post("/api/coach/chat", headers=_auth(token), json={"message": "How do I negotiate?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Here is some concrete career advice."


def test_coach_daily_ceiling_blocks(client, db_session, monkeypatch):
    """The per-user/day LLM ceiling is a wallet-drain defense — it must actually block."""
    token = _register(client, "premium-ceiling@example.com")
    _make_premium(db_session)

    class _FakeCoach:
        def __init__(self, db):
            pass

        @staticmethod
        def available():
            return True

        def chat(self, user, message, session_id=None, job_context=None):
            return "reply"

    monkeypatch.setattr(asgi, "CareerCoach", _FakeCoach)
    monkeypatch.setattr(asgi, "LLM_DAILY_CEILING", 2)

    for _ in range(2):
        ok = client.post("/api/coach/chat", headers=_auth(token), json={"message": "hi"})
        assert ok.status_code == 200, ok.text
    blocked = client.post("/api/coach/chat", headers=_auth(token), json={"message": "hi"})
    assert blocked.status_code == 429
    assert "daily" in blocked.json()["detail"].lower()
