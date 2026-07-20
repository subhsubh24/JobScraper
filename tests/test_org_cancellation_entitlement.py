"""Coverage gap: org cancellation with no backup entitlement sources.

This test verifies the critical path where an organization's Stripe subscription is canceled
and members who lack other entitlement sources (individual Stripe sub, mobile RevenueCat) are
correctly demoted to FREE tier. This is a correctness invariant: members should lose PREMIUM
when their ONLY source of entitlement (org seat) disappears.

The gap: test_org_billing.py covers org cancellation with a backup (individual sub), but does
NOT cover the case where an org member has ONLY the org seat and no other sources.
"""
import hashlib
import hmac
import json
import time

from src.db.models import User, UserTier


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


def test_canceling_org_drops_member_to_free_when_no_backup_sources(client, monkeypatch, db_session):
    """COVERAGE GAP: An org member with ONLY a seat (no individual sub, no mobile entitlement)
    drops to FREE when the org subscription is canceled.

    This is the critical entitlement-reconciliation correctness invariant: if a user's ONLY
    PREMIUM source vanishes (org status becomes "canceled"), they must lose PREMIUM immediately.
    A sibling test covers the case where the member HAS a backup (individual sub) and correctly
    stays PREMIUM. This test covers the case with NO backup — the regression that would be caught:
    - Removing the _recompute_all_member_tiers call on org cancellation
    - Breaking the _has_active_org_seat check to not verify Organization.status
    - Failing to call recompute_user_tier on all affected members
    """
    _, otoken = _register(client, "owner-cancel-solo@example.com")
    member_id, _ = _register(client, "member-cancel-solo@example.com")

    # Create and activate an org with the member
    org = client.post("/api/org", json={"name": "Team CancelSolo"}, headers=_auth(otoken)).json()
    _activate_org(client, monkeypatch, org["id"], seats=2)
    r = client.post(
        "/api/org/members",
        json={"email": "member-cancel-solo@example.com"},
        headers=_auth(otoken),
    )
    assert r.status_code == 200, r.text

    db_session.expire_all()
    # Baseline: member is PREMIUM because of the org seat
    member = db_session.query(User).filter(User.id == member_id).first()
    assert member.tier == UserTier.PREMIUM, "Member should be PREMIUM from org seat"

    # Cancel the ORG subscription (the member's ONLY source of entitlement)
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WHSEC)
    cancel_payload = _event(
        "customer.subscription.deleted",
        {
            "id": f"sub_{org['id'][:6]}",
            "metadata": {"org_id": org["id"]},
        },
    )
    r = _post_event(client, cancel_payload)
    assert r.status_code == 200, r.text

    db_session.expire_all()
    # After org cancellation, member should drop to FREE (no backup sources)
    member = db_session.query(User).filter(User.id == member_id).first()
    assert (
        member.tier == UserTier.FREE
    ), (
        "Member should drop to FREE when org cancels and no backup sources exist. "
        "If this fails, the _recompute_all_member_tiers call may be missing on org deletion, "
        "or recompute_user_tier may not correctly check Organization.status."
    )
