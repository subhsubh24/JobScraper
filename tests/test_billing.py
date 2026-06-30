"""Track C (web Stripe billing) + F4.1 side-effect round-trip guards.

These prove SIDE-EFFECT INTEGRITY for the billing path:
- checkout makes a REAL stripe call when configured and refuses HONESTLY (no fake success)
  when it isn't — granting NOTHING either way (entitlement only moves via the webhook);
- the webhook grants/revokes Premium ONLY from a signature-VERIFIED event; a forged or
  unsigned payload changes nothing. The "effect" (user.tier flip + Subscription row) is
  asserted directly, never inferred from a 200.
"""
import hashlib
import hmac
import json
import time
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.billing import _period_end, _user_for_subscription
from src.db.models import Subscription, User, UserTier

WHSEC = "whsec_test_secret"


def _register(client, email="buyer@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _sign(payload: bytes, secret: str = WHSEC) -> str:
    """Build a valid Stripe-Signature header (t=<ts>,v1=<hmac>) for a raw payload."""
    ts = int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _event(etype: str, obj: dict) -> bytes:
    return json.dumps(
        {"id": "evt_test", "object": "event", "type": etype, "data": {"object": obj}}
    ).encode()


# --------------------------------------------------------------------------- checkout
def test_checkout_refuses_honestly_when_unconfigured(client, monkeypatch, db_session):
    """No Stripe key configured -> 503, no charge, tier unchanged (never a fake success)."""
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    _, token = _register(client)
    r = client.post("/api/billing/checkout", json={"plan": "pro_annual"}, headers=_auth(token))
    assert r.status_code == 503
    assert db_session.query(User).first().tier == UserTier.FREE


def test_checkout_unknown_plan_is_rejected(client, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    _, token = _register(client)
    r = client.post("/api/billing/checkout", json={"plan": "nope"}, headers=_auth(token))
    assert r.status_code == 400


def test_checkout_creates_real_stripe_session(client, monkeypatch):
    """When configured, the endpoint makes the REAL stripe.checkout.Session.create call with
    the right price + user mapping and returns its hosted URL."""
    import stripe

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_PRO_ANNUAL", "price_annual_123")
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(url="https://checkout.stripe.test/session_abc")

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(fake_create))

    user_id, token = _register(client)
    r = client.post("/api/billing/checkout", json={"plan": "pro_annual"}, headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["url"] == "https://checkout.stripe.test/session_abc"
    # The real call carried the right price, mode, and user mapping.
    assert captured["mode"] == "subscription"
    assert captured["line_items"][0]["price"] == "price_annual_123"
    assert captured["client_reference_id"] == user_id
    assert captured["metadata"]["user_id"] == user_id


def test_checkout_blocks_when_already_premium(client, monkeypatch, db_session):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_PRO_ANNUAL", "price_annual_123")
    _, token = _register(client)
    user = db_session.query(User).first()
    user.tier = UserTier.PREMIUM
    db_session.commit()
    r = client.post("/api/billing/checkout", json={"plan": "pro_annual"}, headers=_auth(token))
    assert r.status_code == 400


# --------------------------------------------------------------------------- webhook
def test_webhook_grants_premium_on_signed_checkout_completed(client, monkeypatch, db_session):
    """The round-trip: a signature-VERIFIED checkout.session.completed flips the user to
    Premium AND writes a Subscription row. The effect is asserted in the DB, not from 200."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client)
    payload = _event(
        "checkout.session.completed",
        {
            "id": "cs_test_1",
            "object": "checkout.session",
            "client_reference_id": user_id,
            "customer": "cus_123",
            "subscription": "sub_123",
            "payment_status": "paid",
            "metadata": {"user_id": user_id, "plan": "pro_annual"},
        },
    )
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert r.status_code == 200, r.text

    user = db_session.query(User).filter(User.id == user_id).first()
    assert user.tier == UserTier.PREMIUM
    sub = db_session.query(Subscription).filter(Subscription.user_id == user_id).first()
    assert sub is not None
    assert sub.stripe_subscription_id == "sub_123"
    assert sub.plan == "pro_annual"
    assert sub.status == "active"


def test_webhook_unpaid_async_checkout_grants_nothing(client, monkeypatch, db_session):
    """An async-payment checkout that completes UNPAID must not grant Premium — money
    hasn't cleared. Entitlement waits for the subscription to go active."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client)
    payload = _event(
        "checkout.session.completed",
        {
            "id": "cs_unpaid",
            "client_reference_id": user_id,
            "customer": "cus_u",
            "subscription": "sub_u",
            "payment_status": "unpaid",
            "metadata": {"user_id": user_id, "plan": "pro_annual"},
        },
    )
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert r.status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.FREE


def test_webhook_rejects_forged_signature_and_grants_nothing(client, monkeypatch, db_session):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client)
    payload = _event(
        "checkout.session.completed",
        {"id": "cs_x", "client_reference_id": user_id, "metadata": {"user_id": user_id}},
    )
    r = client.post(
        "/api/billing/webhook",
        content=payload,
        headers={"stripe-signature": "t=123,v1=deadbeef"},
    )
    assert r.status_code == 400
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.FREE


def test_webhook_unconfigured_returns_503(client, monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    payload = _event("checkout.session.completed", {"id": "cs_x"})
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert r.status_code == 503


def test_webhook_downgrades_on_subscription_deleted(client, monkeypatch, db_session):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client)
    # First grant Premium via a completed checkout.
    grant = _event(
        "checkout.session.completed",
        {
            "id": "cs_1",
            "client_reference_id": user_id,
            "customer": "cus_9",
            "subscription": "sub_9",
            "metadata": {"user_id": user_id, "plan": "pro_monthly"},
        },
    )
    client.post("/api/billing/webhook", content=grant, headers={"stripe-signature": _sign(grant)})
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.PREMIUM

    # Now the subscription is cancelled at period end / deleted -> back to FREE.
    delete = _event(
        "customer.subscription.deleted",
        {"id": "sub_9", "customer": "cus_9", "status": "canceled",
         "metadata": {"user_id": user_id}},
    )
    r = client.post(
        "/api/billing/webhook", content=delete, headers={"stripe-signature": _sign(delete)}
    )
    assert r.status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.FREE


def test_account_deletion_cascades_subscription(client, monkeypatch, db_session):
    """A new user-owned table must not orphan rows on account deletion (Track D)."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, token = _register(client)
    grant = _event(
        "checkout.session.completed",
        {"id": "cs_2", "client_reference_id": user_id, "customer": "cus_2",
         "subscription": "sub_2", "metadata": {"user_id": user_id, "plan": "pro_annual"}},
    )
    client.post("/api/billing/webhook", content=grant, headers={"stripe-signature": _sign(grant)})
    assert db_session.query(Subscription).count() == 1

    assert client.delete("/api/auth/me", headers=_auth(token)).status_code == 200
    db_session.expire_all()
    assert db_session.query(Subscription).count() == 0


# --------------------------------------------------- webhook user-mapping fallbacks
# Stripe does not always echo our metadata back. customer.subscription.* events fired by
# Stripe's own lifecycle (renewals, dunning, portal cancels) often carry no `metadata.user_id`,
# so the webhook must still resolve the user from a PRIOR Subscription row by customer id and,
# failing that, by subscription id. Every existing test sends metadata.user_id, so these two
# fallback chains in _user_for_subscription were entirely unexercised — a silent
# entitlement-loss risk on real renewal events.
def test_webhook_resolves_user_by_customer_id_when_metadata_absent(client, monkeypatch, db_session):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client)
    # A prior Subscription row records the Stripe customer for this user (as a real grant would).
    db_session.add(Subscription(user_id=user_id, stripe_customer_id="cus_known", status="active"))
    db_session.commit()

    # A renewal-style event with NO metadata.user_id, but the SAME customer.
    payload = _event(
        "customer.subscription.updated",
        {"id": "sub_new", "customer": "cus_known", "status": "active", "metadata": {}},
    )
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert r.status_code == 200, r.text
    db_session.expire_all()
    # The user was found via the customer-id fallback and granted Premium.
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.PREMIUM
    sub = db_session.query(Subscription).filter(Subscription.user_id == user_id).first()
    assert sub.stripe_subscription_id == "sub_new"


def test_webhook_resolves_user_by_subscription_id_when_no_customer(client, monkeypatch, db_session):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client)
    # A prior row records the subscription id (but the incoming event has no customer/metadata).
    db_session.add(
        Subscription(user_id=user_id, stripe_subscription_id="sub_anchor", status="active")
    )
    db_session.commit()

    payload = _event(
        "customer.subscription.deleted",
        {"id": "sub_anchor", "status": "canceled", "metadata": {}},
    )
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert r.status_code == 200, r.text
    db_session.expire_all()
    # Found via the subscription-id fallback and downgraded.
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.FREE


def test_webhook_unknown_subscription_grants_nothing(client, monkeypatch, db_session):
    """No metadata, no matching customer/subscription row -> no user, no entitlement change."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client)
    payload = _event(
        "customer.subscription.updated",
        {"id": "sub_orphan", "customer": "cus_orphan", "status": "active", "metadata": {}},
    )
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert r.status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.FREE


def test_user_for_subscription_prefers_metadata_over_stale_rows(client, db_session):
    """metadata.user_id wins even if a stale Subscription row points elsewhere."""
    a_id, _ = _register(client, email="a@example.com")
    b_id, _ = _register(client, email="b@example.com")
    # A stale row maps cus_shared -> user B.
    db_session.add(Subscription(user_id=b_id, stripe_customer_id="cus_shared", status="active"))
    db_session.commit()
    obj = {"id": "sub_x", "customer": "cus_shared", "metadata": {"user_id": a_id}}
    user = _user_for_subscription(db_session, obj)
    assert user is not None and user.id == a_id


# ----------------------------------------------------------- _period_end edge cases
# current_period_end drives renewal records; Stripe can omit it or (rarely) send junk.
# The helper must degrade to None, never raise into the webhook handler.
@pytest.mark.parametrize(
    "value",
    [None, "", "garbage", 10 ** 30, -(10 ** 30)],
    ids=["missing", "empty", "non-numeric", "overflow", "negative-overflow"],
)
def test_period_end_returns_none_on_bad_input(value):
    obj = {} if value is None else {"current_period_end": value}
    assert _period_end(obj) is None


def test_period_end_parses_valid_unix_timestamp():
    assert _period_end({"current_period_end": 1700000000}) == datetime.utcfromtimestamp(1700000000)


# --------------------------------------------------------------------------- lifecycle status
# These pin the entitlement decision on subscription STATUS, which production Stripe events
# exercise but the existing tests never did: a trial grants access, a non-active status
# revokes it, and a $0/trial checkout (no_payment_required) still grants. A regression that
# narrowed _ACTIVE_STATUSES or the checkout payment-status allow-list would silently break a
# real paying/trialing user — these fail LOUD if that happens.


def test_webhook_trialing_subscription_grants_premium(client, monkeypatch, db_session):
    """A ``customer.subscription.updated`` with status="trialing" must grant Premium —
    Stripe trials are entitled access, and "trialing" is in _ACTIVE_STATUSES."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client, email="trial@example.com")
    payload = _event(
        "customer.subscription.updated",
        {
            "id": "sub_trial",
            "customer": "cus_trial",
            "status": "trialing",
            "metadata": {"user_id": user_id, "plan": "pro_monthly"},
        },
    )
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert r.status_code == 200, r.text
    db_session.expire_all()
    user = db_session.query(User).filter(User.id == user_id).first()
    assert user.tier == UserTier.PREMIUM
    sub = db_session.query(Subscription).filter(Subscription.user_id == user_id).first()
    assert sub is not None and sub.status == "trialing"


def test_webhook_inactive_status_revokes_premium(client, monkeypatch, db_session):
    """A subscription that goes ``past_due`` (or any non-active status) via .updated must
    drop the user back to FREE — the else-branch of the entitlement decision."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client, email="pastdue@example.com")
    # Grant first via an active subscription.
    grant = _event(
        "customer.subscription.updated",
        {"id": "sub_pd", "customer": "cus_pd", "status": "active",
         "metadata": {"user_id": user_id, "plan": "pro_monthly"}},
    )
    client.post("/api/billing/webhook", content=grant, headers={"stripe-signature": _sign(grant)})
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.PREMIUM
    # Now it goes past_due -> revoke (without a delete event).
    lapse = _event(
        "customer.subscription.updated",
        {"id": "sub_pd", "customer": "cus_pd", "status": "past_due",
         "metadata": {"user_id": user_id, "plan": "pro_monthly"}},
    )
    r = client.post(
        "/api/billing/webhook", content=lapse, headers={"stripe-signature": _sign(lapse)}
    )
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.FREE


def test_webhook_no_payment_required_checkout_grants_premium(client, monkeypatch, db_session):
    """A trial/$0 checkout completes with payment_status="no_payment_required" — money was
    never owed, so it MUST grant (it's in the checkout allow-list), unlike "unpaid"."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client, email="freetrial@example.com")
    payload = _event(
        "checkout.session.completed",
        {
            "id": "cs_npr",
            "client_reference_id": user_id,
            "customer": "cus_npr",
            "subscription": "sub_npr",
            "payment_status": "no_payment_required",
            "metadata": {"user_id": user_id, "plan": "pro_monthly"},
        },
    )
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.PREMIUM
