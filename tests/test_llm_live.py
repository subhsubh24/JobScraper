"""REAL Gemini path validation — runs ONLY when GEMINI_API_KEY is present.

This is the test that closes the `ai` validation gap (docs/ci/VALIDATION.md). Without a key
it is skipped (CI's default degraded mode); the moment a spend-capped GEMINI_API_KEY is added
to CI, this exercises the actual Gemini chat + embedding calls and asserts a sane response —
so a loop change that breaks the real AI integration (prompt shape, client construction,
response parsing) is caught instead of silently passing in degraded mode.
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set — real-AI validation skipped (degraded mode). "
    "See OWNER_ACTION validate-ai-ci.",
)


def test_real_gemini_chat_responds():
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


def test_real_gemini_embedding_has_dimensions():
    import src.llm as llm

    client = llm.get_llm_client()
    assert client is not None
    emb = client.embeddings.create(model=llm.embedding_model(), input="software engineer resume")
    vec = emb.data[0].embedding
    assert isinstance(vec, list) and len(vec) > 100, "embedding must return a real vector"
