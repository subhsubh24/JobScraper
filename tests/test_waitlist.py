"""Waitlist capture endpoint (Track G/H).

Outcome-asserting: the real side-effect is a row in the `waitlist` table, and the response
must never (a) reveal whether an email is already on the list (enumeration), nor (b) claim an
email was sent (none is — no provider is wired; SIDE-EFFECT INTEGRITY).
"""
from src.db.models import Waitlist


def test_join_creates_waitlist_row(client, db_session):
    r = client.post("/api/waitlist/join", json={"email": "alice@example.com", "full_name": "Alice"})
    assert r.status_code == 200
    assert r.json()["success"] is True

    row = db_session.query(Waitlist).filter(Waitlist.email == "alice@example.com").one()
    assert row.full_name == "Alice"
    assert row.source == "organic"  # default when not supplied
    assert row.confirmed_at is None  # double-opt-in not wired yet


def test_email_is_normalized_lowercase(client, db_session):
    r = client.post("/api/waitlist/join", json={"email": "  MixedCase@Example.COM "})
    assert r.status_code == 200
    assert db_session.query(Waitlist).filter(Waitlist.email == "mixedcase@example.com").count() == 1


def test_source_is_recorded(client, db_session):
    client.post("/api/waitlist/join", json={"email": "ref@example.com", "source": "referral"})
    row = db_session.query(Waitlist).filter(Waitlist.email == "ref@example.com").one()
    assert row.source == "referral"


def test_enumeration_defense_existing_email_indistinguishable(client, db_session):
    """An already-present email returns the IDENTICAL response to a fresh one — no signal
    about whether the address is on the list — and never creates a duplicate row."""
    first = client.post("/api/waitlist/join", json={"email": "dup@example.com"})
    second = client.post("/api/waitlist/join", json={"email": "dup@example.com"})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()  # byte-identical body
    assert db_session.query(Waitlist).filter(Waitlist.email == "dup@example.com").count() == 1


def test_no_fake_email_claim(client):
    """SIDE-EFFECT INTEGRITY: no email is sent, so the response must not imply one was."""
    body = client.post("/api/waitlist/join", json={"email": "honest@example.com"}).json()
    msg = body.get("message", "").lower()
    assert "check your" not in msg and "inbox" not in msg and "sent" not in msg


def test_invalid_email_rejected(client, db_session):
    for bad in ["notanemail", "no@domain", "@example.com", "spaces in@email.com"]:
        r = client.post("/api/waitlist/join", json={"email": bad})
        assert r.status_code == 400, bad
    assert db_session.query(Waitlist).count() == 0


def test_rate_limited_after_burst(client):
    """5 signups/hour per IP; the 6th from the same client is throttled (abuse defense)."""
    for i in range(5):
        assert client.post("/api/waitlist/join", json={"email": f"user{i}@example.com"}).status_code == 200
    blocked = client.post("/api/waitlist/join", json={"email": "user6@example.com"})
    assert blocked.status_code == 429
