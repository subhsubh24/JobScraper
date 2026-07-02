"""Cross-instance rate-limit + LLM spend-ceiling counter (ROADMAP Track F).

The counter lives in the shared ``rate_counters`` Postgres table, not in process memory, so
the limit holds GLOBALLY across serverless instances (the previous in-memory dicts only
slowed abuse within one warm instance — the LLM spend ceiling in particular multiplied per
instance). These tests pin the real behavior at the DB level + through the HTTP surface.
"""
import time

from sqlalchemy.orm import sessionmaker

import asgi
from src.db.models import RateCounter


def _session(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def test_counter_enforces_limit_and_persists(_engine):
    db = _session(_engine)
    # First two consume calls pass (limit=2), the third is rejected.
    assert asgi._consume_counter(db, "ip-1", "write", 2, 60) is True
    assert asgi._consume_counter(db, "ip-1", "write", 2, 60) is True
    assert asgi._consume_counter(db, "ip-1", "write", 2, 60) is False
    db.close()


def test_counter_is_cross_instance(_engine):
    """Two SEPARATE sessions on the same DB share the tally — this is the whole point: a
    second serverless instance (a fresh session/connection) sees the first's increments."""
    inst_a = _session(_engine)
    inst_b = _session(_engine)
    assert asgi._consume_counter(inst_a, "user-x", "llm_daily", 3, 86400) is True
    assert asgi._consume_counter(inst_b, "user-x", "llm_daily", 3, 86400) is True
    assert asgi._consume_counter(inst_a, "user-x", "llm_daily", 3, 86400) is True
    # Fourth call from EITHER instance is over the shared ceiling.
    assert asgi._consume_counter(inst_b, "user-x", "llm_daily", 3, 86400) is False
    inst_a.close()
    inst_b.close()


def test_counter_separate_subjects_and_buckets_are_independent(_engine):
    db = _session(_engine)
    assert asgi._consume_counter(db, "ip-a", "write", 1, 60) is True
    assert asgi._consume_counter(db, "ip-a", "write", 1, 60) is False
    # Different subject — own tally.
    assert asgi._consume_counter(db, "ip-b", "write", 1, 60) is True
    # Different bucket, same subject — own tally.
    assert asgi._consume_counter(db, "ip-a", "ingest", 1, 60) is True
    db.close()


def test_counter_new_window_resets_and_prunes_stale_rows(_engine, monkeypatch):
    db = _session(_engine)
    base = time.time()
    monkeypatch.setattr(asgi.time, "time", lambda: base)
    assert asgi._consume_counter(db, "ip-w", "write", 1, 60) is True
    assert asgi._consume_counter(db, "ip-w", "write", 1, 60) is False
    # Advance past the window — the limit resets AND the stale window row is pruned.
    monkeypatch.setattr(asgi.time, "time", lambda: base + 61)
    assert asgi._consume_counter(db, "ip-w", "write", 1, 60) is True
    remaining = db.query(RateCounter).filter(RateCounter.subject == "ip-w").count()
    assert remaining == 1  # only the current window survives
    db.close()


def test_llm_ceiling_enforced_over_http(client, db_session, monkeypatch):
    """A premium user past the daily LLM ceiling gets a 429 from the coach endpoint, proving
    check_llm_ceiling is wired to the DB counter end-to-end."""
    from src.db.models import UserTier
    from src.auth.auth_service import AuthService

    monkeypatch.setattr(asgi, "LLM_DAILY_CEILING", 0)  # ceiling of 0 → first call rejected
    monkeypatch.setattr(asgi.CareerCoach, "available", staticmethod(lambda: True))

    auth = AuthService(db_session)
    user, token = auth.register("ceiling@example.com", "password123")
    user.tier = UserTier.PREMIUM
    db_session.commit()
    # Third-party-AI consent precedes the ceiling check; grant it so the 429 (not a 403
    # consent block) is what this test exercises.
    assert client.post(
        "/api/ai-consent", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 200

    res = client.post(
        "/api/coach/chat",
        json={"message": "hi"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 429
    assert "Daily AI usage limit" in res.json()["detail"]
