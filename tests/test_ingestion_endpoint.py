"""Functional tests for the ATS import-preview endpoint.

All network is mocked so the gate runs offline. We assert the INTENDED OUTCOME for
each branch: real listings on a reachable Greenhouse/Lever board, a truthful empty
state when there are no roles, an honest "unreachable" state (never "no jobs") when the
board errors, an "unsupported" state for other ATSes, and an SSRF refusal for internal
URLs.
"""
import requests

import src.ingestion.detector as detector_mod
import src.ingestion.greenhouse as greenhouse_mod
import src.ingestion.lever as lever_mod
import src.ingestion.url_guard as url_guard


def _token(client) -> str:
    r = client.post(
        "/api/auth/register",
        json={"email": "ats@example.com", "password": "supersecret123"},
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _patch_public_dns(monkeypatch):
    """Make the SSRF guard resolve any hostname to a public IP, offline + deterministic."""
    monkeypatch.setattr(
        url_guard.socket,
        "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )


class _FakeResp:
    def __init__(self, json_data, url="https://boards.greenhouse.io/acme", text=""):
        self._json = json_data
        self.url = url
        self.text = text

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


def _hdr(token):
    return {"Authorization": f"Bearer {token}"}


def test_import_preview_requires_auth(client):
    r = client.post("/api/jobs/import-preview", json={"careers_url": "https://example.com"})
    assert r.status_code == 401


def test_import_preview_returns_real_greenhouse_listings(client, monkeypatch):
    token = _token(client)
    _patch_public_dns(monkeypatch)
    payload = {
        "jobs": [
            {
                "id": 101,
                "title": "Staff Engineer",
                "location": {"name": "Remote - US"},
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/101",
                "updated_at": "2026-06-01T00:00:00Z",
            },
            {
                "id": 102,
                "title": "Product Designer",
                "location": {"name": "New York"},
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/102",
                "updated_at": "2026-06-02T00:00:00Z",
            },
        ]
    }
    monkeypatch.setattr(greenhouse_mod.requests, "get", lambda *a, **k: _FakeResp(payload))

    r = client.post(
        "/api/jobs/import-preview",
        json={"careers_url": "https://boards.greenhouse.io/acme"},
        headers=_hdr(token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ats"] == "greenhouse"
    assert body["supported"] is True
    assert body["reachable"] is True
    assert len(body["jobs"]) == 2
    assert {j["title"] for j in body["jobs"]} == {"Staff Engineer", "Product Designer"}
    assert body["jobs"][0]["company_slug"] == "acme"
    assert body["jobs"][0]["external_id"] == "101"
    assert body["truncated"] is False


def test_import_preview_returns_real_lever_listings(client, monkeypatch):
    token = _token(client)
    _patch_public_dns(monkeypatch)
    payload = [
        {
            "id": "abc-123",
            "text": "Backend Engineer",
            "categories": {"location": "Remote", "team": "Platform", "commitment": "Full-time"},
            "lists": [{"text": "Requirements", "content": "<li>Python</li>"}],
            "descriptionPlain": "Build the platform.",
            "hostedUrl": "https://jobs.lever.co/acme/abc-123",
        }
    ]
    monkeypatch.setattr(lever_mod.requests, "get", lambda *a, **k: _FakeResp(payload))

    r = client.post(
        "/api/jobs/import-preview",
        json={"careers_url": "https://jobs.lever.co/acme"},
        headers=_hdr(token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ats"] == "lever"
    assert body["supported"] is True
    assert body["reachable"] is True
    assert len(body["jobs"]) == 1
    assert body["jobs"][0]["title"] == "Backend Engineer"
    assert body["jobs"][0]["company_slug"] == "acme"


def test_import_preview_truncates_to_limit(client, monkeypatch):
    token = _token(client)
    _patch_public_dns(monkeypatch)
    jobs = [
        {
            "id": i,
            "title": f"Role {i}",
            "location": {"name": "Remote"},
            "absolute_url": f"https://boards.greenhouse.io/acme/jobs/{i}",
            "updated_at": "2026-06-01T00:00:00Z",
        }
        for i in range(60)
    ]
    monkeypatch.setattr(greenhouse_mod.requests, "get", lambda *a, **k: _FakeResp({"jobs": jobs}))

    r = client.post(
        "/api/jobs/import-preview",
        json={"careers_url": "https://boards.greenhouse.io/acme"},
        headers=_hdr(token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["jobs"]) == 50
    assert body["truncated"] is True


def test_import_preview_unreachable_board_is_honest_not_empty(client, monkeypatch):
    token = _token(client)
    _patch_public_dns(monkeypatch)

    def _boom(*a, **k):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(greenhouse_mod.requests, "get", _boom)

    r = client.post(
        "/api/jobs/import-preview",
        json={"careers_url": "https://boards.greenhouse.io/acme"},
        headers=_hdr(token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # The board errored — we must say "unreachable", NEVER imply there are no roles.
    assert body["reachable"] is False
    assert body["jobs"] == []
    assert "unreachable" in body["message"].lower()


def test_import_preview_no_open_roles_is_truthful_empty(client, monkeypatch):
    token = _token(client)
    _patch_public_dns(monkeypatch)
    monkeypatch.setattr(greenhouse_mod.requests, "get", lambda *a, **k: _FakeResp({"jobs": []}))

    r = client.post(
        "/api/jobs/import-preview",
        json={"careers_url": "https://boards.greenhouse.io/acme"},
        headers=_hdr(token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reachable"] is True
    assert body["jobs"] == []
    assert "no open roles" in body["message"].lower()


def test_import_preview_unknown_ats_is_honest(client, monkeypatch):
    token = _token(client)
    _patch_public_dns(monkeypatch)
    # A plain page with no ATS markers -> detector probes it (mocked) -> UNKNOWN.
    monkeypatch.setattr(
        detector_mod.requests,
        "get",
        lambda *a, **k: _FakeResp({}, url="https://example.com/careers", text="<html>jobs</html>"),
    )

    r = client.post(
        "/api/jobs/import-preview",
        json={"careers_url": "https://example.com/careers"},
        headers=_hdr(token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ats"] == "unknown"
    assert body["supported"] is False
    assert body["jobs"] == []
    assert "greenhouse or lever" in body["message"].lower()


def test_import_preview_blocks_ssrf_to_internal_hosts(client):
    token = _token(client)
    # IP literals + non-http schemes resolve offline; the guard must refuse them all.
    for url in (
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata (link-local)
        "http://127.0.0.1:5432/",                     # loopback / internal DB
        "http://10.0.0.5/careers",                    # RFC1918
        "file:///etc/passwd",                          # non-http scheme
    ):
        r = client.post(
            "/api/jobs/import-preview",
            json={"careers_url": url},
            headers=_hdr(token),
        )
        assert r.status_code == 400, f"{url} -> {r.status_code}: {r.text}"
        assert "not allowed" in r.json()["detail"].lower()
