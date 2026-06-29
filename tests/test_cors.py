"""CORS allow-list hardening (Quality #94, Track F).

The API must NEVER fall back to a wide-open ``allow_origins=["*"]`` policy. The unified
Vercel deploy is same-origin and the mobile app is native (CORS is browser-only), so a
locked default breaks no real client while closing the wide-open-CORS hardening gap.
"""
from asgi import resolve_cors_origins


def test_explicit_origins_are_used_verbatim():
    explicit = ["https://app.example.com", "https://example.com"]
    assert resolve_cors_origins(explicit, is_vercel=True) == explicit
    assert resolve_cors_origins(explicit, is_vercel=False) == explicit


def test_production_default_is_locked_not_wildcard():
    # Vercel + no explicit allow-list -> deny cross-origin (same-origin web still works).
    origins = resolve_cors_origins([], is_vercel=True)
    assert origins == []
    assert "*" not in origins


def test_local_default_allows_localhost_dev_not_wildcard():
    # Local dev + no explicit allow-list -> localhost Next dev/E2E origins, never "*".
    origins = resolve_cors_origins([], is_vercel=False)
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:3000" in origins
    assert "*" not in origins


def test_default_never_returns_wildcard_in_any_mode():
    for is_vercel in (True, False):
        assert "*" not in resolve_cors_origins([], is_vercel=is_vercel)
