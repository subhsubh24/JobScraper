"""Referral invite loop (Track G/H — the lowest-CAC growth lever).

Each user gets a unique ``referral_code``; sharing it and having a NEW user sign up with it
grants BOTH sides a real reward — extra free-tier prep packs (``users.bonus_prep_packs``).

Honesty / safety rules baked in (FACTORY_STANDARD §6 + §12):
- The reward is granted immediately and is REAL (it raises the user's actual free-tier prep
  allowance via ``AuthService.check_usage_limits``). We never promise a reward against an
  unbuilt billing grant, so the flow can't dead-end (DECISION COROLLARY).
- An unknown/blank/self code is a silent no-op — a bad referral code NEVER fails signup.
- ``referred_id`` is unique, so a user is attributed to at most one referrer (idempotent).
- The bonus is CAPPED so fake-signup farming can't drain unlimited free generations; CAPTCHA
  on public forms (Track F) is the stronger defense and is tracked separately.
"""
import secrets
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models import Referral, User

CODE_LENGTH = 8
# Prep packs granted to EACH side of a successful referral.
REFERRAL_BONUS_PREP_PACKS = 1
# Hard cap on accumulated bonus per user — bounds abuse from farmed signups.
MAX_BONUS_PREP_PACKS = 10


def generate_code() -> str:
    """A short, URL-safe, hard-to-guess referral code."""
    return secrets.token_urlsafe(6)[:CODE_LENGTH]


def ensure_code(db: Session, user: User) -> str:
    """Return the user's referral code, generating a unique one on first use.

    Resilient to the (astronomically rare) TOCTOU race where two concurrent signups pick the
    same candidate: the flush runs inside a SAVEPOINT so a unique-constraint IntegrityError
    rolls back ONLY that attempt (not the surrounding transaction) and we retry.
    """
    if user.referral_code:
        return user.referral_code
    for _ in range(8):
        candidate = generate_code()
        if db.query(User).filter(User.referral_code == candidate).first():
            continue
        user.referral_code = candidate
        try:
            with db.begin_nested():
                db.flush()
            break
        except IntegrityError:
            user.referral_code = None  # lost the race — pick another and retry
    return user.referral_code


def _grant_bonus(user: User, amount: int) -> None:
    current = user.bonus_prep_packs or 0
    user.bonus_prep_packs = min(MAX_BONUS_PREP_PACKS, current + amount)


def apply_referral(db: Session, code: Optional[str], new_user: User) -> bool:
    """Attribute ``new_user`` to the owner of ``code`` and reward both sides.

    Returns True only when a NEW referral was recorded. Unknown/blank/self codes and a
    user who was already referred are silent no-ops (never raises — must not break signup).
    """
    if not code:
        return False
    code = code.strip()
    if not code:
        return False

    referrer = db.query(User).filter(User.referral_code == code).first()
    if not referrer or referrer.id == new_user.id:
        return False

    # One attribution per referred user (referred_id is unique; guard here too so we never
    # double-grant or hit an IntegrityError on a re-run).
    already = db.query(Referral).filter(Referral.referred_id == new_user.id).first()
    if already:
        return False

    db.add(Referral(referrer_id=referrer.id, referred_id=new_user.id, code=code))
    _grant_bonus(referrer, REFERRAL_BONUS_PREP_PACKS)
    _grant_bonus(new_user, REFERRAL_BONUS_PREP_PACKS)
    db.flush()
    return True


def referral_stats(db: Session, user: User) -> dict:
    """Public referral state for the owner: their code, count, and earned bonus."""
    code = ensure_code(db, user)
    total = db.query(Referral).filter(Referral.referrer_id == user.id).count()
    return {
        "code": code,
        "total_referred": total,
        "bonus_prep_packs": user.bonus_prep_packs or 0,
    }


def purge_user_referrals(db: Session, user: User) -> None:
    """Remove referral rows referencing this user (account-deletion cascade helper).

    The FK columns have no ORM relationship/cascade, so account deletion must clear these
    explicitly or a Postgres FK constraint would block it.
    """
    db.query(Referral).filter(
        (Referral.referrer_id == user.id) | (Referral.referred_id == user.id)
    ).delete(synchronize_session=False)
