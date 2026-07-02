"""Guard for real-service (``live``) test modules: SKIP in local/dev, FAIL LOUD in the nightly lane.

FACTORY_STANDARD §28 (real-service validation fails, not skips): a real-service lane that is
EXPECTED to run MUST redden when its key is missing — never skip to green. Today the ``live``
tests (real Gemini / Stripe test-mode round-trips) use a bare ``skipif(not KEY)``: if the key is
rotated away or never set in the nightly environment, the "real" lane passes having validated
NOTHING — a synthetic green.

These ``live`` tests are deselected per-PR (``pytest -m "not live"``) and run ONLY in the nightly
workflow with the real secrets. So the honest policy is:

- **local / dev / per-PR** — no key, and none is expected → SKIP (the current friendly behavior).
- **nightly lane** — the owner sets ``REQUIRE_LIVE_TESTS=1``; now a missing key is a hard FAILURE,
  so a rotated-away or never-set secret reddens instead of silently passing.

The workflow-env wiring (setting ``REQUIRE_LIVE_TESTS`` in ``.github/workflows/nightly.yml``) is the
owner's half — the loop never edits ``.github``. See PENDING_OPS ``require-live-tests``.
"""
from __future__ import annotations

import os

import pytest

_TRUTHY = {"1", "true", "yes", "on"}


def live_tests_required() -> bool:
    """True when the environment DECLARES it should actually run the real-service lane (nightly)."""
    return (os.getenv("REQUIRE_LIVE_TESTS") or "").strip().lower() in _TRUTHY


def require_live_key(present: object, name: str) -> None:
    """Gate a ``live`` test module — call from the module's ``setup_module``.

    - ``present`` truthy → return (the real key/config is here; the test runs for real).
    - ``present`` falsy + ``REQUIRE_LIVE_TESTS`` unset → ``pytest.skip`` (honest local/dev; the
      per-PR gate deselects these modules anyway).
    - ``present`` falsy + ``REQUIRE_LIVE_TESTS`` set → ``pytest.fail`` (§28: an expected-but-absent
      real-service key reddens the lane instead of skip-green).
    """
    if present:
        return
    if live_tests_required():
        pytest.fail(
            f"REQUIRE_LIVE_TESTS is set but {name} is absent — the real-service lane cannot "
            f"validate anything, so it must FAIL rather than skip to green. Provide the secret "
            f"in this environment, or remove this lane from the required live run "
            f"(FACTORY_STANDARD §28: expected-but-absent must redden, never skip-green)."
        )
    pytest.skip(
        f"No real {name} — live validation skipped (REQUIRE_LIVE_TESTS unset; local/dev/per-PR)."
    )
