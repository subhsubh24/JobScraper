"""Redirect-aware SSRF guard (``get_with_redirect_guard``).

Closes a real hole: the careers-page probe validated only the INITIAL user-supplied URL and
then followed redirects with ``allow_redirects=True``, so a public URL that 3xx-redirects to an
internal host (cloud metadata 169.254.169.254, localhost, RFC1918) would be fetched anyway —
the classic redirect-bypass SSRF. The guard now re-validates every hop before connecting.

These tests use NUMERIC IPs so ``assert_public_http_url`` classifies each hop arithmetically
with zero network/DNS — public vs. link-local/loopback is deterministic and offline.
"""
import pytest
import requests
from requests.structures import CaseInsensitiveDict

from src.ingestion import url_guard
from src.ingestion.url_guard import UnsafeURLError, get_with_redirect_guard

_PUBLIC = "93.184.216.34"  # a normal public unicast IP (arithmetic classification, no DNS)


class _Resp:
    def __init__(self, status_code, location=None, url="", text="ok"):
        self.status_code = status_code
        self.url = url
        self.text = text
        self.headers = CaseInsensitiveDict()
        if location is not None:
            self.headers["Location"] = location  # real servers send capitalised "Location"

    def raise_for_status(self):
        pass


def _fake_get_sequence(*responses):
    """A requests.get stand-in that records every URL it is asked to fetch, in order."""
    seq = iter(responses)
    calls = []

    def _get(url, **kwargs):
        calls.append(url)
        assert kwargs.get("allow_redirects") is False, "must disable auto-redirects"
        return next(seq)

    return _get, calls


def test_redirect_to_link_local_metadata_is_refused_and_never_fetched(monkeypatch):
    # First (public) hop 302-redirects to the cloud-metadata link-local address.
    fake_get, calls = _fake_get_sequence(
        _Resp(302, location="http://169.254.169.254/latest/meta-data/"),
    )
    monkeypatch.setattr(url_guard.requests, "get", fake_get)

    with pytest.raises(UnsafeURLError):
        get_with_redirect_guard(f"http://{_PUBLIC}/careers", timeout=5)

    # The whole point: the internal target was rejected BEFORE any request went to it.
    assert calls == [f"http://{_PUBLIC}/careers"]


def test_redirect_to_localhost_is_refused(monkeypatch):
    fake_get, calls = _fake_get_sequence(_Resp(301, location="http://127.0.0.1:5432/"))
    monkeypatch.setattr(url_guard.requests, "get", fake_get)
    with pytest.raises(UnsafeURLError):
        get_with_redirect_guard(f"http://{_PUBLIC}/", timeout=5)
    assert "127.0.0.1" not in "".join(calls)


def test_public_redirect_is_followed_to_the_final_response(monkeypatch):
    fake_get, calls = _fake_get_sequence(
        _Resp(302, location=f"http://{_PUBLIC}/final"),
        _Resp(200, url=f"http://{_PUBLIC}/final", text="landing"),
    )
    monkeypatch.setattr(url_guard.requests, "get", fake_get)
    resp = get_with_redirect_guard(f"http://{_PUBLIC}/start", timeout=5)
    assert resp.status_code == 200 and resp.text == "landing"
    assert calls == [f"http://{_PUBLIC}/start", f"http://{_PUBLIC}/final"]


def test_relative_redirect_is_resolved_against_current_url(monkeypatch):
    fake_get, calls = _fake_get_sequence(
        _Resp(302, location="/jobs"),  # relative Location
        _Resp(200, text="jobs page"),
    )
    monkeypatch.setattr(url_guard.requests, "get", fake_get)
    get_with_redirect_guard(f"http://{_PUBLIC}/careers", timeout=5)
    assert calls[1] == f"http://{_PUBLIC}/jobs"


def test_redirect_loop_is_capped(monkeypatch):
    def _always_redirect(url, **kwargs):
        return _Resp(302, location=f"http://{_PUBLIC}/next")

    monkeypatch.setattr(url_guard.requests, "get", _always_redirect)
    with pytest.raises(UnsafeURLError, match="Too many redirects"):
        get_with_redirect_guard(f"http://{_PUBLIC}/", timeout=5, max_redirects=3)


def test_no_redirect_returns_response_directly(monkeypatch):
    fake_get, calls = _fake_get_sequence(_Resp(200, text="direct"))
    monkeypatch.setattr(url_guard.requests, "get", fake_get)
    resp = get_with_redirect_guard(f"http://{_PUBLIC}/careers", timeout=5)
    assert resp.text == "direct"
    assert len(calls) == 1


def test_request_exception_propagates(monkeypatch):
    def _boom(url, **kwargs):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(url_guard.requests, "get", _boom)
    # A normal transport error propagates as RequestException (callers already handle it).
    with pytest.raises(requests.RequestException):
        get_with_redirect_guard(f"http://{_PUBLIC}/careers", timeout=5)
