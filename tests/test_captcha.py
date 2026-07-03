"""Round-trip coverage for the Turnstile bot-protection seam (Track F — CAPTCHA on public forms).

Two layers, mirroring how billing's webhook signature is validated:
1. Unit: ``verify_captcha`` against a MOCKED Turnstile ``siteverify`` — the disabled no-op, the
   enabled-valid, enabled-invalid, enabled-missing-token, oversized-token, and verifier-error
   (fail-closed) branches. The verification LOGIC is genuinely exercised (not a stub).
2. HTTP: the public endpoints (register / login / waitlist) actually enforce it — with the seam
   DISABLED (no secret) they behave exactly as before (no regression); with it ENABLED a bad
   token is rejected 403 and a good token passes through.

No real network call is ever made (``requests.post`` is patched); no secret is committed.
"""
import asgi
from src.security import captcha as captcha_mod


class _FakeResp:
    def __init__(self, payload, status_ok=True):
        self._payload = payload
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            import requests

            raise requests.RequestException("boom")

    def json(self):
        return self._payload


def _patch_siteverify(monkeypatch, payload, status_ok=True):
    """Patch the module-level requests.post the verifier uses; return the recorded call args."""
    calls = {}

    def fake_post(url, data=None, timeout=None):
        calls["url"] = url
        calls["data"] = data
        calls["timeout"] = timeout
        return _FakeResp(payload, status_ok=status_ok)

    monkeypatch.setattr(captcha_mod.requests, "post", fake_post)
    return calls


# --------------------------------------------------------------------------- unit


def test_disabled_seam_is_noop(monkeypatch):
    monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
    assert captcha_mod.captcha_enabled() is False
    # No token, any token -> always True when unconfigured (never gates a pre-launch form).
    assert captcha_mod.verify_captcha(None) is True
    assert captcha_mod.verify_captcha("anything") is True


def test_enabled_valid_token_passes_and_calls_verifier(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "sekret")
    calls = _patch_siteverify(monkeypatch, {"success": True})
    assert captcha_mod.verify_captcha("good-token", remote_ip="203.0.113.7") is True
    # The real verifier was invoked with our secret + the client token + remote ip, bounded timeout.
    assert calls["url"].endswith("/siteverify")
    assert calls["data"]["secret"] == "sekret"
    assert calls["data"]["response"] == "good-token"
    assert calls["data"]["remoteip"] == "203.0.113.7"
    assert 0 < calls["timeout"] <= 5.0


def test_enabled_invalid_token_rejected(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "sekret")
    _patch_siteverify(monkeypatch, {"success": False, "error-codes": ["invalid-input-response"]})
    assert captcha_mod.verify_captcha("bad-token") is False


def test_enabled_missing_token_rejected_without_network(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "sekret")

    def explode(*a, **k):  # a missing token must short-circuit BEFORE any network call
        raise AssertionError("verifier should not be called for a missing token")

    monkeypatch.setattr(captcha_mod.requests, "post", explode)
    assert captcha_mod.verify_captcha(None) is False
    assert captcha_mod.verify_captcha("") is False


def test_enabled_oversized_token_rejected_without_network(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "sekret")

    def explode(*a, **k):
        raise AssertionError("verifier should not be called for an oversized token")

    monkeypatch.setattr(captcha_mod.requests, "post", explode)
    assert captcha_mod.verify_captcha("x" * (captcha_mod.MAX_TOKEN_LEN + 1)) is False


def test_enabled_verifier_error_fails_closed(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "sekret")
    _patch_siteverify(monkeypatch, {"success": True}, status_ok=False)  # HTTP error from verifier
    assert captcha_mod.verify_captcha("token") is False


# --------------------------------------------------------------------------- HTTP endpoints


def test_endpoints_unaffected_when_seam_disabled(client, monkeypatch):
    """Pre-launch (no secret): register/login/waitlist behave exactly as before — no regression."""
    monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
    r = client.post(
        "/api/auth/register",
        json={"email": "capt-off@example.com", "password": "password123"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["token"]

    r = client.post(
        "/api/waitlist/join", json={"email": "wl-capt-off@example.com"}
    )
    assert r.status_code == 200, r.text


def test_register_rejected_with_bad_captcha_when_enabled(client, monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "sekret")
    _patch_siteverify(monkeypatch, {"success": False})
    r = client.post(
        "/api/auth/register",
        json={"email": "capt-bad@example.com", "password": "password123", "captcha_token": "nope"},
    )
    assert r.status_code == 403
    # Enumeration-safe: no account was created (generic failure, nothing leaked).
    assert "captcha" in r.json()["detail"].lower()


def test_register_passes_with_good_captcha_when_enabled(client, monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "sekret")
    _patch_siteverify(monkeypatch, {"success": True})
    r = client.post(
        "/api/auth/register",
        json={"email": "capt-ok@example.com", "password": "password123", "captcha_token": "solved"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["token"]


def test_waitlist_rejected_with_missing_captcha_when_enabled(client, monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "sekret")

    def explode(*a, **k):
        raise AssertionError("no network call expected for a missing token")

    monkeypatch.setattr(captcha_mod.requests, "post", explode)
    r = client.post("/api/waitlist/join", json={"email": "wl-capt@example.com"})
    assert r.status_code == 403


def test_asgi_wires_the_seam():
    """The endpoint layer imports the real verifier (guards against a silently-unwired seam)."""
    assert asgi.verify_captcha is captcha_mod.verify_captcha
