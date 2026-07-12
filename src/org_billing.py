"""Organization / team-seat billing (B2B2C tier — Track C, docs/BUSINESS_CASE.md lever 2).

An organization (a bootcamp, outplacement firm, or employer) buys a POOL of seats with ONE
quantity-based Stripe subscription and assigns them to member users. This is the named
floor-lever: higher ARPA + lower CAC per seat than individual acquisition.

Design rules (mirrors ``src/billing.py`` exactly — SIDE-EFFECT INTEGRITY):
- **No fake success.** ``create_seat_checkout_session`` makes a REAL, quantity-based
  ``stripe.checkout.Session.create`` call; when Stripe isn't configured it raises
  ``BillingNotConfigured`` (the caller returns an honest 503, no charge) — never a fake URL.
- **Entitlement only from a verified webhook.** An org's ``status`` and ``seats_purchased`` are
  written ONLY from a signature-verified Stripe event (the shared ``billing.construct_event``
  path); a member's entitlement is reconciled into ``users.tier`` by
  ``billing.recompute_user_tier`` — never a client-supplied flag.
- **Never grant more than paid.** The seat-assignment endpoint refuses to exceed
  ``seats_purchased``; a webhook seat REDUCTION re-enforces the cap (newest members freed
  first). A team seat grants the base paid (Pro) level only — Career+ stays an individual upsell.

Live Stripe keys + the team Price ID (``STRIPE_PRICE_TEAM_ANNUAL``) are owner-only (PENDING_OPS).
"""
import os
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src import billing
from src.billing import BillingNotConfigured, UnknownPlan, _ACTIVE_STATUSES
from src.db.models import Organization, OrganizationMember, User

# Public org plan id -> env var holding that plan's Stripe Price ID (a PER-SEAT recurring price;
# the checkout multiplies it by the seat quantity). Owner sets it in the deploy env; never committed.
_ORG_PLAN_PRICE_ENV = {
    "team_annual": "STRIPE_PRICE_TEAM_ANNUAL",
}

# Seat-count bounds on a checkout — a wallet-drain / fat-finger guard (server-side).
MIN_SEATS = 1
MAX_SEATS = 200


class OrgError(Exception):
    """Base class for organization-domain errors the API maps to 4xx."""


class OrgAlreadyExists(OrgError):
    """The user already owns an organization (one owned org per user)."""


class OrgNotActive(OrgError):
    """The org has no active paid seat subscription yet — buy seats before assigning them."""


class NoSeatsAvailable(OrgError):
    """All purchased seats are occupied."""


class MemberNotFound(OrgError):
    """No user account exists for the invited email (they must sign up first)."""


class AlreadyInAnotherOrg(OrgError):
    """The target user already occupies a seat in a different organization."""


def org_billing_enabled() -> bool:
    """True only when Stripe is configured (shared with individual billing)."""
    return billing.billing_enabled()


def price_id_for_org_plan(plan: str) -> str:
    env_var = _ORG_PLAN_PRICE_ENV.get(plan)
    if not env_var:
        raise UnknownPlan(plan)
    price_id = os.getenv(env_var)
    if not price_id:
        raise BillingNotConfigured(f"No price configured for org plan '{plan}' ({env_var}).")
    return price_id


# --------------------------------------------------------------------------- domain queries

def owned_org(db: Session, user: User) -> Optional[Organization]:
    """The organization this user administers (owns), if any."""
    return db.query(Organization).filter(Organization.owner_id == user.id).first()


def active_membership(db: Session, user: User) -> Optional[OrganizationMember]:
    """The user's active seat membership (in any org), if any. ``user_id`` is globally unique
    among member rows, so a user occupies at most one seat."""
    return (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.active.is_(True),
        )
        .first()
    )


def org_for_user(db: Session, user: User) -> Optional[Organization]:
    """The org relevant to this user: the one they OWN, else the one they're a seat member of."""
    org = owned_org(db, user)
    if org is not None:
        return org
    member = active_membership(db, user)
    if member is not None:
        return db.query(Organization).filter(Organization.id == member.org_id).first()
    return None


def seats_used(db: Session, org: Organization) -> int:
    """Number of seats currently occupied (active members)."""
    return (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.org_id == org.id,
            OrganizationMember.active.is_(True),
        )
        .count()
    )


def is_org_active(org: Organization) -> bool:
    return org.status in _ACTIVE_STATUSES


# --------------------------------------------------------------------------- domain mutations

def create_org(db: Session, owner: User, name: str) -> Organization:
    """Create an organization administered by ``owner`` (one owned org per user).

    No seats exist yet — the owner buys them via ``create_seat_checkout_session`` and then
    assigns members. The owner is an administrator, NOT automatically a seat occupant; to get
    entitlement for themselves they add their own email as a member (consuming a seat).
    """
    if owned_org(db, owner) is not None:
        raise OrgAlreadyExists("You already own an organization.")
    org = Organization(name=name.strip(), owner_id=owner.id, status=None, seats_purchased=0)
    db.add(org)
    try:
        db.flush()
    except IntegrityError:
        # A concurrent create raced past the app-level ``owned_org`` check above; the
        # UNIQUE(owner_id) constraint (uq_org_owner) rejected this second insert. Surface it as
        # the same clean 409 the check would have, never a 500 (§6c: fix the cause, fail loud).
        db.rollback()
        raise OrgAlreadyExists("You already own an organization.")
    return org


def add_member(db: Session, org: Organization, email: str) -> OrganizationMember:
    """Assign a seat to the user with ``email`` (idempotent if already an active member here).

    Enforces the paid-seat invariant: the org must be active AND have a free seat. The user must
    already have an account (we never invent one), and must not already hold a seat elsewhere.
    Reactivates a prior deactivated row for this user rather than creating a duplicate (``user_id``
    is globally unique among members).
    """
    if not is_org_active(org):
        raise OrgNotActive("Purchase seats before assigning them.")

    # Serialize concurrent seat assignments for THIS org by locking its row for the transaction
    # (mirrors the ``.with_for_update()`` idiom the spend-ceiling / rate-counter paths already use
    # in asgi.py). Without it, two parallel POST /api/org/members could both read
    # ``seats_used == cap - 1`` under READ COMMITTED, both pass the check, and both commit —
    # over-provisioning PAID entitlement for a seat that was never bought. On SQLite (tests) the
    # single connection already serializes, so this is a Postgres-only correctness lock.
    locked = db.query(Organization).filter(Organization.id == org.id).with_for_update().first()
    if locked is not None:
        org = locked
        if not is_org_active(org):
            raise OrgNotActive("Purchase seats before assigning them.")

    target = db.query(User).filter(User.email == email.strip().lower()).first()
    if target is None:
        raise MemberNotFound("No account exists for that email.")

    existing = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == target.id)
        .first()
    )
    if existing is not None:
        if existing.org_id != org.id:
            if existing.active:
                raise AlreadyInAnotherOrg("That user already belongs to another organization.")
            # An inactive row in another org: free to move — repoint it here below.
        if existing.active and existing.org_id == org.id:
            return existing  # idempotent
        # Reactivating (or moving) a seat consumes a seat — enforce the cap.
        if seats_used(db, org) >= (org.seats_purchased or 0):
            raise NoSeatsAvailable("All purchased seats are in use.")
        existing.org_id = org.id
        existing.role = "member"
        existing.active = True
        db.flush()
        billing.recompute_user_tier(db, target)
        return existing

    if seats_used(db, org) >= (org.seats_purchased or 0):
        raise NoSeatsAvailable("All purchased seats are in use.")
    member = OrganizationMember(org_id=org.id, user_id=target.id, role="member", active=True)
    db.add(member)
    try:
        db.flush()
    except IntegrityError:
        # A concurrent add raced past the app-level ``existing`` check above; the
        # UNIQUE(user_id) constraint (uq_org_member_user — a user belongs to at most one org)
        # rejected this second insert. Surface it as the same clean 409 the check would have,
        # never a 500 — mirroring ``create_org`` on its owner_id race (§6c: fix the cause,
        # fail loud). The user is now in the org that won the race.
        db.rollback()
        raise AlreadyInAnotherOrg("That user already belongs to another organization.")
    billing.recompute_user_tier(db, target)
    return member


def remove_member(db: Session, org: Organization, target_user_id: str) -> bool:
    """Free the seat held by ``target_user_id`` in ``org`` (soft — keeps the row for audit).

    Returns True if a seat was freed. Recomputes the removed user's tier (they lose the seat
    grant but keep any individual subscription). No-op (False) if they weren't an active member.
    """
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.org_id == org.id,
            OrganizationMember.user_id == target_user_id,
            OrganizationMember.active.is_(True),
        )
        .first()
    )
    if member is None:
        return False
    member.active = False
    db.flush()
    target = db.query(User).filter(User.id == target_user_id).first()
    if target is not None:
        billing.recompute_user_tier(db, target)
    return True


def list_members(db: Session, org: Organization) -> List[OrganizationMember]:
    """All active seat members of the org, oldest first."""
    return (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.org_id == org.id,
            OrganizationMember.active.is_(True),
        )
        .order_by(OrganizationMember.created_at.asc())
        .all()
    )


def _recompute_all_member_tiers(db: Session, org: Organization) -> None:
    """Reconcile ``users.tier`` for every member of the org (entitlement source may have changed)."""
    members = db.query(OrganizationMember).filter(OrganizationMember.org_id == org.id).all()
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user is not None:
            billing.recompute_user_tier(db, user)


def _enforce_seat_cap(db: Session, org: Organization) -> None:
    """Re-establish ``active members <= seats_purchased`` after a seat REDUCTION.

    Fair + deterministic: the OLDEST members keep their seats; the newest are deactivated until
    the count fits the paid pool. Then all affected tiers are reconciled. This runs on a webhook
    seat downgrade so an org can never keep granting more entitlement than it currently pays for.
    """
    cap = org.seats_purchased or 0
    active = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.org_id == org.id,
            OrganizationMember.active.is_(True),
        )
        .order_by(OrganizationMember.created_at.asc())
        .all()
    )
    if len(active) <= cap:
        return
    for m in active[cap:]:
        m.active = False
    db.flush()


# --------------------------------------------------------------------------- Stripe integration

def create_seat_checkout_session(
    owner: User,
    org: Organization,
    plan: str,
    seats: int,
    success_url: str,
    cancel_url: str,
) -> str:
    """Create a REAL quantity-based Stripe Checkout session for ``seats`` seats; return its URL.

    Raises UnknownPlan / BillingNotConfigured (never a fake URL) so the caller can surface an
    honest error. We stamp ``org_id``/``plan``/``seats`` into BOTH the session metadata and the
    subscription metadata so every later webhook maps back to this org.
    """
    if not org_billing_enabled():
        raise BillingNotConfigured("STRIPE_SECRET_KEY is not set.")
    if seats < MIN_SEATS or seats > MAX_SEATS:
        raise OrgError(f"Seats must be between {MIN_SEATS} and {MAX_SEATS}.")
    price_id = price_id_for_org_plan(plan)  # raises before any network call if misconfigured

    stripe = billing.configure_stripe()  # sub-budget HTTP timeout (see billing.configure_stripe)
    meta = {"org_id": org.id, "plan": plan, "seats": str(seats)}
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": seats}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=owner.id,
        customer_email=owner.email,
        metadata=meta,
        subscription_data={"metadata": meta},
        allow_promotion_codes=True,
    )
    return session.url


def _org_for_event_obj(db: Session, obj) -> Optional[Organization]:
    """Map a Stripe object back to our Organization (prefer stamped metadata, then stored ids)."""
    meta = obj.get("metadata") or {}
    org_id = meta.get("org_id")
    if org_id:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if org:
            return org
    customer_id = obj.get("customer")
    if customer_id:
        org = db.query(Organization).filter(
            Organization.stripe_customer_id == customer_id
        ).first()
        if org:
            return org
    sub_id = obj.get("id")
    if sub_id:
        org = db.query(Organization).filter(
            Organization.stripe_subscription_id == sub_id
        ).first()
        if org:
            return org
    return None


def _seat_quantity(obj) -> Optional[int]:
    """Extract the seat count from a Stripe subscription object's line item quantity."""
    try:
        items = (obj.get("items") or {}).get("data") or []
        if items:
            qty = items[0].get("quantity")
            if qty is not None:
                return int(qty)
    except (AttributeError, TypeError, ValueError):
        pass
    return None


def apply_event(event, db: Session) -> Optional[str]:
    """Apply a verified Stripe event to ORGANIZATION entitlement state; return the org id, or
    ``None`` if this event is NOT an org event (so the caller falls back to individual billing).

    An event is an org event only if it references a known Organization (by stamped ``org_id``
    metadata, or a customer/subscription id we've already stored). Only a signature-verified
    event reaches here — a forged payload never does, so entitlement can't be forged.
    """
    etype = event["type"]
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        meta = obj.get("metadata") or {}
        if not meta.get("org_id"):
            return None  # individual checkout — not ours
        org = _org_for_event_obj(db, obj)
        if not org:
            return None
        # Async payment methods complete unpaid — do not grant until the subscription is active.
        if obj.get("payment_status") not in (None, "paid", "no_payment_required"):
            return org.id
        org.stripe_customer_id = obj.get("customer") or org.stripe_customer_id
        org.stripe_subscription_id = obj.get("subscription") or org.stripe_subscription_id
        org.plan = meta.get("plan") or org.plan
        org.status = "active"
        try:
            org.seats_purchased = max(int(meta.get("seats", org.seats_purchased or 0)), 0)
        except (TypeError, ValueError):
            pass
        db.flush()
        _enforce_seat_cap(db, org)
        _recompute_all_member_tiers(db, org)
        return org.id

    if etype in ("customer.subscription.created", "customer.subscription.updated"):
        org = _org_for_event_obj(db, obj)
        if not org:
            return None
        status = obj.get("status")
        meta = obj.get("metadata") or {}
        org.stripe_customer_id = obj.get("customer") or org.stripe_customer_id
        org.stripe_subscription_id = obj.get("id") or org.stripe_subscription_id
        org.plan = meta.get("plan") or org.plan
        org.status = status
        qty = _seat_quantity(obj)
        if qty is not None:
            org.seats_purchased = max(qty, 0)
        db.flush()
        _enforce_seat_cap(db, org)
        _recompute_all_member_tiers(db, org)
        return org.id

    if etype == "customer.subscription.deleted":
        org = _org_for_event_obj(db, obj)
        if not org:
            return None
        org.status = "canceled"
        db.flush()
        _recompute_all_member_tiers(db, org)
        return org.id

    return None


def purge_user_orgs(db: Session, user: User) -> None:
    """Remove all org rows referencing ``user`` before an account deletion (no ORM cascade to
    users). Deletes orgs the user OWNS (cascade-removing their member rows) and frees any seat
    the user occupies elsewhere — then reconciles every affected member's tier so a deleted
    owner's members correctly drop to FREE (unless they pay individually).
    """
    # 1) The user's own seat membership (in someone else's org): free it.
    own_membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .all()
    )
    for m in own_membership:
        db.delete(m)
    db.flush()

    # 2) Orgs the user owns: collect affected members, delete the orgs, reconcile the members.
    orgs = db.query(Organization).filter(Organization.owner_id == user.id).all()
    affected_user_ids = set()
    for org in orgs:
        for m in db.query(OrganizationMember).filter(
            OrganizationMember.org_id == org.id
        ).all():
            if m.user_id != user.id:
                affected_user_ids.add(m.user_id)
        db.delete(org)  # ORM cascade removes the org's member rows
    db.flush()
    for uid in affected_user_ids:
        member_user = db.query(User).filter(User.id == uid).first()
        if member_user is not None:
            billing.recompute_user_tier(db, member_user)
    db.flush()
