"""Database initialization and session management."""
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

_engine_kwargs = {
    "echo": os.getenv("SQL_DEBUG", "false").lower() == "true",
    "pool_pre_ping": True,
}

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
