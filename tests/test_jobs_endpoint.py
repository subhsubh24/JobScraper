"""Track A/F: outcome + authorization-boundary guards for the jobs endpoints.

The core product loop is add-job → score → track status. These assert the INTENDED
OUTCOME at runtime (the status really persists; a foreign job is never reachable),
not just a < 400 status. The authorization-boundary tests are the important ones:
they prove user B can neither read nor mutate user A's job, and that the refusal is
an indistinguishable 404 (no existence leak).
"""

from src.db.models import ApplicationStatus


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
