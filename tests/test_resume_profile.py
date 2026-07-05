"""Résumé read/update profile endpoints (GET + PATCH /api/profile/resume).

Closes a real user-facing DEAD-END: several features (the tailored-résumé generator, the
skill-gap heatmap / learning plan) tell the user to "add your résumé in Settings", but before
this there was NO way to set or update the résumé after signup — resume_text was write-once at
registration and no Settings field or endpoint existed. These tests pin the update path AND the
end-to-end unblock (a user who signs up résumé-less can now add one and reach the gated feature).
"""

from src.db.models import User, UserTier


def _register(client, email="resume@example.com", password="hunter2pw", resume_text=None):
    body = {"email": email, "password": password}
    if resume_text is not None:
        body["resume_text"] = resume_text
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_get_resume_empty_for_new_user(client):
    _uid, token = _register(client)
    r = client.get("/api/profile/resume", headers=_auth(token))
    assert r.status_code == 200, r.text
    # Empty string, never null, so the client always renders an editable field.
    assert r.json() == {"success": True, "resume_text": ""}


def test_patch_resume_saves_and_get_returns_it(client):
    _uid, token = _register(client)
    text = "Senior Python engineer. FastAPI, AWS, Postgres. Led a 5-person team."
    r = client.patch("/api/profile/resume", headers=_auth(token), json={"resume_text": text})
    assert r.status_code == 200, r.text
    assert r.json() == {"success": True, "has_resume": True}

    # It is durably persisted and read back verbatim.
    got = client.get("/api/profile/resume", headers=_auth(token))
    assert got.json()["resume_text"] == text


def test_patch_resume_trims_whitespace(client):
    _uid, token = _register(client)
    r = client.patch(
        "/api/profile/resume", headers=_auth(token), json={"resume_text": "  padded résumé  "}
    )
    assert r.status_code == 200, r.text
    assert client.get("/api/profile/resume", headers=_auth(token)).json()["resume_text"] == "padded résumé"


def test_blank_body_clears_the_resume(client, db_session):
    _uid, token = _register(client, resume_text="Existing résumé text.")
    # A blank / whitespace-only save CLEARS the résumé (stored as NULL) — the user can remove it.
    r = client.patch("/api/profile/resume", headers=_auth(token), json={"resume_text": "   "})
    assert r.status_code == 200, r.text
    assert r.json() == {"success": True, "has_resume": False}
    assert client.get("/api/profile/resume", headers=_auth(token)).json()["resume_text"] == ""
    # NULL, not "" — a cleared résumé is indistinguishable from never-set at the DB layer.
    user = db_session.query(User).filter(User.email == "resume@example.com").first()
    assert user.resume_text is None


def test_resume_over_bound_is_rejected(client):
    _uid, token = _register(client)
    # 50_000 is the wallet-drain bound (résumé text is embedded verbatim into LLM prompts).
    r = client.patch(
        "/api/profile/resume", headers=_auth(token), json={"resume_text": "x" * 50_001}
    )
    assert r.status_code == 422, r.text
    # The over-long payload must NOT have been persisted.
    assert client.get("/api/profile/resume", headers=_auth(token)).json()["resume_text"] == ""


def test_resume_endpoints_require_auth(client):
    assert client.get("/api/profile/resume").status_code == 401
    assert client.patch("/api/profile/resume", json={"resume_text": "x"}).status_code == 401


def test_one_user_cannot_read_or_write_anothers_resume(client):
    _u1, t1 = _register(client, email="a@example.com")
    _u2, t2 = _register(client, email="b@example.com")
    client.patch("/api/profile/resume", headers=_auth(t1), json={"resume_text": "user A résumé"})
    # B's résumé is independent (tenant isolation — the endpoint keys off the auth'd user only).
    assert client.get("/api/profile/resume", headers=_auth(t2)).json()["resume_text"] == ""


def test_added_resume_unblocks_the_tailored_resume_dead_end(client, db_session):
    """The dead-end, end to end: a résumé-less user is blocked by the tailored-résumé 400, adds a
    résumé via the new endpoint, and the guard now passes it (fails past the résumé check)."""
    _uid, token = _register(client)
    # Make the user Premium so the tier gate isn't the thing blocking us.
    user = db_session.query(User).filter(User.email == "resume@example.com").first()
    user.tier = UserTier.PREMIUM
    db_session.commit()
    job = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": "Staff Engineer", "company_name": "Acme", "description": "python fastapi"},
    )
    job_id = job.json()["job"]["id"]

    # BEFORE adding a résumé: honest 400 telling the user to add one first (the dead-end message).
    before = client.post(
        "/api/prep/tailored-resume", headers=_auth(token), json={"job_id": job_id}
    )
    assert before.status_code == 400, before.text
    assert "résumé" in before.json()["detail"].lower() or "resume" in before.json()["detail"].lower()

    # Add the résumé via the endpoint this run introduced.
    client.patch(
        "/api/profile/resume",
        headers=_auth(token),
        json={"resume_text": "Senior engineer. Python, FastAPI, AWS."},
    )

    # AFTER: the résumé guard no longer fires. Without a Gemini key the flow degrades to an honest
    # 503 (or a consent 403) — anything BUT the 400 dead-end proves the résumé gate is satisfied.
    after = client.post(
        "/api/prep/tailored-resume", headers=_auth(token), json={"job_id": job_id}
    )
    assert after.status_code != 400, after.text
