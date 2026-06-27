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
