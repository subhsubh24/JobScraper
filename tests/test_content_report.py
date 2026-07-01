"""Track D — user report/flag of AI-generated content (Apple/Google 2026 GenAI/UGC).

Proves the real side-effect (a persisted, moderator-reviewable row), the input bounds
(constrained category + bounded free-text), auth + rate-limit protection, and that the
account-deletion cascade purges reports (store/GDPR: no orphaned user-owned rows).
"""
from src.db.models import ContentReport, User


def _register(client, email="reporter@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_report_requires_auth(client):
    r = client.post("/api/report", json={"content_type": "coach", "reason": "harmful"})
    assert r.status_code == 401


def test_report_persists_real_row(client, db_session):
    """A valid report is a REAL side-effect: a row a moderator can review, with the
    reporter, surface, reason, excerpt and default 'open' status all recorded."""
    token = _register(client)
    r = client.post(
        "/api/report",
        headers=_auth(token),
        json={
            "content_type": "coach",
            "reason": "inaccurate",
            "content_ref": "sess-123",
            "content_excerpt": "The coach told me to lie on my resume.",
            "detail": "This advice is wrong and could get me fired.",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    # Honest message — no claim of a downstream notification we don't send.
    assert "review" in body["message"].lower()

    rows = db_session.query(ContentReport).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.content_type == "coach"
    assert row.reason == "inaccurate"
    assert row.content_ref == "sess-123"
    assert "lie on my resume" in row.content_excerpt
    assert row.detail.startswith("This advice is wrong")
    assert row.status == "open"
    # Attributed to the real reporter.
    assert row.user_id == db_session.query(User).one().id


def test_report_minimal_payload_ok(client, db_session):
    """Only content_type + reason are required (excerpt/detail/ref optional)."""
    token = _register(client, "minimal@example.com")
    r = client.post(
        "/api/report",
        headers=_auth(token),
        json={"content_type": "prep_pack", "reason": "offensive"},
    )
    assert r.status_code == 200, r.text
    row = db_session.query(ContentReport).one()
    assert row.content_type == "prep_pack"
    assert row.content_ref is None
    assert row.content_excerpt is None


def test_report_rejects_unknown_content_type(client):
    token = _register(client, "badtype@example.com")
    r = client.post(
        "/api/report",
        headers=_auth(token),
        json={"content_type": "billing", "reason": "harmful"},
    )
    assert r.status_code == 422


def test_report_rejects_unknown_reason(client):
    token = _register(client, "badreason@example.com")
    r = client.post(
        "/api/report",
        headers=_auth(token),
        json={"content_type": "coach", "reason": "i-just-dont-like-it"},
    )
    assert r.status_code == 422


def test_report_rejects_overlong_free_text(client):
    """Bounds guard the unbounded-write vector on the free-text fields."""
    token = _register(client, "toolong@example.com")
    for field, over in (
        ("content_excerpt", "x" * 5001),
        ("detail", "y" * 1001),
        ("content_ref", "z" * 65),
    ):
        r = client.post(
            "/api/report",
            headers=_auth(token),
            json={"content_type": "coach", "reason": "other", field: over},
        )
        assert r.status_code == 422, f"{field} should be rejected"


def test_report_is_rate_limited(client):
    """The 'report' bucket (20/window) throttles a flood so it can't spam the table."""
    token = _register(client, "flood@example.com")
    payload = {"content_type": "coach", "reason": "other"}
    codes = [
        client.post("/api/report", headers=_auth(token), json=payload).status_code
        for _ in range(22)
    ]
    assert 200 in codes
    assert 429 in codes


def test_reports_purged_on_account_deletion(client, db_session):
    """Account deletion must leave ZERO user-owned rows — including reports (cascade)."""
    token = _register(client, "deleteme@example.com")
    r = client.post(
        "/api/report",
        headers=_auth(token),
        json={"content_type": "coach", "reason": "harmful", "content_excerpt": "bad"},
    )
    assert r.status_code == 200
    assert db_session.query(ContentReport).count() == 1

    d = client.delete("/api/auth/me", headers=_auth(token))
    assert d.status_code == 200, d.text
    assert db_session.query(ContentReport).count() == 0
    assert db_session.query(User).count() == 0
