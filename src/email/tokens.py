"""Stateless HMAC confirmation tokens for the waitlist double-opt-in.

A confirm token is ``HMAC-SHA256(JWT_SECRET, "waitlist-confirm:<email>")``. It is bound to the
email, so tampering with the address in the link invalidates the token; it needs no DB column
(hence no migration) and cannot be forged without the server secret. Verification is
constant-time. We reuse ``JWT_SECRET`` (already required server-side in production) so no new
secret / owner action is introduced.
"""
import hashlib
import hmac
import os

_PURPOSE = "waitlist-confirm"


def _secret() -> bytes:
    # Same secret the auth layer signs sessions with; required (and fail-loud) in production.
    return os.getenv("JWT_SECRET", "dev-secret-change-in-production").encode("utf-8")


def make_confirm_token(email: str) -> str:
    """Return the HMAC confirm token for ``email`` (case-insensitive)."""
    message = f"{_PURPOSE}:{email.strip().lower()}".encode("utf-8")
    return hmac.new(_secret(), message, hashlib.sha256).hexdigest()


def verify_confirm_token(email: str, token: str) -> bool:
    """Constant-time check that ``token`` is the valid confirm token for ``email``."""
    if not token:
        return False
    expected = make_confirm_token(email)
    return hmac.compare_digest(expected, token)
