"""create_job idempotency: a re-submitted identical posting must NOT create a duplicate row
or double-fire its side-effects (score / usage-count / analytics).

QUALITY_SCORECARD named this a correctness gap: POST /api/jobs twice inserted unconditionally.
These tests assert the guard both dedups the identical case AND still creates genuinely-different
jobs, and that an idempotent re-submit does not consume the free-tier cap.
"""
import pytest
from src.db.models import Application, JobPosting


def _register(client, email="dedup@example.com", pw="supersecret123"):
    r = client.post("/api/auth/register", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


_JOB = {"title": "Senior Engineer", "company_name": "Acme", "description": "python fastapi",
        "url": "https://acme.example/jobs/1"}


def test_identical_resubmit_returns_existing_no_duplicate(client, db_session):
    h = _register(client)

    first = client.post("/api/jobs", headers=h, json=_JOB)
    assert first.status_code == 200, first.text
    assert first.json().get("duplicate") is None  # first insert is not a duplicate
    first_id = first.json()["job"]["id"]

    second = client.post("/api/jobs", headers=h, json=_JOB)
    assert second.status_code == 200, second.text
    assert second.json()["duplicate"] is True
    assert second.json()["job"]["id"] == first_id  # same job, not a new row

    # Exactly ONE JobPosting + ONE Application persisted (no duplicate side-effects).
    assert db_session.query(JobPosting).count() == 1
    assert db_session.query(Application).count() == 1


def test_dedup_does_not_consume_free_tier_cap(client):
    """Re-submitting a job you already track must not count against the 5-job free cap."""
    h = _register(client, email="cap@example.com")

    # Fill the free tier with 5 DISTINCT jobs.
    for i in range(5):
        r = client.post("/api/jobs", headers=h,
                        json={"title": f"Role {i}", "company_name": "Acme",
                              "url": f"https://acme.example/jobs/{i}"})
        assert r.status_code == 200, r.text

    # A 6th DISTINCT job is correctly blocked by the cap.
    blocked = client.post("/api/jobs", headers=h,
                          json={"title": "Role 6", "company_name": "Acme",
                                "url": "https://acme.example/jobs/6"})
    assert blocked.status_code == 403

    # But re-submitting an EXISTING job (Role 0) returns it idempotently — never a 403.
    resubmit = client.post("/api/jobs", headers=h,
                           json={"title": "Role 0", "company_name": "Acme",
                                 "url": "https://acme.example/jobs/0"})
    assert resubmit.status_code == 200, resubmit.text
    assert resubmit.json()["duplicate"] is True


def test_different_url_is_not_deduped(client, db_session):
    h = _register(client, email="diff@example.com")

    client.post("/api/jobs", headers=h, json=_JOB)
    other = dict(_JOB, url="https://acme.example/jobs/2")  # same title+company, different url
    r = client.post("/api/jobs", headers=h, json=other)
    assert r.status_code == 200
    assert r.json().get("duplicate") is None
    assert db_session.query(JobPosting).count() == 2  # genuinely different posting -> new row


def test_null_url_dedups_on_title_and_company(client, db_session):
    """A posting with no URL still dedups on (title, company) — url IS NULL matches IS NULL."""
    h = _register(client, email="nourl@example.com")
    payload = {"title": "Analyst", "company_name": "Globex", "description": "sql"}  # no url

    a = client.post("/api/jobs", headers=h, json=payload)
    b = client.post("/api/jobs", headers=h, json=payload)
    assert a.status_code == 200 and b.status_code == 200
    assert b.json()["duplicate"] is True
    assert db_session.query(JobPosting).count() == 1


def test_same_posting_isolated_per_user(client, db_session):
    """Two different users adding the 'same' posting each get their own row (no cross-user dedup)."""
    h1 = _register(client, email="u1@example.com")
    h2 = _register(client, email="u2@example.com")
    client.post("/api/jobs", headers=h1, json=_JOB)
    r = client.post("/api/jobs", headers=h2, json=_JOB)
    assert r.status_code == 200
    assert r.json().get("duplicate") is None  # a different user's identical posting is NOT a dup
    assert db_session.query(JobPosting).count() == 2


# --- ATOMIC backstop: the read-guard above is a read-then-write TOCTOU; these prove the DB
#     unique constraint (uq_job_user_title_company_url) makes a genuinely-CONCURRENT identical
#     add fail loud + recover as a dedup, rather than creating a duplicate row. ---

def test_duplicate_posting_rejected_by_db_constraint(client, db_session):
    """The DB actually enforces uniqueness of (user_id, title, company_name, url): a second
    identical row inserted OUT-OF-BAND (bypassing the endpoint read-guard) trips IntegrityError.
    Revert-provable: drop the UniqueConstraint from JobPosting and this insert silently succeeds.
    """
    from sqlalchemy.exc import IntegrityError
    from src.db.models import User

    h = _register(client, email="dbc@example.com")
    first = client.post("/api/jobs", headers=h, json=_JOB)
    assert first.status_code == 200, first.text
    uid = db_session.query(User).filter(User.email == "dbc@example.com").first().id

    # Insert a byte-identical posting directly (simulates the loser of a concurrent race whose
    # read-guard saw no existing row). The DB must reject it.
    db_session.add(JobPosting(
        user_id=uid, title=_JOB["title"], company_name=_JOB["company_name"], url=_JOB["url"],
    ))
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_concurrent_add_recovers_as_dedup_not_500(_engine, monkeypatch):
    """Two genuinely-simultaneous identical POSTs both pass the read-guard (`existing is None`)
    and both INSERT; the loser trips uq_job_user_title_company_url -> IntegrityError. create_job
    must ROLL BACK and return the winner's row as a dedup (200, duplicate=True, ONE row) — not an
    uncaught 500 that surfaces a DB error to the user and double-counts nothing.

    Deterministic simulation (mirrors tests/test_billing.py's concurrent-insert-race test): the
    IntegrityError surfaces at create_job's `db.flush()` after `db.add(job)`, so inject the fault
    there — on the losing flush, discard our insert, durably commit a WINNER posting for the same
    4-tuple, then raise the IntegrityError the DB would have raised. LOAD-BEARING: revert
    create_job's `except IntegrityError` recovery and this call 500s.
    """
    from fastapi.testclient import TestClient
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import sessionmaker

    import asgi
    from src.db import get_db
    from src.db.models import Application, ApplicationStatus, User

    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    state = {"armed": False, "user_id": None, "flushes": 0}

    def override_get_db():
        db = TestingSession()
        real_flush = db.flush
        real_commit = db.commit

        def flaky_flush(*a, **k):
            # Trip exactly once, on the create_job job-insert flush (a JobPosting pending in
            # db.new after arming). Registration + any other flush passes straight through.
            if not (state["armed"] and any(isinstance(o, JobPosting) for o in db.new)):
                return real_flush(*a, **k)
            state["armed"] = False  # one-shot
            state["flushes"] += 1
            db.rollback()  # our losing INSERT is discarded
            db.add(JobPosting(
                user_id=state["user_id"], title=_JOB["title"],
                company_name=_JOB["company_name"], url=_JOB["url"],
            ))
            db.flush = real_flush  # let the winner + its Application flush normally
            db.flush()
            winner = (
                db.query(JobPosting)
                .filter(JobPosting.user_id == state["user_id"], JobPosting.title == _JOB["title"])
                .first()
            )
            db.add(Application(
                user_id=state["user_id"], job_id=winner.id, status=ApplicationStatus.SAVED,
            ))
            real_commit()  # the concurrent WINNER's row is now durable
            db.flush = flaky_flush  # restore (harmless; one-shot already disarmed)
            raise IntegrityError("dup", {}, Exception("UNIQUE constraint failed: job_postings"))

        db.flush = flaky_flush
        try:
            yield db
        finally:
            db.close()

    asgi.app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(asgi.app) as c:
            r = c.post("/api/auth/register", json={"email": "race@example.com", "password": "supersecret123"})
            assert r.status_code == 200, r.text
            h = {"Authorization": f"Bearer {r.json()['token']}"}
            seed = TestingSession()
            state["user_id"] = seed.query(User).filter(User.email == "race@example.com").first().id
            seed.close()
            state["armed"] = True  # arm the race for the next job-insert flush
            resp = c.post("/api/jobs", headers=h, json=_JOB)
            assert resp.status_code == 200, resp.text  # recovered, not an uncaught 500
            assert resp.json()["duplicate"] is True
        verify = TestingSession()
        assert verify.query(JobPosting).count() == 1  # winner only — no duplicate row
        assert state["flushes"] == 1  # the race actually fired at the job-insert flush
        verify.close()
    finally:
        asgi.app.dependency_overrides.clear()
