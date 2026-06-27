"""Centralized, optional OpenAI client.

The product must DEGRADE GRACEFULLY when no API key is configured (VISION quality
bar): scoring falls back to heuristics, and LLM features return a truthful
"needs configuration" response instead of crashing. This module is the single place
that decides whether the LLM is available.
"""
import os
from typing import Optional


def llm_available() -> bool:
    """True only when an OpenAI API key is configured."""
    return bool(os.getenv("OPENAI_API_KEY"))


def get_openai_client() -> Optional["object"]:
    """Return an OpenAI client, or None when no key is configured.

    Never raises on a missing key — callers check the return value.
    """
    if not llm_available():
        return None
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
