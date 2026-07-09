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

# Curated, verified-live fallback chat models (probed against the REAL Gemini endpoint
# 2026-07-09: all returned 200). A PINNED model can be DECOMMISSIONED by Google at any time
# — e.g. `gemini-2.0-flash` now returns 404 "no longer available" — and without a fallback a
# single upstream model death 502s the ENTIRE monetized AI surface (mock interview, coach,
# prep pack, cover letter, tailored résumé, salary negotiation, learning plan). The primary
# fallback is `gemini-flash-latest`: a FLOATING alias Google rolls forward to the current GA
# flash model, so it cannot be version-decommissioned the way a pinned `gemini-X.Y-flash` can.
# Env-overridable (comma-separated) so ops can adjust without a code deploy.
_DEFAULT_FALLBACK_CHAT_MODELS = ("gemini-flash-latest", "gemini-2.5-flash-lite")

# DEEP_DIAGNOSIS rule (a): every external/LLM call MUST time out SHORTER than the
# serverless function budget (vercel.json maxDuration=60s) — a graceful try/except is
# useless if Vercel kills the function first. Keep this < maxDuration with headroom.
_LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))


def llm_available() -> bool:
    """True only when a Gemini API key is configured."""
    return bool(os.getenv("GEMINI_API_KEY"))


def chat_model() -> str:
    return os.getenv("GEMINI_MODEL", _DEFAULT_CHAT_MODEL)


def _fallback_chat_models() -> tuple:
    """Ordered fallback models, env-overridable via GEMINI_FALLBACK_MODELS (comma-separated)."""
    raw = os.getenv("GEMINI_FALLBACK_MODELS")
    if raw:
        return tuple(m.strip() for m in raw.split(",") if m.strip())
    return _DEFAULT_FALLBACK_CHAT_MODELS


def _is_model_unavailable(exc: Exception) -> bool:
    """True ONLY for a model-not-found / decommissioned error (an HTTP 404 from the provider).

    We fall back for THIS class alone. Every other failure — auth (401/403), rate limit (429),
    timeout, and 5xx server errors — must PROPAGATE so a real outage is surfaced honestly and is
    never masked by silently churning through the whole model list (which would also waste the
    caller's quota and hide the true cause). A decommissioned Gemini model returns 404 with a body
    like "This model models/gemini-2.0-flash is no longer available".
    """
    try:
        from openai import NotFoundError

        if isinstance(exc, NotFoundError):
            return True
    except Exception:  # noqa: BLE001 - openai import/skew must not break the check
        pass
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    return status == 404


def resilient_chat_completion(client: "object", **kwargs):
    """``client.chat.completions.create(**kwargs)`` with automatic fallback on model death.

    Tries the configured model first, and ONLY on a model-not-found (404) error retries through
    the curated, verified-live fallback chain (``_fallback_chat_models``). This is the single
    defense that stops one upstream model decommission (a real, recurring event — Google has
    already killed ``gemini-2.0-flash``) from 502-ing the entire monetized AI surface. All other
    errors propagate immediately (see ``_is_model_unavailable``). If EVERY model in the chain is
    dead the call FAILS LOUD (raises) — never a fake success — so the endpoint returns an honest
    error rather than a blank artifact.
    """
    if client is None:
        raise RuntimeError("LLM client is not configured")
    primary = kwargs.pop("model", None) or chat_model()
    candidates = [primary] + [m for m in _fallback_chat_models() if m != primary]
    tried = []
    last_exc: Optional[Exception] = None
    for model in candidates:
        try:
            return client.chat.completions.create(model=model, **kwargs)
        except Exception as exc:  # noqa: BLE001 - classify then re-raise or fall back
            if not _is_model_unavailable(exc):
                raise
            tried.append(model)
            last_exc = exc
            import logging

            logging.getLogger("career_operator").warning(
                "LLM model %r unavailable (404); trying next fallback", model
            )
    raise RuntimeError(
        "All configured LLM models are unavailable "
        f"(tried {tried}). The provider may have decommissioned them; "
        "set GEMINI_MODEL / GEMINI_FALLBACK_MODELS to a current model."
    ) from last_exc


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
        return OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url=GEMINI_BASE_URL,
            timeout=_LLM_TIMEOUT_SECONDS,  # rule (a): sub-budget timeout
            max_retries=1,                 # bounded: retries must not blow the budget
        )
    except Exception:  # noqa: BLE001 - construction failure must degrade, not crash
        import logging
        logging.getLogger("career_operator").exception("LLM client construction failed")
        return None


# Back-compat alias (older imports referenced get_openai_client).
get_openai_client = get_llm_client
