"""Track A/F: outcome + authorization-boundary guards for the jobs endpoints.

The core product loop is add-job → score → track status. These assert the INTENDED
OUTCOME at runtime (the status really persists; a foreign job is never reachable),
not just a < 400 status. The authorization-boundary tests are the important ones:
they prove user B can neither read nor mutate user A's job, and that the refusal is
an indistinguishable 404 (no existence leak).
"""

from sqlalchemy.exc import IntegrityError

import asgi
from src.db.models import Application, ApplicationStatus, JobPosting, User, UserTier


def _register(client, email, password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _add_job(client, token, title="Senior Engineer", company="Acme"):
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": title, "company_name": company, "description": "python fastapi"},
    )
    assert r.status_code == 200, r.text
    return r.json()["job"]["id"]


def test_all_status_transitions_persist(client):
    """Every ApplicationStatus the UI can set must round-trip through PATCH and persist."""
    token = _register(client, "transitions@example.com")
    job_id = _add_job(client, token)
    for status in [s.value for s in ApplicationStatus]:
        r = client.patch(f"/api/jobs/{job_id}", headers=_auth(token), json={"status": status})
        assert r.status_code == 200, f"{status}: {r.text}"
        assert r.json()["job"]["status"] == status
        # Re-fetch to prove it actually persisted, not just echoed back.
        got = client.get(f"/api/jobs/{job_id}", headers=_auth(token))
        assert got.json()["job"]["status"] == status


def test_get_nonexistent_job_is_404(client):
    token = _register(client, "missing@example.com")
    r = client.get("/api/jobs/does-not-exist", headers=_auth(token))
    assert r.status_code == 404


def test_get_foreign_job_is_404_not_leaked(client):
    """Authorization boundary: user B must NOT be able to read user A's job, and the
    refusal must be a 404 (indistinguishable from 'never existed' — no enumeration)."""
    token_a = _register(client, "owner-a@example.com")
    job_id = _add_job(client, token_a, title="A's secret role")

    token_b = _register(client, "intruder-b@example.com")
    r = client.get(f"/api/jobs/{job_id}", headers=_auth(token_b))
    assert r.status_code == 404
    # The owner's title must never appear in the refusal body.
    assert "secret" not in r.text.lower()


def test_patch_foreign_job_is_404_and_does_not_mutate(client):
    """User B cannot change the status of user A's job; A's data is untouched."""
    token_a = _register(client, "owner-a2@example.com")
    job_id = _add_job(client, token_a)
    client.patch(f"/api/jobs/{job_id}", headers=_auth(token_a), json={"status": "applied"})

    token_b = _register(client, "intruder-b2@example.com")
    r = client.patch(f"/api/jobs/{job_id}", headers=_auth(token_b), json={"status": "rejected"})
    assert r.status_code == 404

    # A's job is unchanged.
    still = client.get(f"/api/jobs/{job_id}", headers=_auth(token_a))
    assert still.json()["job"]["status"] == "applied"


def test_jobs_list_is_scoped_to_the_caller(client):
    token_a = _register(client, "list-a@example.com")
    _add_job(client, token_a, title="A only")
    token_b = _register(client, "list-b@example.com")
    r = client.get("/api/jobs", headers=_auth(token_b))
    assert r.status_code == 200
    assert r.json()["jobs"] == []


def test_patch_survives_concurrent_application_insert_race(db_session, monkeypatch):
    """Two concurrent PATCHes on a job that has no Application row yet both take the "create"
    branch; the loser trips ``Application.job_id``'s UNIQUE constraint on commit. The endpoint
    must NOT 500 — it rolls back and re-applies the status onto the row the winner created.

    We drive the race deterministically: the first ``commit`` simulates the winning request by
    persisting a competing Application row (via a real commit) and then raising the same
    ``IntegrityError`` the DB would. The endpoint's except-branch must recover and the status
    must still land. Reverting the fix (dropping the try/except) makes this raise a 500."""
    user = User(email="patch-race@example.com", password_hash="x", tier=UserTier.FREE)
    db_session.add(user)
    db_session.flush()
    job = JobPosting(user_id=user.id, title="Engineer", company_name="Acme")
    db_session.add(job)
    db_session.commit()  # persist the job with NO Application row yet
    job_id = job.id

    real_commit = db_session.commit
    state = {"raised": False}

    def flaky_commit():
        if not state["raised"]:
            state["raised"] = True
            # Simulate the concurrent winner: drop our own pending insert (as a rolled-back
            # IntegrityError would), persist the competing row, then raise like the DB did.
            db_session.rollback()
            db_session.add(
                Application(user_id=user.id, job_id=job_id, status=ApplicationStatus.SAVED)
            )
            real_commit()
            raise IntegrityError("INSERT application", {}, Exception("UNIQUE job_id"))
        real_commit()

    monkeypatch.setattr(db_session, "commit", flaky_commit)

    res = asgi.update_job_status(
        job_id=job_id,
        data=asgi.JobUpdate(status=ApplicationStatus.APPLIED.value),
        user=user,
        db=db_session,
    )

    # No 500: the update landed on the winner's row and the response is honest.
    assert state["raised"] is True, "the race path was not exercised"
    assert res["job"]["status"] == ApplicationStatus.APPLIED.value
    # And exactly one Application row exists for the job (no duplicate, constraint held).
    assert db_session.query(Application).filter(Application.job_id == job_id).count() == 1
