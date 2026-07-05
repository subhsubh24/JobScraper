"""Evals for GitHub profile enrichment (Track A /expand).

A deterministic golden (per-PR, offline) pins the exact ranked competencies for a fixed repos
fixture — languages ranked by repo count, forks excluded, topics folded in and deduped. This is
the real logic; enrichment is NOT an LLM feature (it reads STRUCTURED GitHub API data — no model
call, so the eval-coverage gate doesn't require it).

There is deliberately NO live happy-path fetch here: the PUBLIC GitHub API is rate-limited to 60
req/hr per IP for UNAUTHENTICATED callers, so from shared CI IPs it returns 403 unpredictably — a
live happy-path test would be a flaky false-red (a churn signal), not a reliable §28 real-service
lane. The graceful-DEGRADE path (a 403/network error → an empty result, never a raise) IS the
real, observable behavior and is pinned by the mocked round-trip in ``tests/test_github_enrichment.py``
(``test_discover_unknown_user_returns_empty`` / ``test_discover_network_error_degrades``).
VALIDATION.md declares this capability ``mock`` for that reason (honest, not a synthetic ``real``).
"""
import requests

from src.enrichment import github_enricher
from src.enrichment.github_enricher import discover_github_competencies


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def json(self):
        return self._payload


_GOLDEN_REPOS = [
    {"language": "Python", "topics": ["fastapi", "backend"], "fork": False},
    {"language": "Python", "topics": ["backend"], "fork": False},
    {"language": "Python", "topics": [], "fork": False},
    {"language": "TypeScript", "topics": ["react"], "fork": False},
    {"language": "TypeScript", "topics": [], "fork": False},
    {"language": "Go", "topics": [], "fork": False},
    {"language": "Ruby", "topics": [], "fork": True},  # fork → excluded
]


def test_golden_ranking(monkeypatch):
    monkeypatch.setattr(
        github_enricher.requests, "get", lambda *a, **k: _FakeResp(_GOLDEN_REPOS)
    )
    out = discover_github_competencies("golden")
    skills = [d.skill for d in out]

    # Languages first, ranked by repo count: python(3) > typescript(2) > go(1). Fork's ruby gone.
    assert skills[:3] == ["python", "typescript", "go"]
    assert "ruby" not in skills
    # Topics folded in AFTER languages, deduped, most-common first (backend 2 > fastapi 1 > react 1).
    topic_part = skills[3:]
    assert topic_part[0] == "backend"
    assert set(topic_part) == {"backend", "fastapi", "react"}
    # Evidence is honest + pluralized.
    assert next(d for d in out if d.skill == "python").evidence == "Primary language in 3 repositories"
    assert next(d for d in out if d.skill == "go").evidence == "Primary language in 1 repository"
