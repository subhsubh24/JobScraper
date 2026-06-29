"""Trusted client-IP extraction for rate limiting behind a proxy.

WHY THIS EXISTS
---------------
The rate limiter keys its buckets by client IP. On Vercel (and any reverse
proxy), ``request.client.host`` is the IP of the *proxy*, not the end user —
so every visitor collapses into ONE bucket. That makes per-IP limits either
useless (one shared bucket) or a self-inflicted DoS (all users throttled
together). To rate-limit real clients we must read the originating IP from the
forwarding headers the platform sets.

TRUST MODEL (the important part)
--------------------------------
Forwarding headers are CLIENT-CONTROLLED unless a trusted proxy overwrites
them. If we blindly trusted ``X-Forwarded-For`` a client could spoof a fresh
value per request and bypass the limiter entirely — strictly worse than today.
So we only consult forwarding headers when we KNOW a trusted proxy sits in
front of us (``TRUST_PROXY_HEADERS`` is set, which we default ON when the
``VERCEL`` runtime env is present). On Vercel, ``X-Vercel-Forwarded-For`` /
``X-Real-IP`` are set by the platform edge and overwrite any client-supplied
value, so they are trustworthy; ``X-Forwarded-For`` has the real client as its
first (left-most) hop. When NOT behind a trusted proxy (local/dev/tests) we use
the direct socket peer, which cannot be spoofed.
"""

from __future__ import annotations

import ipaddress
import os
from typing import Optional

from fastapi import Request


def _trust_proxy_headers() -> bool:
    """Whether to trust forwarding headers for the client IP.

    Read live (not cached at import) so tests can toggle it via env. Defaults
    ON whenever the Vercel runtime env is present; otherwise opt-in via
    ``TRUST_PROXY_HEADERS=1``.
    """
    explicit = os.getenv("TRUST_PROXY_HEADERS")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes", "on"}
    return bool(os.getenv("VERCEL"))


def _valid_ip(candidate: Optional[str]) -> Optional[str]:
    """Return the candidate if it parses as an IP address, else None."""
    if not candidate:
        return None
    candidate = candidate.strip()
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return None
    return candidate


def get_client_ip(request: Request) -> str:
    """Best-effort originating client IP for rate-limit bucketing.

    Behind a trusted proxy: prefer the platform-set single-value headers
    (``X-Real-IP`` / ``X-Vercel-Forwarded-For``), then the left-most entry of
    ``X-Forwarded-For``. Otherwise (and as a final fallback) use the direct
    socket peer. Always returns a non-empty, stable string so a missing/garbled
    header degrades to coarser bucketing — never to "no limit".
    """
    direct = request.client.host if request.client else None

    if _trust_proxy_headers():
        # Single-value, platform-set headers first (not client-spoofable on Vercel).
        for header in ("x-real-ip", "x-vercel-forwarded-for"):
            ip = _valid_ip(request.headers.get(header))
            if ip:
                return ip
        # X-Forwarded-For: "client, proxy1, proxy2" — the left-most is the origin.
        xff = request.headers.get("x-forwarded-for")
        if xff:
            ip = _valid_ip(xff.split(",")[0])
            if ip:
                return ip

    return direct or "unknown"
