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


def _make_backend_from_env() -> EmailBackend:
    name = (os.getenv("EMAIL_BACKEND") or "dryrun").strip().lower()
    if name == "capture":
        return CaptureBackend()
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
