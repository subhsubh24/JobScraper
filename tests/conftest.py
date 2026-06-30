"""Test harness: a throwaway sqlite DB + a TestClient, with NO Gemini key so the
graceful-degradation paths are exercised deterministically."""
import os

# Force a known, key-free environment BEFORE importing the app. python-dotenv's
# load_dotenv(override=False) will not clobber these already-present values.
os.environ["GEMINI_API_KEY"] = ""
os.environ["JWT_SECRET"] = "test-secret"
os.environ.setdefault("ALLOWED_ORIGINS", "http://testserver")
# Tests build their own in-memory schema; don't let importing asgi create a real DB.
os.environ["AUTO_CREATE_TABLES"] = "0"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import asgi  # noqa: E402
from src.db import get_db  # noqa: E402
from src.db.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    """The rate-limit + LLM-ceiling counters are now in the shared ``rate_counters`` table,
    which is recreated empty per test by the function-scoped ``_engine`` fixture — so no
    reset is needed for those. The per-account login lockout is still a process-global
    in-memory dict; clear it before each test so an earlier failed-login test can't leak a
    lockout into a later one (flaky, order-dependent)."""
    asgi._LOGIN_FAILURES.clear()
    yield


@pytest.fixture()
def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(_engine):
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    asgi.app.dependency_overrides[get_db] = override_get_db
    with TestClient(asgi.app) as c:
        yield c
    asgi.app.dependency_overrides.clear()


@pytest.fixture()
def db_session(_engine):
    """A session on the SAME in-memory DB the `client` fixture uses, so a test can seed
    rows the API can't easily create (LLM-gated prep/chat) and assert on them directly."""
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    s = TestingSession()
    try:
        yield s
    finally:
        s.close()
