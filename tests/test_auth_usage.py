"""Coverage for AuthService.check_usage_limits — the free-tier metering + monthly reset.

This path gates a paid feature (free tier = 5 jobs, 1 prep pack/month). A regression here is
a real revenue/UX bug: it either locks free users out early or hands out unlimited free usage.
The monthly reset (counters zeroed once 30+ days pass since the last reset) was untested.
"""
from datetime import datetime, timedelta

from src.auth.auth_service import AuthService
from src.db.models import User, UserTier


def _free_user(db, **kw) -> User:
    user = User(email=kw.get("email", "usage@example.com"), password_hash="x",
                tier=UserTier.FREE)
    for k, v in kw.items():
        setattr(user, k, v)
    db.add(user)
    db.flush()
    return user


def test_monthly_usage_resets_after_30_days(db_session):
    auth = AuthService(db_session)
    stale = datetime.utcnow() - timedelta(days=31)
    user = _free_user(db_session, jobs_added_this_month=5, prep_packs_this_month=1,
                      usage_reset_date=stale)

    limits = auth.check_usage_limits(user)

    # Counters were zeroed and the reset date moved forward to ~now.
    assert user.jobs_added_this_month == 0
    assert user.prep_packs_this_month == 0
    assert (datetime.utcnow() - user.usage_reset_date) < timedelta(minutes=1)
    # And the freshly-reset month grants the full free allowance again.
    assert limits["can_add_job"] is True
    assert limits["can_generate_prep"] is True
    assert limits["jobs_remaining"] == 5
    assert limits["prep_packs_remaining"] == 1


def test_usage_not_reset_within_the_window(db_session):
    auth = AuthService(db_session)
    recent = datetime.utcnow() - timedelta(days=10)
    user = _free_user(db_session, email="usage2@example.com",
                      jobs_added_this_month=5, prep_packs_this_month=1,
                      usage_reset_date=recent)

    limits = auth.check_usage_limits(user)

    # Inside the 30-day window the counters are NOT reset — the limit is exhausted.
    assert user.jobs_added_this_month == 5
    assert limits["can_add_job"] is False
    assert limits["can_generate_prep"] is False
    assert limits["jobs_remaining"] == 0
    assert limits["prep_packs_remaining"] == 0


def test_referral_bonus_raises_the_prep_allowance(db_session):
    auth = AuthService(db_session)
    user = _free_user(db_session, email="usage3@example.com",
                      prep_packs_this_month=1, bonus_prep_packs=2)

    limits = auth.check_usage_limits(user)

    # 1 base + 2 earned bonus = 3 allowed; 1 used -> 2 remaining, still generating.
    assert limits["can_generate_prep"] is True
    assert limits["prep_packs_remaining"] == 2


def test_premium_user_is_unlimited(db_session):
    auth = AuthService(db_session)
    user = _free_user(db_session, email="usage4@example.com", tier=UserTier.PREMIUM,
                      jobs_added_this_month=999, prep_packs_this_month=999)

    limits = auth.check_usage_limits(user)

    assert limits["can_add_job"] is True
    assert limits["can_generate_prep"] is True
    assert limits["jobs_remaining"] == "unlimited"
    assert limits["prep_packs_remaining"] == "unlimited"
