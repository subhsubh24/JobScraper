"""Security invariants on AuthService entitlement management.

Premium entitlement must be granted ONLY through a signature-verified provider webhook
(`src/billing.py` for Stripe, `src/mobile_billing.py` for RevenueCat). AuthService must NOT
expose an unguarded tier-flip helper — an earlier `upgrade_to_premium()` (with a "verify the
receipt later" TODO) set `user.tier = PREMIUM` with no payment proof, a client-trusted-unlock
booby-trap that any future caller could resurrect. This is the tripwire that keeps it out.
"""
from src.auth.auth_service import AuthService


def test_no_unguarded_premium_unlock():
    # No method on AuthService may flip a user to Premium without going through the
    # verified billing webhook. `upgrade_to_premium` was removed for exactly this reason;
    # re-introducing any such helper should fail this test loudly.
    assert not hasattr(AuthService, "upgrade_to_premium"), (
        "AuthService must not expose an unguarded tier-upgrade method — entitlement is "
        "granted only by a signature-verified provider webhook."
    )
