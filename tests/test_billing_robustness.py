"""Billing-path robustness — graceful failure on the paid surface (FACTORY_STANDARD §6/§6c).

Two guarantees that keep the money paths honest under adverse RUNTIME conditions (a slow
provider, a concurrent write) rather than only on the happy path:

1. Every Stripe HTTP call is bounded BELOW the serverless function budget (Vercel
   maxDuration=60s). stripe-python's default is 80s — LONGER than the budget — so a slow/hung
   Stripe API would be killed by the platform mid-request (possibly after a charge) with no
   response the caller can surface. A sub-budget timeout makes the call fail LOUD in-request.
   (DEEP_DIAGNOSIS rule (a): every external call needs a timeout shorter than the budget.)

2. A concurrent race that adds the SAME user to two orgs surfaces a clean 409
   (``AlreadyInAnotherOrg``), never a bare ``IntegrityError`` 500 — mirroring the guard
   ``create_org`` already has on its ``owner_id`` race.
"""
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from src import billing, org_billing
from src.db.models import Organization


# --------------------------------------------------------------------------- 1. Stripe timeout

def test_configure_stripe_sets_subbudget_timeout(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    stripe = billing.configure_stripe()
    # The configured client's timeout must be exactly our constant AND strictly below Vercel's
    # 60s function budget — a longer timeout lets the platform kill the function mid-request.
    assert stripe.default_http_client._timeout == billing.STRIPE_HTTP_TIMEOUT_SECONDS
    assert billing.STRIPE_HTTP_TIMEOUT_SECONDS < 60


def test_individual_checkout_routes_through_bounded_client(monkeypatch):
    """The REAL create_checkout_session issues its Stripe call through the bounded client."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_PRO_ANNUAL", "price_pro_annual_x")
    import stripe

    seen = {}

    def _fake_create(**kwargs):
        # Captured AT CALL TIME: proves the default client was bounded before the network call.
        seen["timeout"] = stripe.default_http_client._timeout
        return SimpleNamespace(url="https://checkout.stripe.test/sess")

    monkeypatch.setattr(stripe.checkout.Session, "create", _fake_create)
    user = SimpleNamespace(id="u_1", email="a@b.co")
    url = billing.create_checkout_session(user, "pro_annual", "http://s", "http://c")
    assert url == "https://checkout.stripe.test/sess"
    assert seen["timeout"] == billing.STRIPE_HTTP_TIMEOUT_SECONDS


def test_org_seat_checkout_routes_through_bounded_client(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_TEAM_ANNUAL", "price_team_annual_x")
    import stripe

    seen = {}

    def _fake_create(**kwargs):
        seen["timeout"] = stripe.default_http_client._timeout
        return SimpleNamespace(url="https://checkout.stripe.test/team")

    monkeypatch.setattr(stripe.checkout.Session, "create", _fake_create)
    owner = SimpleNamespace(id="o_1", email="owner@b.co")
    org = SimpleNamespace(id="org_1")
    url = org_billing.create_seat_checkout_session(
        owner, org, "team_annual", 5, "http://s", "http://c"
    )
    assert url == "https://checkout.stripe.test/team"
    assert seen["timeout"] == billing.STRIPE_HTTP_TIMEOUT_SECONDS


# ------------------------------------------------------------- 2. Concurrent add_member -> 409

def _register(client, email):
    r = client.post("/api/auth/register", json={"email": email, "password": "hunter2pw"})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"]


def test_add_member_race_surfaces_409_not_500(client, db_session, monkeypatch):
    """Two concurrent adds of the SAME user both pass the app-level ``existing`` check (both see
    None), then the second INSERT violates UNIQUE(user_id). add_member must convert that
    IntegrityError into ``AlreadyInAnotherOrg`` (endpoint-mapped to 409), never a bare 500.

    The race is simulated deterministically: the member-insert ``flush`` raises the same
    IntegrityError the DB would raise on the lost race. If the try/except is removed, a bare
    IntegrityError escapes and this test reddens — so the guard is load-bearing.
    """
    owner_id = _register(client, "owner@race.co")
    _register(client, "target@race.co")
    org = Organization(name="Racers", owner_id=owner_id, status="active", seats_purchased=1)
    db_session.add(org)
    db_session.commit()

    def _boom(*a, **k):
        raise IntegrityError("INSERT", {}, Exception("uq_org_member_user"))

    monkeypatch.setattr(db_session, "flush", _boom)

    with pytest.raises(org_billing.AlreadyInAnotherOrg):
        org_billing.add_member(db_session, org, "target@race.co")
