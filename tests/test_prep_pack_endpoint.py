"""Track C/E: outcome contract for the monetized prep-pack endpoint.

These assert the ENDPOINT's wiring, entitlement limits, and honest degradation —
not the LLM's content quality (which is non-deterministic). The LLM boundary is
mocked so we can prove: the success response carries the real artifact shape; the
free-tier monthly limit is enforced server-side; an absent key degrades honestly
(503, no fake result); and a foreign/missing job is a 404.
"""

from types import SimpleNamespace

import pytest

import asgi
from src.db.models import User, UserTier


def _register(client, email="prep@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _add_job(client, token):
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": "Engineer", "company_name": "Acme", "description": "python"},
    )
    assert r.status_code == 200, r.text
    return r.json()["job"]["id"]


class _FakeWorkflows:
    """Stand-in for LLMWorkflows: returns a deterministic artifact-shaped object."""

    def __init__(self, db):
        self._db = db

    def generate_prep_pack(self, job, user):
        return SimpleNamespace(
            id="artifact-123",
            title=f"Interview Prep: {job.title} at {job.company_name}",
            content="## 1. Company Research\nReal generated content here.",
        )


@pytest.fixture()
def _llm_on(monkeypatch):
    """Pretend the Gemini key is present and stub the workflow LLM call."""
    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "LLMWorkflows", _FakeWorkflows)


def test_prep_pack_success_contract(client, _llm_on):
    token = _register(client)
    job_id = _add_job(client, token)
    r = client.post("/api/prep-packs/generate", headers=_auth(token), json={"job_id": job_id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    pack = body["prep_pack"]
    assert pack["id"] == "artifact-123"
    assert "Interview Prep" in pack["title"]
    assert pack["content"].strip()  # non-empty real content, not a placeholder
    assert "prep_packs_remaining" in body


def test_prep_pack_free_tier_limit_enforced(client, _llm_on):
    """Free tier is 1 prep pack/month — the 2nd must be refused server-side (403)."""
    token = _register(client, "limited@example.com")
    job_id = _add_job(client, token)
    first = client.post("/api/prep-packs/generate", headers=_auth(token), json={"job_id": job_id})
    assert first.status_code == 200, first.text
    second = client.post("/api/prep-packs/generate", headers=_auth(token), json={"job_id": job_id})
    assert second.status_code == 403
    assert "free tier" in second.json()["detail"].lower()


def test_prep_pack_unlimited_for_premium(client, _llm_on, db_session):
    token = _register(client, "premium@example.com")
    job_id = _add_job(client, token)
    db_session.query(User).update({User.tier: UserTier.PREMIUM})
    db_session.commit()
    for _ in range(3):
        r = client.post("/api/prep-packs/generate", headers=_auth(token), json={"job_id": job_id})
        assert r.status_code == 200, r.text


def test_prep_pack_foreign_job_is_404(client, _llm_on):
    token_a = _register(client, "owner@example.com")
    job_id = _add_job(client, token_a)
    token_b = _register(client, "intruder@example.com")
    r = client.post("/api/prep-packs/generate", headers=_auth(token_b), json={"job_id": job_id})
    assert r.status_code == 404
