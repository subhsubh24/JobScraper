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

pytestmark = pytest.mark.skipif(
    not LIVE_KEY,
    reason="No real GEMINI_API_KEY in CI — real-AI validation skipped (degraded mode). "
    "See OWNER_ACTION validation-capability-gemini.",
)


def test_real_gemini_chat_responds(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)  # restore the real key (conftest blanked it)
    import src.llm as llm

    assert llm.llm_available()
    client = llm.get_llm_client()
    assert client is not None, "client must construct when a key is present"
    resp = client.chat.completions.create(
        model=llm.chat_model(),
        messages=[{"role": "user", "content": "Reply with exactly the word: PONG"}],
        max_tokens=5,
    )
    text = (resp.choices[0].message.content or "").strip().upper()
    assert "PONG" in text, f"real Gemini chat returned unexpected content: {text!r}"


def test_real_gemini_embedding_has_dimensions(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)  # restore the real key (conftest blanked it)
    import src.llm as llm

    client = llm.get_llm_client()
    assert client is not None
    emb = client.embeddings.create(model=llm.embedding_model(), input="software engineer resume")
    vec = emb.data[0].embedding
    assert isinstance(vec, list) and len(vec) > 100, "embedding must return a real vector"
