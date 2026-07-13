"""Track F: per-USER rate limiting on the authed read endpoints.

``/api/auth/me``, ``/api/jobs``, ``/api/jobs/{id}``, ``/api/referrals/me``,
``/api/profile/enrichment`` and ``/api/analytics/pipeline`` are hit on every app launch,
session restore, and pull-to-refresh. Behind carrier-grade NAT many distinct users share ONE
public IP, so an IP-keyed limit would false-429 legitimate mobile users the moment a busy NAT
crossed the threshold. The limiter is therefore keyed by USER id (``rate_limit_user``), which
both removes that shared-IP hazard AND caps a single compromised token from hammering these
DB-reading endpoints. These tests pin: (1) each read endpoint 429s once the per-user window is
exhausted (job detail included — the limiter runs BEFORE the 404 lookup); (2) the limit is
per-USER, not per-IP (a second user on the SAME client is unaffected).
"""
import time

from sqlalchemy.orm import sessionmaker

from src.db.models import RateCounter

# All six now carry ``rate_limit_user("user_read", 120)``. The job-detail path uses a
# non-existent id on purpose: the limiter dependency fires before the handler's 404 lookup, so
# a maxed-out user gets 429 (not 404) — which proves the decorator is actually attached.
READ_ENDPOINTS = [
    "/api/auth/me",
    "/api/referrals/me",
    "/api/jobs",
    "/api/jobs/does-not-exist",
    "/api/profile/enrichment",
    "/api/analytics/pipeline",
]

_READ_LIMIT = 120


def _register(client, email):
    r = client.post(
        "/api/auth/register", json={"email": email, "password": "correct-horse-battery"}
    )
    assert r.status_code == 200, r.text
    return r.json()


def _hdr(token):
    return {"Authorization": f"Bearer {token}"}


def _max_out_read_window(engine, user_id):
    """Seed the per-user read counter to its limit for the CURRENT window so the next call 429s.

    Mirrors exactly what ``_consume_counter`` would compute (subject ``user:<id>``, bucket
    ``user_read``, window key ``time()//60``) — driving 120 real requests would be slow and
    prove nothing extra.
    """
    session = sessionmaker(bind=engine)()
    session.add(
        RateCounter(
            subject=f"user:{user_id}",
            bucket="user_read",
            window_key=int(time.time() // 60),
            count=_READ_LIMIT,
        )
    )
    session.commit()
    session.close()


def test_authed_reads_are_rate_limited_per_user(client, _engine, monkeypatch):
    # Freeze `time.time` so the seeded window (below) and the request's own
    # `_consume_counter` window key (`int(time.time() // 60)`) always match — a 60s boundary
    # falling between the seed and the call otherwise sends the request to a fresh, unseeded
    # window (200, not 429). Same fixed-window flake class fixed across the suite 2026-07-13.
    monkeypatch.setattr(time, "time", lambda: 1_700_000_000.0)
    reg = _register(client, "reader@example.com")
    # Seed the window to its limit BEFORE any real call, so the very next request to each read
    # endpoint 429s — including job detail, where the limiter fires before the 404 lookup
    # (dependency order), which is what proves the decorator is actually attached.
    _max_out_read_window(_engine, reg["user"]["id"])
    for path in READ_ENDPOINTS:
        r = client.get(path, headers=_hdr(reg["token"]))
        assert r.status_code == 429, f"{path} was not rate-limited: {r.status_code} {r.text}"


def test_reads_permit_normal_use_and_key_by_user_not_ip(client, _engine, monkeypatch):
    """The point of per-USER keying: a second user on the SAME client/IP is unaffected when the
    first user's window is exhausted (an IP-keyed limit would wrongly 429 them) — and normal
    single-call use of every read endpoint stays well under the ceiling."""
    # Freeze time so the seeded window and each request's window key match (see the sibling
    # test above) — deterministic against the 60s fixed-window boundary flake.
    monkeypatch.setattr(time, "time", lambda: 1_700_000_000.0)
    a = _register(client, "usera@example.com")
    b = _register(client, "userb@example.com")
    _max_out_read_window(_engine, a["user"]["id"])

    # User A is limited...
    assert client.get("/api/auth/me", headers=_hdr(a["token"])).status_code == 429
    # ...but user B — same TestClient, same client IP, unseeded — is not, and every read
    # endpoint permits normal single-call use (never a false 429).
    for path in READ_ENDPOINTS:
        r = client.get(path, headers=_hdr(b["token"]))
        assert r.status_code != 429, f"{path} 429'd a fresh user: {r.status_code} {r.text}"
