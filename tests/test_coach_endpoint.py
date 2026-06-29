"""Track C/E/F4.1: outcome contract + side-effect round-trip for the AI coach.

Asserts: the Premium gate refuses Free users (403); an absent key degrades honestly
(503, no fake reply); the success response carries the model reply; the per-user/day
LLM ceiling actually blocks (429). Plus a deterministic, KEY-FREE side-effect
round-trip on the moderation path: a self-harm message returns crisis resources AND
persists the exchange (user + assistant ChatMessage rows) — proving the effect, not
just the screen.
"""

import asgi
from src.ai_coach.career_coach import CareerCoach
from src.db.models import ChatMessage, User, UserTier


def _register(client, email="coach@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _make_premium(db_session):
    db_session.query(User).update({User.tier: UserTier.PREMIUM})
    db_session.commit()


def test_coach_is_premium_gated(client):
    """A Free user is honestly refused (403), never silently served."""
    token = _register(client, "free@example.com")
    r = client.post("/api/coach/chat", headers=_auth(token), json={"message": "Hi"})
    assert r.status_code == 403
    assert "premium" in r.json()["detail"].lower()


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


def test_moderation_path_persists_exchange_keyfree(db_session):
    """KEY-FREE side-effect round-trip: a self-harm message returns crisis resources AND
    persists both sides of the exchange, with NO LLM client involved (the moderation
    branch runs before the key check). Proves the persisted effect, not just the reply."""
    from src.auth.auth_service import AuthService

    user, _token = AuthService(db_session).register(email="hurt@example.com", password="hunter2pw")
    coach = CareerCoach(db_session)
    assert coach.client is None  # no key in the test env

    reply = coach.chat(user=user, message="I want to kill myself", session_id="s1")
    assert reply  # a real, non-empty crisis response was returned
    assert "988" in reply or "crisis" in reply.lower() or "lifeline" in reply.lower()

    rows = db_session.query(ChatMessage).filter(ChatMessage.user_id == user.id).all()
    roles = {m.role for m in rows}
    assert "user" in roles and "assistant" in roles
    assert any("kill myself" in m.content for m in rows if m.role == "user")
