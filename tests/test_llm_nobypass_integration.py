"""Per-PR guards that the LLM model-death resilience is actually WIRED, not just unit-tested.

WHY THIS EXISTS (a real, recurring incident — 2026-07-09): Google decommissioned the shipped
default chat model and every monetized AI feature 502'd. The fix (#330) added
``src/llm.resilient_chat_completion`` — a wrapper that transparently falls back to a live model
on a 404. ``tests/test_llm_fallback.py`` proves that wrapper works IN ISOLATION. But two failure
CLASSES that isolation test cannot catch would silently re-introduce the outage, and BOTH pass
every per-PR gate green today because the only live-model eval is nightly-only:

  1. A NEW AI call site that calls ``client.chat.completions.create(...)`` DIRECTLY, bypassing the
     wrapper — so a future model death 502s that one feature even though the wrapper still "exists."
  2. The wrapper being imported but not actually reached by the real WORKFLOW code the endpoints
     call (a refactor that routes around it).

This module closes both:
  * ``test_no_raw_chat_completion_call_bypasses_the_resilient_wrapper`` — a source-scan guard: the
    raw ``chat.completions.create`` call may live ONLY in src/llm.py (the wrapper itself).
  * ``test_workflow_*_degrades_when_primary_model_is_decommissioned`` — drives the REAL workflow
    entrypoint (``LLMWorkflows._call_llm``, the path prep packs / cover letters / study plans /
    negotiation scripts run through) with a fake provider whose PRIMARY model is dead, and asserts
    it transparently serves the fallback instead of raising — one layer below the endpoint.

All cheap, no live key, no network — safe on every PR.
"""
import pathlib

import pytest

from src import llm
from src.enrichment.llm_workflows import LLMWorkflows

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


class _Status404(Exception):
    """The provider's HTTP-404 "model no longer available" shape (a decommissioned model)."""

    status_code = 404


class _Msg:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})()


class _Usage:
    total_tokens = 7


class _Resp:
    """Minimal chat-completion response: ``.choices[0].message.content`` + ``.usage``."""

    def __init__(self, model, content):
        self.model = model
        self.choices = [_Msg(content)]
        self.usage = _Usage()


class _DeadPrimaryClient:
    """A fake OpenAI-shaped client: the PRIMARY model 404s (decommissioned), the fallback answers.

    Mirrors exactly the 2026-07-09 outage: the pinned default is dead upstream while the floating
    fallback alias is live. Records attempts so the test can prove the fallback was actually used.
    """

    def __init__(self, dead_models, reply):
        self.attempts = []
        self._dead = set(dead_models)
        self._reply = reply

        class _Completions:
            def create(_self, *, model, **kwargs):
                self.attempts.append(model)
                if model in self._dead:
                    raise _Status404(f"This model models/{model} is no longer available")
                return _Resp(model, self._reply)

        self.chat = type("Chat", (), {"completions": _Completions()})()


# ── Guard 1: no product code path may bypass the resilient wrapper ──────────────────────────────

def test_no_raw_chat_completion_call_bypasses_the_resilient_wrapper():
    """The raw ``chat.completions.create`` call may appear ONLY in src/llm.py (the wrapper).

    Every other AI call site MUST go through ``resilient_chat_completion`` so a single upstream
    model decommission can never 502 that feature. A new endpoint that calls the client directly
    is the exact regression that would silently re-open the 2026-07-09 outage — this fails LOUD on
    it at merge time, on every PR, without a live key.
    """
    offenders = []
    for path in sorted(_REPO_ROOT.glob("src/**/*.py")) + [_REPO_ROOT / "asgi.py"]:
        if path == _REPO_ROOT / "src" / "llm.py":
            continue  # the wrapper itself legitimately owns the raw call
        if "chat.completions.create" in path.read_text(encoding="utf-8"):
            offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert offenders == [], (
        "These files call chat.completions.create directly, bypassing the model-death fallback "
        f"in src.llm.resilient_chat_completion: {offenders}. Route the call through "
        "resilient_chat_completion so a decommissioned model can't 502 the feature."
    )


# ── Guard 2: the real workflow entrypoint degrades on a dead primary model ───────────────────────

def _workflow_with_client(fake_client):
    """An LLMWorkflows whose provider is the fake (db is unused by ``_call_llm``)."""
    wf = LLMWorkflows(db=None)
    wf.client = fake_client
    return wf


def test_workflow_structured_path_degrades_when_primary_model_is_decommissioned(monkeypatch):
    """The structured (JSON) generation path serves the fallback instead of raising on a dead primary."""
    monkeypatch.setattr(llm, "_DEFAULT_FALLBACK_CHAT_MODELS", ("gemini-flash-latest",))
    fake = _DeadPrimaryClient(dead_models={LLMWorkflows.MODEL}, reply='{"ok": true}')
    wf = _workflow_with_client(fake)

    content = wf._call_llm("system", "user", json_mode=True)

    assert content == '{"ok": true}'  # transparently served, not a 502
    assert fake.attempts == [LLMWorkflows.MODEL, "gemini-flash-latest"]  # primary tried, then fell back


def test_workflow_prose_path_degrades_when_primary_model_is_decommissioned(monkeypatch):
    """The moderated user-facing prose path (prep packs / cover letters) also falls back cleanly.

    Benign fallback content passes the conservative output moderator, so the only thing exercised
    is the model-death fallback — proving the resilient wrapper is reached on the prose path too.
    """
    monkeypatch.setattr(llm, "_DEFAULT_FALLBACK_CHAT_MODELS", ("gemini-flash-latest",))
    fake = _DeadPrimaryClient(
        dead_models={LLMWorkflows.MODEL},
        reply="Here are three concrete talking points for your interview.",
    )
    wf = _workflow_with_client(fake)

    content = wf._call_llm("system", "user", json_mode=False)

    assert content == "Here are three concrete talking points for your interview."
    assert fake.attempts == [LLMWorkflows.MODEL, "gemini-flash-latest"]


def test_workflow_fails_loud_when_every_model_is_dead(monkeypatch):
    """If the WHOLE chain is decommissioned the workflow raises — never a fake/blank success (§6)."""
    monkeypatch.setattr(llm, "_DEFAULT_FALLBACK_CHAT_MODELS", ("gemini-flash-latest",))
    fake = _DeadPrimaryClient(
        dead_models={LLMWorkflows.MODEL, "gemini-flash-latest"}, reply="unused"
    )
    wf = _workflow_with_client(fake)

    with pytest.raises(RuntimeError, match="All configured LLM models are unavailable"):
        wf._call_llm("system", "user", json_mode=True)
