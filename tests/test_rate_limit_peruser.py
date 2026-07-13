"""Per-user rate limiting on authed endpoints (ROADMAP Track F; security A→A+).

The authed reads/writes below were IP-keyed, so MANY distinct users behind one
carrier-grade-NAT public IP shared a single limit — one busy user (or a stranger on the same
NAT) could false-429 everyone else, and a compromised token got no per-account bound. These
endpoints now key the limiter by USER id (``rate_limit_user``, subject ``user:<id>``), like the
read endpoints already covered by ``test_read_rate_limit.py``.

This suite pins the KEYING for EVERY migrated endpoint (mirroring test_read_rate_limit.py's
parametrized approach): once user A's per-user window for an endpoint's bucket is exhausted, A
gets a 429 while user B on the SAME client IP is untouched. Reverting any one endpoint back to
the IP-keyed ``rate_limit`` reddens the parametrized case for that endpoint — the seeded
``user:<id>`` counter is ignored, so A's call passes (the endpoint would tally the shared
client IP instead).

The LLM / ingest / pre-auth (register/login/verify-purchase/delete-account) buckets are
intentionally left IP-keyed as deliberate wallet-drain / account-rotation defenses and are out
of scope here.
"""
import time

import pytest
from sqlalchemy.orm import sessionmaker

import asgi
from src.db.models import RateCounter, User

# (method, path, bucket, body) for every endpoint migrated to rate_limit_user. Paths that take
# a body get a VALID one so the only possible error is the seeded limiter's 429 (never a 422
# that would mask the keying). Bucket is the counter the endpoint checks — seeding it past the
# limit for user A must 429 A while leaving user B (unseeded) free. jobs PATCH uses a
# non-existent id on purpose: the limiter fires before the handler's 404 lookup.
MIGRATED_ENDPOINTS = [
    ("POST", "/api/ai-consent", "auth", None),
    ("DELETE", "/api/ai-consent", "auth", None),
    ("POST", "/api/jobs", "write",
     {"title": "Engineer", "company_name": "Acme", "description": "Build and run services."}),
    ("PATCH", "/api/jobs/does-not-exist", "write", {"status": "applied"}),
    ("GET", "/api/coach/suggestions", "suggest", None),
    ("POST", "/api/report", "report", {"content_type": "coach", "reason": "other"}),
    ("GET", "/api/insights/skill-gaps", "suggest", None),
    ("GET", "/api/profile/resume", "read", None),
    ("PATCH", "/api/profile/resume", "write", {"resume_text": "Senior engineer, Python + React."}),
    ("POST", "/api/profile/enrich/github", "write", {"github": "torvalds"}),
    ("DELETE", "/api/profile/enrichment", "write", None),
]

_OVER_ANY_LIMIT = 1000  # ≥ every per-endpoint limit, so the current window is exhausted


def _register(client, email):
    r = client.post("/api/auth/register", json={"email": email, "password": "hunter2pw"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _uid(db, email):
    return db.query(User).filter(User.email == email).one().id


def _seed_bucket(engine, user_id, bucket):
    """Seed the per-user counter for (user:<id>, bucket, current window) past every limit, so
    the next call to any endpoint on that bucket 429s — exactly what _consume_counter would
    compute, without driving hundreds of real requests."""
    session = sessionmaker(bind=engine)()
    session.add(
        RateCounter(
            subject=f"user:{user_id}",
            bucket=bucket,
            window_key=int(time.time() // 60),
            count=_OVER_ANY_LIMIT,
        )
    )
    session.commit()
    session.close()


@pytest.mark.parametrize("method,path,bucket,body", MIGRATED_ENDPOINTS)
def test_migrated_endpoint_is_per_user_not_per_ip(client, _engine, method, path, bucket, body, monkeypatch):
    # Freeze `time.time` so `_seed_bucket`'s window key and the request's own
    # `_consume_counter` window key (`int(time.time() // 60)`) always match — a 60s boundary
    # between the seed and the call otherwise sends A to a fresh, unseeded window (200, not
    # 429). Fixed-window boundary flake class, fixed across the suite 2026-07-13.
    monkeypatch.setattr(time, "time", lambda: 1_700_000_000.0)
    token_a = _register(client, "pu-a@example.com")
    token_b = _register(client, "pu-b@example.com")
    uid_a = _uid(sessionmaker(bind=_engine)(), "pu-a@example.com")
    _seed_bucket(_engine, uid_a, bucket)

    # User A's window for this bucket is exhausted -> 429 (the limiter fires before the handler).
    ra = client.request(method, path, headers={"Authorization": f"Bearer {token_a}"}, json=body)
    assert ra.status_code == 429, f"{method} {path}: expected 429 for exhausted user, got {ra.status_code} {ra.text}"

    # User B shares the SAME TestClient IP but has an untouched per-user budget -> NOT 429.
    # (Under the reverted IP-keyed limiter, B would 429 off A's shared client-IP tally.)
    rb = client.request(method, path, headers={"Authorization": f"Bearer {token_b}"}, json=body)
    assert rb.status_code != 429, f"{method} {path}: user B wrongly throttled off user A's tally ({rb.status_code})"


def test_coach_suggestions_round_trip_via_real_consume_counter(client, db_session, monkeypatch):
    """A full HTTP round-trip that exhausts the budget through the REAL _consume_counter path
    (not a seeded row): A is 429, B on the same IP gets a real 200 with suggestions."""
    # Freeze time so the 30 seeding consume-calls and the two HTTP requests all share ONE
    # window; a boundary crossing mid-loop otherwise resets the count and A never reaches 30.
    monkeypatch.setattr(time, "time", lambda: 1_700_000_000.0)
    token_a = _register(client, "rt-a@example.com")
    token_b = _register(client, "rt-b@example.com")
    uid_a = _uid(db_session, "rt-a@example.com")
    for _ in range(30):
        assert asgi._consume_counter(db_session, f"user:{uid_a}", "suggest", 30, 60) is True

    ra = client.get("/api/coach/suggestions", headers={"Authorization": f"Bearer {token_a}"})
    assert ra.status_code == 429, ra.text
    rb = client.get("/api/coach/suggestions", headers={"Authorization": f"Bearer {token_b}"})
    assert rb.status_code == 200, rb.text
