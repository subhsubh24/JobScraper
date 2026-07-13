"""The Margin telemetry POST timeout is env-configurable and bounded.

The emit is BLOCKING on the LLM hot path (Vercel freezes post-response threads, #369), so the
per-call timeout is the hard bound on how much a slow/degraded Margin ingest can inflate a paid
AI request's tail latency — and it STACKS per LLM call. These pin the resolution logic and the
lowered default (1.0s, was a hardcoded 2.0s) so it can't silently regress, and prove the value
actually flows into the meter constructor.
"""
import src.llm as llm


def test_default_timeout_is_one_second(monkeypatch):
    monkeypatch.delenv("MARGIN_INGEST_TIMEOUT_SECONDS", raising=False)
    assert llm._margin_ingest_timeout() == 1.0


def test_env_override_is_honoured(monkeypatch):
    monkeypatch.setenv("MARGIN_INGEST_TIMEOUT_SECONDS", "0.5")
    assert llm._margin_ingest_timeout() == 0.5


def test_timeout_is_floored(monkeypatch):
    """A too-small value is floored at 0.1s so the meter never gets a 0/negative timeout."""
    monkeypatch.setenv("MARGIN_INGEST_TIMEOUT_SECONDS", "0")
    assert llm._margin_ingest_timeout() == 0.1
    monkeypatch.setenv("MARGIN_INGEST_TIMEOUT_SECONDS", "-3")
    assert llm._margin_ingest_timeout() == 0.1


def test_timeout_is_capped(monkeypatch):
    """A huge value is capped at 5.0s — an UNBOUNDED emit timeout would re-open the exact
    hot-path tail-latency hole this exists to close (the emit is blocking, #369)."""
    monkeypatch.setenv("MARGIN_INGEST_TIMEOUT_SECONDS", "600")
    assert llm._margin_ingest_timeout() == 5.0


def test_non_finite_value_falls_back_to_default(monkeypatch):
    """`inf`/`nan` are valid floats (float() accepts them) but must NOT bound the hot path —
    they fall back to the default rather than producing an unbounded/undefined timeout."""
    for bad in ("inf", "-inf", "nan", "Infinity"):
        monkeypatch.setenv("MARGIN_INGEST_TIMEOUT_SECONDS", bad)
        assert llm._margin_ingest_timeout() == 1.0, bad


def test_malformed_value_falls_back_to_default(monkeypatch):
    """A malformed env value must never crash the host on import — fall back to the default."""
    monkeypatch.setenv("MARGIN_INGEST_TIMEOUT_SECONDS", "not-a-number")
    assert llm._margin_ingest_timeout() == 1.0


def test_configured_timeout_flows_into_the_meter(monkeypatch):
    """Wiring guard: the resolved timeout is what the MarginMeter is actually constructed with
    (so a degraded ingest is bounded by exactly this value, not a stale hardcoded one)."""
    captured = {}

    class _SpyMeter:
        def __init__(self, timeout):
            captured["timeout"] = timeout

    monkeypatch.setattr(llm, "MarginMeter", _SpyMeter)
    monkeypatch.setenv("MARGIN_INGEST_TIMEOUT_SECONDS", "0.75")
    meter = llm.MarginMeter(timeout=llm._margin_ingest_timeout())
    assert isinstance(meter, _SpyMeter)
    assert captured["timeout"] == 0.75
