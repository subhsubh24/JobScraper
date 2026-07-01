"""Regression guard: coach suggested-questions must use BOUNDED existence checks.

`get_suggested_questions` runs on every coach-tab open. It used to load EVERY Application row
for the user just to test two booleans ("any application?" / "any at the interview stage?"),
an unbounded query that grows with the pipeline. It now uses `.first()` existence checks, so
the query count is constant regardless of application count — this test locks that in and
verifies the three state branches still return the correct suggestion set.
"""
from sqlalchemy import event

from src.ai_coach.career_coach import CareerCoach
from src.db.models import Application, ApplicationStatus, Company, JobPosting, User, UserTier


def _seed(db, email, statuses):
    user = User(email=email, password_hash="x", tier=UserTier.PREMIUM)
    db.add(user)
    db.flush()
    company = Company(name="Acme")
    db.add(company)
    db.flush()
    for i, status in enumerate(statuses):
        job = JobPosting(user_id=user.id, company_id=company.id,
                         title=f"Engineer {i}", company_name="Acme")
        db.add(job)
        db.flush()
        db.add(Application(user_id=user.id, job_id=job.id, status=status))
    db.flush()
    return user


def _capture_statements(db, fn):
    conn = db.connection()
    stmts = []

    def _on_exec(_conn, _cursor, statement, *_a, **_k):
        stmts.append(statement)

    event.listen(conn, "after_cursor_execute", _on_exec)
    try:
        fn()
    finally:
        event.remove(conn, "after_cursor_execute", _on_exec)
    return stmts


def test_suggestions_query_is_bounded_not_full_load(db_session):
    """Every SELECT against `applications` must be BOUNDED (`.first()` → `LIMIT 1`), never a
    full-table load. This is the real regression guard: the OLD `.all()` code issued the SAME
    number of statements (one), so a statement-COUNT check could NOT catch it — but the old
    full load has no `LIMIT`, so this assertion fails against it and passes only for the
    bounded existence checks (confirmed load-bearing by mutation: reverting to `.all()` drops
    the LIMIT and fails this test)."""
    coach = CareerCoach(db_session)
    user = _seed(db_session, "sugg-bounded@example.com", [ApplicationStatus.APPLIED] * 25)
    db_session.expire_all()

    stmts = _capture_statements(db_session, lambda: coach.get_suggested_questions(user))
    app_selects = [
        s for s in stmts
        if s.lstrip().lower().startswith("select") and "application" in s.lower()
    ]
    assert app_selects, "expected at least one SELECT against applications"
    unbounded = [s for s in app_selects if "limit" not in s.lower()]
    assert not unbounded, f"applications loaded WITHOUT a LIMIT (full load): {unbounded}"


def test_suggestions_match_user_state(db_session):
    coach = CareerCoach(db_session)

    no_apps = _seed(db_session, "sugg-none@example.com", [])
    applied_only = _seed(db_session, "sugg-applied@example.com",
                         [ApplicationStatus.APPLIED, ApplicationStatus.SAVED])
    interviewing = _seed(db_session, "sugg-interview@example.com",
                         [ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEW])

    s_none = coach.get_suggested_questions(no_apps)
    s_applied = coach.get_suggested_questions(applied_only)
    s_interview = coach.get_suggested_questions(interviewing)

    # No applications → onboarding prompts.
    assert any("resume for ATS" in s for s in s_none)
    # Applications but no interview → response-rate/follow-up prompts.
    assert any("response rate" in s for s in s_applied)
    # An interview-stage application → interview-prep prompts (the branch the bounded
    # existence check must still detect).
    assert any("technical interview" in s for s in s_interview)


def test_suggestions_detects_phone_screen(db_session):
    """PHONE_SCREEN also counts as interviewing (both members of the in_ filter)."""
    coach = CareerCoach(db_session)
    user = _seed(db_session, "sugg-phone@example.com",
                 [ApplicationStatus.SAVED, ApplicationStatus.PHONE_SCREEN])
    assert any("technical interview" in s for s in coach.get_suggested_questions(user))
