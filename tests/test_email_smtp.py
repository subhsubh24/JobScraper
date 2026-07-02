"""SMTPBackend tests — the real delivering email path, validated WITHOUT a live SMTP server.

`smtplib.SMTP` is monkeypatched with an in-memory fake, so we assert the real envelope/headers
are built and dispatched correctly, that STARTTLS + login fire when configured, and — critically
for SIDE-EFFECT INTEGRITY — that a send FAILURE returns ``delivered=False`` (never a false "sent")
without raising. Also pins the honest env selection (incomplete SMTP config -> dry-run, not a
silent no-op that claims delivery).
"""
import smtplib

import pytest

from src.email import sender
from src.email.sender import (
    DryRunBackend,
    EmailMessage,
    SMTPBackend,
    email_enabled,
    get_email_backend,
    set_email_backend,
)


class FakeSMTP:
    """Records what a real ``smtplib.SMTP`` would receive; supports the ``with`` protocol."""

    instances = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_args = None
        self.sent = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, user, password):
        self.login_args = (user, password)

    def send_message(self, mime):
        self.sent.append(mime)


@pytest.fixture(autouse=True)
def _reset_backend():
    FakeSMTP.instances = []
    yield
    set_email_backend(None)  # reset to env-selected so no test leaks a backend


def _backend(**over):
    cfg = dict(host="smtp.example.com", from_addr="noreply@careeroperator.app", port=587)
    cfg.update(over)
    return SMTPBackend(**cfg)


def test_send_delivers_and_builds_correct_envelope(monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    backend = _backend(username="apikey", password="secret")

    result = backend.send(EmailMessage(
        to="user@example.com", subject="Confirm your spot", text_body="Click the link."))

    assert result.delivered is True
    assert result.backend == "smtp"
    assert len(FakeSMTP.instances) == 1
    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port) == ("smtp.example.com", 587)
    assert smtp.timeout == 10.0  # fail-fast default, below any serverless budget
    assert smtp.started_tls is True
    assert smtp.login_args == ("apikey", "secret")
    assert len(smtp.sent) == 1
    mime = smtp.sent[0]
    assert mime["To"] == "user@example.com"
    assert mime["From"] == "noreply@careeroperator.app"
    assert mime["Subject"] == "Confirm your spot"
    assert mime.get_payload(decode=True).decode("utf-8") == "Click the link."


def test_no_login_when_username_absent(monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    backend = _backend()  # no username

    result = backend.send(EmailMessage(to="u@example.com", subject="s", text_body="b"))

    assert result.delivered is True
    assert FakeSMTP.instances[0].login_args is None  # never attempted a login without a username


def test_no_starttls_when_disabled(monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    backend = _backend(use_starttls=False)

    backend.send(EmailMessage(to="u@example.com", subject="s", text_body="b"))

    assert FakeSMTP.instances[0].started_tls is False


def test_html_multipart_when_html_body_present(monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    backend = _backend()

    backend.send(EmailMessage(
        to="u@example.com", subject="s", text_body="plain", html_body="<b>rich</b>"))

    mime = FakeSMTP.instances[0].sent[0]
    assert mime.is_multipart()
    types = {p.get_content_type() for p in mime.get_payload()}
    assert types == {"text/plain", "text/html"}


def test_send_failure_returns_not_delivered_without_raising(monkeypatch):
    def boom(*a, **k):
        raise smtplib.SMTPConnectError(421, "cannot connect")

    monkeypatch.setattr(smtplib, "SMTP", boom)
    backend = _backend()

    result = backend.send(EmailMessage(to="u@example.com", subject="s", text_body="b"))

    assert result.delivered is False  # SIDE-EFFECT INTEGRITY: no false "sent" on failure
    assert "SMTP send failed" in result.detail


def test_from_env_returns_none_when_config_incomplete(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_FROM", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    assert SMTPBackend.from_env() is None


def test_from_env_builds_backend_when_configured(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.com")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_STARTTLS", "false")
    backend = SMTPBackend.from_env()
    assert isinstance(backend, SMTPBackend)
    assert backend.host == "smtp.example.com"
    assert backend.port == 2525
    assert backend.use_starttls is False


def test_from_addr_falls_back_to_username(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.delenv("SMTP_FROM", raising=False)
    monkeypatch.setenv("SMTP_USERNAME", "login@example.com")
    backend = SMTPBackend.from_env()
    assert backend is not None and backend.from_addr == "login@example.com"


def test_env_selection_smtp_incomplete_falls_back_to_dryrun(monkeypatch):
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_FROM", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    set_email_backend(None)  # force re-read from env
    backend = get_email_backend()
    assert isinstance(backend, DryRunBackend)  # honest: no silent no-op that claims delivery
    assert email_enabled() is False


def test_env_selection_smtp_complete_selects_smtp(monkeypatch):
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.com")
    set_email_backend(None)  # force re-read from env
    backend = get_email_backend()
    assert isinstance(backend, SMTPBackend)
    assert email_enabled() is True


def test_email_enabled_false_for_dryrun():
    set_email_backend(DryRunBackend())
    assert email_enabled() is False


def test_smtp_backend_declares_delivers():
    assert _backend().delivers is True
    assert sender.DryRunBackend.delivers is False
