"""Bounded retry/backoff on transient ATS upstream failures (Track F / QUALITY correctness gap).

A busy Greenhouse/Lever board briefly returns 429/5xx; without a retry ONE transient blip is
reported to the user as "board unreachable" and every good job in it is dropped. ``get_with_retry``
retries such fast-failing signals (429/5xx + ConnectionError) with a bounded backoff, but NEVER a
Timeout (which already consumed serverless budget). These tests pin: it retries then succeeds,
gives up gracefully after the cap, never retries a Timeout, and the clients keep degrading
honestly on exhaustion.
"""
import requests

from src.ingestion import base
from src.ingestion.base import get_with_retry, _MAX_RETRIES
from src.ingestion.greenhouse import GreenhouseClient
from src.ingestion.lever import LeverClient


class _Resp:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload if payload is not None else {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._payload


def _seq(monkeypatch, responses):
    """Feed get_with_retry a sequence of Response objects / exceptions; count the calls."""
    calls = {"n": 0}

    def fake_get(url, **kwargs):
        i = calls["n"]
        calls["n"] += 1
        item = responses[min(i, len(responses) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(base.requests, "get", fake_get)
    monkeypatch.setattr(base.time, "sleep", lambda _s: None)  # no real backoff in tests
    return calls


def test_retries_then_succeeds(monkeypatch):
    calls = _seq(monkeypatch, [_Resp(503), _Resp(200, {"ok": True})])
    resp = get_with_retry("https://x", timeout=5)
    assert resp.status_code == 200 and calls["n"] == 2


def test_gives_up_after_cap_and_returns_last(monkeypatch):
    # All attempts 429 → returns the final response (caller's raise_for_status then raises).
    calls = _seq(monkeypatch, [_Resp(429)])
    resp = get_with_retry("https://x", timeout=5)
    assert resp.status_code == 429 and calls["n"] == _MAX_RETRIES + 1


def test_connection_error_retried_then_raised(monkeypatch):
    calls = _seq(monkeypatch, [requests.ConnectionError("down")])
    try:
        get_with_retry("https://x", timeout=5)
        assert False, "expected ConnectionError after exhausting retries"
    except requests.ConnectionError:
        pass
    assert calls["n"] == _MAX_RETRIES + 1


def test_timeout_not_retried(monkeypatch):
    # A Timeout already consumed budget — it must NOT be retried (raised on the first attempt).
    calls = _seq(monkeypatch, [requests.Timeout("slow")])
    try:
        get_with_retry("https://x", timeout=5)
        assert False, "expected Timeout to propagate without retry"
    except requests.Timeout:
        pass
    assert calls["n"] == 1


def test_connect_timeout_not_retried(monkeypatch):
    # ConnectTimeout subclasses BOTH Timeout and ConnectionError — it must be treated as a
    # Timeout (raised immediately, NO retry), or a run of connect-timeouts at HTTP_TIMEOUT=20s
    # would cost ~3x and overrun the 60s serverless budget. Regression for the exact hierarchy
    # overlap a bare `except ConnectionError` would wrongly retry.
    calls = _seq(monkeypatch, [requests.exceptions.ConnectTimeout("connect slow")])
    try:
        get_with_retry("https://x", timeout=5)
        assert False, "expected ConnectTimeout to propagate without retry"
    except requests.Timeout:
        pass
    assert calls["n"] == 1


def test_success_first_try_no_retry(monkeypatch):
    calls = _seq(monkeypatch, [_Resp(200, {"ok": True})])
    get_with_retry("https://x", timeout=5)
    assert calls["n"] == 1


def test_greenhouse_recovers_from_transient(monkeypatch):
    """A 503 then a good payload → the board's jobs are returned, not falsely 'unreachable'."""
    payload = {"jobs": [{"id": 1, "title": "Engineer", "location": {"name": "Remote"}}]}
    _seq(monkeypatch, [_Resp(503), _Resp(200, payload)])
    jobs = GreenhouseClient("acme").fetch_jobs()
    assert len(jobs) == 1 and jobs[0].title == "Engineer"


def test_lever_still_degrades_honestly_on_persistent_5xx(monkeypatch):
    """Persistent 5xx after the retry cap → honest empty + last_error set (unchanged contract)."""
    _seq(monkeypatch, [_Resp(500)])
    client = LeverClient("acme")
    jobs = client.fetch_jobs()
    assert jobs == [] and client.last_error is not None
