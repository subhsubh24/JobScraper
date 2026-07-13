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


def test_default_primary_is_a_floating_alias_not_a_pinned_version():
    """The DEFAULT primary model must be the floating alias, never a pinned gemini-X.Y-flash.

    A pinned default is a single point of failure: on 2026-07-09 the then-pinned default
    ``gemini-2.5-flash`` was 404'd by Google and 502'd the whole monetized AI surface
    (QUALITY_SCORECARD functional-reality D). ``gemini-flash-latest`` is a floating alias Google
    rolls forward, so the HOT path can't be version-decommissioned. This pins that invariant so a
    future edit can't silently re-introduce a pinned default.
    """
    import re

    default = llm._DEFAULT_CHAT_MODEL
    assert default == "gemini-flash-latest"
    assert not re.match(r"^gemini-\d", default), (
        f"default primary {default!r} is a PINNED version — use the floating alias so an upstream "
        "model decommission can't take out the hot path"
    )
    # chat_model() (used to seed LLMWorkflows.MODEL / CareerCoach.MODEL at import) resolves to it
    # when GEMINI_MODEL is unset.
    assert llm.chat_model() == "gemini-flash-latest"


def test_default_fallback_chain_is_two_deep_and_excludes_the_primary_alias():
    """Fallbacks stay a real, ≥2-deep chain of CONCRETE alternates (not the floating alias again).

    With the alias as primary, listing it again as a fallback would collapse the chain to one
    real model on an alias-death. The concrete alternates keep a genuine second line of defense.
    """
    fallbacks = llm._DEFAULT_FALLBACK_CHAT_MODELS
    assert len(fallbacks) >= 2
    assert "gemini-flash-latest" not in fallbacks
    # resilient_chat_completion de-dupes primary from the fallbacks; assert the real attempt order.
    client = _FakeClient(dead_models={"gemini-flash-latest", *fallbacks})
    with pytest.raises(RuntimeError, match="All configured LLM models are unavailable"):
        resilient_chat_completion(client, messages=[])  # no explicit model → uses the default
    assert client.attempts == ["gemini-flash-latest", *fallbacks]


def test_real_openai_notfounderror_is_classified():
    """Guard the isinstance branch against the ACTUAL openai SDK error type (not just status)."""
    import httpx
    from openai import NotFoundError

    resp = httpx.Response(404, request=httpx.Request("POST", "http://x"))
    err = NotFoundError("model no longer available", response=resp, body=None)
    assert llm._is_model_unavailable(err) is True
    assert llm._is_model_unavailable(_Status429("nope")) is False
