"""Tests for the public, no-account demo skill-match endpoint (FACTORY_STANDARD §34).

Covers the HTTP surface: the endpoint is reachable WITHOUT auth, computes the correct
matching/missing split, bounds its input, degrades honestly with no résumé, and is protected
by the captcha seam. The pure ranking math has its own deterministic eval in
``tests/evals/test_demo_match_evals.py``.
"""
# Uses the conftest ``client`` fixture (fresh per-test DB → the shared ``rate_counters`` table is
# recreated empty each test, so the rate-limit dependency can't bleed across tests and mask the
# captcha 403 with a 429). Do NOT instantiate ``TestClient(asgi.app)`` directly here.

# A realistic role that surfaces several known skills from the shared vocabulary.
_JD = (
    "Senior Backend Engineer. You will build services in Python with FastAPI and PostgreSQL, "
    "deploy on AWS using Docker and Kubernetes, and own CI/CD. React knowledge is a plus."
)
_RESUME = "I am a Python engineer. I use FastAPI and PostgreSQL daily and deploy on AWS."


def test_demo_skill_match_is_public_no_auth(client):
    """The demo endpoint requires NO Authorization header (the whole point of §34)."""
    resp = client.post("/api/demo/skill-match", json={"job_description": _JD, "resume_text": _RESUME})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # python/fastapi/postgresql/aws are in BOTH → matching; docker/kubernetes/ci/cd/react are
    # role-only → missing. ("sql" is also matched — it is a substring of "postgresql", which the
    # heuristic extractor surfaces on BOTH sides, so it lands in matching consistently.) Assert
    # the real split, not just that a 200 came back.
    assert set(body["matching_skills"]) == {"aws", "fastapi", "postgresql", "python", "sql"}
    assert {"docker", "kubernetes", "react", "ci/cd"}.issubset(set(body["missing_skills"]))
    assert body["has_resume"] is True
    assert body["role_skill_count"] == body["matching_count"] + body["missing_count"]
    # coverage is matching / role_skill_count, rounded to 3 dp.
    assert body["coverage"] == round(body["matching_count"] / body["role_skill_count"], 3)


def test_demo_skill_match_no_resume_is_honest(client):
    """With no résumé, every detected role skill is 'missing' and has_resume is False — so the UI
    can invite a résumé instead of implying a real 0% verdict."""
    resp = client.post("/api/demo/skill-match", json={"job_description": _JD})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["has_resume"] is False
    assert body["matching_skills"] == []
    assert body["missing_count"] == body["role_skill_count"] > 0
    assert body["coverage"] == 0.0


def test_demo_skill_match_requires_job_description(client):
    """An empty job description is a 422 (min_length=1) — no silent empty result."""
    resp = client.post("/api/demo/skill-match", json={"job_description": ""})
    assert resp.status_code == 422


def test_demo_skill_match_bounds_input(client):
    """Oversized pastes are rejected at the schema layer (body-spam fence), not processed."""
    over_jd = client.post("/api/demo/skill-match", json={"job_description": "x" * 25001})
    assert over_jd.status_code == 422
    over_resume = client.post(
        "/api/demo/skill-match",
        json={"job_description": _JD, "resume_text": "y" * 30001},
    )
    assert over_resume.status_code == 422


def test_demo_skill_match_no_known_skills_no_divide_by_zero(client):
    """A JD with no recognized skills returns coverage 0.0, never a divide-by-zero / NaN."""
    resp = client.post(
        "/api/demo/skill-match",
        json={"job_description": "We want a friendly teammate who enjoys coffee and karaoke."},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["role_skill_count"] == 0
    assert body["coverage"] == 0.0
    assert body["missing_skills"] == []


def test_demo_skill_match_captcha_seam_fails_closed_when_enabled(client, monkeypatch):
    """When the owner connects Turnstile, a demo request with no token is rejected 403 — proving
    the seam is actually WIRED (enumeration-safe), not decorative. (No-op otherwise: the other
    tests pass with no token because the seam is disabled by default.)"""
    monkeypatch.setenv("TURNSTILE_SECRET", "test-secret")
    resp = client.post("/api/demo/skill-match", json={"job_description": _JD, "resume_text": _RESUME})
    assert resp.status_code == 403
    assert "captcha" in resp.json()["detail"].lower()
