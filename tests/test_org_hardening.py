"""Hardening for the run-39 team/org endpoints (security deep-audit, run 40).

Two real integrity gaps on the newly-shipped seat-tier feature:
  1. no DB-level "one owned org per user" guarantee -> a concurrent create could race past the
     app-level ``owned_org()`` check and leave a user owning two orgs (entitlement ambiguity);
  2. the org-name ``min_length`` ran BEFORE stripping, so ``"   "`` created an empty-named org.

Effects are asserted directly (DB row count / status code), never inferred loosely.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from src import org_billing
from src.db.models import Organization


def _register(client, email, password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_db_rejects_two_orgs_with_same_owner(client, db_session):
    """UNIQUE(owner_id) is enforced at the DB layer, not just the app-level check."""
    uid, _ = _register(client, "dbowner@example.com")
    db_session.add(Organization(name="First", owner_id=uid, seats_purchased=0))
    db_session.flush()
    db_session.add(Organization(name="Second", owner_id=uid, seats_purchased=0))
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_create_org_race_surfaces_as_409_not_500(client, db_session, monkeypatch):
    """A concurrent create that slips past ``owned_org()`` hits the constraint and becomes a
    clean 409 (OrgAlreadyExists), never an unhandled 500 — and exactly one org persists."""
    uid, token = _register(client, "race@example.com")
    r1 = client.post("/api/org", json={"name": "Acme"}, headers=_auth(token))
    assert r1.status_code == 200, r1.text
    # Simulate the race: both callers' ``owned_org()`` returned None before either committed.
    monkeypatch.setattr(org_billing, "owned_org", lambda db, u: None)
    r2 = client.post("/api/org", json={"name": "Acme Two"}, headers=_auth(token))
    assert r2.status_code == 409, r2.text
    assert db_session.query(Organization).filter(Organization.owner_id == uid).count() == 1


def test_whitespace_only_org_name_rejected(client):
    """A name that is only whitespace passes min_length pre-strip but must be rejected (422)."""
    _, token = _register(client, "ws@example.com")
    r = client.post("/api/org", json={"name": "   "}, headers=_auth(token))
    assert r.status_code == 422, r.text


def test_org_name_is_stored_stripped(client, db_session):
    """A valid padded name still succeeds and is persisted stripped."""
    _, token = _register(client, "strip@example.com")
    r = client.post("/api/org", json={"name": "  Padded Co  "}, headers=_auth(token))
    assert r.status_code == 200, r.text
    assert db_session.query(Organization).filter(Organization.name == "Padded Co").first() is not None
