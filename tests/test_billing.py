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
from types import SimpleNamespace

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
