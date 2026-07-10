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
