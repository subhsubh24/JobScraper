"""Stripe subscription billing for the web product (Track C).

Design rules (FACTORY_STANDARD §6 — SIDE-EFFECT INTEGRITY):
- NO fake success. The checkout endpoint makes a REAL ``stripe.checkout.Session.create``
  call; when Stripe is not configured (no live keys) it refuses HONESTLY rather than
  pretending a charge happened. Live keys + price IDs are owner-only (PENDING_OPS).
- Entitlement is granted ONLY downstream of a Stripe-signed webhook event whose signature
  we verify with ``stripe.Webhook.construct_event``. The user's ``tier`` is the single
  source of truth for gating; the ``subscriptions`` table is the durable Stripe bookkeeping.

Persistence is a NEW ``subscriptions`` table + an UPDATE of the existing ``users.tier``
column — never an added column on ``users`` (AUTO_CREATE_TABLES only creates missing
*tables*, so a new User column would silently not exist on the live DB).
"""
import os
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import Subscription, User, UserTier

# Stripe subscription statuses that should grant the Premium entitlement.
_ACTIVE_STATUSES = {"active", "trialing"}

# Bound EVERY Stripe HTTP call BELOW the serverless function budget (Vercel maxDuration=60s,
# vercel.json). stripe-python's default HTTP timeout is 80s — LONGER than the budget — so a
# slow/hung Stripe API would let the platform kill the function mid-request (possibly after a
# charge) with NO response the caller can act on. A sub-budget timeout makes the call fail LOUD
# in-request instead, so the endpoint returns an honest error. (DEEP_DIAGNOSIS rule (a): every
# external call needs a timeout shorter than the serverless budget — the same rule src/llm.py
# already honors for the Gemini calls.)
STRIPE_HTTP_TIMEOUT_SECONDS = 25


def configure_stripe():
    """Set the Stripe api key AND a sub-budget HTTP timeout; return the ``stripe`` module.

    Centralizes both so every network-making call (individual + org seat checkout) is bounded
    identically. ``new_default_http_client`` selects the best available backend (requests/…),
    all of which honor ``timeout``; reassigning the default client is idempotent and cheap on a
    cold serverless invocation. Webhook signature verification (``construct_event``) is pure
    crypto with no HTTP, so it is unaffected.
    """
    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    stripe.default_http_client = stripe.new_default_http_client(
        timeout=STRIPE_HTTP_TIMEOUT_SECONDS
    )
    return stripe


# Public plan id -> the env var holding that plan's Stripe Price ID. The owner creates the
# products/prices in Stripe and sets these in the deploy env; they are never committed.
_PLAN_PRICE_ENV = {
    "pro_monthly": "STRIPE_PRICE_PRO_MONTHLY",
    "pro_annual": "STRIPE_PRICE_PRO_ANNUAL",
    "careerplus_monthly": "STRIPE_PRICE_CAREERPLUS_MONTHLY",
    "careerplus_annual": "STRIPE_PRICE_CAREERPLUS_ANNUAL",
}


# Entitlement LEVELS within the paid tier. ``UserTier`` stays binary (FREE/PREMIUM) at the
# DB layer — no risky native-enum ``ALTER TYPE`` migration — and the *level* (Pro vs Career+)
# is DERIVED from the webhook-authoritative ``Subscription.plan`` id. So Career+ is a REAL,
# verified entitlement: only a signature-verified Stripe event ever writes ``plan``, never a
# client-supplied flag. A missing/garbled plan degrades to ``pro`` (the base paid level), so a
# corrupt row can never accidentally unlock the higher tier.
_CAREERPLUS_PREFIX = "careerplus"


def plan_level_for_plan(plan: Optional[str]) -> str:
    """Map a stored ``Subscription.plan`` id to an entitlement level: ``pro`` | ``career_plus``.

    Fail-safe: an unknown/None paid plan returns ``pro`` (never ``career_plus``).
    """
    if plan and plan.startswith(_CAREERPLUS_PREFIX):
        return "career_plus"
    return "pro"


def current_plan_level(user: User, subscription: Optional[Subscription]) -> str:
    """A user's effective entitlement level: ``free`` | ``pro`` | ``career_plus``.

    ``users.tier`` is the source of truth for paid-vs-free; the verified ``Subscription.plan``
    distinguishes Career+ from Pro among PREMIUM users. Career+ is derived ONLY from a subscription
    that is CURRENTLY ACTIVE — never merely non-None. This matters now that ``users.tier`` can be
    PREMIUM from a source OTHER than the user's own individual subscription (a team/org Pro seat,
    ``recompute_user_tier``): a former individual Career+ subscriber keeps a CANCELED
    ``Subscription`` row with a stale ``plan="careerplus_*"`` forever, and if they later occupy an
    org Pro seat their ``tier`` flips back to PREMIUM — deriving Career+ from that stale plan would
    silently unlock the higher tier for free. Gating on the active status closes that bypass; a team
    seat grants the base Pro level only. Pure function — pass the ``Subscription`` row (or ``None``).
    """
    if user.tier != UserTier.PREMIUM:
        return "free"
    if subscription is None or subscription.status not in _ACTIVE_STATUSES:
        return "pro"
    return plan_level_for_plan(subscription.plan)


def _has_active_individual_sub(db: Session, user: User) -> bool:
    """True iff the user has their OWN active/trialing individual Stripe subscription."""
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    return bool(sub and sub.status in _ACTIVE_STATUSES)


def _has_active_org_seat(db: Session, user: User) -> bool:
    """True iff the user occupies an ACTIVE seat in an ACTIVE organization (B2B2C tier).

    Imported lazily to avoid a hard import cycle and to keep this module usable if the org
    tables aren't present in an old schema (the query simply returns no rows).
    """
    from src.db.models import Organization, OrganizationMember

    row = (
        db.query(OrganizationMember.id)
        .join(Organization, OrganizationMember.org_id == Organization.id)
        .filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.active.is_(True),
            Organization.status.in_(_ACTIVE_STATUSES),
        )
        .first()
    )
    return row is not None


def recompute_user_tier(db: Session, user: User) -> None:
    """The SINGLE authority that writes ``users.tier`` from ALL THREE verified entitlement sources.

    A user is PREMIUM iff ANY of: an active individual Stripe subscription, an active organization
    seat, or an active mobile (RevenueCat) entitlement (``users.mobile_entitlement_active``). ORing
    all three means no source can wrongly downgrade another — canceling a Stripe sub must not strip
    a user who still holds a team seat or a mobile subscription; revoking a seat must not strip a
    user who pays individually or on mobile; and vice versa. Every path that can change ANY source
    routes through here: the Stripe webhook (``apply_event``), the org webhook + seat assign/remove
    + org-owner account deletion (``src/org_billing.py``), and the RevenueCat webhook
    (``src/mobile_billing.py``). It reads ONLY verified state (never a client flag). Behaviour is
    identical to the old direct ``user.tier`` flip for any user whose only source is the one being
    changed, so existing single-source billing guarantees hold.
    """
    premium = (
        _has_active_individual_sub(db, user)
        or _has_active_org_seat(db, user)
        or bool(user.mobile_entitlement_active)
    )
    user.tier = UserTier.PREMIUM if premium else UserTier.FREE


class BillingNotConfigured(Exception):
    """Raised when a billing operation is attempted without the required Stripe config."""


class UnknownPlan(Exception):
    """Raised when an unrecognized plan id is requested."""


def billing_enabled() -> bool:
    """True only when a Stripe secret key is configured (owner-provided, server-side)."""
    return bool(os.getenv("STRIPE_SECRET_KEY"))


def price_id_for_plan(plan: str) -> str:
    env_var = _PLAN_PRICE_ENV.get(plan)
    if not env_var:
        raise UnknownPlan(plan)
    price_id = os.getenv(env_var)
    if not price_id:
        raise BillingNotConfigured(f"No price configured for plan '{plan}' ({env_var}).")
    return price_id


def create_checkout_session(
    user: User,
    plan: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """Create a REAL Stripe Checkout session for a subscription and return its hosted URL.

    Raises UnknownPlan / BillingNotConfigured (never a fake URL) so the caller can surface
    an honest error. We tag the session with the user id in BOTH client_reference_id and
    metadata, and propagate it to subscription_data.metadata, so every later webhook event
    (subscription.updated/deleted) can be mapped back to the user.
    """
    if not billing_enabled():
        raise BillingNotConfigured("STRIPE_SECRET_KEY is not set.")
    price_id = price_id_for_plan(plan)  # raises before any network call if misconfigured

    stripe = configure_stripe()
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=user.id,
        customer_email=user.email,
        metadata={"user_id": user.id, "plan": plan},
        subscription_data={"metadata": {"user_id": user.id, "plan": plan}},
        allow_promotion_codes=True,
    )
    return session.url


def construct_event(payload: bytes, sig_header: str):
    """Verify a webhook payload's Stripe signature and return the parsed event.

    Raises BillingNotConfigured if no signing secret is set; lets stripe raise on a bad
    signature so the caller can return 400 and grant NOTHING.
    """
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise BillingNotConfigured("STRIPE_WEBHOOK_SECRET is not set.")

    import stripe

    return stripe.Webhook.construct_event(payload, sig_header, secret)


def _period_end(obj) -> Optional[datetime]:
    ts = obj.get("current_period_end")
    if not ts:
        return None
    try:
        return datetime.utcfromtimestamp(int(ts))
    except (TypeError, ValueError, OverflowError):
        return None


def _user_for_subscription(db: Session, obj) -> Optional[User]:
    """Map a Stripe subscription object back to our User.

    Prefer the user id we stamped into metadata; fall back to the customer/subscription id
    recorded on a prior Subscription row.
    """
    meta = obj.get("metadata") or {}
    user_id = meta.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user
    customer_id = obj.get("customer")
    if customer_id:
        sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
        if sub:
            return db.query(User).filter(User.id == sub.user_id).first()
    sub_id = obj.get("id")
    if sub_id:
        sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
        if sub:
            return db.query(User).filter(User.id == sub.user_id).first()
    return None


def _upsert_subscription(
    db: Session,
    user: User,
    *,
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
    plan: Optional[str] = None,
    status: Optional[str] = None,
    current_period_end: Optional[datetime] = None,
) -> Subscription:
    """Create or update the single Subscription row for a user (one row per user)."""
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if sub is None:
        sub = Subscription(user_id=user.id)
        db.add(sub)
    if stripe_customer_id:
        sub.stripe_customer_id = stripe_customer_id
    if stripe_subscription_id:
        sub.stripe_subscription_id = stripe_subscription_id
    if plan:
        sub.plan = plan
    if status:
        sub.status = status
    if current_period_end:
        sub.current_period_end = current_period_end
    sub.updated_at = datetime.utcnow()
    db.flush()
    return sub


def apply_event(event, db: Session) -> Optional[str]:
    """Apply a verified Stripe event to entitlement state. Returns the affected user id.

    Only these events change anything; everything else is acknowledged and ignored. The
    user.tier flip is the entitlement; the Subscription row is the audit/renewal record.
    """
    etype = event["type"]
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        meta = obj.get("metadata") or {}
        user_id = obj.get("client_reference_id") or meta.get("user_id")
        if not user_id:
            return None
        # Async payment methods (bank transfer, ACH, SEPA) complete the session with
        # payment_status="unpaid" — money has NOT cleared. Granting Premium here would hand
        # out ~a billing cycle of free access until the payment fails. Wait for the
        # subscription to go active (customer.subscription.created/updated) instead.
        if obj.get("payment_status") not in (None, "paid", "no_payment_required"):
            return None
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        _upsert_subscription(
            db,
            user,
            stripe_customer_id=obj.get("customer"),
            stripe_subscription_id=obj.get("subscription"),
            plan=meta.get("plan"),
            status="active",
        )
        recompute_user_tier(db, user)
        return user.id

    if etype in ("customer.subscription.created", "customer.subscription.updated"):
        user = _user_for_subscription(db, obj)
        if not user:
            return None
        status = obj.get("status")
        meta = obj.get("metadata") or {}
        _upsert_subscription(
            db,
            user,
            stripe_customer_id=obj.get("customer"),
            stripe_subscription_id=obj.get("id"),
            plan=meta.get("plan"),
            status=status,
            current_period_end=_period_end(obj),
        )
        recompute_user_tier(db, user)
        return user.id

    if etype == "customer.subscription.deleted":
        user = _user_for_subscription(db, obj)
        if not user:
            return None
        _upsert_subscription(db, user, stripe_subscription_id=obj.get("id"), status="canceled")
        recompute_user_tier(db, user)
        return user.id

    return None
