"""Track E/F correctness: the per-user/day AI ceiling is REFUNDED on a provider outage.

``check_llm_ceiling`` consumes one daily slot UP FRONT (before the LLM call) as a wallet-drain
defense — an attempt that costs money must count even if the request later errors. But an
upstream provider OUTAGE (a 502 from a dead/erroring LLM provider) costs nothing and is not the
user's fault, so it must NOT burn a legitimate user's daily quota. ``refund_llm_ceiling`` gives
the slot back on exactly that path.

These tests pin the contract so a regression that drops the refund (a flaky provider silently
eating a user's whole day of AI) fails LOUD:
  * the counter primitive refunds correctly and never underflows below 0;
  * a run of provider 502s does NOT lock a user out (each failure is refunded);
  * a genuine SUCCESS still consumes (the refund didn't neuter the ceiling).
"""
from sqlalchemy.orm import sessionmaker

import asgi

OK_PW = "hunter2pw"


def _session(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


# ---------------------------------------------------------------------------
# Counter primitive
# ---------------------------------------------------------------------------
def test_refund_counter_returns_a_consumed_slot(_engine):
    db = _session(_engine)
    # Consume 2 of a 3-slot window.
    assert asgi._consume_counter(db, "u1", "llm_daily", 3, 86400) is True
    assert asgi._consume_counter(db, "u1", "llm_daily", 3, 86400) is True
    # Refund one — the tally drops back to 1, so THREE more consumes now fit before the cap.
    asgi._refund_counter(db, "u1", "llm_daily", 86400)
    assert asgi._consume_counter(db, "u1", "llm_daily", 3, 86400) is True  # 2
    assert asgi._consume_counter(db, "u1", "llm_daily", 3, 86400) is True  # 3
    assert asgi._consume_counter(db, "u1", "llm_daily", 3, 86400) is False  # cap
    db.close()


def test_refund_counter_never_underflows(_engine):
    """A refund with no matching prior consume (window rolled over / double refund) is a no-op —
    it must never drive the count negative, which would hand out FREE extra slots."""
    db = _session(_engine)
    # Refund with no row at all: harmless no-op.
    asgi._refund_counter(db, "u2", "llm_daily", 86400)
    # One consume, then two refunds — the second must floor at 0, not go to -1.
    assert asgi._consume_counter(db, "u2", "llm_daily", 2, 86400) is True
    asgi._refund_counter(db, "u2", "llm_daily", 86400)
    asgi._refund_counter(db, "u2", "llm_daily", 86400)
    # The full limit is still available; no free bonus slot was created.
    assert asgi._consume_counter(db, "u2", "llm_daily", 2, 86400) is True
    assert asgi._consume_counter(db, "u2", "llm_daily", 2, 86400) is True
    assert asgi._consume_counter(db, "u2", "llm_daily", 2, 86400) is False
    db.close()


def test_refund_is_cross_instance(_engine):
    """The refund lands in the shared DB tally — a DIFFERENT serverless instance sees it."""
    inst_a = _session(_engine)
    inst_b = _session(_engine)
    assert asgi._consume_counter(inst_a, "u3", "llm_daily", 1, 86400) is True
    # Instance B (fresh session) would be blocked...
    assert asgi._consume_counter(inst_b, "u3", "llm_daily", 1, 86400) is False
    # ...until instance A refunds; then B fits again.
    asgi._refund_counter(inst_a, "u3", "llm_daily", 86400)
    assert asgi._consume_counter(inst_b, "u3", "llm_daily", 1, 86400) is True
    inst_a.close()
    inst_b.close()


# ---------------------------------------------------------------------------
# End-to-end through the coach endpoint (a representative LLM surface)
# ---------------------------------------------------------------------------
def _register_premium_consented(client, db_session, email):
    from src.db.models import User, UserTier

    r = client.post("/api/auth/register", json={"email": email, "password": OK_PW})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    db_session.query(User).update({User.tier: UserTier.PREMIUM})
    db_session.commit()
    # Third-party-AI consent is required before any Gemini call (Apple 5.1.2(i)).
    assert client.post(
        "/api/ai-consent", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 200
    return token


def test_provider_502s_do_not_burn_the_daily_quota(client, db_session, monkeypatch):
    """A run of provider outages must NOT lock the user out — each 502 refunds its slot, so a
    later SUCCESS still goes through. Without the refund, calls past the ceiling would 429."""
    token = _register_premium_consented(client, db_session, "refund-502@example.com")
    auth = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(asgi, "LLM_DAILY_CEILING", 2)

    class _FailingCoach:
        def __init__(self, db):
            pass

        @staticmethod
        def available():
            return True

        def chat(self, user, message, session_id=None, job_context=None):
            raise RuntimeError("simulated upstream provider 502")

    monkeypatch.setattr(asgi, "CareerCoach", _FailingCoach)
    # Five provider failures in a row against a ceiling of 2 — every one is a 502 (provider error),
    # NEVER a 429 (would mean the refund failed and the ceiling wrongly counted the outages).
    for _ in range(5):
        r = client.post("/api/coach/chat", headers=auth, json={"message": "hi"})
        assert r.status_code == 502, r.text

    # The quota is untouched: a real success now goes through (proving the failures were refunded).
    class _OkCoach(_FailingCoach):
        def chat(self, user, message, session_id=None, job_context=None):
            return "Here is some concrete advice."

    monkeypatch.setattr(asgi, "CareerCoach", _OkCoach)
    ok = client.post("/api/coach/chat", headers=auth, json={"message": "hi"})
    assert ok.status_code == 200, ok.text
    assert ok.json()["message"] == "Here is some concrete advice."


def test_success_still_consumes_the_ceiling(client, db_session, monkeypatch):
    """The refund must not neuter the wallet-drain defense: genuine successes still count, so the
    ceiling still blocks a runaway once real generations exhaust it."""
    token = _register_premium_consented(client, db_session, "refund-success@example.com")
    auth = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(asgi, "LLM_DAILY_CEILING", 2)

    class _OkCoach:
        def __init__(self, db):
            pass

        @staticmethod
        def available():
            return True

        def chat(self, user, message, session_id=None, job_context=None):
            return "reply"

    monkeypatch.setattr(asgi, "CareerCoach", _OkCoach)
    for _ in range(2):
        assert client.post("/api/coach/chat", headers=auth, json={"message": "hi"}).status_code == 200
    blocked = client.post("/api/coach/chat", headers=auth, json={"message": "hi"})
    assert blocked.status_code == 429
    assert "daily" in blocked.json()["detail"].lower()
