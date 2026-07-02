"""REAL Stripe TEST-MODE validation — runs ONLY when a Stripe test key + a price are in CI.

The webhook signature round-trip (the security-critical path: only a signature-VERIFIED event
grants Premium) is already validated with real crypto in tests/test_billing.py. This closes the
one remaining mocked gap — the OUTBOUND checkout call — by creating a REAL Checkout Session
against Stripe's TEST API (no real money), validating our params/price wiring are accepted.
Upgrades the `billing` capability from mock -> real.

Runs only with a `sk_test_...` key (refuses a live key in CI) AND a configured price id; skips
otherwise. See OWNER_ACTION `stripe-account` for the one-time test-mode setup.
"""
import os

import pytest

from src import billing
from src.db.models import User, UserTier

STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY") or ""
# the first plan whose Stripe Price ID is configured in this environment
CONFIGURED_PLAN = next((plan for plan, env in billing._PLAN_PRICE_ENV.items() if os.getenv(env)), None)

pytestmark = pytest.mark.skipif(
    not (STRIPE_KEY.startswith("sk_test") and CONFIGURED_PLAN),
    reason="No Stripe TEST key (sk_test_) + configured price in CI — real billing validation "
    "skipped. See OWNER_ACTION stripe-account.",
)


def test_real_stripe_test_mode_checkout_session(db_session):
    user = User(email="stripe-live@example.com", password_hash="x", tier=UserTier.FREE)
    db_session.add(user)
    db_session.flush()

    url = billing.create_checkout_session(
        user,
        CONFIGURED_PLAN,
        success_url="https://example.com/billing/success",
        cancel_url="https://example.com/billing/cancel",
    )
    # A real hosted Stripe Checkout URL came back from the TEST API (params accepted, price valid).
    assert isinstance(url, str) and "stripe.com" in url, f"expected a real Stripe checkout URL, got: {url!r}"
