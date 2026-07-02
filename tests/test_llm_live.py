"""REAL Gemini path validation — runs ONLY when a real GEMINI_API_KEY is available in CI.

conftest.py forces GEMINI_API_KEY="" for the whole suite (deterministic graceful-degradation
testing), stashing the real value (if any) in GEMINI_API_KEY_LIVE first. This test reads that
stashed value and restores it for its own calls — so it exercises a REAL Gemini chat +
embedding round-trip when the owner has added the secret, and skips cleanly otherwise. This is
what upgrades the `ai` capability from degraded_only -> real (docs/ci/VALIDATION.md); a loop
change that breaks the real Gemini integration (prompt shape, client, response parsing) fails
here instead of silently passing in degraded mode.
"""
import os

import pytest

# conftest stashes the real key here before blanking GEMINI_API_KEY; fall back to a directly-set
# key (e.g. running this file without conftest's blanking).
LIVE_KEY = os.getenv("GEMINI_API_KEY_LIVE") or os.getenv("GEMINI_API_KEY") or ""

pytestmark = pytest.mark.live


def setup_module(module):
    # §28: skip in local/dev (no key expected) but FAIL LOUD in the nightly lane
    # (REQUIRE_LIVE_TESTS=1) if the real key is unexpectedly absent — never skip-green.
    from tests.live_guard import require_live_key

    require_live_key(LIVE_KEY, "GEMINI_API_KEY")


def test_real_gemini_chat_responds(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)  # restore the real key (conftest blanked it)
    import src.llm as llm

    assert llm.llm_available()
    client = llm.get_llm_client()
    assert client is not None, "client must construct when a key is present"
    # gemini-2.5-flash is a THINKING model: max_tokens caps thinking + answer, so a tight budget
    # leaves empty visible content. Use a realistic budget and validate that a real chat call
    # returns usable non-empty text (a broken client/endpoint/key raises instead). Robust for a
    # required gate — no dependence on exact model wording.
    resp = client.chat.completions.create(
        model=llm.chat_model(),
        messages=[{"role": "user", "content": "In one short sentence, say hello."}],
        max_tokens=512,
    )
    text = (resp.choices[0].message.content or "").strip()
    assert len(text) >= 3, f"real Gemini chat returned no usable content: {text!r}"


def test_real_gemini_embedding_has_dimensions(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)  # restore the real key (conftest blanked it)
    import src.llm as llm

    client = llm.get_llm_client()
    assert client is not None
    emb = client.embeddings.create(model=llm.embedding_model(), input="software engineer resume")
    vec = emb.data[0].embedding
    assert isinstance(vec, list) and len(vec) > 100, "embedding must return a real vector"
