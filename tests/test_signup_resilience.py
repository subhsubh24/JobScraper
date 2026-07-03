"""Signup-resilience regression guard (FACTORY_STANDARD §32, issue #212).

A non-essential side-effect must NEVER hard-block a core user action. The register endpoint
commits the new account FIRST, then runs best-effort side-effects (referral attribution +
aggregate analytics). These tests FORCE each side-effect to fail and assert the account is
STILL created and the failure is LOGGED — so a future refactor that moves a side-effect
before the commit, or drops its guard, fails LOUD here instead of causing a signup outage
(the AptDesignerAI class of bug: a profile-insert trigger that rolled back auth.users).
"""
import logging
from contextlib import contextmanager

from src.db.models import User

# The register endpoint logs side-effect failures through the app's "career_operator" logger.
# Capturing that log robustly in a FULL-suite run (not just in isolation) requires bypassing
# two forms of shared-state pollution left by earlier tests — the real reason PR #216's
# assertion passed alone but flaked in the suite, so auto-merge never went green:
#   1. `setup_logging()` (src/api/logging_config.py) REPLACES the root logger's handlers, which
#      destabilizes pytest's caplog (a root handler) — so we attach a handler DIRECTLY to the
#      app logger instead of relying on propagation to root.
#   2. Some earlier test leaves the "career_operator" logger `.disabled = True` (the classic
#      `dictConfig(disable_existing_loggers=True)` side effect), which makes `logger.warning()`
#      a silent no-op — so we force `.disabled = False` for the capture window (and restore it).
# The product logger is never disabled in prod (setup_logging doesn't disable it), so the §32
# log genuinely fires there; this only shields the assertion from suite-wide test pollution.
APP_LOGGER = "career_operator"


@contextmanager
def _capture_app_warnings():
    logger = logging.getLogger(APP_LOGGER)
    records: list[logging.LogRecord] = []
    handler = logging.Handler()
    handler.emit = records.append  # type: ignore[method-assign]
    old_level, old_disabled = logger.level, logger.disabled
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    logger.disabled = False
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
        logger.disabled = old_disabled


def _register(client, email, ref=None):
    body = {"email": email, "password": "password123"}
    if ref is not None:
        body["referral_code"] = ref
    return client.post("/api/auth/register", json=body)


def _boom(*args, **kwargs):
    raise RuntimeError("forced side-effect failure")


def _account_rows(db, email):
    return db.query(User).filter(User.email == email).count()


def test_signup_succeeds_when_referral_apply_fails(client, db_session, monkeypatch):
    """referrals.apply_referral blowing up must not fail the signup — the account is already
    committed, and the endpoint swallows + logs the referral failure."""
    monkeypatch.setattr("asgi.referrals.apply_referral", _boom)
    with _capture_app_warnings() as records:
        r = _register(client, "ref-apply-fail@example.com")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True and body["token"]
    assert _account_rows(db_session, "ref-apply-fail@example.com") == 1
    assert any("referral" in rec.getMessage().lower() for rec in records)


def test_signup_succeeds_when_referral_ensure_code_fails(client, db_session, monkeypatch):
    """A failure in the FIRST referral step (ensure_code) must also leave the account created."""
    monkeypatch.setattr("asgi.referrals.ensure_code", _boom)
    r = _register(client, "ref-code-fail@example.com")
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True
    assert _account_rows(db_session, "ref-code-fail@example.com") == 1


def test_signup_succeeds_when_analytics_raises(client, db_session, monkeypatch):
    """record_event() is contractually never-raising, but the endpoint must NOT depend on
    that: force it to raise and assert the account is STILL created + the failure logged
    (FACTORY_STANDARD §32 defense-in-depth at the call site). Without the call-site guard
    this would 500 despite the account row already being committed."""
    monkeypatch.setattr("asgi.analytics.record_event", _boom)
    with _capture_app_warnings() as records:
        r = _register(client, "analytics-fail@example.com")
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True
    assert _account_rows(db_session, "analytics-fail@example.com") == 1
    assert any("analytics" in rec.getMessage().lower() for rec in records)


def test_signup_succeeds_when_every_side_effect_fails(client, db_session, monkeypatch):
    """Belt-and-suspenders: with BOTH the referral step AND analytics failing at once, a brand
    new user still gets a usable account (row persisted + a real token returned)."""
    monkeypatch.setattr("asgi.referrals.apply_referral", _boom)
    monkeypatch.setattr("asgi.referrals.ensure_code", _boom)
    monkeypatch.setattr("asgi.analytics.record_event", _boom)
    r = _register(client, "all-fail@example.com")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True and body["token"]
    assert _account_rows(db_session, "all-fail@example.com") == 1
    # The returned token actually authenticates — the account is truly usable, not orphaned.
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "all-fail@example.com"
