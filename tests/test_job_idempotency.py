"""create_job idempotency: a re-submitted identical posting must NOT create a duplicate row
or double-fire its side-effects (score / usage-count / analytics).

QUALITY_SCORECARD named this a correctness gap: POST /api/jobs twice inserted unconditionally.
These tests assert the guard both dedups the identical case AND still creates genuinely-different
jobs, and that an idempotent re-submit does not consume the free-tier cap.
"""
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
