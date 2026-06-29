"""Track C (mobile RevenueCat IAP) server-side entitlement guards.

These prove SIDE-EFFECT INTEGRITY for the mobile billing path, mirroring the Stripe webhook
guards: a mobile user becomes Premium ONLY from a webhook whose shared-secret Authorization
header we verify; a forged / missing / unconfigured secret grants NOTHING. The effect
(user.tier flip) is asserted directly on the DB, never inferred from a 200.
"""
import json

from src.db.models import User, UserTier
from src.mobile_billing import apply_event

RC_SECRET = "rc_webhook_shared_secret_test"


def _register(client, email="mobilebuyer@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], r.json()["token"]


def _rc_body(etype: str, app_user_id: str, **extra) -> bytes:
    event = {"type": etype, "app_user_id": app_user_id, "id": "evt_rc_test"}
    event.update(extra)
    return json.dumps({"event": event, "api_version": "1.0"}).encode()


def _post(client, body: bytes, auth: str = RC_SECRET):
    headers = {"Content-Type": "application/json"}
    if auth is not None:
        headers["Authorization"] = auth
    return client.post("/api/billing/revenuecat-webhook", content=body, headers=headers)


def _tier(db, user_id):
    db.expire_all()
    return db.query(User).filter(User.id == user_id).first().tier


# --------------------------------------------------------------------- auth verification
def test_webhook_unconfigured_returns_503_and_grants_nothing(client, monkeypatch, db_session):
    monkeypatch.delenv("REVENUECAT_WEBHOOK_AUTH", raising=False)
    uid, _ = _register(client)
    r = _post(client, _rc_body("INITIAL_PURCHASE", uid))
    assert r.status_code == 503
    assert _tier(db_session, uid) == UserTier.FREE


def test_webhook_rejects_missing_auth_and_grants_nothing(client, monkeypatch, db_session):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", RC_SECRET)
    uid, _ = _register(client)
    r = _post(client, _rc_body("INITIAL_PURCHASE", uid), auth=None)
    assert r.status_code == 401
    assert _tier(db_session, uid) == UserTier.FREE


def test_webhook_rejects_forged_auth_and_grants_nothing(client, monkeypatch, db_session):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", RC_SECRET)
    uid, _ = _register(client)
    r = _post(client, _rc_body("INITIAL_PURCHASE", uid), auth="wrong-secret")
    assert r.status_code == 401
    assert _tier(db_session, uid) == UserTier.FREE


# --------------------------------------------------------------------- entitlement effect
def test_webhook_grants_premium_on_verified_initial_purchase(client, monkeypatch, db_session):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", RC_SECRET)
    uid, _ = _register(client)
    r = _post(client, _rc_body("INITIAL_PURCHASE", uid, product_id="pro_annual"))
    assert r.status_code == 200
    assert _tier(db_session, uid) == UserTier.PREMIUM


def test_webhook_renewal_keeps_premium(client, monkeypatch, db_session):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", RC_SECRET)
    uid, _ = _register(client)
    _post(client, _rc_body("INITIAL_PURCHASE", uid))
    r = _post(client, _rc_body("RENEWAL", uid))
    assert r.status_code == 200
    assert _tier(db_session, uid) == UserTier.PREMIUM


def test_webhook_expiration_revokes_premium(client, monkeypatch, db_session):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", RC_SECRET)
    uid, _ = _register(client)
    _post(client, _rc_body("INITIAL_PURCHASE", uid))
    assert _tier(db_session, uid) == UserTier.PREMIUM
    r = _post(client, _rc_body("EXPIRATION", uid))
    assert r.status_code == 200
    assert _tier(db_session, uid) == UserTier.FREE


def test_webhook_paused_revokes_premium(client, monkeypatch, db_session):
    # PAUSED (Android): the user surrendered access for the pause window -> revoke.
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", RC_SECRET)
    uid, _ = _register(client)
    _post(client, _rc_body("INITIAL_PURCHASE", uid))
    assert _tier(db_session, uid) == UserTier.PREMIUM
    r = _post(client, _rc_body("PAUSED", uid))
    assert r.status_code == 200
    assert _tier(db_session, uid) == UserTier.FREE


def test_webhook_malformed_json_returns_400_and_grants_nothing(client, monkeypatch, db_session):
    # A valid secret but a non-JSON body must 400 cleanly (no partial commit), never 500.
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", RC_SECRET)
    uid, _ = _register(client)
    r = _post(client, b"not-json-at-all")
    assert r.status_code == 400
    assert _tier(db_session, uid) == UserTier.FREE


def test_webhook_cancellation_does_not_revoke(client, monkeypatch, db_session):
    # CANCELLATION only turns off auto-renew; access lasts until EXPIRATION. Tier must hold.
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", RC_SECRET)
    uid, _ = _register(client)
    _post(client, _rc_body("INITIAL_PURCHASE", uid))
    r = _post(client, _rc_body("CANCELLATION", uid))
    assert r.status_code == 200
    assert _tier(db_session, uid) == UserTier.PREMIUM


def test_webhook_unknown_user_grants_nothing(client, monkeypatch, db_session):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", RC_SECRET)
    uid, _ = _register(client)
    r = _post(client, _rc_body("INITIAL_PURCHASE", "no-such-user-id"))
    assert r.status_code == 200  # acknowledged so RevenueCat stops retrying
    assert _tier(db_session, uid) == UserTier.FREE


def test_webhook_test_event_changes_nothing(client, monkeypatch, db_session):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", RC_SECRET)
    uid, _ = _register(client)
    r = _post(client, _rc_body("TEST", uid))
    assert r.status_code == 200
    assert _tier(db_session, uid) == UserTier.FREE


# --------------------------------------------------------------------- unit: resolver/aliases
def test_apply_event_resolves_user_via_alias(db_session):
    user = User(email="alias@example.com", password_hash="x", tier=UserTier.FREE)
    db_session.add(user)
    db_session.flush()
    payload = {"event": {"type": "RENEWAL", "app_user_id": "anon-123", "aliases": [user.id]}}
    affected = apply_event(payload, db_session)
    assert affected == user.id
    assert user.tier == UserTier.PREMIUM
