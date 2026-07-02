"""FUNCTIONAL journey: waitlist double-opt-in round-trip (Track H / F4.1).

Proves the SIDE-EFFECT end-to-end against a running app: joining dispatches a real confirmation
message (via the in-memory capture backend that stands in for a connected provider), the emailed
HMAC link actually flips ``confirmed_at``, forged links grant nothing, and — crucially — with the
default dry-run backend the flow still WORKS (row captured) and NEVER claims a false send.
"""
import re
from urllib.parse import parse_qs, urlparse

import pytest

from src.db.models import Waitlist
from src.email import CaptureBackend, DryRunBackend, set_email_backend


@pytest.fixture(autouse=True)
def _email_env(monkeypatch):
    # WEB_APP_URL is the TRUSTED origin the confirm link is built from (never the request Host,
    # to avoid a Host-header phishing primitive). Set it so the operational send path runs.
    monkeypatch.setenv("WEB_APP_URL", "http://testserver")
    yield
    set_email_backend(None)


def _confirm_link(message) -> str:
    m = re.search(r"http://\S+/api/waitlist/confirm\?\S+", message.text_body)
    assert m, f"no confirm link in email body: {message.text_body!r}"
    return m.group(0)


def test_double_optin_full_round_trip(client, db_session):
    cap = CaptureBackend()
    set_email_backend(cap)  # simulate a connected provider

    # 1) Join -> row captured + a confirm email dispatched to the right recipient.
    r = client.post("/api/waitlist/join", json={"email": "New.User@Example.com", "full_name": "N"})
    assert r.status_code == 200, r.text
    assert "confirm" in r.json()["message"].lower()  # honest: a provider IS connected
    assert len(cap.outbox) == 1
    assert cap.outbox[0].to == "new.user@example.com"

    row = db_session.query(Waitlist).filter(Waitlist.email == "new.user@example.com").one()
    assert row.confirmed_at is None  # not confirmed until the link is followed

    # 2) Follow the emailed link -> confirmed_at is stamped, redirect says ok.
    link = _confirm_link(cap.outbox[0])
    q = parse_qs(urlparse(link).query)
    r2 = client.get("/api/waitlist/confirm", params={"email": q["email"][0], "token": q["token"][0]},
                    follow_redirects=False)
    assert r2.status_code == 303
    assert "/waitlist/confirmed?status=ok" in r2.headers["location"]

    db_session.expire_all()
    row = db_session.query(Waitlist).filter(Waitlist.email == "new.user@example.com").one()
    assert row.confirmed_at is not None
    first_confirmed = row.confirmed_at

    # 3) Idempotent: following the link again is still ok and does NOT re-stamp.
    r3 = client.get("/api/waitlist/confirm", params={"email": q["email"][0], "token": q["token"][0]},
                    follow_redirects=False)
    assert r3.status_code == 303
    assert "status=ok" in r3.headers["location"]
    db_session.expire_all()
    reloaded = db_session.query(Waitlist).filter(Waitlist.email == "new.user@example.com").one()
    assert reloaded.confirmed_at == first_confirmed  # not re-stamped on the second click


def test_forged_token_confirms_nothing(client, db_session):
    set_email_backend(CaptureBackend())
    client.post("/api/waitlist/join", json={"email": "victim@example.com"})

    r = client.get("/api/waitlist/confirm", params={"email": "victim@example.com", "token": "not-a-valid-hmac"},
                   follow_redirects=False)
    assert r.status_code == 303
    assert "status=invalid" in r.headers["location"]

    db_session.expire_all()
    row = db_session.query(Waitlist).filter(Waitlist.email == "victim@example.com").one()
    assert row.confirmed_at is None  # a forged link grants nothing


def test_no_email_sent_without_trusted_base(client, db_session, monkeypatch):
    # SECURITY REGRESSION: a real provider is connected but WEB_APP_URL is unset. The confirm
    # link must NOT be derived from the request Host header (a spoofed Host would email a victim
    # an attacker-domain link — a phishing primitive). So NO email is sent and the response must
    # not claim one was; the row is still captured.
    monkeypatch.delenv("WEB_APP_URL", raising=False)
    cap = CaptureBackend()
    set_email_backend(cap)
    r = client.post("/api/waitlist/join", json={"email": "notrust@example.com"})
    assert r.status_code == 200, r.text
    assert "check your email" not in r.json()["message"].lower()
    assert cap.outbox == []  # no Host-derived link ever emailed
    row = db_session.query(Waitlist).filter(Waitlist.email == "notrust@example.com").one()
    assert row.email == "notrust@example.com"  # primary side-effect still happened


def test_confirm_redirect_is_never_host_derived(client, monkeypatch):
    # SECURITY REGRESSION (open-redirect / CWE-601): with WEB_APP_URL unset, the confirm
    # endpoint's redirect Location must be HOST-RELATIVE (same-origin), never built from the
    # attacker-controlled Host header — even on the invalid-token branch (no valid token needed).
    monkeypatch.delenv("WEB_APP_URL", raising=False)
    r = client.get(
        "/api/waitlist/confirm",
        params={"email": "x@example.com", "token": "bogus"},
        headers={"Host": "evil.example.com"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    loc = r.headers["location"]
    assert "evil.example.com" not in loc  # attacker Host never reaches the redirect target
    assert loc.startswith("/waitlist/confirmed")  # host-relative, same-origin by construction


def test_dryrun_captures_row_without_faking_delivery(client, db_session):
    # Default state (no provider): the row is still captured, the visitor is NOT dead-ended,
    # and the response does NOT claim an email was sent (no fake success).
    set_email_backend(DryRunBackend())
    r = client.post("/api/waitlist/join", json={"email": "pre@example.com"})
    assert r.status_code == 200, r.text
    assert "check your email" not in r.json()["message"].lower()

    row = db_session.query(Waitlist).filter(Waitlist.email == "pre@example.com").one()
    assert row.email == "pre@example.com"  # real side-effect happened
    assert row.confirmed_at is None


def test_existing_signup_is_enumeration_safe_and_does_not_resend(client):
    cap = CaptureBackend()
    set_email_backend(cap)
    first = client.post("/api/waitlist/join", json={"email": "dup@example.com"})
    second = client.post("/api/waitlist/join", json={"email": "dup@example.com"})
    assert first.json()["message"] == second.json()["message"]  # indistinguishable
    assert len(cap.outbox) == 1  # the repeat submit does NOT re-send (spam/enumeration defense)
