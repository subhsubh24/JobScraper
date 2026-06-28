"""Regression guards for the DEEP_DIAGNOSIS hard rules (fail loud next time)."""
import pytest


def test_llm_client_has_subbudget_timeout(monkeypatch):
    # Rule (a): the LLM client must carry a sub-budget timeout + bounded retries, so a
    # hung Gemini call fails INSIDE the function budget (the graceful except actually runs).
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    import src.llm as llm

    client = llm.get_llm_client()
    assert client is not None
    assert client.max_retries == 1
    assert float(client.timeout) == 45.0


def test_jwt_secret_fails_loud_in_production(monkeypatch):
    # Rule (b): in production (VERCEL set), an unset / dev-default JWT_SECRET must raise,
    # never silently sign tokens with a forgeable key.
    import asgi

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("JWT_SECRET", "dev-secret-change-in-production")
    with pytest.raises(RuntimeError):
        asgi._assert_required_secrets()

    monkeypatch.setenv("JWT_SECRET", "")
    with pytest.raises(RuntimeError):
        asgi._assert_required_secrets()

    monkeypatch.setenv("JWT_SECRET", "a-genuinely-strong-secret")
    asgi._assert_required_secrets()  # real secret -> no raise


def test_jwt_secret_not_required_outside_production(monkeypatch):
    import asgi

    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("JWT_SECRET", "")
    asgi._assert_required_secrets()  # not on Vercel -> never raises (local dev OK)
