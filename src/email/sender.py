"""Email sending abstraction with honest degradation.

Contract:
- ``send_email(msg)`` returns an ``EmailResult`` whose ``delivered`` flag is TRUE only when a
  backend that actually delivers accepted the message. The default dry-run backend returns
  ``delivered=False`` — it logs and drops. Callers MUST NOT report "sent" to a user unless
  ``result.delivered`` is true (or ``email_enabled()`` is true for the connected provider).
- No exception escapes a backend for an ordinary "can't deliver" condition; a backend returns
  a non-delivered result instead, so a best-effort caller never breaks its primary side-effect.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger("career_operator.email")


@dataclass
class EmailMessage:
    """A single outbound message. ``html_body`` is optional; ``text_body`` is required."""

    to: str
    subject: str
    text_body: str
    html_body: Optional[str] = None


@dataclass
class EmailResult:
    """Outcome of a send attempt. ``delivered`` is the ONLY honest signal of success."""

    delivered: bool
    backend: str
    detail: str = ""


class EmailBackend:
    """Base backend. ``delivers`` declares whether this backend actually sends real email."""

    name = "base"
    delivers = False

    def send(self, message: EmailMessage) -> EmailResult:  # pragma: no cover - overridden
        raise NotImplementedError


class DryRunBackend(EmailBackend):
    """Default backend: log the message and report NOT delivered.

    Used pre-launch when no provider is connected. It never raises and never claims delivery —
    the honest state for "email is not wired yet".
    """

    name = "dryrun"
    delivers = False

    def send(self, message: EmailMessage) -> EmailResult:
        logger.info(
            "email dry-run (no provider connected): to=%s subject=%r — NOT delivered",
            message.to,
            message.subject,
        )
        return EmailResult(
            delivered=False,
            backend=self.name,
            detail="no email provider connected; message logged, not delivered",
        )


class CaptureBackend(EmailBackend):
    """In-memory backend for tests: records messages in ``outbox`` and reports delivered.

    Stands in for a connected provider so the confirm round-trip can be exercised in CI (assert
    the message was dispatched to the right recipient, then follow the link) without a live key.
    """

    name = "capture"
    delivers = True

    def __init__(self) -> None:
        self.outbox: List[EmailMessage] = []

    def send(self, message: EmailMessage) -> EmailResult:
        self.outbox.append(message)
        return EmailResult(delivered=True, backend=self.name, detail="captured in-memory outbox")


def _truthy(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off", ""}


class SMTPBackend(EmailBackend):
    """Real delivering backend over SMTP — the production email path.

    Config is read from the environment (NAMES only; never committed):
      - ``SMTP_HOST``     (required) — the SMTP server host
      - ``SMTP_FROM``     (required) — the ``From:`` address (falls back to ``SMTP_USERNAME``)
      - ``SMTP_PORT``     (default 587)
      - ``SMTP_USERNAME`` / ``SMTP_PASSWORD`` (optional — login when a username is set)
      - ``SMTP_STARTTLS`` (default true) — upgrade the connection with STARTTLS
      - ``SMTP_TIMEOUT``  (default 10s) — socket timeout (fail fast; never hang a request)

    Honesty contract (SIDE-EFFECT INTEGRITY + §28):
      - ``delivers = True`` — selecting this backend asserts a real provider IS connected. But
        it is only SELECTED when the required config is present (:meth:`from_env` returns ``None``
        otherwise), so ``email_enabled()`` never lies about an incomplete config.
      - ``send`` returns ``delivered=True`` ONLY after the server accepted the message. On ANY
        failure it LOGS and returns ``delivered=False`` — no exception escapes, so a best-effort
        caller (e.g. the waitlist confirm email) never breaks its primary side-effect, and never
        reports a false "sent".
    """

    name = "smtp"
    delivers = True

    def __init__(
        self,
        *,
        host: str,
        from_addr: str,
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_starttls: bool = True,
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.from_addr = from_addr
        self.port = port
        self.username = username
        self.password = password
        self.use_starttls = use_starttls
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> Optional["SMTPBackend"]:
        """Build from env, or ``None`` when the required config (host + from) is incomplete."""
        host = (os.getenv("SMTP_HOST") or "").strip()
        from_addr = (os.getenv("SMTP_FROM") or os.getenv("SMTP_USERNAME") or "").strip()
        if not host or not from_addr:
            return None
        try:
            port = int(os.getenv("SMTP_PORT") or 587)
            timeout = float(os.getenv("SMTP_TIMEOUT") or 10.0)
        except ValueError:
            logger.error("Invalid SMTP_PORT/SMTP_TIMEOUT — falling back to no SMTP backend.")
            return None
        return cls(
            host=host,
            from_addr=from_addr,
            port=port,
            username=(os.getenv("SMTP_USERNAME") or None),
            password=(os.getenv("SMTP_PASSWORD") or None),
            use_starttls=_truthy(os.getenv("SMTP_STARTTLS"), True),
            timeout=timeout,
        )

    def _build_mime(self, message: EmailMessage):
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        if message.html_body:
            mime = MIMEMultipart("alternative")
            mime.attach(MIMEText(message.text_body, "plain", "utf-8"))
            mime.attach(MIMEText(message.html_body, "html", "utf-8"))
        else:
            mime = MIMEText(message.text_body, "plain", "utf-8")
        mime["Subject"] = message.subject
        mime["From"] = self.from_addr
        mime["To"] = message.to
        return mime

    def send(self, message: EmailMessage) -> EmailResult:
        import smtplib

        try:
            mime = self._build_mime(message)
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as smtp:
                if self.use_starttls:
                    smtp.starttls()
                if self.username:
                    smtp.login(self.username, self.password or "")
                smtp.send_message(mime)
        except Exception as exc:  # never let a delivery failure break the caller's primary op
            logger.warning("SMTP send to %s failed: %s", message.to, exc)
            return EmailResult(delivered=False, backend=self.name, detail=f"SMTP send failed: {exc}")
        logger.info("email sent via SMTP: to=%s subject=%r", message.to, message.subject)
        return EmailResult(delivered=True, backend=self.name, detail="sent via SMTP")


def _make_backend_from_env() -> EmailBackend:
    name = (os.getenv("EMAIL_BACKEND") or "dryrun").strip().lower()
    if name == "capture":
        return CaptureBackend()
    if name == "smtp":
        backend = SMTPBackend.from_env()
        if backend is not None:
            return backend
        # EMAIL_BACKEND=smtp but the config is incomplete: fail LOUD (explicit log) and fall back
        # to the honest dry-run (delivers=False) — never a silent no-op that claims a send (§28).
        logger.error(
            "EMAIL_BACKEND=smtp but SMTP_HOST/SMTP_FROM are unset — email is DISABLED "
            "(dry-run, nothing delivered). Set the SMTP_* config to enable real delivery."
        )
    return DryRunBackend()


_backend: Optional[EmailBackend] = None


def get_email_backend() -> EmailBackend:
    """Return the process email backend, constructing it from ``EMAIL_BACKEND`` on first use."""
    global _backend
    if _backend is None:
        _backend = _make_backend_from_env()
    return _backend


def set_email_backend(backend: Optional[EmailBackend]) -> None:
    """Override the active backend (test hook). Pass ``None`` to reset to env-selected."""
    global _backend
    _backend = backend


def email_enabled() -> bool:
    """True only when the active backend actually delivers email (a real provider is connected)."""
    return get_email_backend().delivers


def send_email(message: EmailMessage) -> EmailResult:
    """Send via the active backend. Returns the honest ``EmailResult`` (never claims a false send)."""
    return get_email_backend().send(message)
