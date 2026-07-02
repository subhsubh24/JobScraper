"""Third-party-AI consent gate (Apple App Store Review 5.1.2(i)).

Apple requires EXPLICIT, revocable consent BEFORE personal data is shared with a third-party
AI. Career Operator sends resume / job text / coach messages to Google Gemini, so every
generative AI path is gated server-side on ``users.ai_consent_at``.

These tests prove the REAL behaviour, not just that the code compiles:
- the core loop (add job -> fit score) still WORKS before consent, via a fully-local
  heuristic that sends nothing to Gemini (no dead-end);
- the consent state round-trips through /api/ai-consent + /api/auth/me (grant + revoke);
- every generative endpoint (prep pack, salary negotiation, coach) BLOCKS with a
  machine-readable 403 and DOES NOT invoke the LLM when consent is absent — the gate fires
  BEFORE the third-party call (SIDE-EFFECT INTEGRITY: no data leaves without consent);
- granting consent UNLOCKS the same endpoints.
"""
import types

import asgi
from src.db.models import Subscription, User, UserTier


def _register(client, email="consent@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _add_job(client, token):
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": "Backend Engineer", "company_name": "Acme", "description": "python fastapi"},
    )
    assert r.status_code == 200, r.text
    return r.json()["job"]


def _make_premium(db_session, career_plus=False):
    """Promote the (single) registered user to PREMIUM, optionally Career+."""
    user = db_session.query(User).one()
    user.tier = UserTier.PREMIUM
    if career_plus:
        db_session.add(
            Subscription(user_id=user.id, plan="careerplus_monthly", status="active")
        )
    db_session.commit()


# --------------------------------------------------------------------------- #
# Core loop still works before consent (honest local degrade, no dead-end)
# --------------------------------------------------------------------------- #
def test_scoring_works_without_consent_via_local_heuristic(client):
    """A brand-new user (no consent) can still add a job and get a REAL fit score — the
    scorer runs the local skills heuristic (no Gemini call), so the core loop never
    dead-ends waiting for consent."""
    token = _register(client)
    job = _add_job(client, token)
    # A heuristic score is produced (not None) — the loop's 'aha' is not gated behind consent.
    assert job["score"] is not None


# --------------------------------------------------------------------------- #
# Consent state round-trips (grant + revoke) via the API
# --------------------------------------------------------------------------- #
def test_consent_state_round_trip(client):
    token = _register(client)

    me = client.get("/api/auth/me", headers=_auth(token)).json()["user"]
    assert me["ai_consent"] is False
    assert me["ai_consent_at"] is None

    granted = client.post("/api/ai-consent", headers=_auth(token))
    assert granted.status_code == 200, granted.text
    gu = granted.json()["user"]
    assert gu["ai_consent"] is True
    assert gu["ai_consent_at"] is not None
    # /me reflects it on a fresh read.
    assert client.get("/api/auth/me", headers=_auth(token)).json()["user"]["ai_consent"] is True

    revoked = client.delete("/api/ai-consent", headers=_auth(token))
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["user"]["ai_consent"] is False
    assert client.get("/api/auth/me", headers=_auth(token)).json()["user"]["ai_consent"] is False


def test_consent_endpoints_require_auth(client):
    assert client.post("/api/ai-consent").status_code == 401
    assert client.delete("/api/ai-consent").status_code == 401


# --------------------------------------------------------------------------- #
# Prep pack: blocked (no LLM call) without consent; unlocked after consent
# --------------------------------------------------------------------------- #
def test_prep_pack_blocked_without_consent_and_makes_no_llm_call(client, monkeypatch):
    token = _register(client)
    job = _add_job(client, token)

    # Pretend a key IS configured so we get PAST the 503 and reach the consent gate.
    monkeypatch.setattr(asgi, "llm_available", lambda: True)

    # If the generator is EVER reached without consent, that is a data-leak bug — fail loud.
    def _boom(self, job, user):  # noqa: ANN001
        raise AssertionError("generate_prep_pack must not run before consent")

    monkeypatch.setattr(asgi.LLMWorkflows, "generate_prep_pack", _boom)

    r = client.post("/api/prep-packs/generate", headers=_auth(token), json={"job_id": job["id"]})
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["code"] == "ai_consent_required"


def test_prep_pack_unlocked_after_consent(client, monkeypatch):
    token = _register(client)
    job = _add_job(client, token)
    client.post("/api/ai-consent", headers=_auth(token))

    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    called = {}

    def _fake_prep(self, job, user):  # noqa: ANN001
        called["yes"] = True
        return types.SimpleNamespace(id="art1", title="Prep for Acme", content="# Prep\n...")

    monkeypatch.setattr(asgi.LLMWorkflows, "generate_prep_pack", _fake_prep)

    r = client.post("/api/prep-packs/generate", headers=_auth(token), json={"job_id": job["id"]})
    assert r.status_code == 200, r.text
    assert called.get("yes") is True
    assert r.json()["prep_pack"]["title"] == "Prep for Acme"


# --------------------------------------------------------------------------- #
# Coach: blocked (no LLM call) without consent; unlocked after consent
# --------------------------------------------------------------------------- #
def test_coach_blocked_without_consent_and_makes_no_llm_call(client, db_session, monkeypatch):
    token = _register(client)
    _make_premium(db_session)

    monkeypatch.setattr(asgi.CareerCoach, "available", staticmethod(lambda: True))

    def _boom(self, **kwargs):
        raise AssertionError("coach.chat must not run before consent")

    monkeypatch.setattr(asgi.CareerCoach, "chat", _boom)

    r = client.post("/api/coach/chat", headers=_auth(token), json={"message": "hi"})
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["code"] == "ai_consent_required"


def test_coach_unlocked_after_consent(client, db_session, monkeypatch):
    token = _register(client)
    _make_premium(db_session)
    client.post("/api/ai-consent", headers=_auth(token))

    monkeypatch.setattr(asgi.CareerCoach, "available", staticmethod(lambda: True))
    called = {}

    def _fake_chat(self, **kwargs):
        called["yes"] = True
        return "Here is some career advice."

    monkeypatch.setattr(asgi.CareerCoach, "chat", _fake_chat)

    r = client.post("/api/coach/chat", headers=_auth(token), json={"message": "hi"})
    assert r.status_code == 200, r.text
    assert called.get("yes") is True
    assert r.json()["message"] == "Here is some career advice."


# --------------------------------------------------------------------------- #
# Salary negotiation (Career+ exclusive): also gated on consent
# --------------------------------------------------------------------------- #
def test_salary_negotiation_blocked_without_consent(client, db_session, monkeypatch):
    token = _register(client)
    _make_premium(db_session, career_plus=True)
    job = _add_job(client, token)

    monkeypatch.setattr(asgi, "llm_available", lambda: True)

    def _boom(self, job, target_salary):  # noqa: ANN001
        raise AssertionError("generate_salary_negotiation must not run before consent")

    monkeypatch.setattr(asgi.LLMWorkflows, "generate_salary_negotiation", _boom)

    r = client.post(
        "/api/prep/salary-negotiation",
        headers=_auth(token),
        json={"job_id": job["id"], "target_salary": 150000},
    )
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["code"] == "ai_consent_required"


def test_salary_negotiation_unlocked_after_consent(client, db_session, monkeypatch):
    token = _register(client)
    _make_premium(db_session, career_plus=True)
    job = _add_job(client, token)
    client.post("/api/ai-consent", headers=_auth(token))

    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    called = {}

    def _fake(self, job, target_salary):  # noqa: ANN001
        called["yes"] = True
        return types.SimpleNamespace(id="s1", title="Negotiation", content="Ask for more.")

    monkeypatch.setattr(asgi.LLMWorkflows, "generate_salary_negotiation", _fake)

    r = client.post(
        "/api/prep/salary-negotiation",
        headers=_auth(token),
        json={"job_id": job["id"], "target_salary": 150000},
    )
    assert r.status_code == 200, r.text
    assert called.get("yes") is True
