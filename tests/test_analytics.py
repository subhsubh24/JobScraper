"""Privacy-safe aggregate analytics: record_event upsert, allowlist, best-effort safety,
and the shared-secret-gated read endpoint (503 unset / 401 wrong / 200 right), plus the
real activation-funnel round-trip through the live API (signup -> job_added -> fit_score).
"""
from datetime import date, datetime

from src import analytics
from src.db.models import AggregateEvent


# ---------------------------------------------------------------------------
# record_event (unit)
# ---------------------------------------------------------------------------
def test_record_event_creates_then_increments_same_day(db_session):
    analytics.record_event(db_session, "signup")
    analytics.record_event(db_session, "signup")

    rows = db_session.query(AggregateEvent).filter_by(event_type="signup").all()
    assert len(rows) == 1  # one (event_type, day) row, not one per call
    assert rows[0].count == 2
    assert rows[0].event_date == datetime.utcnow().date()  # code stamps UTC — assert UTC, not local date.today()


def test_record_event_separate_types_and_days_are_distinct_rows(db_session):
    analytics.record_event(db_session, "signup")
    analytics.record_event(db_session, "job_added")
    analytics.record_event(db_session, "signup", when=date(2020, 1, 1))

    assert db_session.query(AggregateEvent).count() == 3
    assert (
        db_session.query(AggregateEvent)
        .filter_by(event_type="signup", event_date=date(2020, 1, 1))
        .one()
        .count
        == 1
    )


def test_record_event_ignores_unknown_type(db_session):
    analytics.record_event(db_session, "not_a_real_event")
    analytics.record_event(db_session, "")
    assert db_session.query(AggregateEvent).count() == 0


def test_record_event_never_raises_on_broken_session():
    """Best-effort contract: a broken session must be swallowed, never surfaced to a request."""

    class _BrokenSession:
        def query(self, *a, **k):
            raise RuntimeError("db is down")

        def rollback(self):
            pass

    # Must NOT raise (would otherwise break the user-facing endpoint that called it).
    analytics.record_event(_BrokenSession(), "signup")


def test_summary_shape_is_stable_when_empty(db_session):
    out = analytics.summary(db_session)
    assert set(out["totals"]) == set(analytics.EVENT_TYPES)
    assert all(v == 0 for v in out["totals"].values())
    assert out["funnel"] == {"signups": 0, "job_added": 0, "fit_score_generated": 0}


def test_summary_counts_and_funnel(db_session):
    for _ in range(3):
        analytics.record_event(db_session, "signup")
    analytics.record_event(db_session, "job_added")
    analytics.record_event(db_session, "fit_score_generated")

    out = analytics.summary(db_session)
    assert out["totals"]["signup"] == 3
    assert out["funnel"] == {"signups": 3, "job_added": 1, "fit_score_generated": 1}


# ---------------------------------------------------------------------------
# Read endpoint gating (shared secret; never any-authed-user)
# ---------------------------------------------------------------------------
def test_summary_endpoint_503_when_token_unset(client, monkeypatch):
    monkeypatch.delenv("ANALYTICS_READ_TOKEN", raising=False)
    r = client.get("/api/analytics/summary")
    assert r.status_code == 503


def test_summary_endpoint_401_on_wrong_or_missing_token(client, monkeypatch):
    monkeypatch.setenv("ANALYTICS_READ_TOKEN", "s3cret")
    assert client.get("/api/analytics/summary").status_code == 401
    assert (
        client.get(
            "/api/analytics/summary", headers={"Authorization": "Bearer wrong"}
        ).status_code
        == 401
    )


def test_summary_endpoint_200_with_correct_token(client, monkeypatch):
    monkeypatch.setenv("ANALYTICS_READ_TOKEN", "s3cret")
    r = client.get(
        "/api/analytics/summary", headers={"Authorization": "Bearer s3cret"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert set(body["analytics"]["totals"]) == set(analytics.EVENT_TYPES)


# ---------------------------------------------------------------------------
# Real activation funnel round-trip through the live API
# ---------------------------------------------------------------------------
def test_activation_funnel_recorded_end_to_end(client, monkeypatch):
    reg = client.post(
        "/api/auth/register",
        json={"email": "a@example.com", "password": "password123", "resume_text": "python sql aws"},
    )
    assert reg.status_code == 200
    token = reg.json()["token"]

    job = client.post(
        "/api/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Backend Engineer", "company_name": "Acme", "description": "python aws"},
    )
    assert job.status_code == 200

    monkeypatch.setenv("ANALYTICS_READ_TOKEN", "s3cret")
    totals = client.get(
        "/api/analytics/summary", headers={"Authorization": "Bearer s3cret"}
    ).json()["analytics"]["totals"]

    assert totals["signup"] == 1
    assert totals["job_added"] == 1
    # The heuristic scorer always produces a fit score (key-free), so the aha step is recorded.
    assert totals["fit_score_generated"] == 1
