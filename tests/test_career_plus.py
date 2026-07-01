"""Career+ ($24) as a REAL, differentiated, webhook-verified entitlement tier (Track C /
business-case-strength lever #2).

What these prove:
- ``plan_level`` is derived ONLY from the webhook-authoritative ``Subscription.plan`` — a
  client can never set it (no client-trusted unlock), and a lapsed subscription drops the
  level back to ``free`` even if the stale plan string still says careerplus.
- The Career+-exclusive salary-negotiation endpoint gates on ``career_plus`` server-side,
  BEFORE any LLM work, so a Pro/Free user gets a clean 403 (never a 503). The feature is
  ADDITIVE (no endpoint existed before) so gating it to Career+ removes nothing from Pro —
  no dark pattern.
- Honest degradation: a Career+ user with no LLM key gets a 503 (proving the entitlement
  gate PASSED), never a fake/blank negotiation script (SIDE-EFFECT INTEGRITY §6).
"""

from types import SimpleNamespace

import pytest

import asgi
from src import billing
from src.db.models import Subscription, User, UserTier


# --------------------------------------------------------------------------- helpers
def _register(client, email="cp@example.com", password="hunter2pw"):
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


def _make_career_plus(db_session, user_id, plan="careerplus_monthly"):
    """Seed the verified-entitlement state a signed webhook would produce: PREMIUM tier + a
    Subscription row whose plan id carries the careerplus prefix."""
    db_session.query(User).filter(User.id == user_id).update({User.tier: UserTier.PREMIUM})
    db_session.add(Subscription(user_id=user_id, plan=plan, status="active"))
    db_session.commit()


def _make_pro(db_session, user_id, plan="pro_monthly"):
    db_session.query(User).filter(User.id == user_id).update({User.tier: UserTier.PREMIUM})
    db_session.add(Subscription(user_id=user_id, plan=plan, status="active"))
    db_session.commit()


class _FakeWorkflows:
    """Stand-in for LLMWorkflows: returns a deterministic artifact-shaped object."""

    def __init__(self, db):
        self._db = db

    def generate_salary_negotiation(self, job, target_salary):
        assert isinstance(target_salary, int)
        return SimpleNamespace(
            id="art-neg-1",
            title=f"Salary Negotiation: {job.title}",
            content="## Talking points\nReal, specific negotiation scripts here.",
        )


@pytest.fixture()
def _llm_on(monkeypatch):
    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "LLMWorkflows", _FakeWorkflows)


# --------------------------------------------------------------------------- unit: plan level
def test_plan_level_for_plan_maps_prefix():
    assert billing.plan_level_for_plan("careerplus_monthly") == "career_plus"
    assert billing.plan_level_for_plan("careerplus_annual") == "career_plus"
    assert billing.plan_level_for_plan("pro_monthly") == "pro"
    assert billing.plan_level_for_plan("pro_annual") == "pro"


def test_plan_level_for_plan_is_fail_safe():
    """An unknown/None/garbled plan can NEVER accidentally unlock Career+ — defaults to pro."""
    assert billing.plan_level_for_plan(None) == "pro"
    assert billing.plan_level_for_plan("") == "pro"
    assert billing.plan_level_for_plan("garbage") == "pro"
    assert billing.plan_level_for_plan("enterprise_careerplus") == "pro"  # prefix must lead


def test_current_plan_level_covers_every_state():
    free = SimpleNamespace(tier=UserTier.FREE)
    prem = SimpleNamespace(tier=UserTier.PREMIUM)
    assert billing.current_plan_level(free, None) == "free"
    # A FREE user with a stale careerplus sub row is still free — tier is the source of truth
    # (a canceled/expired webhook flips tier to FREE; the plan string may lag).
    assert billing.current_plan_level(free, SimpleNamespace(plan="careerplus_monthly")) == "free"
    assert billing.current_plan_level(prem, None) == "pro"
    assert billing.current_plan_level(prem, SimpleNamespace(plan="pro_monthly")) == "pro"
    assert billing.current_plan_level(prem, SimpleNamespace(plan="careerplus_annual")) == "career_plus"


# --------------------------------------------------------------------------- /me plan_level
def test_me_reports_free_plan_level(client):
    _, token = _register(client)
    r = client.get("/api/auth/me", headers=_auth(token))
    assert r.status_code == 200, r.text
    u = r.json()["user"]
    assert u["plan_level"] == "free"
    assert u["career_plus"] is False


def test_me_reports_pro_and_career_plus(client, db_session):
    uid_pro, tok_pro = _register(client, "pro@example.com")
    uid_cp, tok_cp = _register(client, "cp2@example.com")
    _make_pro(db_session, uid_pro)
    _make_career_plus(db_session, uid_cp)

    pro = client.get("/api/auth/me", headers=_auth(tok_pro)).json()["user"]
    assert pro["plan_level"] == "pro"
    assert pro["career_plus"] is False

    cp = client.get("/api/auth/me", headers=_auth(tok_cp)).json()["user"]
    assert cp["plan_level"] == "career_plus"
    assert cp["career_plus"] is True


# --------------------------------------------------------------------------- endpoint gating
def test_salary_negotiation_blocked_for_free(client):
    _, token = _register(client)
    job_id = _add_job(client, token)
    r = client.post(
        "/api/prep/salary-negotiation",
        headers=_auth(token),
        json={"job_id": job_id, "target_salary": 180000},
    )
    assert r.status_code == 403
    assert "career+" in r.json()["detail"].lower()


def test_salary_negotiation_blocked_for_pro_not_a_dark_pattern(client, db_session):
    """A Pro (PREMIUM) user is refused — the feature is ADDITIVE (Pro never had it), so this
    removes nothing. Proves plan_level, not the binary tier, is the gate."""
    uid, token = _register(client, "pro3@example.com")
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    r = client.post(
        "/api/prep/salary-negotiation",
        headers=_auth(token),
        json={"job_id": job_id, "target_salary": 180000},
    )
    assert r.status_code == 403


def test_salary_negotiation_gate_precedes_job_lookup(client):
    """A non-Career+ user gets 403 even with a bogus job id — the entitlement check runs
    before the DB lookup (no information leak about job existence, clean gate)."""
    _, token = _register(client, "free2@example.com")
    r = client.post(
        "/api/prep/salary-negotiation",
        headers=_auth(token),
        json={"job_id": "does-not-exist", "target_salary": 100000},
    )
    assert r.status_code == 403


def test_career_plus_passes_gate_but_degrades_honestly_without_key(client, db_session):
    """A Career+ user with NO Gemini key gets 503 (honest degradation) — crucially NOT 403,
    which PROVES the entitlement gate passed and the block is only the missing key."""
    uid, token = _register(client, "cp3@example.com")
    job_id = _add_job(client, token)
    _make_career_plus(db_session, uid)
    r = client.post(
        "/api/prep/salary-negotiation",
        headers=_auth(token),
        json={"job_id": job_id, "target_salary": 180000},
    )
    assert r.status_code == 503
    assert "gemini_api_key" in r.json()["detail"].lower()


def test_career_plus_generates_real_artifact(client, db_session, _llm_on):
    uid, token = _register(client, "cp4@example.com")
    job_id = _add_job(client, token)
    _make_career_plus(db_session, uid)
    r = client.post(
        "/api/prep/salary-negotiation",
        headers=_auth(token),
        json={"job_id": job_id, "target_salary": 180000},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    art = body["artifact"]
    assert art["id"] == "art-neg-1"
    assert "Salary Negotiation" in art["title"]
    assert art["content"].strip()  # real content, not a placeholder


def test_career_plus_foreign_job_is_404(client, db_session, _llm_on):
    uid_owner, tok_owner = _register(client, "owner@example.com")
    job_id = _add_job(client, tok_owner)
    uid_cp, tok_cp = _register(client, "cp5@example.com")
    _make_career_plus(db_session, uid_cp)
    r = client.post(
        "/api/prep/salary-negotiation",
        headers=_auth(tok_cp),
        json={"job_id": job_id, "target_salary": 180000},
    )
    assert r.status_code == 404


# --------------------------------------------------------------------------- webhook round-trip
def test_verified_webhook_grants_career_plus_level(client, db_session):
    """The ONLY way to become Career+ is a verified event: apply a careerplus
    checkout.session.completed and assert tier=PREMIUM + plan recorded + /me reports
    career_plus. No client input set the level."""
    uid, token = _register(client, "buyer-cp@example.com")
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": uid,
                "payment_status": "paid",
                "customer": "cus_x",
                "subscription": "sub_x",
                "metadata": {"user_id": uid, "plan": "careerplus_annual"},
            }
        },
    }
    affected = billing.apply_event(event, db_session)
    db_session.commit()
    assert affected == uid

    user = db_session.query(User).filter(User.id == uid).first()
    assert user.tier == UserTier.PREMIUM
    sub = db_session.query(Subscription).filter(Subscription.user_id == uid).first()
    assert sub.plan == "careerplus_annual"

    me = client.get("/api/auth/me", headers=_auth(token)).json()["user"]
    assert me["plan_level"] == "career_plus"
    assert me["career_plus"] is True
