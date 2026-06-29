"""Mobile in-app-subscription entitlement via RevenueCat webhooks (Track C).

The native apps purchase through StoreKit (iOS) and Play Billing (Android); RevenueCat is
the cross-store receipt validator. RevenueCat POSTs a signed webhook to us on every
subscription lifecycle event. This module is the SERVER-SIDE verification + entitlement
half — the only thing that may flip a user to Premium for a mobile purchase.

Design rules mirror the Stripe webhook (``src/billing.py``) — SIDE-EFFECT INTEGRITY:
- **No client-trusted unlocks.** The mobile app never tells us "I'm premium." Entitlement
  changes ONLY downstream of a RevenueCat webhook whose shared-secret ``Authorization``
  header we verify with a constant-time comparison. A forged / missing / wrong header
  grants NOTHING.
- **Honest when unconfigured.** Until the owner sets ``REVENUECAT_WEBHOOK_AUTH`` (Human-Core,
  PENDING_OPS) the endpoint refuses honestly (503) and grants nothing — never a fake unlock.
- **``users.tier`` is the single source of truth** for gating (same column the Stripe path
  flips), so web and mobile entitlement converge on one switch the API already reads.

We resolve the user from the event's ``app_user_id`` — the mobile app configures RevenueCat
with our ``User.id`` as the app user id, so every event (including renewals that omit
metadata) maps back to a user without any durable per-provider row.
"""
import os
import secrets
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import User, UserTier

# RevenueCat event types that should GRANT the Premium entitlement (an active subscription).
_GRANT_EVENTS = {
    "INITIAL_PURCHASE",
    "RENEWAL",
    "UNCANCELLATION",
    "PRODUCT_CHANGE",
    "NON_RENEWING_PURCHASE",
    "SUBSCRIPTION_EXTENDED",
}
# Event types that REVOKE entitlement (access has actually lapsed). Note CANCELLATION is NOT
# here: a cancellation only turns OFF auto-renew — the user keeps access until the period
# ends, at which point RevenueCat sends EXPIRATION. BILLING_ISSUE is a grace period, also not
# an immediate revoke. PAUSED (Android) DOES revoke: the user has surrendered access for the
# pause window, and a subsequent RENEWAL re-grants on resume. Everything not in either set is
# acknowledged with no entitlement change — including TRANSFER (entitlement moved between
# app_user_ids), an intentional no-op for now: handling it would need to revoke the SOURCE
# user (requires the transfer's source id), tracked as a follow-up. It can only UNDER-grant
# (the source keeps access), never wrongly grant Premium to an unverified caller.
_REVOKE_EVENTS = {"EXPIRATION", "PAUSED"}


class MobileBillingNotConfigured(Exception):
    """Raised when the RevenueCat webhook secret is not configured (owner-only)."""


class InvalidWebhookAuth(Exception):
    """Raised when the webhook's Authorization header fails verification — grant NOTHING."""


def mobile_billing_enabled() -> bool:
    """True only when the RevenueCat webhook shared secret is configured (server-side)."""
    return bool(os.getenv("REVENUECAT_WEBHOOK_AUTH"))


def verify_authorization(auth_header: Optional[str]) -> None:
    """Verify the RevenueCat webhook ``Authorization`` header against the shared secret.

    Raises ``MobileBillingNotConfigured`` if no secret is set (caller -> 503), or
    ``InvalidWebhookAuth`` on any mismatch / missing header (caller -> 401, grants nothing).
    Uses a constant-time compare so the secret can't be discovered by timing.
    """
    expected = os.getenv("REVENUECAT_WEBHOOK_AUTH")
    if not expected:
        raise MobileBillingNotConfigured("REVENUECAT_WEBHOOK_AUTH is not set.")
    if not auth_header or not secrets.compare_digest(auth_header, expected):
        raise InvalidWebhookAuth("RevenueCat webhook authorization failed.")


def _user_for_event(db: Session, event: dict) -> Optional[User]:
    """Resolve the User a webhook event refers to via its ``app_user_id``.

    The app configures RevenueCat's app user id = our ``User.id``. RevenueCat may also send
    ``aliases`` (e.g. an anonymous id before login); we try the primary id, then any alias.
    """
    candidates = []
    primary = event.get("app_user_id")
    if primary:
        candidates.append(primary)
    aliases = event.get("aliases") or []
    candidates.extend(a for a in aliases if a)
    for uid in candidates:
        user = db.query(User).filter(User.id == uid).first()
        if user:
            return user
    return None


def apply_event(payload: dict, db: Session) -> Optional[str]:
    """Apply a VERIFIED RevenueCat webhook payload to entitlement state.

    Returns the affected user id, or None when the event maps to no known user or is a type
    that changes nothing (it is still acknowledged with 200 so RevenueCat stops retrying).
    The caller is responsible for ``db.commit()``.
    """
    event = (payload or {}).get("event") or {}
    etype = event.get("type")
    if etype not in _GRANT_EVENTS and etype not in _REVOKE_EVENTS:
        # TEST events, CANCELLATION (auto-renew off, still entitled), BILLING_ISSUE (grace),
        # SUBSCRIBER_ALIAS, TRANSFER, etc. — acknowledge, change nothing.
        return None

    user = _user_for_event(db, event)
    if not user:
        return None

    user.tier = UserTier.PREMIUM if etype in _GRANT_EVENTS else UserTier.FREE
    return user.id
