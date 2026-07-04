"""Pro-tier AI tailored-résumé endpoint (ROADMAP Track A — the highest-value premium AI hook).

Same server-side contract as the other prep tools (test_prep_tools.py): Pro+ gate BEFORE any LLM
work, honest 503 degradation (never a fake artifact), consent before Gemini. The feature adds ONE
guard the others don't have — it REQUIRES a saved résumé: you cannot "tailor" a résumé that doesn't
exist without fabricating a whole work history, and fabrication is the one thing this feature must
never do (VISION "honest > flashy"). So a paid user with an empty résumé gets an honest 400, never
an invented résumé. These tests pin all of that.
"""

from types import SimpleNamespace

import pytest

import asgi
from src.db.models import Subscription, User, UserTier


# --------------------------------------------------------------------------- helpers
def _register(client, email="tr@example.com", password="hunter2pw"):
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


def _make_premium(db_session, user_id, plan="pro_monthly", resume="Senior Python engineer. FastAPI, AWS."):
    """Seed the verified-entitlement state a signed webhook would produce (PREMIUM + Subscription),
    plus a saved résumé (the tailored-résumé feature requires one). Pass resume="" to seed a paid
    user with NO résumé (the 400-guard case)."""
    db_session.query(User).filter(User.id == user_id).update(
        {User.tier: UserTier.PREMIUM, User.resume_text: resume}
    )
    db_session.add(Subscription(user_id=user_id, plan=plan, status="active"))
    db_session.commit()


def _grant_consent(client, token):
    assert client.post("/api/ai-consent", headers=_auth(token)).status_code == 200


class _FakeWorkflows:
    """Stand-in for LLMWorkflows returning a deterministic artifact-shaped object."""

    def __init__(self, db):
        self._db = db

    def generate_tailored_resume(self, job, user):
        return SimpleNamespace(
            id="art-tr-1",
            title=f"Tailored Résumé: {job.title} at {job.company_name}",
            content="## Jane Doe\nSenior Python engineer — FastAPI, AWS. (tailored from real résumé)",
        )


@pytest.fixture()
def _llm_on(monkeypatch):
    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "LLMWorkflows", _FakeWorkflows)


# ============================================================ gate
def test_tailored_resume_blocked_for_free(client):
    _, token = _register(client)
    job_id = _add_job(client, token)
    r = client.post("/api/prep/tailored-resume", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 403
    assert "pro" in r.json()["detail"].lower()


def test_tailored_resume_gate_precedes_job_lookup(client):
    """A FREE user gets 403 even with a bogus job id — the tier check runs before the DB lookup."""
    _, token = _register(client, "free-tr@example.com")
    r = client.post(
        "/api/prep/tailored-resume", headers=_auth(token), json={"job_id": "does-not-exist"}
    )
    assert r.status_code == 403


def test_tailored_resume_foreign_job_is_404(client, db_session, _llm_on):
    uid_owner, tok_owner = _register(client, "owner-tr@example.com")
    job_id = _add_job(client, tok_owner)
    uid_pro, tok_pro = _register(client, "pro-tr@example.com")
    _make_premium(db_session, uid_pro)
    r = client.post("/api/prep/tailored-resume", headers=_auth(tok_pro), json={"job_id": job_id})
    assert r.status_code == 404


# ============================================================ résumé-required guard (unique to this feature)
def test_tailored_resume_requires_saved_resume(client, db_session, _llm_on):
    """A paid user with NO saved résumé gets an honest 400 (add your résumé first), NEVER a
    fabricated résumé — and crucially NOT a 503, proving the guard ran before the LLM path."""
    uid, token = _register(client, "pro-nr@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid, resume="")  # PREMIUM but no résumé
    _grant_consent(client, token)
    r = client.post("/api/prep/tailored-resume", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 400
    assert "résumé" in r.json()["detail"].lower() or "resume" in r.json()["detail"].lower()


def test_tailored_resume_resume_guard_precedes_key_check(client, db_session):
    """No key AND no résumé → the résumé guard (400) wins over the key check (503): the endpoint
    refuses honestly for the reason the user can actually fix, and never touches the LLM path."""
    uid, token = _register(client, "pro-nr2@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid, resume="")  # no key configured in test env either
    r = client.post("/api/prep/tailored-resume", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 400


# ============================================================ honest degradation + consent
def test_tailored_resume_pro_passes_gate_but_degrades_without_key(client, db_session):
    """A Pro user WITH a résumé but NO Gemini key gets 503 — NOT 403 (gate passed) and NOT 400
    (résumé present), proving the block is only the missing key (honest degradation)."""
    uid, token = _register(client, "pro-tr2@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid)  # seeds a résumé
    r = client.post("/api/prep/tailored-resume", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 503
    assert "gemini_api_key" in r.json()["detail"].lower()


def test_tailored_resume_requires_consent_before_llm(client, db_session, _llm_on):
    """A PREMIUM user WITH a key + a résumé is still blocked (403 ai_consent_required) until they
    grant third-party-AI consent (Apple 5.1.2(i)) — the résumé never reaches Gemini without it."""
    uid, token = _register(client, "pro-tr3@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid)
    r = client.post("/api/prep/tailored-resume", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "ai_consent_required"


# ============================================================ happy path
def test_tailored_resume_pro_generates_real_artifact(client, db_session, _llm_on):
    uid, token = _register(client, "pro-tr4@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid)
    _grant_consent(client, token)
    r = client.post("/api/prep/tailored-resume", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    art = body["artifact"]
    assert art["id"] == "art-tr-1"
    assert "Tailored Résumé" in art["title"]
    assert art["content"].strip()  # real content, not a placeholder


def test_tailored_resume_available_to_career_plus_too(client, db_session, _llm_on):
    """A Pro-tier feature is available to Career+ (a strict superset) as well."""
    uid, token = _register(client, "cp-tr@example.com")
    job_id = _add_job(client, token)
    _make_premium(db_session, uid, plan="careerplus_monthly")
    _grant_consent(client, token)
    r = client.post("/api/prep/tailored-resume", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 200, r.text
