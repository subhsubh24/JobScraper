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
from fastapi.testclient import TestClient

from src.billing import _period_end, _user_for_subscription, current_plan_level
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


def _sign_at(payload: bytes, ts: int, secret: str = WHSEC) -> str:
    """Like ``_sign`` but stamps an EXPLICIT timestamp so a test can produce a signature with a
    VALID HMAC yet an out-of-window ``t=`` — exercising Stripe's replay (tolerance) check rather
    than the HMAC check."""
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


# --------------------------------------------------------------------------- billing portal
def test_portal_refuses_honestly_when_unconfigured(client, monkeypatch):
    """No Stripe key -> honest 503, never a fake portal URL."""
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    _, token = _register(client)
    r = client.post("/api/billing/portal", headers=_auth(token))
    assert r.status_code == 503


def test_portal_400_when_user_has_no_subscription(client, monkeypatch):
    """Configured, but the user never checked out (no Stripe customer on record) -> honest 400,
    no fake portal (there is nothing to manage)."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    _, token = _register(client)
    r = client.post("/api/billing/portal", headers=_auth(token))
    assert r.status_code == 400


def test_portal_creates_real_stripe_session(client, monkeypatch, db_session):
    """When configured AND the user has a Stripe customer on record, the endpoint makes the REAL
    stripe.billing_portal.Session.create call scoped to THAT customer and returns its hosted URL."""
    import stripe

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    user_id, token = _register(client)
    # A prior grant recorded the Stripe customer for this user (as a real webhook would).
    db_session.add(
        Subscription(user_id=user_id, stripe_customer_id="cus_portal_1", status="active")
    )
    db_session.commit()

    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(url="https://billing.stripe.test/portal_xyz")

    monkeypatch.setattr(stripe.billing_portal.Session, "create", staticmethod(fake_create))

    r = client.post("/api/billing/portal", headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["url"] == "https://billing.stripe.test/portal_xyz"
    # The real call was scoped to THIS user's customer and carries a return_url back into the app.
    assert captured["customer"] == "cus_portal_1"
    assert "return_url" in captured and captured["return_url"].endswith("/app/settings")


def test_portal_maps_stripe_timeout_to_honest_503(client, monkeypatch, db_session):
    """A transient Stripe failure on the portal call becomes a retryable 503, never an uncaught
    500 (mirrors the checkout timeout contract; DEEP_DIAGNOSIS rule (a))."""
    import stripe

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    user_id, token = _register(client)
    db_session.add(
        Subscription(user_id=user_id, stripe_customer_id="cus_timeout", status="active")
    )
    db_session.commit()

    def _raise_timeout(**kwargs):
        raise stripe.error.APIConnectionError("Request timed out.")

    monkeypatch.setattr(stripe.billing_portal.Session, "create", staticmethod(_raise_timeout))
    r = client.post("/api/billing/portal", headers=_auth(token))
    assert r.status_code == 503


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


def test_webhook_redelivered_checkout_is_idempotent_one_subscription_row(
    client, monkeypatch, db_session
):
    """Stripe redelivers webhook events (retries on any non-2xx, network blip, or at-least-once
    delivery) — the SAME signed ``checkout.session.completed`` can legitimately arrive more than
    once. Entitlement must be idempotent: the second delivery must return 200, keep exactly one
    Subscription row, and not corrupt state. Two layers guarantee this, and nothing pinned
    EITHER: (1) app-level, ``_upsert_subscription`` keeps one row per user
    (SELECT-then-create-if-absent), so redelivery is a clean UPDATE; (2) DB-level, ``user_id`` has
    a UNIQUE constraint as defense-in-depth. A refactor to a blind ``db.add(Subscription(...))``
    would trip that constraint on redelivery → IntegrityError → the webhook 500s, so Stripe keeps
    retrying and entitlement bookkeeping breaks — this test catches that (the second delivery must
    still 200 and leave exactly one row). Deterministic; no live call.
    """
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client)
    payload = _event(
        "checkout.session.completed",
        {
            "id": "cs_redeliver",
            "object": "checkout.session",
            "client_reference_id": user_id,
            "customer": "cus_redeliver",
            "subscription": "sub_redeliver",
            "payment_status": "paid",
            "metadata": {"user_id": user_id, "plan": "pro_annual"},
        },
    )
    # Same event id ("evt_test" from _event) + same signature body = a true Stripe redelivery.
    for _ in range(2):
        r = client.post(
            "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
        )
        assert r.status_code == 200, r.text

    user = db_session.query(User).filter(User.id == user_id).first()
    assert user.tier == UserTier.PREMIUM
    # The load-bearing assertion: redelivery upserts, it does not duplicate.
    rows = db_session.query(Subscription).filter(Subscription.user_id == user_id).all()
    assert len(rows) == 1
    assert rows[0].stripe_subscription_id == "sub_redeliver"
    assert rows[0].status == "active"


def test_webhook_recovers_from_concurrent_insert_race_one_row(_engine, monkeypatch):
    """CONCURRENT first delivery of the same event (distinct from the SEQUENTIAL redelivery
    above): two instances both SELECT no Subscription row and INSERT; the loser's commit trips
    the ``subscriptions.user_id`` UNIQUE constraint -> IntegrityError. The webhook must ROLL
    BACK and RE-APPLY (retry-as-update), returning 200 with EXACTLY ONE Subscription row +
    PREMIUM — not an uncaught 500 that makes Stripe re-deliver and delays entitlement.

    Deterministic simulation (mirrors ``tests/test_rate_counter.py``'s insert-race test). The
    real ``IntegrityError`` surfaces at ``_upsert_subscription``'s explicit ``db.flush()``
    (``billing.py``), NOT at the later ``db.commit()`` — so this injects the fault at FLUSH to
    be faithful: on the webhook's first flush the per-request session discards our losing
    INSERT, durably commits a WINNER Subscription row for the same user, then raises the
    IntegrityError the DB would have raised on our duplicate flush. On the retry,
    ``billing.apply_event``'s SELECT finds the winner and takes the idempotent UPDATE path ->
    one row. LOAD-BEARING: revert the webhook's ``except IntegrityError`` retry loop (or narrow
    the ``try`` back to only ``db.commit()``) and this call 500s (the flush-time error is
    uncaught).
    """
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import sessionmaker

    import asgi
    from src.db import get_db

    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    state = {"armed": False, "user_id": None, "flushes": 0}

    def override_get_db():
        db = TestingSession()
        real_flush = db.flush
        real_commit = db.commit

        def flaky_flush(*a, **k):
            # Trip exactly once, on the webhook's apply_event insert-flush (after arming). All
            # other flushes (registration, the retry's UPDATE flush) pass straight through.
            if not state["armed"]:
                return real_flush(*a, **k)
            state["armed"] = False  # one-shot
            state["flushes"] += 1
            db.rollback()  # our losing INSERT is discarded
            db.add(
                Subscription(
                    user_id=state["user_id"], status="active",
                    stripe_subscription_id="sub_winner",
                )
            )
            real_commit()  # the concurrent WINNER's row is now durable
            raise IntegrityError("dup", {}, Exception("UNIQUE constraint failed: subscriptions.user_id"))

        db.flush = flaky_flush
        try:
            yield db
        finally:
            db.close()

    asgi.app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(asgi.app) as c:
            uid, _ = _register(c)
            state["user_id"] = uid
            state["armed"] = True  # arm the race for the webhook's first apply_event flush
            payload = _event(
                "checkout.session.completed",
                {
                    "id": "cs_race",
                    "object": "checkout.session",
                    "client_reference_id": uid,
                    "customer": "cus_race",
                    "subscription": "sub_redeliver",
                    "payment_status": "paid",
                    "metadata": {"user_id": uid, "plan": "pro_annual"},
                },
            )
            r = c.post(
                "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
            )
            assert r.status_code == 200, r.text  # recovered, not an uncaught 500
        verify = TestingSession()
        rows = verify.query(Subscription).filter(Subscription.user_id == uid).all()
        assert len(rows) == 1  # winner + our retried UPDATE == one row, not a duplicate/crash
        assert rows[0].stripe_subscription_id == "sub_redeliver"  # the retry UPDATED the winner
        assert verify.query(User).filter(User.id == uid).first().tier == UserTier.PREMIUM
        assert state["flushes"] == 1  # the race fired at flush and the retry recovered
        verify.close()
    finally:
        asgi.app.dependency_overrides.clear()


def test_webhook_fails_closed_when_integrityerror_persists(_engine, monkeypatch):
    """If BOTH retry attempts hit an IntegrityError (a persistent constraint problem, not the
    ordinary first-delivery race that one UPDATE resolves), the webhook must FAIL CLOSED — a 500
    so Stripe re-delivers — and grant NOTHING. It must NEVER return 200 with nothing committed
    (that would make Stripe stop retrying and silently drop the entitlement update). Pins the
    fail-closed guarantee (mirrors ``_consume_counter`` exhausting its retry with ``return
    False`` rather than claiming success)."""
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import sessionmaker

    import asgi
    from src.db import get_db

    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    state = {"armed": False}

    def override_get_db():
        db = TestingSession()
        real_flush = db.flush

        def always_failing_flush(*a, **k):
            if not state["armed"]:
                return real_flush(*a, **k)
            db.rollback()  # discard the pending insert; no winner is ever committed
            raise IntegrityError("dup", {}, Exception("UNIQUE constraint failed: subscriptions.user_id"))

        db.flush = always_failing_flush
        try:
            yield db
        finally:
            db.close()

    asgi.app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(asgi.app, raise_server_exceptions=False) as c:
            uid, _ = _register(c)
            state["armed"] = True  # every subsequent apply_event flush raises -> both attempts fail
            payload = _event(
                "checkout.session.completed",
                {
                    "id": "cs_persist",
                    "object": "checkout.session",
                    "client_reference_id": uid,
                    "customer": "cus_persist",
                    "subscription": "sub_persist",
                    "payment_status": "paid",
                    "metadata": {"user_id": uid, "plan": "pro_annual"},
                },
            )
            r = c.post(
                "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
            )
            assert r.status_code == 500  # FAIL CLOSED, never a fake 200
        verify = TestingSession()
        # Grant NOTHING: no Subscription row, tier stays FREE.
        assert verify.query(Subscription).filter(Subscription.user_id == uid).count() == 0
        assert verify.query(User).filter(User.id == uid).first().tier == UserTier.FREE
        verify.close()
    finally:
        asgi.app.dependency_overrides.clear()


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


def test_webhook_unpaid_async_checkout_persists_ids_and_activates_without_metadata(
    client, monkeypatch, db_session
):
    """An UNPAID async checkout (bank transfer / ACH / SEPA) must GRANT NOTHING yet, but it must
    PERSIST the customer/subscription ids so the later activation event can map back — even if
    Stripe drops the ``metadata.user_id`` on that event.

    Regression net for the individual path's parity with the org path
    (``test_org_billing.py::test_async_payment_persists_ids_and_activates_even_if_later_metadata_is_dropped``):
    before the fix, ``apply_event`` returned ``None`` on the unpaid checkout WITHOUT writing a
    Subscription row, so ``_user_for_subscription`` had no customer/subscription id to fall back on.
    A real ``customer.subscription.created`` that arrives with EMPTY metadata (Stripe lifecycle
    events routinely omit the app metadata) would then resolve to no user → a PAYING customer stuck
    FREE forever. Revert-proven load-bearing: drop the unpaid-branch ``_upsert_subscription`` and the
    activation below can't find the user → the final PREMIUM assertion fails.
    """
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client)

    # 1) Unpaid async checkout completes: grant nothing, but record the ids for the later map-back.
    unpaid = _event(
        "checkout.session.completed",
        {
            "id": "cs_async",
            "client_reference_id": user_id,
            "customer": "cus_async",
            "subscription": "sub_async",
            "payment_status": "unpaid",
            "metadata": {"user_id": user_id, "plan": "pro_annual"},
        },
    )
    r = client.post(
        "/api/billing/webhook", content=unpaid, headers={"stripe-signature": _sign(unpaid)}
    )
    assert r.status_code == 200
    db_session.expire_all()
    # Still FREE (money hasn't cleared) ...
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.FREE
    # ... but the ids are now on the (inactive) Subscription row — the fallback anchor.
    sub = db_session.query(Subscription).filter(Subscription.user_id == user_id).first()
    assert sub is not None
    assert sub.stripe_customer_id == "cus_async"
    assert sub.stripe_subscription_id == "sub_async"
    assert sub.status not in ("active", "trialing")

    # 2) The payment clears. Stripe sends subscription.created with NO app metadata — the only way
    #    back to the user is the customer id we stored above.
    activated = _event(
        "customer.subscription.created",
        {
            "id": "sub_async",
            "customer": "cus_async",
            "status": "active",
            "metadata": {},
            "items": {"data": [{"price": {"id": "price_x"}}]},
        },
    )
    r = client.post(
        "/api/billing/webhook", content=activated, headers={"stripe-signature": _sign(activated)}
    )
    assert r.status_code == 200
    db_session.expire_all()
    # The paying customer is now PREMIUM — the map-back succeeded despite the dropped metadata.
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.PREMIUM


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


def test_webhook_rejects_replayed_ancient_timestamp_and_grants_nothing(client, monkeypatch, db_session):
    """A signature with a VALID HMAC but an ANCIENT timestamp must be rejected on Stripe's
    replay-window (tolerance ~5 min) check — a DISTINCT defense from the forged-HMAC case above.

    Regression net: every other signed-webhook test uses ``_sign`` (a fresh ``time.time()``
    timestamp), so the replay-window path was never exercised. If a library bump or a
    misconfiguration disabled the timestamp check, a captured, correctly-signed event could be
    replayed to re-grant entitlement — and nothing here would have caught it. Deterministic; no
    live Stripe call.
    """
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client)
    payload = _event(
        "checkout.session.completed",
        {
            "id": "cs_replay",
            "client_reference_id": user_id,
            "payment_status": "paid",
            "metadata": {"user_id": user_id, "plan": "pro_monthly"},
        },
    )
    # Valid HMAC over the payload, but the timestamp is from 1970 — far outside the tolerance.
    r = client.post(
        "/api/billing/webhook",
        content=payload,
        headers={"stripe-signature": _sign_at(payload, 1000)},
    )
    assert r.status_code == 400, r.text
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.FREE
    # And the replayed event created no Subscription row.
    assert (
        db_session.query(Subscription).filter(Subscription.user_id == user_id).first() is None
    )


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


# ---------------------------------------------------------- authoritative plan on portal changes
# Stripe stamps metadata.plan only at CHECKOUT-session creation and NEVER refreshes it on a plan
# change made through the hosted billing portal (/api/billing/portal). So a portal upgrade/downgrade
# fires customer.subscription.updated with the NEW price in items.data[0].price but STALE metadata.
# The webhook must re-derive the plan from the authoritative price, else the entitlement LEVEL goes
# stale — a Career+->Pro downgrade would keep Career+ access (a real entitlement bypass). These pin
# that the price wins over metadata, and that metadata-only events (no line items) are unaffected.


def test_webhook_updated_uses_authoritative_price_over_stale_plan_metadata(
    client, monkeypatch, db_session
):
    """Portal DOWNGRADE Career+ -> Pro: the .updated event carries the new Pro price but stale
    careerplus metadata. The webhook must record ``pro_annual`` (from the price), dropping the user
    to Pro-level entitlement. LOAD-BEARING: trust metadata here and the bypass reopens — the user
    keeps Career+ they no longer pay for. Fails on the pre-fix code (plan stays careerplus)."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    monkeypatch.setenv("STRIPE_PRICE_PRO_ANNUAL", "price_pro_annual_id")
    monkeypatch.setenv("STRIPE_PRICE_CAREERPLUS_ANNUAL", "price_cplus_annual_id")
    user_id, _ = _register(client, email="downgrade@example.com")
    # Seed an active Career+ subscription + PREMIUM tier, exactly as an app checkout would leave it.
    db_session.add(
        Subscription(
            user_id=user_id, stripe_customer_id="cus_dg", stripe_subscription_id="sub_dg",
            plan="careerplus_annual", status="active",
        )
    )
    db_session.query(User).filter(User.id == user_id).first().tier = UserTier.PREMIUM
    db_session.commit()

    payload = _event(
        "customer.subscription.updated",
        {
            "id": "sub_dg", "customer": "cus_dg", "status": "active",
            "metadata": {"user_id": user_id, "plan": "careerplus_annual"},  # STALE — Stripe kept it
            "items": {"data": [{"price": {"id": "price_pro_annual_id"}}]},   # AUTHORITATIVE new plan
        },
    )
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert r.status_code == 200, r.text
    db_session.expire_all()
    sub = db_session.query(Subscription).filter(Subscription.user_id == user_id).first()
    assert sub.plan == "pro_annual"  # authoritative price won over the stale careerplus metadata
    user = db_session.query(User).filter(User.id == user_id).first()
    assert current_plan_level(user, sub) == "pro"  # not career_plus -> the bypass is closed


def test_webhook_updated_falls_back_to_metadata_plan_when_no_known_price(
    client, monkeypatch, db_session
):
    """A renewal-style .updated with NO line items (or an unknown price) still records the plan from
    metadata — the authoritative derivation returns None and defers to metadata, so existing
    metadata-only events are unaffected (backward-compat)."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    user_id, _ = _register(client, email="renew@example.com")
    payload = _event(
        "customer.subscription.updated",
        {
            "id": "sub_rn", "customer": "cus_rn", "status": "active",
            "metadata": {"user_id": user_id, "plan": "careerplus_monthly"},
        },
    )
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert r.status_code == 200, r.text
    db_session.expire_all()
    sub = db_session.query(Subscription).filter(Subscription.user_id == user_id).first()
    assert sub.plan == "careerplus_monthly"


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
