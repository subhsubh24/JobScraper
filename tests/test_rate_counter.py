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


def test_counter_recovers_from_a_concurrent_insert_race(_engine, monkeypatch):
    """The insert-race retry (``asgi._consume_counter``'s ``except IntegrityError`` branch).

    Two serverless instances can both see NO row for the same (subject, bucket, window) and race
    to INSERT it; the loser's commit hits the unique constraint and the DB raises IntegrityError.
    The counter must ROLL BACK its lost insert and RETRY the window as an UPDATE of the winner's
    row — returning a correct allow/deny, never surfacing an uncaught 500 to the caller (this is
    the cross-instance rate-limit / LLM spend-ceiling wallet-drain defense, so a spurious error
    here would wrongly reject a legitimate request or drop a spend increment). This except +
    retry-as-update branch had no coverage.

    Faithful simulation (deterministic): freeze the clock so the window key is fixed, then make the
    first commit discard our losing insert, durably commit a WINNER row for that exact window, and
    raise the IntegrityError our own commit would have hit. On the retry the SELECT now finds the
    winner and takes the UPDATE path (``row.count += 1``) — so the final count is 2 (winner's 1 +
    our retried increment), the real two-request outcome. LOAD-BEARING: remove the
    ``except IntegrityError: rollback; continue`` and this call raises IntegrityError instead of
    returning True; a naive re-insert (not an update) would leave count == 1, so the ``== 2``
    assert also pins that the retry genuinely hit the update branch.
    """
    from sqlalchemy.exc import IntegrityError

    db = _session(_engine)
    base = 1_000_000.0
    monkeypatch.setattr(asgi.time, "time", lambda: base)  # fix the window key
    window_key = int(base // 60)
    real_commit = db.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            # Our INSERT lost the race: drop it, durably commit the WINNER's row for this exact
            # window, then raise the unique-violation the real DB would have raised on our commit.
            db.rollback()
            db.add(RateCounter(subject="racer", bucket="write", window_key=window_key, count=1))
            real_commit()
            raise IntegrityError("duplicate window", {}, Exception("UNIQUE constraint failed"))
        return real_commit()

    monkeypatch.setattr(db, "commit", flaky_commit)

    result = asgi._consume_counter(db, "racer", "write", 5, 60)

    assert result is True  # recovered via retry-as-update, not an uncaught IntegrityError/500
    assert calls["n"] >= 2  # the retry path actually executed (the first commit raised)
    row = (
        db.query(RateCounter)
        .filter(RateCounter.subject == "racer", RateCounter.bucket == "write")
        .first()
    )
    # Winner's count (1) + our retried update (+1) == 2 — proof the retry took the UPDATE branch
    # (a re-insert would have left count == 1). The readback is a pure query (no commit needed).
    assert row is not None and row.count == 2
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
