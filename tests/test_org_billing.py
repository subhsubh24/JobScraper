"""Team / organization seat tier (B2B2C — Track C, business-case lever 2).

Proves SIDE-EFFECT INTEGRITY + entitlement correctness for the seat tier, at the same bar as
the individual billing tests (``tests/test_billing.py``):
- seat checkout makes a REAL quantity-based Stripe call when configured and refuses HONESTLY
  (503, no charge) when it isn't — granting NOTHING either way;
- an org's ``status``/``seats_purchased`` move ONLY on a signature-VERIFIED webhook; a forged
  payload changes nothing;
- a member gets PREMIUM entitlement ONLY while the org is active AND they occupy a seat, and
  the paid-seat invariant (``active members <= seats_purchased``) is enforced on assignment AND
  on a webhook seat reduction (newest freed first);
- the dual-grant reconciliation never wrongly downgrades (individual sub OR org seat);
- authz + tenant isolation (only the owner manages seats; a member can't) and account-deletion
  purge (no orphaned org rows) hold.

Effects are asserted directly in the DB, never inferred from a 200.
"""
import hashlib
import hmac
import json
import time
from types import SimpleNamespace

from src.db.models import Organization, OrganizationMember, User, UserTier

WHSEC = "whsec_test_secret"


def _register(client, email, password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _sign(payload: bytes, secret: str = WHSEC) -> str:
    ts = int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _event(etype: str, obj: dict) -> bytes:
    return json.dumps(
        {"id": "evt_test", "object": "event", "type": etype, "data": {"object": obj}}
    ).encode()


def _post_event(client, payload: bytes):
    return client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": _sign(payload)}
    )


def _activate_org(client, monkeypatch, org_id, seats):
    """Drive a signed subscription.created event that activates the org with ``seats`` seats."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    payload = _event(
        "customer.subscription.created",
        {
            "id": f"sub_{org_id[:6]}",
            "customer": f"cus_{org_id[:6]}",
            "status": "active",
            "metadata": {"org_id": org_id, "plan": "team_annual"},
            "items": {"data": [{"quantity": seats}]},
        },
    )
    r = _post_event(client, payload)
    assert r.status_code == 200, r.text


# --------------------------------------------------------------------------- org creation
def test_create_org_and_get(client):
    _, token = _register(client, "owner@example.com")
    r = client.post("/api/org", json={"name": "Bootcamp X"}, headers=_auth(token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Bootcamp X"
    assert body["is_owner"] is True
    assert body["active"] is False
    assert body["seats_purchased"] == 0
    assert body["seats_used"] == 0

    got = client.get("/api/org", headers=_auth(token))
    assert got.status_code == 200
    assert got.json()["organization"]["id"] == body["id"]


def test_one_owned_org_per_user(client):
    _, token = _register(client, "owner2@example.com")
    assert client.post("/api/org", json={"name": "Team A"}, headers=_auth(token)).status_code == 200
    dup = client.post("/api/org", json={"name": "Team B"}, headers=_auth(token))
    assert dup.status_code == 409


def test_get_org_none_when_no_org(client):
    _, token = _register(client, "solo@example.com")
    r = client.get("/api/org", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["organization"] is None


# --------------------------------------------------------------------------- seat checkout
def test_org_checkout_refuses_honestly_when_unconfigured(client, monkeypatch, db_session):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    _, token = _register(client, "o3@example.com")
    client.post("/api/org", json={"name": "Team C"}, headers=_auth(token))
    r = client.post(
        "/api/org/checkout", json={"plan": "team_annual", "seats": 10}, headers=_auth(token)
    )
    assert r.status_code == 503
    # No org was activated, no charge.
    org = db_session.query(Organization).first()
    assert org.status is None and (org.seats_purchased or 0) == 0


def test_org_checkout_requires_an_org_first(client, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    _, token = _register(client, "noorg@example.com")
    r = client.post(
        "/api/org/checkout", json={"plan": "team_annual", "seats": 5}, headers=_auth(token)
    )
    assert r.status_code == 404


def test_org_checkout_makes_real_quantity_stripe_call(client, monkeypatch):
    import stripe

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_TEAM_ANNUAL", "price_team_123")
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(url="https://checkout.stripe.test/team_abc")

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(fake_create))

    owner_id, token = _register(client, "o4@example.com")
    org = client.post("/api/org", json={"name": "Team D"}, headers=_auth(token)).json()
    r = client.post(
        "/api/org/checkout", json={"plan": "team_annual", "seats": 25}, headers=_auth(token)
    )
    assert r.status_code == 200, r.text
    assert r.json()["url"] == "https://checkout.stripe.test/team_abc"
    assert captured["mode"] == "subscription"
    assert captured["line_items"][0]["price"] == "price_team_123"
    assert captured["line_items"][0]["quantity"] == 25  # QUANTITY-based (seats)
    assert captured["metadata"]["org_id"] == org["id"]
    assert captured["metadata"]["seats"] == "25"


def test_org_checkout_seat_bounds_enforced(client, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    _, token = _register(client, "o5@example.com")
    client.post("/api/org", json={"name": "Team E"}, headers=_auth(token))
    # 0 and 9999 are outside [MIN_SEATS, MAX_SEATS] -> 422 (Pydantic bound).
    assert client.post(
        "/api/org/checkout", json={"plan": "team_annual", "seats": 0}, headers=_auth(token)
    ).status_code == 422
    assert client.post(
        "/api/org/checkout", json={"plan": "team_annual", "seats": 9999}, headers=_auth(token)
    ).status_code == 422


# --------------------------------------------------------------------------- webhook activation
def test_signed_subscription_event_activates_seats(client, monkeypatch, db_session):
    _, token = _register(client, "o6@example.com")
    org = client.post("/api/org", json={"name": "Team F"}, headers=_auth(token)).json()
    _activate_org(client, monkeypatch, org["id"], seats=5)

    db_session.expire_all()
    row = db_session.query(Organization).filter(Organization.id == org["id"]).first()
    assert row.status == "active"
    assert row.seats_purchased == 5
    assert row.stripe_subscription_id is not None


def test_async_payment_persists_ids_and_activates_even_if_later_metadata_is_dropped(
    client, monkeypatch, db_session
):
    """Async (bank transfer/SEPA) org checkout: the UNPAID completion grants nothing but must
    persist the customer/subscription ids so the org can still activate from the later
    ``customer.subscription.*`` event even if THAT event's ``org_id`` metadata is dropped.

    Without persisting the ids on the unpaid completion, the only map back to the org is the
    stamped metadata; if Stripe drops it on the activation event the org would never activate —
    a paying customer charged with zero usable seats, stuck forever. This pins the defense.
    """
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    _, token = _register(client, "async@example.com")
    org = client.post("/api/org", json={"name": "Team Async"}, headers=_auth(token)).json()

    # 1) Async payment completes UNPAID: ids persisted, but NO grant yet.
    unpaid = _event(
        "checkout.session.completed",
        {
            "metadata": {"org_id": org["id"], "plan": "team_annual", "seats": "3"},
            "customer": "cus_async1",
            "subscription": "sub_async1",
            "payment_status": "unpaid",
        },
    )
    assert _post_event(client, unpaid).status_code == 200
    db_session.expire_all()
    row = db_session.query(Organization).filter(Organization.id == org["id"]).first()
    assert row.stripe_customer_id == "cus_async1"
    assert row.stripe_subscription_id == "sub_async1"
    assert row.status != "active" and (row.seats_purchased or 0) == 0  # granted NOTHING yet

    # 2) Payment clears; the activation event arrives with its org_id metadata DROPPED. The org
    #    is still found via the id we stored in step 1, and now activates.
    activate = _event(
        "customer.subscription.created",
        {
            "id": "sub_async1",
            "customer": "cus_async1",
            "status": "active",
            "metadata": {},  # org_id dropped — forces the stored-id fallback
            "items": {"data": [{"quantity": 3}]},
        },
    )
    assert _post_event(client, activate).status_code == 200
    db_session.expire_all()
    row = db_session.query(Organization).filter(Organization.id == org["id"]).first()
    assert row.status == "active"
    assert row.seats_purchased == 3


def test_forged_webhook_grants_no_seats(client, monkeypatch, db_session):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    _, token = _register(client, "o7@example.com")
    org = client.post("/api/org", json={"name": "Team G"}, headers=_auth(token)).json()
    payload = _event(
        "customer.subscription.created",
        {"id": "sub_x", "status": "active", "metadata": {"org_id": org["id"]},
         "items": {"data": [{"quantity": 50}]}},
    )
    # A bad signature -> 400, org untouched.
    r = client.post(
        "/api/billing/webhook", content=payload, headers={"stripe-signature": "t=1,v1=bad"}
    )
    assert r.status_code == 400
    db_session.expire_all()
    row = db_session.query(Organization).filter(Organization.id == org["id"]).first()
    assert row.status is None and (row.seats_purchased or 0) == 0


# --------------------------------------------------------------------------- membership + entitlement
def test_member_gets_premium_only_while_seated_in_active_org(client, monkeypatch, db_session):
    _, otoken = _register(client, "owner8@example.com")
    member_id, _ = _register(client, "member8@example.com")
    org = client.post("/api/org", json={"name": "Team H"}, headers=_auth(otoken)).json()

    # Before activation: cannot assign (no active seats).
    r = client.post("/api/org/members", json={"email": "member8@example.com"}, headers=_auth(otoken))
    assert r.status_code == 400

    _activate_org(client, monkeypatch, org["id"], seats=2)

    r = client.post("/api/org/members", json={"email": "member8@example.com"}, headers=_auth(otoken))
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.PREMIUM

    # Removing the seat drops entitlement back to FREE.
    r = client.delete(f"/api/org/members/{member_id}", headers=_auth(otoken))
    assert r.status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.FREE


def test_cannot_assign_beyond_purchased_seats(client, monkeypatch, db_session):
    _, otoken = _register(client, "owner9@example.com")
    _register(client, "m1@example.com")
    _register(client, "m2@example.com")
    org = client.post("/api/org", json={"name": "Team I"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=1)

    assert client.post(
        "/api/org/members", json={"email": "m1@example.com"}, headers=_auth(otoken)
    ).status_code == 200
    # Second assignment exceeds the 1 purchased seat.
    r = client.post("/api/org/members", json={"email": "m2@example.com"}, headers=_auth(otoken))
    assert r.status_code == 400


def test_assign_unknown_email_404(client, monkeypatch):
    _, otoken = _register(client, "owner10@example.com")
    org = client.post("/api/org", json={"name": "Team J"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=3)
    r = client.post("/api/org/members", json={"email": "ghost@example.com"}, headers=_auth(otoken))
    assert r.status_code == 404


def test_member_cannot_belong_to_two_orgs(client, monkeypatch):
    _, oa = _register(client, "ownerA@example.com")
    _, ob = _register(client, "ownerB@example.com")
    _register(client, "shared@example.com")
    orga = client.post("/api/org", json={"name": "Team A"}, headers=_auth(oa)).json()
    orgb = client.post("/api/org", json={"name": "Team B"}, headers=_auth(ob)).json()
    _activate_org(client, monkeypatch, orga["id"], seats=2)
    _activate_org(client, monkeypatch, orgb["id"], seats=2)
    assert client.post(
        "/api/org/members", json={"email": "shared@example.com"}, headers=_auth(oa)
    ).status_code == 200
    r = client.post("/api/org/members", json={"email": "shared@example.com"}, headers=_auth(ob))
    assert r.status_code == 409


def test_only_owner_can_manage_seats(client, monkeypatch):
    _, otoken = _register(client, "owner11@example.com")
    _, mtoken = _register(client, "member11@example.com")
    org = client.post("/api/org", json={"name": "Team K"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=3)
    client.post("/api/org/members", json={"email": "member11@example.com"}, headers=_auth(otoken))
    # The member is not an owner -> owned_org(None) -> 404 on manage endpoints.
    assert client.post(
        "/api/org/members", json={"email": "member11@example.com"}, headers=_auth(mtoken)
    ).status_code == 404
    assert client.post(
        "/api/org/checkout", json={"plan": "team_annual", "seats": 5}, headers=_auth(mtoken)
    ).status_code == 404


def test_member_sees_summary_not_roster(client, monkeypatch):
    _, otoken = _register(client, "owner12@example.com")
    _, mtoken = _register(client, "member12@example.com")
    org = client.post("/api/org", json={"name": "Team L"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=3)
    client.post("/api/org/members", json={"email": "member12@example.com"}, headers=_auth(otoken))
    got = client.get("/api/org", headers=_auth(mtoken)).json()["organization"]
    assert got["is_owner"] is False
    assert "members" not in got  # a member never sees the roster (tenant/priv isolation)


# --------------------------------------------------------------------------- dual-grant + downgrade
def test_canceling_org_does_not_strip_individual_premium(client, monkeypatch, db_session):
    """A user with BOTH an org seat and an individual sub keeps PREMIUM when the ORG cancels."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    _, otoken = _register(client, "owner13@example.com")
    member_id, _ = _register(client, "member13@example.com")
    org = client.post("/api/org", json={"name": "Team M"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=2)
    client.post("/api/org/members", json={"email": "member13@example.com"}, headers=_auth(otoken))

    # Give the member their OWN active individual subscription too.
    ind = _event(
        "checkout.session.completed",
        {"id": "cs_m13", "client_reference_id": member_id, "customer": "cus_m13",
         "subscription": "sub_m13", "payment_status": "paid",
         "metadata": {"user_id": member_id, "plan": "pro_annual"}},
    )
    assert _post_event(client, ind).status_code == 200

    # Cancel the ORG subscription.
    cancel = _event(
        "customer.subscription.deleted",
        {"id": f"sub_{org['id'][:6]}", "metadata": {"org_id": org["id"]}},
    )
    assert _post_event(client, cancel).status_code == 200

    db_session.expire_all()
    # Org is canceled, but the member keeps PREMIUM from their individual sub.
    assert db_session.query(Organization).filter(
        Organization.id == org["id"]
    ).first().status == "canceled"
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.PREMIUM


def test_org_seat_removal_does_not_strip_mobile_subscriber(client, monkeypatch, db_session):
    """Regression (3rd reviewer finding): a MOBILE (RevenueCat) subscriber who also holds an org
    seat must KEEP Premium when the seat is removed — mobile is a first-class entitlement source
    reconciled by recompute_user_tier, not clobbered by an org-seat change."""
    _, otoken = _register(client, "owner18@example.com")
    member_id, mtoken = _register(client, "member18@example.com")

    # 1) The member has an active mobile subscription (verified RevenueCat webhook).
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", "rc_secret")
    grant = {"event": {"type": "INITIAL_PURCHASE", "app_user_id": member_id}}
    r = client.post(
        "/api/billing/revenuecat-webhook", json=grant, headers={"Authorization": "rc_secret"}
    )
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.PREMIUM

    # 2) They also join an org seat, then the owner removes it.
    org = client.post("/api/org", json={"name": "Team R"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=2)
    client.post("/api/org/members", json={"email": "member18@example.com"}, headers=_auth(otoken))
    assert client.delete(f"/api/org/members/{member_id}", headers=_auth(otoken)).status_code == 200

    # 3) The seat is gone but the MOBILE subscription still grants Premium (not stripped to FREE).
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.PREMIUM

    # And a verified mobile EXPIRATION now correctly drops them (no other source).
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", "rc_secret")
    expire = {"event": {"type": "EXPIRATION", "app_user_id": member_id}}
    assert client.post(
        "/api/billing/revenuecat-webhook", json=expire, headers={"Authorization": "rc_secret"}
    ).status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.FREE


def test_member_removal_preserves_individual_subscription(client, monkeypatch, db_session):
    """A member who ALSO holds their own individual Stripe sub keeps PREMIUM when the owner
    removes them from the org seat. This is the REMOVAL path with an individual sub — distinct
    from the org-CANCEL + individual regression (above) and the seat-removal + MOBILE regression
    (above). Guards recompute_user_tier on the DELETE /api/org/members endpoint so a refactor
    can't silently strip a paying individual subscriber when their org seat changes."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    _, otoken = _register(client, "owner-rm-ind@example.com")
    member_id, _ = _register(client, "member-rm-ind@example.com")
    org = client.post("/api/org", json={"name": "Team RmInd"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=2)
    client.post("/api/org/members", json={"email": "member-rm-ind@example.com"}, headers=_auth(otoken))

    # The member also buys their OWN individual subscription.
    ind = _event(
        "checkout.session.completed",
        {"id": "cs_rmind", "client_reference_id": member_id, "customer": "cus_rmind",
         "subscription": "sub_rmind", "payment_status": "paid",
         "metadata": {"user_id": member_id, "plan": "pro_annual"}},
    )
    assert _post_event(client, ind).status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.PREMIUM

    # Owner removes them from the org seat.
    assert client.delete(f"/api/org/members/{member_id}", headers=_auth(otoken)).status_code == 200

    db_session.expire_all()
    # Seat gone, but the individual sub still grants PREMIUM (not stripped to FREE).
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.PREMIUM


def test_remove_nonmember_returns_404(client, monkeypatch):
    """Removing a user who is not an active member of the owner's org returns a truthful 404 —
    the remove_member() -> False -> 404 branch, previously exercised only on the success path.
    Pins the honest error so a refactor of the None check can't silently 200 a no-op removal."""
    _, otoken = _register(client, "owner-rm-404@example.com")
    nonmember_id, _ = _register(client, "nonmember-rm-404@example.com")
    org = client.post("/api/org", json={"name": "Team Rm404"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=2)
    r = client.delete(f"/api/org/members/{nonmember_id}", headers=_auth(otoken))
    assert r.status_code == 404
    assert "isn't an active member" in r.json()["detail"]


def test_canceling_individual_sub_does_not_strip_mobile_subscriber(client, monkeypatch, db_session):
    """Regression: the {individual Stripe sub + mobile RevenueCat} pair, NO org.

    Completes the entitlement-reconciliation matrix — the other two pairs, {org, individual} and
    {org, mobile}, are covered by the two tests above. A user who pays BOTH individually (Stripe)
    AND on mobile (RevenueCat) must KEEP Premium when EITHER source ends, because
    ``recompute_user_tier`` ORs all three verified sources. Critically this uses the Stripe
    ``customer.subscription.deleted`` webhook (``billing.apply_event`` -> ``recompute_user_tier``)
    as the trigger with the MOBILE entitlement as the SURVIVING source — a path neither sibling
    test hits, so a regression that made the Stripe-cancel branch flip ``tier -> FREE`` directly
    (instead of reconciling through all sources) would silently strip a paying mobile subscriber.
    """
    user_id, _ = _register(client, "dualpay@example.com")

    # 1) Active mobile subscription (verified RevenueCat webhook) -> PREMIUM.
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", "rc_secret")
    grant = {"event": {"type": "INITIAL_PURCHASE", "app_user_id": user_id}}
    assert client.post(
        "/api/billing/revenuecat-webhook", json=grant, headers={"Authorization": "rc_secret"}
    ).status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.PREMIUM

    # 2) They ALSO buy an individual Stripe subscription -> still PREMIUM (two live sources).
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    buy = _event(
        "checkout.session.completed",
        {"id": "cs_dual", "client_reference_id": user_id, "customer": "cus_dual",
         "subscription": "sub_dual", "payment_status": "paid",
         "metadata": {"user_id": user_id, "plan": "pro_annual"}},
    )
    assert _post_event(client, buy).status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.PREMIUM

    # 3) Cancel the INDIVIDUAL Stripe sub -> STAY PREMIUM: the mobile entitlement still grants it.
    #    This is the reconciliation path neither sibling test exercises.
    cancel = _event(
        "customer.subscription.deleted",
        {"id": "sub_dual", "customer": "cus_dual", "metadata": {"user_id": user_id}},
    )
    assert _post_event(client, cancel).status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.PREMIUM

    # 4) The mobile entitlement now EXPIRES too -> FREE (no verified source remains).
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", "rc_secret")
    expire = {"event": {"type": "EXPIRATION", "app_user_id": user_id}}
    assert client.post(
        "/api/billing/revenuecat-webhook", json=expire, headers={"Authorization": "rc_secret"}
    ).status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == user_id).first().tier == UserTier.FREE


def test_webhook_seat_reduction_frees_newest_members(client, monkeypatch, db_session):
    """A seat DOWNGRADE re-enforces the cap: oldest members keep seats, newest lose them."""
    _, otoken = _register(client, "owner14@example.com")
    m1, _ = _register(client, "m14a@example.com")
    m2, _ = _register(client, "m14b@example.com")
    org = client.post("/api/org", json={"name": "Team N"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=2)
    client.post("/api/org/members", json={"email": "m14a@example.com"}, headers=_auth(otoken))
    client.post("/api/org/members", json={"email": "m14b@example.com"}, headers=_auth(otoken))
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == m1).first().tier == UserTier.PREMIUM
    assert db_session.query(User).filter(User.id == m2).first().tier == UserTier.PREMIUM

    # Downgrade to 1 seat via a signed subscription.updated.
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    payload = _event(
        "customer.subscription.updated",
        {"id": f"sub_{org['id'][:6]}", "customer": f"cus_{org['id'][:6]}", "status": "active",
         "metadata": {"org_id": org["id"], "plan": "team_annual"},
         "items": {"data": [{"quantity": 1}]}},
    )
    assert _post_event(client, payload).status_code == 200
    db_session.expire_all()
    # The FIRST-added member keeps the seat; the newest is freed.
    assert db_session.query(User).filter(User.id == m1).first().tier == UserTier.PREMIUM
    assert db_session.query(User).filter(User.id == m2).first().tier == UserTier.FREE
    assert db_session.query(Organization).filter(
        Organization.id == org["id"]
    ).first().seats_purchased == 1


def test_webhook_update_without_line_items_preserves_seats(client, monkeypatch, db_session):
    """A benign subscription.updated that carries NO line items must NOT clobber seats.

    Stripe sends `customer.subscription.updated` for many reasons (a metadata edit, a payment-
    method change, a status refresh) and such an event may omit `items.data`. `_seat_quantity`
    returns None then, and `apply_event` must LEAVE `seats_purchased` untouched — a regression
    that unconditionally wrote `max(qty or 0, 0)` would silently zero the org's paid seats and
    strip every member's entitlement off a no-op event. This pins that protection.
    """
    _, otoken = _register(client, "owner-noitems@example.com")
    member_id, _ = _register(client, "member-noitems@example.com")
    org = client.post("/api/org", json={"name": "Team NoItems"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=3)
    client.post("/api/org/members", json={"email": "member-noitems@example.com"}, headers=_auth(otoken))
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.PREMIUM

    # subscription.updated with an EMPTY items list (no quantity) — e.g. a metadata-only change.
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    payload = _event(
        "customer.subscription.updated",
        {"id": f"sub_{org['id'][:6]}", "customer": f"cus_{org['id'][:6]}", "status": "active",
         "metadata": {"org_id": org["id"], "plan": "team_annual"},
         "items": {"data": []}},
    )
    assert _post_event(client, payload).status_code == 200
    db_session.expire_all()
    # Seats survive the itemless event; the member keeps their entitlement.
    assert db_session.query(Organization).filter(
        Organization.id == org["id"]
    ).first().seats_purchased == 3
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.PREMIUM


def test_seat_quantity_none_when_items_missing_or_malformed():
    """`_seat_quantity` returns None (not 0 / not a raise) for the payload shapes a real event
    can take when it carries no usable quantity — the guard the test above depends on."""
    from src.org_billing import _seat_quantity

    assert _seat_quantity({}) is None                       # no items key
    assert _seat_quantity({"items": {}}) is None            # items present, no data
    assert _seat_quantity({"items": {"data": []}}) is None  # empty data
    assert _seat_quantity({"items": {"data": [{}]}}) is None  # item present, no quantity
    assert _seat_quantity({"items": {"data": [{"quantity": 7}]}}) == 7  # the happy path still works


# --------------------------------------------------------------------------- account-deletion purge
def test_deleting_owner_purges_org_and_drops_members(client, monkeypatch, db_session):
    _, otoken = _register(client, "owner15@example.com")
    member_id, _ = _register(client, "member15@example.com")
    org = client.post("/api/org", json={"name": "Team O"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=2)
    client.post("/api/org/members", json={"email": "member15@example.com"}, headers=_auth(otoken))
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.PREMIUM

    # Owner deletes their account -> org gone, member row gone, member dropped to FREE.
    assert client.delete("/api/auth/me", headers=_auth(otoken)).status_code == 200
    db_session.expire_all()
    assert db_session.query(Organization).filter(Organization.id == org["id"]).first() is None
    assert db_session.query(OrganizationMember).count() == 0
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.FREE


def test_org_pro_seat_does_not_unlock_careerplus_via_stale_plan(client, monkeypatch, db_session):
    """Regression: a former individual Career+ subscriber (canceled -> stale plan row) who later
    occupies a TEAM Pro seat must get Pro, NOT Career+. Before the fix, ``current_plan_level``
    derived Career+ from the stale non-None ``Subscription.plan`` once the org seat re-flipped
    ``tier`` to PREMIUM — a paywall bypass. A team seat grants Pro only."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    _, otoken = _register(client, "owner17@example.com")
    member_id, mtoken = _register(client, "member17@example.com")

    # 1) Member buys individual Career+ then cancels -> canceled row with stale careerplus plan.
    buy = _event(
        "checkout.session.completed",
        {"id": "cs_m17", "client_reference_id": member_id, "customer": "cus_m17",
         "subscription": "sub_m17", "payment_status": "paid",
         "metadata": {"user_id": member_id, "plan": "careerplus_monthly"}},
    )
    assert _post_event(client, buy).status_code == 200
    cancel = _event(
        "customer.subscription.deleted",
        {"id": "sub_m17", "customer": "cus_m17", "metadata": {"user_id": member_id}},
    )
    assert _post_event(client, cancel).status_code == 200
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.FREE

    # 2) They join an org on a PRO seat -> PREMIUM again, but only Pro-level entitlement.
    org = client.post("/api/org", json={"name": "Team Q"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=2)
    client.post("/api/org/members", json={"email": "member17@example.com"}, headers=_auth(otoken))
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == member_id).first().tier == UserTier.PREMIUM

    # The Career+-exclusive salary-negotiation tool stays gated (403), never unlocked for free.
    r = client.post(
        "/api/prep/salary-negotiation",
        json={"job_id": "nonexistent", "target_salary": 100000},
        headers=_auth(mtoken),
    )
    assert r.status_code == 403, r.text  # Career+ gate blocks BEFORE any job/consent/LLM step
    # /api/auth/me reports the honest level = pro, not career_plus.
    me = client.get("/api/auth/me", headers=_auth(mtoken)).json()["user"]
    assert me["plan_level"] == "pro"
    assert me["career_plus"] is False


def test_deleting_member_frees_their_seat(client, monkeypatch, db_session):
    _, otoken = _register(client, "owner16@example.com")
    member_id, mtoken = _register(client, "member16@example.com")
    org = client.post("/api/org", json={"name": "Team P"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=2)
    client.post("/api/org/members", json={"email": "member16@example.com"}, headers=_auth(otoken))

    assert client.delete("/api/auth/me", headers=_auth(mtoken)).status_code == 200
    db_session.expire_all()
    assert db_session.query(OrganizationMember).count() == 0
    # The org survives (owner still there); the freed seat is reflected.
    org_row = db_session.query(Organization).filter(Organization.id == org["id"]).first()
    assert org_row is not None
    got = client.get("/api/org", headers=_auth(otoken)).json()["organization"]
    assert got["seats_used"] == 0


# --- price_id_for_org_plan: the seat-tier (highest-ARPA lever) price resolver ------------------
# Cheap deterministic guards on the two error branches. A typo in a new plan's env-var name, or
# a forgotten STRIPE_PRICE_* in the deploy env, must be caught HERE — not silently at webhook
# time after the customer has already clicked "buy seats".

def test_price_id_for_org_plan_returns_configured_price(monkeypatch):
    from src.org_billing import price_id_for_org_plan

    monkeypatch.setenv("STRIPE_PRICE_TEAM_ANNUAL", "price_team_annual_123")
    assert price_id_for_org_plan("team_annual") == "price_team_annual_123"


def test_price_id_for_org_plan_unknown_plan_raises(monkeypatch):
    from src.org_billing import price_id_for_org_plan, UnknownPlan
    import pytest

    with pytest.raises(UnknownPlan):
        price_id_for_org_plan("no_such_plan")


def test_price_id_for_org_plan_unconfigured_price_raises(monkeypatch):
    # A KNOWN plan whose price env var is unset must fail loud (BillingNotConfigured), never
    # return an empty/None price that would produce a broken Stripe checkout.
    from src.org_billing import price_id_for_org_plan, BillingNotConfigured
    import pytest

    monkeypatch.delenv("STRIPE_PRICE_TEAM_ANNUAL", raising=False)
    with pytest.raises(BillingNotConfigured):
        price_id_for_org_plan("team_annual")
