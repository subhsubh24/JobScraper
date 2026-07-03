"""Serverless data-loss guard (FACTORY_STANDARD §28, issue #222).

`src/db` defaults DATABASE_URL to a local SQLite file. SQLite has NO persistence on a
serverless filesystem — every cold start gets a fresh, empty, ephemeral disk — so booting
on Vercel/Lambda against that default would silently WIPE every user's data on each cold
start while the app looks healthy. `_assert_persistent_db` must FAIL LOUD (refuse to boot)
in that case rather than run on disappearing storage.

These tests assert the pure guard directly — the import-time call site is a single trivial
line (`_assert_persistent_db(DATABASE_URL, _is_serverless)`), so the guard logic is what
must not silently regress.
"""
import pytest

from src.db import _assert_persistent_db


def test_serverless_with_sqlite_raises():
    with pytest.raises(RuntimeError, match="postgresql"):
        _assert_persistent_db("sqlite:///data/jobscraper.db", is_serverless=True)


def test_serverless_with_non_postgres_raises_and_does_not_leak_creds():
    # A mis-set URL with embedded credentials must fail loud AND the message must only echo
    # the scheme, never the user:password (error hygiene).
    with pytest.raises(RuntimeError) as exc:
        _assert_persistent_db("mysql://user:s3cret@host/db", is_serverless=True)
    assert "s3cret" not in str(exc.value)
    assert "mysql" in str(exc.value)


def test_serverless_with_postgres_is_allowed():
    # The supported production config must NOT raise.
    _assert_persistent_db("postgresql://u:p@host:5432/db", is_serverless=True)


def test_non_serverless_with_sqlite_is_allowed():
    # Local dev / CI runs on SQLite off-serverless — must never be blocked.
    _assert_persistent_db("sqlite:///data/jobscraper.db", is_serverless=False)
