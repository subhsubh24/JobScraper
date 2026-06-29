"""Track F: proxy-aware client-IP extraction for rate limiting + Permissions-Policy.

The rate limiter must bucket by the ORIGINATING client, not the proxy, when we
sit behind a trusted edge — otherwise every user shares one bucket. But it must
NOT trust client-supplied forwarding headers when there is no trusted proxy, or
the limiter is trivially bypassable. These tests pin both halves of that
contract, plus the new Permissions-Policy security header.
"""

import os
from types import SimpleNamespace

import pytest

from src.api.ip_extraction import get_client_ip


def _request(headers=None, peer="203.0.113.9"):
    """Minimal stand-in for a Starlette Request (only .headers + .client used)."""
    # Starlette lowercases header keys; mimic that with a case-insensitive get.
    hdrs = {k.lower(): v for k, v in (headers or {}).items()}
    return SimpleNamespace(
        headers=SimpleNamespace(get=lambda k, default=None: hdrs.get(k.lower(), default)),
        client=SimpleNamespace(host=peer) if peer else None,
    )


@pytest.fixture(autouse=True)
def _clear_proxy_env():
    saved = {k: os.environ.get(k) for k in ("TRUST_PROXY_HEADERS", "VERCEL")}
    for k in saved:
        os.environ.pop(k, None)
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_untrusted_ignores_forwarding_headers():
    # No trusted proxy: a spoofed X-Forwarded-For must NOT change the bucket key —
    # we use the direct socket peer (which cannot be spoofed).
    req = _request({"X-Forwarded-For": "1.2.3.4", "X-Real-IP": "5.6.7.8"}, peer="203.0.113.9")
    assert get_client_ip(req) == "203.0.113.9"


def test_trusted_prefers_x_real_ip():
    os.environ["TRUST_PROXY_HEADERS"] = "1"
    req = _request({"X-Real-IP": "5.6.7.8", "X-Forwarded-For": "9.9.9.9"}, peer="10.0.0.1")
    assert get_client_ip(req) == "5.6.7.8"


def test_trusted_uses_leftmost_xff_when_no_real_ip():
    os.environ["TRUST_PROXY_HEADERS"] = "1"
    req = _request({"X-Forwarded-For": "8.8.8.8, 70.0.0.1, 70.0.0.2"}, peer="10.0.0.1")
    assert get_client_ip(req) == "8.8.8.8"


def test_vercel_env_enables_trust_by_default():
    os.environ["VERCEL"] = "1"
    req = _request({"X-Real-IP": "5.6.7.8"}, peer="10.0.0.1")
    assert get_client_ip(req) == "5.6.7.8"


def test_explicit_opt_out_overrides_vercel():
    # The escape hatch: even on Vercel, TRUST_PROXY_HEADERS=0 forces use of the socket
    # peer (e.g. if a future deploy's trust surface changes).
    os.environ["VERCEL"] = "1"
    os.environ["TRUST_PROXY_HEADERS"] = "0"
    req = _request({"X-Real-IP": "5.6.7.8", "X-Forwarded-For": "9.9.9.9"}, peer="10.0.0.1")
    assert get_client_ip(req) == "10.0.0.1"


def test_garbage_forwarding_header_falls_back_to_peer():
    os.environ["TRUST_PROXY_HEADERS"] = "1"
    req = _request({"X-Forwarded-For": "not-an-ip", "X-Real-IP": "also-bad"}, peer="10.0.0.1")
    assert get_client_ip(req) == "10.0.0.1"


def test_no_client_returns_unknown():
    os.environ["TRUST_PROXY_HEADERS"] = "1"
    req = _request({}, peer=None)
    assert get_client_ip(req) == "unknown"


def test_permissions_policy_header_present():
    from fastapi.testclient import TestClient

    from asgi import app

    with TestClient(app) as client:
        r = client.get("/api/health")
    pp = r.headers.get("Permissions-Policy", "")
    assert "camera=()" in pp
    assert "geolocation=()" in pp
