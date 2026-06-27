"""RUNTIME FUNCTIONAL journey suite (BUILDS != WORKS).

These assert the user-visible OUTCOME against a running app + seeded throwaway DB —
not HTTP<400, not "the handler is wired". A dead end / wrong result fails the build.

Covers: signup -> login -> a WORKING dashboard -> core product loop (add job ->
scored result renders -> save/track/update status -> pipeline analytics) -> graceful
paywall/AI-degradation states. Runs with NO OpenAI key, so it works anywhere.
"""


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health_reports_llm_disabled(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["llm_enabled"] is False  # no key in test env


def test_full_core_journey(client):
    # --- signup ---
    reg = client.post(
        "/api/auth/register",
        json={
            "email": "Jane@Example.com",
            "password": "supersecret123",
            "full_name": "Jane Seeker",
            "resume_text": "Senior Python engineer. FastAPI, SQL, AWS, Docker.",
        },
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["token"]
    assert token and token.count(".") == 2  # real JWT shape
    assert reg.json()["user"]["tier"] == "free"

    # --- login (case-insensitive email) ---
    login = client.post(
        "/api/auth/login",
        json={"email": "jane@example.com", "password": "supersecret123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["token"]
    h = _auth_headers(token)

    # --- working dashboard (me) shows real state, not an error ---
    me = client.get("/api/auth/me", headers=h)
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "jane@example.com"
    assert me.json()["user"]["jobs_remaining"] == 5

    # --- core loop: add a job, get a REAL heuristic score back (no LLM key) ---
    add = client.post(
        "/api/jobs",
        headers=h,
        json={
            "title": "Senior Backend Engineer",
            "company_name": "Acme",
            "location": "Remote US",
            "salary_min": 160000,
            "salary_max": 200000,
            "description": "Python, FastAPI, PostgreSQL, AWS, Docker, Kubernetes.",
            "requirements": "5+ years Python. SQL. AWS.",
        },
    )
    assert add.status_code == 200, add.text
    job = add.json()["job"]
    job_id = job["id"]
    assert job["company"] == "Acme"
    assert job["status"] == "saved"
    # Heuristic scoring must produce a real number (matching skills overlap).
    assert isinstance(job["score"], (int, float)) and job["score"] > 0

    # --- list renders the job ---
    jobs = client.get("/api/jobs", headers=h)
    assert jobs.status_code == 200
    assert len(jobs.json()["jobs"]) == 1
    assert jobs.json()["jobs"][0]["id"] == job_id

    # --- detail ---
    detail = client.get(f"/api/jobs/{job_id}", headers=h)
    assert detail.status_code == 200
    assert detail.json()["job"]["id"] == job_id

    # --- update status moves it through the pipeline ---
    upd = client.patch(f"/api/jobs/{job_id}", headers=h, json={"status": "applied"})
    assert upd.status_code == 200, upd.text
    assert upd.json()["job"]["status"] == "applied"

    bad = client.patch(f"/api/jobs/{job_id}", headers=h, json={"status": "nonsense"})
    assert bad.status_code == 422  # server-side validation

    # --- pipeline analytics reflect the real data ---
    stats = client.get("/api/analytics/pipeline", headers=h)
    assert stats.status_code == 200
    s = stats.json()["stats"]
    assert s["total_jobs"] == 1
    assert s["status_breakdown"].get("applied") == 1
    assert s["average_score"] > 0

    # --- coach suggestions work WITHOUT an LLM key (deterministic) ---
    sug = client.get("/api/coach/suggestions", headers=h)
    assert sug.status_code == 200
    assert len(sug.json()["suggestions"]) >= 1


def test_paywall_and_ai_degrade_gracefully(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "free@example.com", "password": "supersecret123", "full_name": "Free"},
    )
    h = _auth_headers(reg.json()["token"])
    add = client.post(
        "/api/jobs",
        headers=h,
        json={"title": "Eng", "company_name": "Co", "description": "python sql"},
    )
    job_id = add.json()["job"]["id"]

    # Free user hitting the AI coach -> truthful paywall, not a 500.
    chat = client.post("/api/coach/chat", headers=h, json={"message": "help"})
    assert chat.status_code == 403
    assert "Premium" in chat.json()["detail"]

    # Prep pack with no LLM key configured -> truthful 503, not a crash/fake result.
    prep = client.post("/api/prep-packs/generate", headers=h, json={"job_id": job_id})
    assert prep.status_code == 503
    assert "OPENAI_API_KEY" in prep.json()["detail"]


def test_auth_failures_are_safe(client):
    # No token -> 401
    assert client.get("/api/jobs").status_code == 401
    # Garbage token -> 401, not 500
    assert client.get("/api/jobs", headers=_auth_headers("not.a.token")).status_code == 401
    # Wrong password -> generic message (no email enumeration)
    client.post(
        "/api/auth/register",
        json={"email": "x@example.com", "password": "supersecret123", "full_name": "X"},
    )
    bad = client.post("/api/auth/login", json={"email": "x@example.com", "password": "wrongpass1"})
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid email or password"


def test_free_tier_job_limit_enforced(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "limit@example.com", "password": "supersecret123", "full_name": "L"},
    )
    h = _auth_headers(reg.json()["token"])
    for i in range(5):
        r = client.post(
            "/api/jobs",
            headers=h,
            json={"title": f"Job {i}", "company_name": "Co", "description": "python"},
        )
        assert r.status_code == 200, r.text
    sixth = client.post(
        "/api/jobs",
        headers=h,
        json={"title": "Job 6", "company_name": "Co", "description": "python"},
    )
    assert sixth.status_code == 403
    assert "Upgrade" in sixth.json()["detail"]
