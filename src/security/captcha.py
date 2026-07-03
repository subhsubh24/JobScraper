"""Bot / abuse protection seam for the PUBLIC forms (Track F — CAPTCHA on public forms).

Design (mirrors the email/billing seams — a pluggable provider that ENFORCES only when the
owner has connected it):

- Provider = Cloudflare Turnstile (privacy-friendly, no PII, free). The server verifies a
  client-supplied ``captcha_token`` against Turnstile's ``siteverify`` endpoint using the
  owner-provided ``TURNSTILE_SECRET`` (server-side only — the secret NEVER reaches a client;
  the client uses the separate public ``sitekey``).

- DECISION COROLLARY (FACTORY_STANDARD §6): we do NOT introduce a hard gate whose dependency
  isn't wired. Until the owner sets ``TURNSTILE_SECRET`` the seam is a NO-OP —
  ``captcha_enabled()`` is False and ``verify_captcha()`` returns True — so pre-launch flows on
  BOTH web and native mobile work unchanged (no dead-end, no breakage). The rate limiter on
  these endpoints is the always-on baseline defense; captcha is defense-in-depth against
  distributed/automated signup+login floods that rotate IPs.

- !! CONNECT ORDER — READ BEFORE SETTING ``TURNSTILE_SECRET`` (an owner-facing
  ``connect-captcha`` OWNER_ACTION covering this is filed in PENDING_OPS via the accompanying
  bookkeeping PR): the WEB client sends a token once ``NEXT_PUBLIC_TURNSTILE_SITEKEY`` is set,
  but the NATIVE MOBILE app sends NO ``captcha_token`` (no native widget ships in this change —
  it is a native/owner follow-up). Because enforcement fails CLOSED, turning on
  ``TURNSTILE_SECRET`` BEFORE a mobile challenge flow exists would 403 EVERY native mobile
  register + login — a full mobile-auth outage. Likewise, setting ``TURNSTILE_SECRET`` without
  the web ``NEXT_PUBLIC_TURNSTILE_SITEKEY`` would 403 the web forms too. Enable the secret ONLY
  after BOTH the web sitekey AND a mobile widget are deployed.

- FAIL CLOSED when enforcement is ON: a missing token, an invalid token, or a verifier
  error/timeout all reject (return False). Because the whole path is gated on the owner having
  deliberately enabled it, failing closed can't dead-end a pre-launch user; it does stop an
  attacker from bypassing the check by omitting the token or DoSing the verifier. The external
  call has a timeout SHORTER than the serverless budget (FACTORY_STANDARD hard rule).
"""
import logging
import os
from typing import Optional

import requests  # runtime dep (requirements.txt) — same client the ATS ingestion uses

logger = logging.getLogger("career_operator.captcha")

# Cloudflare Turnstile server-side verification endpoint.
_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# Shorter than the serverless function budget so a slow/hung verifier can never exhaust it.
_VERIFY_TIMEOUT_S = 5.0

# Bound the accepted token size (Turnstile tokens are well under this) so a caller can't push
# an unbounded blob through the verifier as an amplification/DoS vector.
MAX_TOKEN_LEN = 4096


def captcha_enabled() -> bool:
    """True only when the owner has connected Turnstile (server secret set).

    While False the seam is a pure no-op: every ``verify_captcha`` returns True, so no public
    form is gated — the honest pre-launch state (rate limits still apply)."""
    return bool(os.getenv("TURNSTILE_SECRET"))


def verify_captcha(token: Optional[str], remote_ip: Optional[str] = None) -> bool:
    """Return True iff the challenge is satisfied.

    - Captcha not configured -> True (no enforcement; honest degrade — DECISION COROLLARY).
    - Configured + valid, unspent token -> True.
    - Configured + missing/oversized/invalid token, or verifier error/timeout -> False
      (fail closed).
    """
    secret = os.getenv("TURNSTILE_SECRET")
    if not secret:
        return True  # seam disabled — do not gate

    if not token or len(token) > MAX_TOKEN_LEN:
        return False  # enabled but no/oversized token -> reject

    data = {"secret": secret, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        resp = requests.post(_SITEVERIFY_URL, data=data, timeout=_VERIFY_TIMEOUT_S)
        resp.raise_for_status()
        body = resp.json()
    except (requests.RequestException, ValueError):
        # Network/timeout/HTTP error or non-JSON body: fail closed. Only reachable when the
        # owner has ENABLED enforcement, so this never dead-ends a pre-launch user.
        logger.warning("captcha verification call failed; rejecting (fail-closed)", exc_info=True)
        return False

    return body.get("success") is True
