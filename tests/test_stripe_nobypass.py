"""Per-PR guard: every Stripe Checkout call goes through the sub-budget-bounded client.

WHY THIS EXISTS (a real, recently-fixed incident class — run 43 / PR #361): stripe-python's
default HTTP timeout is 80s, LONGER than Vercel's 60s ``maxDuration``, so a slow/hung Stripe call
is killed by the PLATFORM mid-request — possibly after a charge — with no response the endpoint
can surface. ``billing.configure_stripe()`` fixes this by installing a 25s
``new_default_http_client`` before the call; both existing checkout paths route through it.

But that fix only protects the TWO call sites that exist today. A NEW raw
``stripe.checkout.Session.create(...)`` added in some future file — without first calling
``configure_stripe()`` — silently inherits the 80s default and re-opens the exact
mid-request-kill-with-charge-ambiguity incident. That regression passes every other per-PR gate
green (the timeout only bites against a real slow Stripe response). This module fails LOUD on it
at merge time, on every PR, with no network — the same discipline the LLM model-death no-bypass
guard (``tests/test_llm_nobypass_integration.py``) applies to ``chat.completions.create``.
"""
import pathlib
import re

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

# The ONLY modules allowed to make a raw Stripe Checkout call — each calls
# ``billing.configure_stripe()`` (which bounds the HTTP client below the serverless budget)
# immediately before it. Add a module here ONLY together with that configure_stripe() call.
_CONFIGURED_MODULES = {"src/billing.py", "src/org_billing.py"}

# Matches a real CALL (open paren) — not a prose/docstring mention like asgi.py's
# "...makes a REAL stripe.checkout.Session.create call..." (no paren).
_CHECKOUT_CALL = re.compile(r"stripe\.checkout\.Session\.create\s*\(")

# Matches a CALL to configure_stripe (``configure_stripe(...)`` or ``billing.configure_stripe(...)``).
# The ``def configure_stripe():`` definition line is excluded separately at the call site — see
# the proximity check below — so this can't be satisfied by the definition in src/billing.py.
_CONFIGURE_CALL = re.compile(r"(?:billing\.)?configure_stripe\s*\(")

# How many lines of preceding context the bounding call must appear within. The two real sites
# call it 2-3 lines above the checkout call; 20 is a comfortable margin that still cannot reach
# billing.py's far-away ``def configure_stripe():`` (~170 lines above its call site).
_BOUND_WINDOW = 20


def _py_sources():
    return sorted(_REPO_ROOT.glob("src/**/*.py")) + [_REPO_ROOT / "asgi.py"]


def test_no_stripe_checkout_call_bypasses_the_bounded_client():
    """A raw ``stripe.checkout.Session.create(...)`` may live ONLY in the configured modules.

    Any other file making the call would run on the unbounded 80s default client — the exact
    regression PR #361 fixed. Fails LOUD so a future bypass can't ship silently.
    """
    offenders = []
    for path in _py_sources():
        rel = str(path.relative_to(_REPO_ROOT))
        if rel in _CONFIGURED_MODULES:
            continue
        if _CHECKOUT_CALL.search(path.read_text(encoding="utf-8")):
            offenders.append(rel)
    assert offenders == [], (
        "These files call stripe.checkout.Session.create() directly, bypassing the sub-budget "
        f"bounded client from billing.configure_stripe(): {offenders}. Move the call into "
        "src/billing.py or src/org_billing.py (which call configure_stripe() first), or call "
        "configure_stripe() before the checkout call so a slow Stripe API can't be killed by the "
        "platform mid-request."
    )


def test_each_checkout_call_site_is_bounded_by_configure_stripe():
    """Every raw checkout call in a configured module must be preceded — within a small window —
    by a ``configure_stripe()`` CALL that bounds the HTTP client.

    A whole-file substring check is NOT enough: ``src/billing.py`` both DEFINES and calls
    ``configure_stripe()``, so ``"configure_stripe(" in text`` is trivially true there even if the
    checkout call site drops the bounding call — the exact PR #361 regression this guards. So we
    validate the call SITE by proximity (and exclude the ``def`` line). Reddens if a checkout call
    is added without the bounding call, or the bounding call is dropped from an existing site.
    Also asserts the allow-list is not stale (each configured module still makes the call).
    """
    for rel in sorted(_CONFIGURED_MODULES):
        lines = (_REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
        call_line_nums = [i for i, ln in enumerate(lines) if _CHECKOUT_CALL.search(ln)]
        assert call_line_nums, (
            f"{rel} is on the Stripe-checkout allow-list but no longer makes the call — remove it "
            "from _CONFIGURED_MODULES to keep the guard meaningful."
        )
        for i in call_line_nums:
            window = lines[max(0, i - _BOUND_WINDOW):i]
            bounded = any(
                _CONFIGURE_CALL.search(ln) and not ln.lstrip().startswith("def ")
                for ln in window
            )
            assert bounded, (
                f"{rel}:{i + 1} makes a Stripe checkout call not preceded within {_BOUND_WINDOW} "
                "lines by a configure_stripe() call — the HTTP client may run on stripe-python's "
                "unbounded 80s default and be killed by the platform mid-request (PR #361)."
            )
