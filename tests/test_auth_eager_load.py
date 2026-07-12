"""The auth token-resolution path eager-loads the one-to-one subscription (perf, hot path).

Every authenticated request resolves its bearer token through
``AuthService.get_user_from_token`` and then serializes the user via ``user_public``
(asgi.py), which reads ``user.subscription`` to derive the plan level. If the subscription
is lazy, that read is a +1 query on the single hottest path (every app launch / session
restore). This asserts it is eager-loaded, so the extra round-trip is gone — and is
load-bearing: dropping the ``joinedload`` puts ``subscription`` back in ``unloaded`` and
reddens the test.
"""
from sqlalchemy import inspect as sa_inspect

from src.auth.auth_service import AuthService
from src.db.models import Subscription


def test_get_user_from_token_eager_loads_subscription(client, db_session):
    r = client.post("/api/auth/register", json={"email": "eager@t.co", "password": "hunter2pw"})
    assert r.status_code == 200, r.text
    uid = r.json()["user"]["id"]
    token = r.json()["token"]

    db_session.add(
        Subscription(
            user_id=uid,
            plan="pro_annual",
            status="active",
            stripe_customer_id="cus_x",
            stripe_subscription_id="sub_x",
        )
    )
    db_session.commit()

    user = AuthService(db_session).get_user_from_token(token)
    assert user is not None and user.id == uid

    unloaded = sa_inspect(user).unloaded
    assert "subscription" not in unloaded, (
        "user.subscription must be eager-loaded on the auth path (joinedload); it is lazy — "
        f"unloaded={sorted(unloaded)}"
    )
    # The eager load returned the real related row (no second query needed downstream).
    assert user.subscription is not None
    assert user.subscription.plan == "pro_annual"
