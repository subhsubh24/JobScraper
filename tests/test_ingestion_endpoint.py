"""Functional tests for the ATS import-preview endpoint.

All network is mocked so the gate runs offline. We assert the INTENDED OUTCOME for
each branch: real listings on a reachable board, a truthful empty state when there are
no roles, and an honest "unreachable" state (never "no jobs") when the board errors.
"""
import requests

import src.ingestion.detector as detector_mod
import src.ingestion.greenhouse as greenhouse_mod


def _token(client) -> str:
    r = client.post(
        "/api/auth/register",
        json={"email": "ats@example.com", "password": "supersecret123"},
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


class _FakeResp:
    def __init__(self, json_data, url="https://boards.greenhouse.io/acme", text=""):
        self._json = json_data
        self.url = url
        self.text = text

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


def test_import_preview_requires_auth(client):
    r = client.post("/api/jobs/import-preview", json={"careers_url": "https://x.co"})
    assert r.status_code == 401


def test_import_preview_returns_real_greenhouse_listings(client, monkeypatch):
    token = _token(client)
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
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ats"] == "greenhouse"
    assert body["reachable"] is True
    assert len(body["jobs"]) == 2
    titles = {j["title"] for j in body["jobs"]}
    assert titles == {"Staff Engineer", "Product Designer"}
    assert body["jobs"][0]["company"] == "acme"
    assert body["jobs"][0]["external_id"] == "101"


def test_import_preview_unreachable_board_is_honest_not_empty(client, monkeypatch):
    token = _token(client)

    def _boom(*a, **k):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(greenhouse_mod.requests, "get", _boom)

    r = client.post(
        "/api/jobs/import-preview",
        json={"careers_url": "https://boards.greenhouse.io/acme"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # The board errored — we must say "unreachable", NEVER imply there are no roles.
    assert body["reachable"] is False
    assert body["jobs"] == []
    assert "unreachable" in body["message"].lower()


def test_import_preview_no_open_roles_is_truthful_empty(client, monkeypatch):
    token = _token(client)
    monkeypatch.setattr(greenhouse_mod.requests, "get", lambda *a, **k: _FakeResp({"jobs": []}))

    r = client.post(
        "/api/jobs/import-preview",
        json={"careers_url": "https://boards.greenhouse.io/acme"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reachable"] is True
    assert body["jobs"] == []
    assert "no open roles" in body["message"].lower()


def test_import_preview_unknown_ats_is_honest(client, monkeypatch):
    token = _token(client)
    # A plain page with no ATS markers -> detector probes it (mocked) -> UNKNOWN.
    monkeypatch.setattr(
        detector_mod.requests,
        "get",
        lambda *a, **k: _FakeResp({}, url="https://example.com/careers", text="<html>jobs</html>"),
    )

    r = client.post(
        "/api/jobs/import-preview",
        json={"careers_url": "https://example.com/careers"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ats"] == "unknown"
    assert body["jobs"] == []
    assert "greenhouse or lever" in body["message"].lower()
