"""Pro-tier AI prep tools: cover-letter + study-plan endpoints (resolves issue #222 —
wire the previously-dead ``generate_cover_letter`` / ``generate_study_plan`` generators).

What these prove (mirroring the Career+ salary-negotiation contract, test_career_plus.py):
- Both endpoints gate on ``user.tier == PREMIUM`` server-side BEFORE any LLM work, so a FREE
  user gets a clean 403 (never a 503). The features are ADDITIVE (no endpoint existed before)
  so gating them to Pro removes nothing from any existing user — no dark pattern.
- Pro AND Career+ (both PREMIUM) can use them — the gate is the paid tier, not the Career+ level.
- Honest degradation: a PREMIUM user with no LLM key gets 503 (proving the gate PASSED), never a
  fake/blank artifact (SIDE-EFFECT INTEGRITY §6).
- Consent (Apple 5.1.2(i)) is enforced before the resume/JD reach Gemini.
- ``study-plan``'s ``days`` is bounded 1–30 (a 422 at the boundary — an honest abuse guard on a
  paid LLM generation) and is passed through to the generator unchanged.
"""

from types import SimpleNamespace

import pytest

import asgi
from src.db.models import Subscription, User, UserTier


# --------------------------------------------------------------------------- helpers
def _register(client, email="pt@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _add_job(client, token):
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": "Staff Engineer", "company_name": "Acme", "description": "python"},
    )
    assert r.status_code == 200, r.text
    return r.json()["job"]["id"]


def _make_premium(db_session, user_id, plan="pro_monthly"):
    """Seed the verified-entitlement state a signed webhook would produce: PREMIUM tier + a
    Subscription row. plan='pro_monthly' → Pro; 'careerplus_monthly' → Career+ (both PREMIUM)."""
    db_session.query(User).filter(User.id == user_id).update({User.tier: UserTier.PREMIUM})
    db_session.add(Subscription(user_id=user_id, plan=plan, status="active"))
    db_session.commit()


def _grant_consent(client, token):
    assert client.post("/api/ai-consent", headers=_auth(token)).status_code == 200


class _FakeWorkflows:
    """Stand-in for LLMWorkflows: returns deterministic artifact-shaped objects and records the
    ``days`` a study-plan call received so we can assert the request value is passed through."""

    last_days = None

    def __init__(self, db):
        self._db = db

    def generate_cover_letter(self, job, user):
        return SimpleNamespace(
            id="art-cl-1",
            title=f"Cover Letter: {job.title} at {job.company_name}",
            content="Dear Hiring Manager,\nA real, tailored cover letter here.",
        )

    def generate_study_plan(self, job, days):
        assert isinstance(days, int)
        _FakeWorkflows.last_days = days
        return SimpleNamespace(
            id="art-sp-1",
            title=f"{days}-Day Study Plan: {job.title}",
            content="## Day 1\nReal, specific study plan content here.",
        )


@pytest.fixture()
def _llm_on(monkeypatch):
    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "LLMWorkflows", _FakeWorkflows)
    _FakeWorkflows.last_days = None


# ============================================================ cover letter
def test_cover_letter_blocked_for_free(client):
    _, token = _register(client)
    job_id = _add_job(client, token)
    r = client.post("/api/prep/cover-letter", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 403
    assert "pro" in r.json()["detail"].lower()


def test_cover_letter_gate_precedes_job_lookup(client):
    """A FREE user gets 403 even with a bogus job id — the tier check runs before the DB lookup
    (no info leak about job existence, clean gate; matches the salary-negotiation contract)."""
    _, token = _register(client, "free-cl@example.com")
    r = client.post(
        "/api/prep/cover-letter", headers=_auth(token), json={"job_id": "does-not-exist"}
    )
    assert r.status_code == 403


def test_cover_letter_pro_passes_gate_but_degrades_without_key(client, db_session):
    """A Pro (PREMIUM) user with NO Gemini key gets 503 — crucially NOT 403, which PROVES the
    entitlement gate passed and the block is only the missing key (honest degradation)."""
    uid, token = _register(client, "pro-cl@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid, plan="pro_monthly")
    r = client.post("/api/prep/cover-letter", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 503
    assert "gemini_api_key" in r.json()["detail"].lower()


def test_cover_letter_requires_consent_before_llm(client, db_session, _llm_on):
    """Even a PREMIUM user WITH a key is blocked (403 ai_consent_required) until they grant
    third-party-AI consent (Apple 5.1.2(i)) — the resume/JD never reach Gemini without it."""
    uid, token = _register(client, "pro-cl2@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid)
    r = client.post("/api/prep/cover-letter", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "ai_consent_required"


def test_cover_letter_pro_generates_real_artifact(client, db_session, _llm_on):
    uid, token = _register(client, "pro-cl3@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid, plan="pro_monthly")
    _grant_consent(client, token)
    r = client.post("/api/prep/cover-letter", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    art = body["artifact"]
    assert art["id"] == "art-cl-1"
    assert "Cover Letter" in art["title"]
    assert art["content"].strip()  # real content, not a placeholder


def test_cover_letter_available_to_career_plus_too(client, db_session, _llm_on):
    """A Pro-tier feature is available to Career+ (a strict superset) as well — the gate is the
    paid tier, not the Career+ level."""
    uid, token = _register(client, "cp-cl@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid, plan="careerplus_monthly")
    _grant_consent(client, token)
    r = client.post("/api/prep/cover-letter", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 200, r.text


def test_cover_letter_foreign_job_is_404(client, db_session, _llm_on):
    uid_owner, tok_owner = _register(client, "owner-cl@example.com")
    job_id = _add_job(client, tok_owner)
    uid_pro, tok_pro = _register(client, "pro-cl4@example.com")
    _make_premium(db_session, uid_pro)
    r = client.post("/api/prep/cover-letter", headers=_auth(tok_pro), json={"job_id": job_id})
    assert r.status_code == 404


# ============================================================ study plan
def test_study_plan_blocked_for_free(client):
    _, token = _register(client, "free-sp@example.com")
    job_id = _add_job(client, token)
    r = client.post(
        "/api/prep/study-plan", headers=_auth(token), json={"job_id": job_id, "days": 7}
    )
    assert r.status_code == 403
    assert "pro" in r.json()["detail"].lower()


def test_study_plan_pro_degrades_without_key(client, db_session):
    uid, token = _register(client, "pro-sp@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid)
    r = client.post(
        "/api/prep/study-plan", headers=_auth(token), json={"job_id": job_id, "days": 7}
    )
    assert r.status_code == 503


def test_study_plan_pro_generates_and_passes_days_through(client, db_session, _llm_on):
    uid, token = _register(client, "pro-sp2@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid)
    _grant_consent(client, token)
    r = client.post(
        "/api/prep/study-plan", headers=_auth(token), json={"job_id": job_id, "days": 14}
    )
    assert r.status_code == 200, r.text
    art = r.json()["artifact"]
    assert art["id"] == "art-sp-1"
    assert "14-Day" in art["title"]
    assert _FakeWorkflows.last_days == 14  # the request value reached the generator unchanged


def test_study_plan_defaults_days_when_omitted(client, db_session, _llm_on):
    uid, token = _register(client, "pro-sp3@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid)
    _grant_consent(client, token)
    r = client.post("/api/prep/study-plan", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 200, r.text
    assert _FakeWorkflows.last_days == 7  # StudyPlanRequest default


@pytest.mark.parametrize("bad_days", [0, -1, 31, 100])
def test_study_plan_days_out_of_bounds_is_422(client, db_session, _llm_on, bad_days):
    """days is bounded 1–30 — an out-of-range value is a 422 at the Pydantic boundary, never a
    wallet-draining LLM call with an inflated prompt."""
    uid, token = _register(client, "pro-sp4@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid)
    _grant_consent(client, token)
    r = client.post(
        "/api/prep/study-plan",
        headers=_auth(token),
        json={"job_id": job_id, "days": bad_days},
    )
    assert r.status_code == 422
