"""Profile enrichment from a user's public GitHub profile (Track A — the market's /expand).

Honest, structured design: no arbitrary-URL scrape (SSRF + hallucination risk) — we validate a
username and read the PUBLIC GitHub REST API at the fixed host api.github.com, aggregating the
repos' own language + topics into source-tagged competencies. These tests pin: username parsing,
the language/topic aggregation (forks skipped, capped), graceful degradation on every failure
mode, the Pro+ gate, the honest found=0 path, re-import REPLACE semantics, and that discovered
skills actually feed fit-scoring.
"""
import pytest
import requests

from src.db.models import EnrichedCompetency, JobPosting, Subscription, User, UserTier
from src.enrichment import github_enricher
from src.enrichment.github_enricher import (
    DiscoveredCompetency,
    discover_github_competencies,
    parse_github_username,
    replace_github_competencies,
    user_enriched_skills,
)


# --------------------------------------------------------------------------- helpers
def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _register(client, email="gh@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], r.json()["token"]


def _make_premium(db_session, user_id, resume="Backend engineer"):
    db_session.query(User).filter(User.id == user_id).update(
        {User.tier: UserTier.PREMIUM, User.resume_text: resume}
    )
    db_session.add(Subscription(user_id=user_id, plan="pro_monthly", status="active"))
    db_session.commit()


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _repos(*specs):
    """Build a repos payload; each spec is (language, topics, fork)."""
    out = []
    for lang, topics, fork in specs:
        out.append({"language": lang, "topics": list(topics), "fork": fork})
    return out


# --------------------------------------------------------------------------- username parsing
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("torvalds", "torvalds"),
        ("  torvalds  ", "torvalds"),
        ("github.com/torvalds", "torvalds"),
        ("https://github.com/torvalds", "torvalds"),
        ("https://www.github.com/torvalds/some-repo", "torvalds"),
        ("octocat-1", "octocat-1"),
    ],
)
def test_parse_username_valid(raw, expected):
    assert parse_github_username(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "-leadinghyphen",
        "trailinghyphen-",
        "double--hyphen",
        "way-too-long-" + "a" * 40,
        "has space",
        "https://gitlab.com/torvalds",  # wrong host
        "https://github.com/",  # no username
        "user@name",
    ],
)
def test_parse_username_invalid(raw):
    assert parse_github_username(raw) is None


# --------------------------------------------------------------------------- discovery
def test_discover_aggregates_languages_and_topics(monkeypatch):
    payload = _repos(
        ("Python", ["fastapi", "backend"], False),
        ("Python", ["cli"], False),
        ("TypeScript", ["react"], False),
        ("JavaScript", [], True),  # fork — must be skipped
    )
    monkeypatch.setattr(github_enricher.requests, "get", lambda *a, **k: _FakeResp(payload))
    out = discover_github_competencies("someone")
    skills = [d.skill for d in out]

    # Languages ranked by repo count (python 2 > typescript 1); fork's JavaScript excluded.
    assert skills[0] == "python"
    assert "typescript" in skills
    assert "javascript" not in skills
    # Topics folded in, lowercased, deduped against languages.
    assert "fastapi" in skills and "react" in skills
    # Evidence is honest + human-readable.
    py = next(d for d in out if d.skill == "python")
    assert "2 repositories" in py.evidence


def test_discover_unknown_user_returns_empty(monkeypatch):
    monkeypatch.setattr(
        github_enricher.requests, "get", lambda *a, **k: _FakeResp([], status=404)
    )
    assert discover_github_competencies("ghost") == []


def test_discover_network_error_degrades(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(github_enricher.requests, "get", boom)
    assert discover_github_competencies("someone") == []


def test_discover_non_json_degrades(monkeypatch):
    monkeypatch.setattr(
        github_enricher.requests,
        "get",
        lambda *a, **k: _FakeResp(ValueError("not json")),
    )
    assert discover_github_competencies("someone") == []


def test_discover_caps_total(monkeypatch):
    payload = _repos(*[(f"Lang{i}", [], False) for i in range(60)])
    monkeypatch.setattr(github_enricher.requests, "get", lambda *a, **k: _FakeResp(payload))
    out = discover_github_competencies("prolific")
    assert len(out) <= github_enricher._MAX_COMPETENCIES


# --------------------------------------------------------------------------- persistence
def test_replace_is_idempotent_upsert(db_session):
    user = User(email="p@example.com", password_hash="x", tier=UserTier.PREMIUM)
    db_session.add(user)
    db_session.flush()

    first = [DiscoveredCompetency("python", "e"), DiscoveredCompetency("go", "e")]
    replace_github_competencies(db_session, user, "https://github.com/x", first)
    db_session.commit()
    assert user_enriched_skills(db_session, user) == {"python", "go"}

    # Re-import with a different set REPLACES (go dropped, rust added) — no stale rows, no dup key.
    second = [DiscoveredCompetency("python", "e"), DiscoveredCompetency("rust", "e")]
    replace_github_competencies(db_session, user, "https://github.com/x", second)
    db_session.commit()
    assert user_enriched_skills(db_session, user) == {"python", "rust"}
    rows = db_session.query(EnrichedCompetency).filter(EnrichedCompetency.user_id == user.id).all()
    assert len(rows) == 2


# --------------------------------------------------------------------------- endpoint
def test_endpoint_requires_pro(client):
    _uid, token = _register(client)
    r = client.post("/api/profile/enrich/github", headers=_auth(token), json={"github": "torvalds"})
    assert r.status_code == 403


def test_endpoint_rejects_bad_handle(client, db_session):
    uid, token = _register(client)
    _make_premium(db_session, uid)
    r = client.post(
        "/api/profile/enrich/github", headers=_auth(token), json={"github": "not a user"}
    )
    assert r.status_code == 400


def test_endpoint_imports_and_reads_back(client, db_session, monkeypatch):
    uid, token = _register(client)
    _make_premium(db_session, uid)
    payload = _repos(("Python", ["fastapi"], False), ("Go", [], False))
    monkeypatch.setattr(github_enricher.requests, "get", lambda *a, **k: _FakeResp(payload))

    r = client.post(
        "/api/profile/enrich/github", headers=_auth(token), json={"github": "github.com/me"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] and body["found"] == 3 and body["username"] == "me"
    skills = {c["skill"] for c in body["competencies"]}
    assert {"python", "go", "fastapi"} <= skills

    # GET reads the persisted state back.
    g = client.get("/api/profile/enrichment", headers=_auth(token))
    assert g.status_code == 200
    assert {c["skill"] for c in g.json()["competencies"]} == skills


def test_endpoint_honest_zero_result(client, db_session, monkeypatch):
    uid, token = _register(client, email="z@example.com")
    _make_premium(db_session, uid)
    monkeypatch.setattr(
        github_enricher.requests, "get", lambda *a, **k: _FakeResp([], status=404)
    )
    r = client.post("/api/profile/enrich/github", headers=_auth(token), json={"github": "ghost"})
    assert r.status_code == 200
    body = r.json()
    # No fake success: found=0, honest message, nothing persisted.
    assert body["found"] == 0 and "No public repositories" in body["message"]
    assert body["competencies"] == []


def test_endpoint_delete_clears(client, db_session, monkeypatch):
    uid, token = _register(client, email="d@example.com")
    _make_premium(db_session, uid)
    monkeypatch.setattr(
        github_enricher.requests,
        "get",
        lambda *a, **k: _FakeResp(_repos(("Python", [], False))),
    )
    client.post("/api/profile/enrich/github", headers=_auth(token), json={"github": "me"})
    d = client.delete("/api/profile/enrichment", headers=_auth(token))
    assert d.status_code == 200 and d.json()["deleted"] == 1
    g = client.get("/api/profile/enrichment", headers=_auth(token))
    assert g.json()["competencies"] == []


# --------------------------------------------------------------------------- feeds scoring
def test_enriched_skills_feed_fit_score(db_session):
    """A GitHub-proven skill the résumé omits should raise the skills match for a role needing it."""
    from src.ranking.scorer import JobScorer

    user = User(email="s@example.com", password_hash="x", tier=UserTier.PREMIUM, resume_text="")
    db_session.add(user)
    db_session.flush()
    job = JobPosting(
        user_id=user.id, title="Rust Engineer", company_name="Acme",
        description="rust", requirements="rust",
    )
    db_session.add(job)
    db_session.flush()

    # Without enrichment: résumé has no skills → the rust requirement is unmatched. Capture the
    # scalar now — score_job mutates the SAME JobScore row in place on the re-score below.
    base = JobScorer(db_session).score_job(job, user, use_embeddings=False)
    assert "rust" not in (base.matching_skills or [])
    base_match = base.skills_match

    replace_github_competencies(
        db_session, user, "https://github.com/s", [DiscoveredCompetency("rust", "e")]
    )
    db_session.commit()

    enriched = JobScorer(db_session).score_job(job, user, use_embeddings=False)
    assert "rust" in (enriched.matching_skills or [])
    assert enriched.skills_match > base_match
