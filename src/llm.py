"""Centralized, optional LLM client (Google Gemini via the OpenAI-compatible API).

We use the `openai` SDK pointed at Gemini's OpenAI-compatible endpoint, so the existing
`client.chat.completions.create(...)` and `client.embeddings.create(...)` call shapes
keep working with no rewrite — we just swap the base URL, the API key (GEMINI_API_KEY),
and the model names.

The product DEGRADES GRACEFULLY when no key is configured (VISION quality bar):
scoring falls back to heuristics, and LLM features return a truthful "needs
configuration" response instead of crashing. This module is the single place that
decides whether the LLM is available and which models to use.
"""
import os
from typing import Optional

# Gemini's OpenAI-compatibility base URL.
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Model names are env-overridable so they can be changed without a code deploy.
_DEFAULT_CHAT_MODEL = "gemini-2.5-flash"
_DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"


def llm_available() -> bool:
    """True only when a Gemini API key is configured."""
    return bool(os.getenv("GEMINI_API_KEY"))


def chat_model() -> str:
    return os.getenv("GEMINI_MODEL", _DEFAULT_CHAT_MODEL)


def embedding_model() -> str:
    return os.getenv("GEMINI_EMBEDDING_MODEL", _DEFAULT_EMBEDDING_MODEL)


def get_llm_client() -> Optional["object"]:
    """Return an OpenAI-SDK client pointed at Gemini, or None when unavailable.

    Never raises: returns None on a missing key OR if the client can't be constructed
    (e.g. a dependency skew like openai/httpx). Callers check the return value and
    degrade gracefully (heuristic scoring; truthful "AI unavailable" responses) instead
    of 500ing.
    """
    if not llm_available():
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url=GEMINI_BASE_URL)
    except Exception:  # noqa: BLE001 - construction failure must degrade, not crash
        import logging
        logging.getLogger("career_operator").exception("LLM client construction failed")
        return None


# Back-compat alias (older imports referenced get_openai_client).
get_openai_client = get_llm_client
