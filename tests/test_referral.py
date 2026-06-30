"""Referral invite loop (Track G/H) — attribution, the real bonus reward, and safety.

Asserts the OUTCOME, not just that handlers are wired: a referred signup creates the row,
BOTH sides' free-tier prep allowance actually rises, bad/self/duplicate codes are silent
no-ops, the bonus is capped, and account deletion purges referral rows.
"""
from src import referrals
from src.auth.auth_service import AuthService
from src.db.models import Referral, User


def _register(client, email, ref=None):
    body = {"email": email, "password": "password123"}
    if ref is not None:
        body["referral_code"] = ref
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_new_user_gets_a_referral_code(client):
    token = _register(client, "owner@example.com")["token"]
    r = client.get("/api/referrals/me", headers=_auth(token))
    assert r.status_code == 200
    ref = r.json()["referral"]
    assert ref["code"] and len(ref["code"]) >= 6
    assert ref["total_referred"] == 0
    assert ref["bonus_prep_packs"] == 0


def test_referral_attribution_grants_both_sides_a_real_bonus(client, db_session):
    inviter = _register(client, "inviter@example.com")
    code = client.get("/api/referrals/me", headers=_auth(inviter["token"])).json()["referral"]["code"]

    # New user signs up with the invite code; the response's own prep allowance reflects the
    # real reward (1 free + 1 bonus = 2 remaining) — not a fake "reward sent" message.
    invited = _register(client, "invited@example.com", ref=code)
    assert invited["user"]["prep_packs_remaining"] == 2

    # The inviter's allowance rose too, and the count shows the join.
    inviter_stats = client.get("/api/referrals/me", headers=_auth(inviter["token"])).json()["referral"]
    assert inviter_stats["total_referred"] == 1
    assert inviter_stats["bonus_prep_packs"] == 1

    rows = db_session.query(Referral).all()
    assert len(rows) == 1
    assert rows[0].code == code


def test_unknown_code_is_a_silent_noop_never_blocks_signup(client, db_session):
    invited = _register(client, "nocode@example.com", ref="totally-bogus")
    # Signup still succeeds and the user lands working; no attribution, no bonus.
    assert invited["user"]["prep_packs_remaining"] == 1
    assert db_session.query(Referral).count() == 0


def test_blank_code_is_ignored(client, db_session):
    invited = _register(client, "blank@example.com", ref="   ")
    assert invited["user"]["prep_packs_remaining"] == 1
    assert db_session.query(Referral).count() == 0


def test_self_referral_is_ignored(db_session):
    user = User(email="self@example.com", password_hash="x")
    db_session.add(user)
    db_session.flush()
    referrals.ensure_code(db_session, user)
    # Applying one's OWN code grants nothing.
    assert referrals.apply_referral(db_session, user.referral_code, user) is False
    assert (user.bonus_prep_packs or 0) == 0
    assert db_session.query(Referral).count() == 0


def test_attribution_is_idempotent(db_session):
    inviter = User(email="a@example.com", password_hash="x")
    invited = User(email="b@example.com", password_hash="x")
    db_session.add_all([inviter, invited])
    db_session.flush()
    code = referrals.ensure_code(db_session, inviter)

    assert referrals.apply_referral(db_session, code, invited) is True
    # A second attempt for an already-referred user does nothing (no double-grant).
    assert referrals.apply_referral(db_session, code, invited) is False
    assert inviter.bonus_prep_packs == 1
    assert invited.bonus_prep_packs == 1
    assert db_session.query(Referral).filter(Referral.referred_id == invited.id).count() == 1


def test_bonus_is_capped(db_session):
    user = User(email="cap@example.com", password_hash="x", bonus_prep_packs=0)
    db_session.add(user)
    db_session.flush()
    referrals._grant_bonus(user, referrals.MAX_BONUS_PREP_PACKS + 5)
    assert user.bonus_prep_packs == referrals.MAX_BONUS_PREP_PACKS


def test_referral_bonus_actually_raises_the_free_prep_limit(db_session):
    user = User(email="limit@example.com", password_hash="x", bonus_prep_packs=2)
    db_session.add(user)
    db_session.flush()
    limits = AuthService(db_session).check_usage_limits(user)
    # 1 free + 2 bonus = 3 prep packs available to a free user who earned referrals.
    assert limits["prep_packs_remaining"] == 3
    assert limits["can_generate_prep"] is True


def test_account_deletion_purges_referral_rows(client, db_session):
    inviter = _register(client, "del-inviter@example.com")
    code = client.get("/api/referrals/me", headers=_auth(inviter["token"])).json()["referral"]["code"]
    invited = _register(client, "del-invited@example.com", ref=code)
    assert db_session.query(Referral).count() == 1

    # Deleting the referred user removes the referral row (no orphaned FK).
    r = client.delete("/api/auth/me", headers=_auth(invited["token"]))
    assert r.status_code in (200, 204)
    assert db_session.query(Referral).count() == 0


def test_account_deletion_purges_rows_when_the_inviter_is_deleted(client, db_session):
    inviter = _register(client, "del2-inviter@example.com")
    code = client.get("/api/referrals/me", headers=_auth(inviter["token"])).json()["referral"]["code"]
    _register(client, "del2-invited@example.com", ref=code)
    assert db_session.query(Referral).count() == 1

    # Deleting the INVITER (the other side of the FK) must also clear the row, not leave a
    # dangling referrer_id — guards against a future one-sided purge regression.
    r = client.delete("/api/auth/me", headers=_auth(inviter["token"]))
    assert r.status_code in (200, 204)
    assert db_session.query(Referral).count() == 0


def test_signup_never_breaks_even_if_the_code_assignment_collides(client, db_session, monkeypatch):
    # Force generate_code to always collide with an existing code: signup must STILL succeed
    # (referral is best-effort), the user just may not get a code on this request.
    from src import referrals

    existing = _register(client, "taken@example.com")
    taken_code = client.get(
        "/api/referrals/me", headers=_auth(existing["token"])
    ).json()["referral"]["code"]
    monkeypatch.setattr(referrals, "generate_code", lambda: taken_code)

    r = client.post("/api/auth/register", json={"email": "racer@example.com", "password": "password123"})
    assert r.status_code == 200, r.text  # signup is durable regardless of referral outcome
