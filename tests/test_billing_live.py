"""REAL Stripe TEST-MODE validation — runs ONLY when a Stripe test key is in CI.

The webhook signature round-trip (the security-critical path: only a signature-VERIFIED event
grants Premium) is already validated with real crypto in tests/test_billing.py. This closes the
one remaining mocked gap — the OUTBOUND checkout call — by creating a REAL Checkout Session
against Stripe's TEST API (no real money), validating our params/price wiring are accepted.
Upgrades the `billing` capability from mock -> real.

COVERAGE (issue #222): every plan in `billing._PLAN_PRICE_ENV` is a live, sellable tier —
checkout accepts `careerplus_*` and the salary-negotiation route gates on Career+ — so a plan
whose Stripe Price ID is UNSET raises `BillingNotConfigured` -> a 503 dead-end in prod that a
"first-configured-plan-only" test would never catch. So in the live lane we assert EVERY plan
is configured and produces a real session; a missing Career+ price now REDDENS the nightly
(§28: fail-not-skip) instead of hiding behind Pro being configured.

ORG/TEAM PARITY: the highest-ARPA tier — team SEAT checkout (`org_billing._ORG_PLAN_PRICE_ENV`,
`STRIPE_PRICE_TEAM_ANNUAL`) — is the SAME 503-dead-end class: an unset/rotated team price makes
`org_billing.create_seat_checkout_session` raise `BillingNotConfigured`, so a team signup 503s
in prod with NO live test reddening. Individual plans were validated live (above); org plans had
only MOCKED-Stripe coverage (tests/test_org_billing.py, tests/test_billing_robustness.py). So we
extend the SAME real-Stripe-test-mode assertion to every org plan — a missing team price now
reddens the nightly too, closing the parity gap for the tier that matters most to the floor.

Runs only with a `sk_test_...` key (refuses a live key in CI); skips otherwise. See
OWNER_ACTION `stripe-account` for the one-time test-mode setup.
"""
import os
from types import SimpleNamespace

import pytest

from src import billing, org_billing
from src.db.models import User, UserTier

STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY") or ""
# Every plan the product can sell — each MUST have its Stripe Price ID configured in the live
# lane, or its checkout 503s in prod (issue #222). We validate the whole set, not just one.
ALL_PLANS = list(billing._PLAN_PRICE_ENV.keys())
# The org/team seat plans — the same "unset price -> 503 dead-end" class for the top-ARPA tier.
ORG_ALL_PLANS = list(org_billing._ORG_PLAN_PRICE_ENV.keys())

pytestmark = pytest.mark.live


def setup_module(module):
    # §28: skip in local/dev (no test key expected) but FAIL LOUD in the nightly lane
    # (REQUIRE_LIVE_TESTS=1) if the Stripe test key is unexpectedly absent — never skip-green.
    from tests.live_guard import require_live_key

    require_live_key(
        STRIPE_KEY.startswith("sk_test"),
        "Stripe TEST key (sk_test_)",
    )


def test_stripe_test_key_is_not_a_live_key():
    # Guardrail: this suite must never run against a LIVE Stripe key in CI.
    assert STRIPE_KEY.startswith("sk_test"), "refusing to run live-billing checks with a non-test key"


@pytest.mark.parametrize("plan", ALL_PLANS)
def test_every_plan_price_is_configured(plan):
    """Every sellable plan MUST have its Stripe Price ID set in the live lane — an unset price
    is a prod 503 dead-end (issue #222). This assertion reddens the nightly if e.g. the
    Career+ prices are missing while Pro is set, which a first-configured-plan-only test hid."""
    env_var = billing._PLAN_PRICE_ENV[plan]
    assert os.getenv(env_var), (
        f"plan '{plan}' has no Stripe Price ID ({env_var} unset) — its checkout would 503 in "
        f"production. Set every {list(billing._PLAN_PRICE_ENV.values())} Price ID in the deploy env."
    )


@pytest.mark.parametrize("plan", ALL_PLANS)
def test_real_stripe_test_mode_checkout_session(plan, db_session):
    """A real hosted Stripe Checkout URL comes back from the TEST API for EVERY plan (params
    accepted, price valid) — proves the whole price wiring, not just the first plan."""
    if not os.getenv(billing._PLAN_PRICE_ENV[plan]):
        pytest.fail(
            f"plan '{plan}' price unset ({billing._PLAN_PRICE_ENV[plan]}) — cannot validate its "
            "checkout; a live sellable tier with no configured price is a prod dead-end (#222)."
        )
    user = User(email=f"stripe-live-{plan}@example.com", password_hash="x", tier=UserTier.FREE)
    db_session.add(user)
    db_session.flush()

    url = billing.create_checkout_session(
        user,
        plan,
        success_url="https://example.com/billing/success",
        cancel_url="https://example.com/billing/cancel",
    )
    assert isinstance(url, str) and "stripe.com" in url, f"expected a real Stripe checkout URL, got: {url!r}"


@pytest.mark.parametrize("plan", ORG_ALL_PLANS)
def test_every_org_plan_price_is_configured(plan):
    """Every sellable ORG/team seat plan MUST have its Stripe Price ID set in the live lane —
    an unset price is a prod 503 dead-end on the highest-ARPA tier (issue #222, org parity).
    This reddens the nightly if e.g. STRIPE_PRICE_TEAM_ANNUAL is missing, which the mocked
    org-billing tests (they monkeypatch the price env) can never catch."""
    env_var = org_billing._ORG_PLAN_PRICE_ENV[plan]
    assert os.getenv(env_var), (
        f"org plan '{plan}' has no Stripe Price ID ({env_var} unset) — a team seat checkout "
        f"would 503 in production. Set every {list(org_billing._ORG_PLAN_PRICE_ENV.values())} "
        "Price ID in the deploy env."
    )


@pytest.mark.parametrize("plan", ORG_ALL_PLANS)
def test_real_stripe_test_mode_seat_checkout_session(plan, db_session):
    """A real hosted Stripe Checkout URL comes back from the TEST API for EVERY org plan
    (quantity-based seat line item, price valid) — proves the team price wiring end-to-end, the
    same way the individual-plan test does. Only owner.id/email and org.id are read, so a real
    owner row + a lightweight org id exercise the real outbound call without a full org fixture."""
    if not os.getenv(org_billing._ORG_PLAN_PRICE_ENV[plan]):
        pytest.fail(
            f"org plan '{plan}' price unset ({org_billing._ORG_PLAN_PRICE_ENV[plan]}) — cannot "
            "validate its seat checkout; a live sellable tier with no configured price is a prod "
            "dead-end (#222)."
        )
    owner = User(email=f"stripe-live-org-{plan}@example.com", password_hash="x", tier=UserTier.FREE)
    db_session.add(owner)
    db_session.flush()
    org = SimpleNamespace(id=f"org-live-{plan}")

    url = org_billing.create_seat_checkout_session(
        owner,
        org,
        plan,
        5,
        success_url="https://example.com/billing/success",
        cancel_url="https://example.com/billing/cancel",
    )
    assert isinstance(url, str) and "stripe.com" in url, f"expected a real Stripe seat-checkout URL, got: {url!r}"
