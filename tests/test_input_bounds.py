"""Track F: server-side input bounds on write endpoints (abuse / wallet-drain hardening).

The free-text fields ``resume_text`` (UserCreate) and ``description``/``requirements``
(JobCreate) are embedded VERBATIM into LLM prompts (coach system prompt + prep-pack
generation). The spend defense is a per-user/day CALL ceiling — it does NOT bound the
PER-CALL token cost, so an unbounded field lets one account drive the bill arbitrarily
high (a real wallet-drain vector while provider spend caps are owner-pending). These
tests pin the max_length / numeric bounds so a regression that drops them fails LOUD.
They also assert a within-bounds value still succeeds (the cap never breaks real use).
"""

OK_PW = "hunter2pw"


def _register(client, email):
    r = client.post("/api/auth/register", json={"email": email, "password": OK_PW})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_rejects_oversized_resume_text(client):
    """A multi-MB resume must be refused (422), never embedded into an LLM prompt."""
    r = client.post(
        "/api/auth/register",
        json={
            "email": "huge-resume@example.com",
            "password": OK_PW,
            "resume_text": "x" * 50001,
        },
    )
    assert r.status_code == 422, r.text


def test_register_accepts_realistic_resume_text(client):
    """A long-but-realistic resume (well within the cap) still works — the bound never
    breaks a real signup."""
    r = client.post(
        "/api/auth/register",
        json={
            "email": "real-resume@example.com",
            "password": OK_PW,
            "resume_text": "Senior engineer. " * 1000,  # ~17k chars, < 50k cap
        },
    )
    assert r.status_code == 200, r.text


def test_create_job_rejects_oversized_description(client):
    token = _register(client, "huge-jd@example.com")
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": "Eng", "company_name": "Acme", "description": "x" * 20001},
    )
    assert r.status_code == 422, r.text


def test_create_job_rejects_oversized_requirements(client):
    token = _register(client, "huge-reqs@example.com")
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": "Eng", "company_name": "Acme", "requirements": "y" * 20001},
    )
    assert r.status_code == 422, r.text


def test_create_job_rejects_negative_salary(client):
    token = _register(client, "neg-salary@example.com")
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": "Eng", "company_name": "Acme", "salary_min": -1},
    )
    assert r.status_code == 422, r.text


def test_create_job_rejects_inverted_salary_range(client):
    """salary_min > salary_max is incoherent data — reject it before it corrupts analytics."""
    token = _register(client, "bad-range@example.com")
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={
            "title": "Eng",
            "company_name": "Acme",
            "salary_min": 200000,
            "salary_max": 100000,
        },
    )
    assert r.status_code == 422, r.text


def test_create_job_accepts_valid_salary_range(client):
    token = _register(client, "ok-range@example.com")
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={
            "title": "Eng",
            "company_name": "Acme",
            "salary_min": 120000,
            "salary_max": 180000,
        },
    )
    assert r.status_code == 200, r.text
    job = r.json()["job"]
    assert job["salary_min"] == 120000 and job["salary_max"] == 180000


def test_prep_pack_rejects_oversized_job_id(client):
    """An over-long job_id is refused at the schema (422) before any DB/string work."""
    token = _register(client, "huge-jobid@example.com")
    r = client.post(
        "/api/prep-packs/generate",
        headers=_auth(token),
        json={"job_id": "z" * 65},
    )
    assert r.status_code == 422, r.text
