"""Database initialization and session management."""
import math
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/jobscraper.db")

# Normalize the scheme some providers hand out (postgres:// -> postgresql://).
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def _db_connect_timeout() -> float:
    """Seconds bounding a SINGLE Postgres CONNECTION attempt (env: DB_CONNECT_TIMEOUT_SECONDS).

    DEEP_DIAGNOSIS rule (a): every external call needs a timeout SHORTER than the serverless
    budget so a hung dependency fails INSIDE the function window instead of riding to Vercel's
    60s hard limit. Every other external call already carries one (LLM 45s, Stripe 25s, HTTP
    12-20s); the database engine was the last unbounded one — a stalled connection (network
    partition, exhausted pooler) would hang the whole request. This is psycopg2's ``connect_timeout``
    (a pure libpq CLIENT-side wait on the TCP+auth handshake): it never touches the server and is
    NOT a Postgres startup parameter, so it is safe with any connection pooler (Neon/Supabase
    pgBouncer) — unlike a server-side ``statement_timeout``, which a transaction-mode pooler may
    reject at startup, so that is deliberately NOT set here (see loop-memory).

    Kept well under the 60s budget (default 10.0s) and env-tunable so ops can tighten it without a
    deploy. Clamped to [1.0s, 30.0s]: too small would fail healthy connects on a cold pooler, and a
    huge / inf / nan value (all of which float() accepts without raising) would re-open the very
    unbounded-tail hole this closes. A malformed (non-numeric) value falls back to the default
    rather than crashing the host on import.
    """
    try:
        raw = float(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "10.0"))
    except (TypeError, ValueError):
        return 10.0
    if not math.isfinite(raw):  # inf / -inf / nan are valid floats but must not bound the connect
        return 10.0
    return max(1.0, min(30.0, raw))


def _build_connect_args(database_url: str) -> dict:
    """DBAPI connect_args for ``database_url``. Postgres gets a client-side connect timeout;
    SQLite (local dev / tests) rejects the psycopg2 keyword, so it gets none."""
    if database_url.startswith("postgresql"):
        return {"connect_timeout": int(_db_connect_timeout())}
    return {}


_engine_kwargs = {
    "echo": os.getenv("SQL_DEBUG", "false").lower() == "true",
    "pool_pre_ping": True,
}

_connect_args = _build_connect_args(DATABASE_URL)
if _connect_args:
    _engine_kwargs["connect_args"] = _connect_args

# On serverless (Vercel) each invocation is short-lived and a per-process pool would
# leak/exhaust connections — use NullPool so connections are opened/closed per request.
# Point DATABASE_URL at a pooled Postgres (e.g. Neon/Supabase pgBouncer) in production.
_is_serverless = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


def _assert_persistent_db(database_url: str, is_serverless: bool) -> None:
    """FAIL LOUD, never silently lose data (FACTORY_STANDARD §28 + DEEP_DIAGNOSIS rule (b)).

    The DATABASE_URL default is a local SQLite file, but SQLite has NO persistence on a
    serverless filesystem — every cold start gets a fresh, empty, ephemeral disk. Booting on
    Vercel/Lambda against that default would look healthy while WIPING every user's data on
    each cold start (silent data loss, far worse than an outage). A serverless deploy with a
    non-Postgres DATABASE_URL must refuse to boot rather than run on disappearing storage.
    (Owner sets DATABASE_URL to a pooled Postgres — PENDING_OPS.)
    """
    if is_serverless and not database_url.startswith("postgresql"):
        scheme = database_url.split(":", 1)[0]  # scheme only — never echo embedded creds
        raise RuntimeError(
            f"DATABASE_URL must be a postgresql:// URL on serverless (VERCEL / AWS_LAMBDA) — "
            f"got {scheme}://…. SQLite has no persistence on serverless (each cold start "
            "wipes the disk = silent data loss); set DATABASE_URL to a pooled Postgres "
            "(e.g. Neon/Supabase pgBouncer) in the deploy env."
        )


_assert_persistent_db(DATABASE_URL, _is_serverless)

if _is_serverless and DATABASE_URL.startswith("postgresql"):
    _engine_kwargs["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")


@contextmanager
def get_session() -> Session:
    """Get a database session with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
