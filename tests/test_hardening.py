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


def test_e2e_rate_limit_bypass_refused_in_production(monkeypatch):
    # The TEST-ONLY rate-limit bypass (E2E_DISABLE_RATE_LIMIT) must NEVER be live in prod.
    # If the deploy env carries it alongside VERCEL, the app must refuse to boot rather than
    # run wide-open to abuse.
    import asgi

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("JWT_SECRET", "a-genuinely-strong-secret")
    monkeypatch.setenv("E2E_DISABLE_RATE_LIMIT", "1")
    with pytest.raises(RuntimeError, match="E2E_DISABLE_RATE_LIMIT"):
        asgi._assert_required_secrets()


def test_e2e_rate_limit_bypass_inactive_by_default():
    # In the normal test/prod environment the bypass flag is unset, so the limiter is LIVE.
    # (The flag is read once at import; the journey suite sets it only for the CI E2E server.)
    import asgi

    assert asgi._RATE_LIMIT_DISABLED is False


def test_db_connect_has_subbudget_timeout(monkeypatch):
    # Rule (a): the DB engine must carry a sub-budget CONNECT timeout so a stalled Postgres
    # connection (network partition / exhausted pooler) fails inside the serverless window
    # instead of riding to Vercel's 60s hard limit. psycopg2 connect_timeout is a client-side
    # libpq wait (not a server startup param), so it is pooler-safe.
    import src.db as db

    args = db._build_connect_args("postgresql://user:pw@host/db")
    assert "connect_timeout" in args
    assert 1 <= args["connect_timeout"] <= 30  # bounded, well under the 60s budget


def test_db_connect_timeout_env_tunable_and_clamped(monkeypatch):
    import src.db as db

    monkeypatch.setenv("DB_CONNECT_TIMEOUT_SECONDS", "5")
    assert db._db_connect_timeout() == 5.0
    # Out-of-range / non-finite / malformed values fall back to the clamped safe range,
    # never leaving the connect unbounded.
    monkeypatch.setenv("DB_CONNECT_TIMEOUT_SECONDS", "9999")
    assert db._db_connect_timeout() == 30.0
    monkeypatch.setenv("DB_CONNECT_TIMEOUT_SECONDS", "inf")
    assert db._db_connect_timeout() == 10.0
    monkeypatch.setenv("DB_CONNECT_TIMEOUT_SECONDS", "not-a-number")
    assert db._db_connect_timeout() == 10.0


def test_db_connect_args_empty_for_sqlite():
    # SQLite (local dev / tests) rejects the psycopg2 connect_timeout keyword — it must not be
    # passed, or the engine would fail to construct.
    import src.db as db

    assert db._build_connect_args("sqlite:///data/jobscraper.db") == {}
