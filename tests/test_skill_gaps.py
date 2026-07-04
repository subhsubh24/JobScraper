"""Cross-pipeline skill-gap heatmap (free GET) + AI learning plan (Pro POST).

What these prove:
- The heatmap GET is FREE (no tier gate), fully LOCAL (works with no Gemini key — no LLM call),
  ownership-scoped, and surfaces honest empty states (no jobs / no résumé) rather than erroring.
- The heatmap ranks REAL data through the endpoint: skills demanded across the pipeline but
  missing from the résumé are GAPS (ranked by how many jobs demand them); skills the résumé has
  are STRENGTHS.
- The learning-plan POST mirrors the other AI generators' contract: Pro gate BEFORE any work,
  actionable 400s (no jobs / no résumé / no gaps) BEFORE the 503 key check and BEFORE a daily
  LLM slot is spent, honest 503 without a key (proving the gate passed), consent (Apple 5.1.2(i))
  before Gemini, and a moderated decline → 422 with NOTHING claimed (SIDE-EFFECT INTEGRITY §6).
- Only the user's OWN jobs feed the analysis (a foreign job never leaks into another user's plan).
"""
import pytest

import asgi
from src.db.models import Subscription, User, UserTier
from src.enrichment.llm_workflows import ModeratedContentError


# --------------------------------------------------------------------------- helpers
def _register(client, email="sg@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _add_job(client, token, title, description):
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": title, "company_name": "Acme", "description": description},
    )
    assert r.status_code == 200, r.text
    return r.json()["job"]["id"]


def _set_resume(db_session, user_id, resume_text):
    db_session.query(User).filter(User.id == user_id).update({User.resume_text: resume_text})
    db_session.commit()


def _make_premium(db_session, user_id, plan="pro_monthly"):
    db_session.query(User).filter(User.id == user_id).update({User.tier: UserTier.PREMIUM})
    db_session.add(Subscription(user_id=user_id, plan=plan, status="active"))
    db_session.commit()


def _grant_consent(client, token):
    assert client.post("/api/ai-consent", headers=_auth(token)).status_code == 200


class _FakeWorkflows:
    """Stand-in for LLMWorkflows: records the exact (gap_skills, job_titles) the endpoint computed
    server-side and passed in, and returns a deterministic plan. Set ``raise_moderated`` to prove
    the 422 path."""

    last_skills = None
    last_titles = None
    raise_moderated = False

    def __init__(self, db):
        self._db = db

    def generate_learning_plan(self, gap_skills, job_titles, user):
        _FakeWorkflows.last_skills = list(gap_skills)
        _FakeWorkflows.last_titles = list(job_titles)
        if _FakeWorkflows.raise_moderated:
            raise ModeratedContentError("withheld")
        return "# Your learning plan\n## kubernetes\nLearn the fundamentals, then build a project."


@pytest.fixture()
def _llm_on(monkeypatch):
    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "LLMWorkflows", _FakeWorkflows)
    _FakeWorkflows.last_skills = None
    _FakeWorkflows.last_titles = None
    _FakeWorkflows.raise_moderated = False


# ============================================================ heatmap (free GET)
def test_heatmap_empty_when_no_jobs(client):
    _, token = _register(client, "sg-empty@example.com")
    r = client.get("/api/insights/skill-gaps", headers=_auth(token))
    assert r.status_code == 200, r.text
    a = r.json()["analysis"]
    assert a["total_jobs"] == 0
    assert a["has_resume"] is False
    assert a["gaps"] == [] and a["strengths"] == []


def test_heatmap_is_free_and_ranks_real_data(client, db_session):
    """A FREE user (no key, no Gemini) gets a real ranked heatmap — the retention hook. Kubernetes
    is demanded by 2 of 3 jobs and absent from the résumé → the #1 gap; python is in the résumé →
    a strength, never a gap."""
    uid, token = _register(client, "sg-free@example.com")
    _set_resume(db_session, uid, "Experienced python and react engineer.")
    _add_job(client, token, "Platform Engineer", "python kubernetes aws")
    _add_job(client, token, "SRE", "kubernetes docker")
    _add_job(client, token, "Frontend", "python react")

    r = client.get("/api/insights/skill-gaps", headers=_auth(token))
    assert r.status_code == 200, r.text
    a = r.json()["analysis"]
    assert a["total_jobs"] == 3 and a["has_resume"] is True

    gap_skills = [g["skill"] for g in a["gaps"]]
    assert gap_skills[0] == "kubernetes"  # most-demanded missing skill ranks first
    assert "python" not in gap_skills and "react" not in gap_skills  # résumé skills aren't gaps
    top = a["gaps"][0]
    assert top["job_count"] == 2 and top["total_jobs"] == 3
    assert top["coverage"] == pytest.approx(2 / 3, abs=1e-3) and top["in_resume"] is False

    strengths = {s["skill"] for s in a["strengths"]}
    assert "python" in strengths and "react" in strengths


def test_heatmap_only_counts_own_jobs(client, db_session):
    owner_id, owner_tok = _register(client, "sg-owner@example.com")
    _add_job(client, owner_tok, "Backend", "kubernetes terraform")

    me_id, me_tok = _register(client, "sg-me@example.com")
    _set_resume(db_session, me_id, "python developer")
    _add_job(client, me_tok, "Data", "python")

    r = client.get("/api/insights/skill-gaps", headers=_auth(me_tok))
    a = r.json()["analysis"]
    assert a["total_jobs"] == 1  # only my one job
    assert all(g["skill"] != "kubernetes" for g in a["gaps"])  # owner's skill never leaks in


# ============================================================ learning plan (Pro POST)
def test_learning_plan_blocked_for_free(client):
    """Free → 403, and the tier gate runs BEFORE the jobs query (no info leak, clean gate)."""
    _, token = _register(client, "lp-free@example.com")
    r = client.post("/api/insights/learning-plan", headers=_auth(token))
    assert r.status_code == 403
    assert "pro" in r.json()["detail"].lower()


def test_learning_plan_pro_no_jobs_is_400(client, db_session):
    uid, token = _register(client, "lp-nojobs@example.com")
    _make_premium(db_session, uid)
    r = client.post("/api/insights/learning-plan", headers=_auth(token))
    assert r.status_code == 400
    assert "track some jobs" in r.json()["detail"].lower()


def test_learning_plan_pro_no_resume_is_400(client, db_session):
    uid, token = _register(client, "lp-noresume@example.com")
    _make_premium(db_session, uid)
    _add_job(client, token, "Platform", "kubernetes aws")
    r = client.post("/api/insights/learning-plan", headers=_auth(token))
    assert r.status_code == 400
    assert "résumé" in r.json()["detail"] or "resume" in r.json()["detail"].lower()


def test_learning_plan_no_gaps_is_400(client, db_session):
    """A résumé that already covers every demanded skill has no gaps → an honest 400, not a
    fabricated plan for nonexistent gaps."""
    uid, token = _register(client, "lp-nogaps@example.com")
    _make_premium(db_session, uid)
    _set_resume(db_session, uid, "python react docker kubernetes")
    _add_job(client, token, "Full stack", "python react")
    r = client.post("/api/insights/learning-plan", headers=_auth(token))
    assert r.status_code == 400
    assert "no skill gaps" in r.json()["detail"].lower()


def test_learning_plan_pro_degrades_without_key(client, db_session):
    """Pro user WITH gaps but NO key → 503 (NOT 403) — proves the gate passed; honest degradation
    with no fake plan (§6). The 400s (jobs/résumé/gaps) are all satisfied, so we reach the key check."""
    uid, token = _register(client, "lp-nokey@example.com")
    _make_premium(db_session, uid)
    _set_resume(db_session, uid, "python engineer")
    _add_job(client, token, "Platform", "kubernetes aws")
    r = client.post("/api/insights/learning-plan", headers=_auth(token))
    assert r.status_code == 503
    assert "gemini_api_key" in r.json()["detail"].lower()


def test_learning_plan_requires_consent_before_llm(client, db_session, _llm_on):
    uid, token = _register(client, "lp-consent@example.com")
    _make_premium(db_session, uid)
    _set_resume(db_session, uid, "python engineer")
    _add_job(client, token, "Platform", "kubernetes aws")
    r = client.post("/api/insights/learning-plan", headers=_auth(token))
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "ai_consent_required"


def test_learning_plan_generates_from_server_computed_gaps(client, db_session, _llm_on):
    """The gaps are recomputed SERVER-SIDE from the user's own jobs (never trusted from a client
    body) and only the top gap skill NAMES + job titles reach the generator."""
    uid, token = _register(client, "lp-ok@example.com")
    _make_premium(db_session, uid, plan="careerplus_monthly")  # Career+ (superset) works too
    _set_resume(db_session, uid, "python developer")
    _add_job(client, token, "Platform Engineer", "kubernetes aws")
    _add_job(client, token, "SRE", "kubernetes docker")
    _grant_consent(client, token)

    r = client.post("/api/insights/learning-plan", headers=_auth(token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    art = body["artifact"]
    assert art["content"].strip() and "learning plan" in art["content"].lower()
    # kubernetes (2 jobs, missing) is the top gap the endpoint computed and passed to the model.
    assert _FakeWorkflows.last_skills[0] == "kubernetes"
    assert "python" not in _FakeWorkflows.last_skills  # a résumé skill is never a gap
    assert art["skills"][0] == "kubernetes"
    assert "Platform Engineer" in _FakeWorkflows.last_titles


def test_learning_plan_moderated_decline_is_422(client, db_session, _llm_on):
    """A moderated decline is not a learning plan — honest 422, nothing claimed (§6)."""
    _FakeWorkflows.raise_moderated = True
    uid, token = _register(client, "lp-mod@example.com")
    _make_premium(db_session, uid)
    _set_resume(db_session, uid, "python developer")
    _add_job(client, token, "Platform", "kubernetes aws")
    _grant_consent(client, token)
    r = client.post("/api/insights/learning-plan", headers=_auth(token))
    assert r.status_code == 422
    assert body_has_no_artifact(r.json())


def body_has_no_artifact(body: dict) -> bool:
    return "artifact" not in body and body.get("success") is not True
