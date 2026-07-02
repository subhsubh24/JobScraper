"""Unit coverage for the email abstraction + waitlist confirm tokens (Track H).

The email seam must degrade HONESTLY: the default dry-run backend reports NOT delivered and
never raises, so a caller can be best-effort without ever claiming a false send. The confirm
token must be a forge-proof, email-bound HMAC.
"""
import pytest

from src.email import (
    CaptureBackend,
    DryRunBackend,
    EmailMessage,
    email_enabled,
    get_email_backend,
    send_email,
    set_email_backend,
)
from src.email.tokens import make_confirm_token, verify_confirm_token


@pytest.fixture(autouse=True)
def _reset_backend():
    # Never leak an overridden backend into another test (env-selected default afterwards).
    yield
    set_email_backend(None)


def _msg(to="a@example.com"):
    return EmailMessage(to=to, subject="Hi", text_body="body")


def test_dryrun_backend_reports_not_delivered_and_never_raises():
    set_email_backend(DryRunBackend())
    result = send_email(_msg())
    assert result.delivered is False
    assert result.backend == "dryrun"
    assert email_enabled() is False  # honest: nothing is actually delivered


def test_capture_backend_records_and_reports_delivered():
    cap = CaptureBackend()
    set_email_backend(cap)
    assert email_enabled() is True
    result = send_email(_msg("who@example.com"))
    assert result.delivered is True
    assert len(cap.outbox) == 1
    assert cap.outbox[0].to == "who@example.com"


def test_backend_selected_from_env(monkeypatch):
    set_email_backend(None)  # force re-read from env
    monkeypatch.setenv("EMAIL_BACKEND", "capture")
    assert isinstance(get_email_backend(), CaptureBackend)
    set_email_backend(None)
    monkeypatch.setenv("EMAIL_BACKEND", "dryrun")
    assert isinstance(get_email_backend(), DryRunBackend)
    set_email_backend(None)
    monkeypatch.delenv("EMAIL_BACKEND", raising=False)
    assert isinstance(get_email_backend(), DryRunBackend)  # default is dry-run


def test_confirm_token_round_trip_and_case_insensitive():
    tok = make_confirm_token("User@Example.com")
    assert verify_confirm_token("user@example.com", tok) is True  # normalized
    assert verify_confirm_token("USER@EXAMPLE.COM", tok) is True


def test_confirm_token_rejects_forgery_and_tamper():
    tok = make_confirm_token("real@example.com")
    # Wrong email (link tampered) -> the HMAC no longer matches.
    assert verify_confirm_token("attacker@example.com", tok) is False
    # A guessed/garbage token is rejected.
    assert verify_confirm_token("real@example.com", "deadbeef") is False
    assert verify_confirm_token("real@example.com", "") is False
    # A different secret would produce a different token (bound to JWT_SECRET).
    assert make_confirm_token("real@example.com") == tok  # deterministic
