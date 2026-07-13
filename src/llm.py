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
import time
from typing import Optional

# Margin meter — cost-per-outcome telemetry. GUARDED so a missing/broken SDK can never break
# the host app on import. The module singleton is fail-safe: record_* short-circuits (no
# network) unless MARGIN_INGEST_URL + MARGIN_INGEST_KEY are set in the env (both unset in CI).
try:
    from margin_meter import MarginMeter
except Exception:  # pragma: no cover - SDK optional; import must never break the host
    MarginMeter = None
_meter = MarginMeter(timeout=2.0) if MarginMeter else None  # pragma: no cover


def _emit_call_metrics(resp, model, elapsed, status):  # pragma: no cover - telemetry, must never affect the call
    """Emit one measured LLM call to Margin. Fail-safe: any error is swallowed.

    BLOCKING by design: on Vercel serverless the function is frozen the instant the handler
    returns, which would kill a fire-and-forget thread before its POST lands. The meter's own
    2.0s timeout bounds the worst case, negligible next to the multi-second LLM call.
    """
    if not _meter:
        return
    try:
        usage = getattr(resp, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        cache_read = int(getattr(getattr(usage, "prompt_tokens_details", None), "cached_tokens", 0) or 0)
        actual_model = getattr(resp, "model", model) if resp is not None else model
        _meter.record_call(
            workflow_id="jobscraper-fit-scoring",
            provider="google",
            model=actual_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read,
            latency_ms=int(elapsed * 1000),
            status=status,
        )
    except Exception:
        pass


# Gemini's OpenAI-compatibility base URL.
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Model names are env-overridable so they can be changed without a code deploy.
# The DEFAULT primary chat model is the FLOATING alias `gemini-flash-latest`, NOT a pinned
# `gemini-X.Y-flash`. A pinned model can be DECOMMISSIONED by Google at any time — on 2026-07-09
# the then-pinned default (`gemini-2.5-flash`) returned a hard 404 and 502'd the ENTIRE monetized
# AI surface (a ship-critical incident, QUALITY_SCORECARD functional-reality D). The floating alias
# rolls forward to the current GA flash model, so the HOT path can't be version-decommissioned out
# from under us — removing the last pinned single-point-of-failure (the fallback below already
# covers a re-decommission, but the primary call should not be the thing that dies first).
# Env-overridable via GEMINI_MODEL.
_DEFAULT_CHAT_MODEL = "gemini-flash-latest"
_DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"

# Curated, verified-live fallback chat models (probed against the REAL Gemini endpoint
# 2026-07-09/07-11: all returned 200), tried in order ONLY on a model-not-found (404). With the
# floating alias as the primary, these are two CONCRETE alternates so the chain still degrades if
# the alias itself ever resolves to a dead target. Env-overridable (comma-separated) via
# GEMINI_FALLBACK_MODELS so ops can adjust without a code deploy.
_DEFAULT_FALLBACK_CHAT_MODELS = ("gemini-2.5-flash", "gemini-2.5-flash-lite")

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
        _t0 = time.perf_counter()
        try:
            resp = client.chat.completions.create(model=model, **kwargs)
            _emit_call_metrics(resp, model, time.perf_counter() - _t0, "ok")  # pragma: no cover
            return resp
        except Exception as exc:  # noqa: BLE001 - classify then re-raise or fall back
            _emit_call_metrics(None, model, time.perf_counter() - _t0, "error")  # pragma: no cover
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
