"""Email provider abstraction (Track H).

A thin, honest sending seam. The DEFAULT backend is **dry-run**: it logs the message and
reports `delivered=False` — it NEVER claims an email was sent when no provider is connected
(SIDE-EFFECT INTEGRITY: a "sent" the user can't verify is a lie). A real provider (SMTP / an
ESP) is a future wire-up gated on an owner-provided key; until then callers must degrade
honestly and never gate a flow on an email that didn't leave the system (DECISION COROLLARY).

Backends are selected by the `EMAIL_BACKEND` env var (`dryrun` default; `capture` for tests).
Tests use the in-memory `CaptureBackend` (which simulates a connected provider) to exercise the
real round-trip — dispatch → retrieve → follow the confirm link — so double-opt-in is proven
end-to-end in CI without any live secret.
"""
from src.email.sender import (
    CaptureBackend,
    DryRunBackend,
    EmailMessage,
    EmailResult,
    email_enabled,
    get_email_backend,
    send_email,
    set_email_backend,
)

__all__ = [
    "EmailMessage",
    "EmailResult",
    "DryRunBackend",
    "CaptureBackend",
    "send_email",
    "email_enabled",
    "get_email_backend",
    "set_email_backend",
]
