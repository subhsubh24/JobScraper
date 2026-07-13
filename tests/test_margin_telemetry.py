"""Fail-safe + inert guards for the Margin cost-telemetry emits (PRs #368/#369).

The margin-meter emits in ``src/llm.py`` (``_emit_call_metrics``) and ``src/ranking/scorer.py``
(``_record_fit_outcome``) are pure OUTBOUND observability that MUST NEVER affect the host app —
they were shipped ``# pragma: no cover`` with no test pinning the contract they promise. These
tests pin it: the emit is INERT without a configured meter, is FAIL-SAFE if the meter raises
(the error is swallowed and never propagates into a scoring/LLM call), and passes the right
measured args when a meter is present. This is the "telemetry can never break the product" rule
made enforceable (declared as capability `margin` in docs/ci/VALIDATION.md).
"""
from unittest import mock

import src.llm as llm
import src.ranking.scorer as scorer


class _FakeUsage:
    prompt_tokens = 120
    completion_tokens = 45
    prompt_tokens_details = mock.Mock(cached_tokens=30)


class _FakeResp:
    usage = _FakeUsage()
    model = "gemini-2.5-flash"


# ── _emit_call_metrics (src/llm.py) ──────────────────────────────────────────

def test_emit_call_metrics_inert_without_meter():
    """No meter configured (no MARGIN_* keys) → a pure no-op, never touches None."""
    with mock.patch.object(llm, "_meter", None):
        llm._emit_call_metrics(_FakeResp(), "gemini-2.5-flash", 1.23, "ok")


def test_emit_call_metrics_passes_measured_args():
    fake = mock.Mock()
    with mock.patch.object(llm, "_meter", fake):
        llm._emit_call_metrics(_FakeResp(), "req-model", 2.0, "ok")
    fake.record_call.assert_called_once()
    kwargs = fake.record_call.call_args.kwargs
    assert kwargs["input_tokens"] == 120
    assert kwargs["output_tokens"] == 45
    assert kwargs["cache_read_tokens"] == 30
    assert kwargs["latency_ms"] == 2000
    assert kwargs["status"] == "ok"
    # The ACTUAL served model (from the response) is preferred over the requested candidate.
    assert kwargs["model"] == "gemini-2.5-flash"


def test_emit_call_metrics_error_path_with_no_response():
    fake = mock.Mock()
    with mock.patch.object(llm, "_meter", fake):
        llm._emit_call_metrics(None, "req-model", 0.5, "error")
    kwargs = fake.record_call.call_args.kwargs
    assert kwargs["status"] == "error"
    assert kwargs["model"] == "req-model"  # no response → falls back to the requested model
    assert kwargs["input_tokens"] == 0 and kwargs["output_tokens"] == 0


def test_emit_call_metrics_swallows_meter_error():
    boom = mock.Mock()
    boom.record_call.side_effect = RuntimeError("margin ingest down")
    with mock.patch.object(llm, "_meter", boom):
        # MUST NOT raise — a telemetry failure can never break the LLM call.
        llm._emit_call_metrics(_FakeResp(), "m", 1.0, "ok")


def test_emit_call_metrics_swallows_malformed_response():
    fake = mock.Mock()
    with mock.patch.object(llm, "_meter", fake):
        # An object with no `.usage`/`.model` must not raise (getattr defaults + try/except).
        llm._emit_call_metrics(object(), "m", 1.0, "ok")


# ── _record_fit_outcome (src/ranking/scorer.py) ──────────────────────────────

def test_record_fit_outcome_inert_without_meter():
    with mock.patch.object(scorer, "_meter", None):
        scorer._record_fit_outcome(82.0)


def test_record_fit_outcome_passes_outcome():
    fake = mock.Mock()
    with mock.patch.object(scorer, "_meter", fake):
        scorer._record_fit_outcome(82.0)
    kwargs = fake.record_outcome.call_args.kwargs
    assert kwargs["passed"] is True
    assert kwargs["quality_score"] == 0.82  # score/100, rounded
    # Honest Margin provenance: a deterministic proxy score (not ground_truth/llm_judge).
    assert kwargs["quality_method"] == "judge_proxy"


def test_record_fit_outcome_swallows_meter_error():
    boom = mock.Mock()
    boom.record_outcome.side_effect = RuntimeError("margin ingest down")
    with mock.patch.object(scorer, "_meter", boom):
        scorer._record_fit_outcome(50.0)  # MUST NOT raise


# ── end-to-end contract ──────────────────────────────────────────────────────

def test_resilient_chat_completion_survives_telemetry_failure():
    """A raising meter must never turn a successful LLM call into an error (the core contract)."""
    boom = mock.Mock()
    boom.record_call.side_effect = RuntimeError("margin ingest down")
    client = mock.Mock()
    client.chat.completions.create.return_value = _FakeResp()
    with mock.patch.object(llm, "_meter", boom):
        resp = llm.resilient_chat_completion(
            client, messages=[{"role": "user", "content": "hi"}]
        )
    assert resp is not None  # the real response is returned despite telemetry blowing up
    client.chat.completions.create.assert_called_once()
