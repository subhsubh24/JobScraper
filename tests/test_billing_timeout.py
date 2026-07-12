"""Stripe checkout timeout → honest 503, never an uncaught 500 (FACTORY_STANDARD §6/§6c).

``billing.configure_stripe`` bounds every Stripe HTTP call below the serverless budget so a
slow/hung Stripe API fails LOUD *in-request* instead of being killed by the platform. But a
bounded call is only useful if the resulting failure is CAUGHT and surfaced honestly — otherwise
stripe-python's ``APIConnectionError`` (what a ``requests`` Timeout/ConnectionError is re-raised
as) escapes the endpoint as a generic 500. These tests pin the completed contract: a transient
Stripe failure on ``Session.create`` becomes a retryable 503 with "No charge was made", for BOTH
the individual and org-seat checkout paths.

Load-bearing: remove the ``except stripe.error.APIConnectionError`` guard in
``billing.create_checkout_session`` / ``org_billing.create_seat_checkout_session`` (or the
matching endpoint handler in asgi.py) and the raw ``APIConnectionError`` escapes → the endpoint
returns 500 and these 503 assertions redden.
"""
import stripe
import pytest
from types import SimpleNamespace

from src import billing, org_billing


def _register(client, email="timeout@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"]["id"], body["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _raise_timeout(**kwargs):
    # Exactly what stripe-python raises when the bounded requests client times out or the
    # connection fails (stripe/_http_client.py RequestsClient._handle_request_error wraps
    # requests.exceptions.Timeout / ConnectionError into APIConnectionError).
    raise stripe.error.APIConnectionError("Request timed out.")


# ------------------------------------------------------------- unit: the billing layer re-raises


def test_individual_checkout_maps_timeout_to_provider_unavailable(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_PRO_ANNUAL", "price_annual_123")
    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(_raise_timeout))
    user = SimpleNamespace(id="u_1", email="a@b.co")
    with pytest.raises(billing.BillingProviderUnavailable):
        billing.create_checkout_session(user, "pro_annual", "http://s", "http://c")


def test_org_seat_checkout_maps_timeout_to_provider_unavailable(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_TEAM_ANNUAL", "price_team_annual_x")
    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(_raise_timeout))
    owner = SimpleNamespace(id="o_1", email="owner@b.co")
    org = SimpleNamespace(id="org_1")
    with pytest.raises(billing.BillingProviderUnavailable):
        org_billing.create_seat_checkout_session(owner, org, "team_annual", 5, "http://s", "http://c")


def test_config_error_is_not_laundered_into_provider_unavailable(monkeypatch):
    """A genuine CONFIG error (bad API key / bad price) is NOT a transient outage — it must NOT be
    caught and softened into ``BillingProviderUnavailable`` (which would surface a misleading
    retryable "temporarily unavailable, try again" 503). It propagates so the endpoint 500s and
    the real bug is logged, not laundered. This PINS the deliberately NARROW ``except`` scope: a
    future refactor widening it to ``stripe.error.StripeError`` would redden this test."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_PRO_ANNUAL", "price_annual_123")

    def _raise_auth(**kwargs):
        raise stripe.error.AuthenticationError("Invalid API key.")

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(_raise_auth))
    user = SimpleNamespace(id="u_1", email="a@b.co")
    # AuthenticationError is a sibling of APIConnectionError under StripeError, so the narrow
    # ``except APIConnectionError`` does NOT catch it — it propagates unchanged.
    with pytest.raises(stripe.error.AuthenticationError):
        billing.create_checkout_session(user, "pro_annual", "http://s", "http://c")


# --------------------------------------------------- endpoint: the user sees 503, not 500, no charge


def test_individual_checkout_endpoint_returns_503_on_timeout(client, monkeypatch, db_session):
    """A Stripe timeout on the individual checkout endpoint is a clean, retryable 503 (never a
    500), the tier is unchanged, and the copy states no charge was made."""
    from src.db.models import User, UserTier

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_PRO_ANNUAL", "price_annual_123")
    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(_raise_timeout))

    user_id, token = _register(client)
    r = client.post("/api/billing/checkout", json={"plan": "pro_annual"}, headers=_auth(token))
    assert r.status_code == 503, r.text
    assert "no charge" in r.json()["detail"].lower()
    # No fake entitlement: the user stays FREE (a charge is only ever granted by a signed webhook).
    assert db_session.get(User, user_id).tier == UserTier.FREE


def test_org_seat_checkout_endpoint_returns_503_on_timeout(client, monkeypatch, db_session):
    """A Stripe timeout on the org seat-checkout endpoint is a clean, retryable 503, not a 500."""
    from src.db.models import Organization

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_TEAM_ANNUAL", "price_team_annual_x")
    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(_raise_timeout))

    owner_id, token = _register(client, email="teamowner@example.com")
    org = Organization(name="Acme", owner_id=owner_id, status="incomplete", seats_purchased=0)
    db_session.add(org)
    db_session.commit()

    r = client.post(
        "/api/org/checkout", json={"plan": "team_annual", "seats": 5}, headers=_auth(token)
    )
    assert r.status_code == 503, r.text
    assert "no charge" in r.json()["detail"].lower()
    # No fake seat grant: the org stays un-activated (status + seats are written only by a signed
    # webhook, never by a failed checkout attempt) — mirrors the individual test's tier check.
    db_session.refresh(org)
    assert org.status == "incomplete"
    assert org.seats_purchased == 0
