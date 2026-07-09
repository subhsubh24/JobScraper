"""Per-PR regression guard for LLM model-death resilience (no live key, no network).

WHY THIS EXISTS: on 2026-07-09 the Quality Auditor found the shipped default model was
reported decommissioned by Google, and `gemini-2.0-flash` genuinely returns a 404 "no longer
available". A single pinned-model death 502s the ENTIRE monetized AI surface (mock interview,
coach, prep pack, cover letter, tailored résumé, salary negotiation, learning plan). The live
real-output evals that would catch it are NIGHTLY-only, so such a regression sails past every
per-PR merge gate green. This CHEAP mocked unit test runs on every PR and pins the contract of
``src/llm.resilient_chat_completion`` so the fallback can't silently rot:

  1. a model-not-found (404) on the primary transparently falls back to a live model;
  2. NON-404 errors (auth/rate-limit/timeout/5xx) propagate immediately — never masked;
  3. when the WHOLE chain is dead the call FAILS LOUD (no fake success).
"""
import pytest

from src import llm
from src.llm import resilient_chat_completion


class _Status404(Exception):
    """Mimics the provider's HTTP-404 "model no longer available" error shape."""

    status_code = 404


class _Status429(Exception):
    """A rate-limit error — must NOT trigger fallback (real, transient, user-facing)."""

    status_code = 429


class _Resp:
    """A minimal chat-completion response so callers can read .choices[0].message.content."""

    def __init__(self, model):
        self.model = model
        self.choices = [type("C", (), {"message": type("M", (), {"content": f"ok:{model}"})()})()]


class _FakeClient:
    """Records every model attempted and fails a configured set of them with 404."""

    def __init__(self, dead_models=(), non_404_on=None):
        self.attempts = []
        self._dead = set(dead_models)
        self._non_404_on = non_404_on

        class _Completions:
            def create(_self, *, model, **kwargs):
                self.attempts.append(model)
                if self._non_404_on is not None and model == self._non_404_on:
                    raise _Status429("Too Many Requests")
                if model in self._dead:
                    raise _Status404(f"This model models/{model} is no longer available")
                return _Resp(model)

        self.chat = type("Chat", (), {"completions": _Completions()})()


def test_primary_alive_no_fallback():
    client = _FakeClient()
    resp = resilient_chat_completion(client, model="gemini-2.5-flash", messages=[])
    assert resp.model == "gemini-2.5-flash"
    assert client.attempts == ["gemini-2.5-flash"]  # no wasted fallback attempts


def test_dead_primary_falls_back_to_live_model(monkeypatch):
    monkeypatch.setattr(llm, "_DEFAULT_FALLBACK_CHAT_MODELS", ("gemini-flash-latest",))
    client = _FakeClient(dead_models={"gemini-2.5-flash"})
    resp = resilient_chat_completion(client, model="gemini-2.5-flash", messages=[])
    # transparently served by the fallback, not a 502
    assert resp.model == "gemini-flash-latest"
    assert client.attempts == ["gemini-2.5-flash", "gemini-flash-latest"]


def test_non_404_error_propagates_without_fallback():
    # A rate-limit on the primary must raise immediately — never churn the whole chain (which
    # would waste quota and hide the true cause).
    client = _FakeClient(non_404_on="gemini-2.5-flash")
    with pytest.raises(_Status429):
        resilient_chat_completion(client, model="gemini-2.5-flash", messages=[])
    assert client.attempts == ["gemini-2.5-flash"]  # stopped at the first, no fallback


def test_whole_chain_dead_fails_loud(monkeypatch):
    monkeypatch.setattr(
        llm, "_DEFAULT_FALLBACK_CHAT_MODELS", ("gemini-flash-latest", "gemini-2.5-flash-lite")
    )
    client = _FakeClient(
        dead_models={"gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"}
    )
    with pytest.raises(RuntimeError, match="All configured LLM models are unavailable"):
        resilient_chat_completion(client, model="gemini-2.5-flash", messages=[])
    # every candidate was genuinely attempted before failing loud
    assert client.attempts == [
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.5-flash-lite",
    ]


def test_env_override_of_fallback_chain(monkeypatch):
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "modelA, modelB")
    assert llm._fallback_chat_models() == ("modelA", "modelB")
    client = _FakeClient(dead_models={"gemini-2.5-flash", "modelA"})
    resp = resilient_chat_completion(client, model="gemini-2.5-flash", messages=[])
    assert resp.model == "modelB"


def test_none_client_fails_loud():
    with pytest.raises(RuntimeError, match="not configured"):
        resilient_chat_completion(None, model="gemini-2.5-flash", messages=[])


def test_real_openai_notfounderror_is_classified():
    """Guard the isinstance branch against the ACTUAL openai SDK error type (not just status)."""
    import httpx
    from openai import NotFoundError

    resp = httpx.Response(404, request=httpx.Request("POST", "http://x"))
    err = NotFoundError("model no longer available", response=resp, body=None)
    assert llm._is_model_unavailable(err) is True
    assert llm._is_model_unavailable(_Status429("nope")) is False
