"""Unit tests for the §28 live-lane guard (tests/live_guard.py).

Proves the honest-skip vs fail-loud behavior directly, so a regression that silently turns the
nightly real-service lane back into a skip-green (or breaks the local skip) is caught. These are
NOT live tests — they exercise the guard's decision logic with no external service.
"""
import pytest

from tests import live_guard


def test_skips_when_flag_unset_and_key_absent(monkeypatch):
    monkeypatch.delenv("REQUIRE_LIVE_TESTS", raising=False)
    with pytest.raises(pytest.skip.Exception):
        live_guard.require_live_key("", "TEST_KEY")


def test_fails_loud_when_flag_set_and_key_absent(monkeypatch):
    monkeypatch.setenv("REQUIRE_LIVE_TESTS", "1")
    with pytest.raises(pytest.fail.Exception) as ei:
        live_guard.require_live_key("", "TEST_KEY")
    assert "REQUIRE_LIVE_TESTS is set" in str(ei.value)
    assert "TEST_KEY" in str(ei.value)


def test_passes_through_when_key_present_even_with_flag(monkeypatch):
    monkeypatch.setenv("REQUIRE_LIVE_TESTS", "1")
    # A truthy `present` must neither skip nor fail — the real lane runs.
    live_guard.require_live_key("a-real-key", "TEST_KEY")


def test_passes_through_when_key_present_and_flag_unset(monkeypatch):
    monkeypatch.delenv("REQUIRE_LIVE_TESTS", raising=False)
    live_guard.require_live_key("a-real-key", "TEST_KEY")


@pytest.mark.parametrize("val", ["1", "true", "YES", "on", " On "])
def test_live_tests_required_true_for_truthy(monkeypatch, val):
    monkeypatch.setenv("REQUIRE_LIVE_TESTS", val)
    assert live_guard.live_tests_required() is True


@pytest.mark.parametrize("val", ["", "0", "false", "off", "no"])
def test_live_tests_required_false_for_falsy(monkeypatch, val):
    monkeypatch.setenv("REQUIRE_LIVE_TESTS", val)
    assert live_guard.live_tests_required() is False


def test_live_tests_required_false_when_unset(monkeypatch):
    monkeypatch.delenv("REQUIRE_LIVE_TESTS", raising=False)
    assert live_guard.live_tests_required() is False
