"""Interview-readiness endpoint (ROADMAP Track A surface 3 — the readiness loop).

GET /api/jobs/{job_id}/readiness is a FREE, fully-local read (no LLM, no consent): it computes a
readiness score + the single next-best-action from the user's REAL signals for one job. These
tests prove the wiring end-to-end: honest 0-state, tenant isolation (404 on someone else's job),
that the score reflects real seeded signals (résumé, mock-interview answers, prep artifacts), and
that it climbs only on real practice. The readiness MATH itself is pinned separately by the
deterministic eval (tests/evals/test_readiness_evals.py)."""
from src.db.models import MockInterview, PrepArtifact, User


def _register(client, email="ready@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _add_job(client, token, description="python react aws"):
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": "Staff Engineer", "company_name": "Acme", "description": description},
    )
    assert r.status_code == 200, r.text
    return r.json()["job"]["id"]


def _set_resume(db_session, user_id, text):
    db_session.query(User).filter(User.id == user_id).update({User.resume_text: text})
    db_session.commit()


def test_readiness_requires_auth(client):
    r = client.get("/api/jobs/whatever/readiness")
    assert r.status_code == 401


def test_zero_state_readiness_is_honest(client):
    _, token = _register(client)
    job_id = _add_job(client, token)  # no résumé, no practice, no artifacts
    r = client.get(f"/api/jobs/{job_id}/readiness", headers=_auth(token))
    assert r.status_code == 200, r.text
    body = r.json()["readiness"]
    assert body["score"] == 0
    assert body["next_action"]["action"] == "add_resume"
    assert body["signals"]["answered_questions"] == 0


def test_readiness_404_on_another_users_job(client):
    _, token_a = _register(client, email="a@example.com")
    job_id = _add_job(client, token_a)
    _, token_b = _register(client, email="b@example.com")
    # User B cannot read User A's job readiness (tenant isolation — never trust the client).
    r = client.get(f"/api/jobs/{job_id}/readiness", headers=_auth(token_b))
    assert r.status_code == 404


def test_readiness_404_on_missing_job(client):
    _, token = _register(client)
    r = client.get("/api/jobs/does-not-exist/readiness", headers=_auth(token))
    assert r.status_code == 404


def test_readiness_reflects_real_signals(client, db_session):
    user_id, token = _register(client)
    job_id = _add_job(client, token, description="python react aws")

    # Baseline: with a résumé that covers some JD skills but no practice/artifacts.
    _set_resume(db_session, user_id, "experienced in python and react")
    r = client.get(f"/api/jobs/{job_id}/readiness", headers=_auth(token))
    base = r.json()["readiness"]
    assert base["components"]["skill_coverage"] == round(2 / 3, 3)  # python+react of python+react+aws
    assert base["next_action"]["action"] == "start_mock_interview"  # résumé present, no session
    assert base["score"] > 0

    # Seed a completed, well-scored mock-interview session + a prep artifact directly (LLM-gated
    # to create via the API, so seed the persisted rows the read consumes).
    db_session.add(MockInterview(
        user_id=user_id, job_id=job_id,
        questions=[{"question": "q1"}, {"question": "q2"}],
        answers=[{"question_index": 0, "overall": 90.0}, {"question_index": 1, "overall": 85.0}],
        status="completed",
    ))
    db_session.add(PrepArtifact(job_id=job_id, artifact_type="prep_pack", content="{}"))
    db_session.commit()

    r = client.get(f"/api/jobs/{job_id}/readiness", headers=_auth(token))
    after = r.json()["readiness"]
    # Real practice + a real artifact raise readiness (monotonic in real inputs).
    assert after["score"] > base["score"]
    assert after["signals"]["answered_questions"] == 2
    assert "prep_pack" in after["signals"]["artifacts_completed"]
    # Next action now points past the (completed, strong) practice — a missing key artifact.
    assert after["next_action"]["action"] in {"generate_artifact", "study_skill", "ready"}
