"""Regression guard: building the coach context must NOT be an N+1 query.

`_get_user_context` summarizes a user's recent applications for the coach prompt. It used to
issue one `JobPosting.get(...)` per application (1 + N queries) on every coach message; now it
eager-loads each application's job via selectinload. This test seeds several applications and
asserts the query count stays bounded (does NOT grow with the number of applications), so the
N+1 can't silently come back.
"""
from sqlalchemy import event

from src.ai_coach.career_coach import CareerCoach
from src.db.models import Application, ApplicationStatus, Company, JobPosting, User, UserTier


def _seed_user_with_applications(db, n: int, email: str) -> User:
    user = User(email=email, password_hash="x", tier=UserTier.PREMIUM,
                full_name="Test User")
    db.add(user)
    db.flush()
    company = Company(name="Acme")
    db.add(company)
    db.flush()
    for i in range(n):
        job = JobPosting(user_id=user.id, company_id=company.id,
                         title=f"Engineer {i}", company_name="Acme")
        db.add(job)
        db.flush()
        db.add(Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.APPLIED))
    db.flush()
    return user


def _count_queries(db, fn):
    conn = db.connection()
    count = {"n": 0}

    def _on_exec(*_args, **_kwargs):
        count["n"] += 1

    event.listen(conn, "after_cursor_execute", _on_exec)
    try:
        fn()
    finally:
        event.remove(conn, "after_cursor_execute", _on_exec)
    return count["n"]


def test_coach_context_is_not_n_plus_one(db_session):
    coach = CareerCoach(db_session)

    user2 = _seed_user_with_applications(db_session, 2, "coach-n1a@example.com")
    db_session.expire_all()  # force fresh loads so the query count reflects real fetches
    q2 = _count_queries(db_session, lambda: coach._get_user_context(user2))

    user5 = _seed_user_with_applications(db_session, 5, "coach-n1b@example.com")
    db_session.expire_all()
    q5 = _count_queries(db_session, lambda: coach._get_user_context(user5))

    # With eager-loading the query count is constant regardless of how many applications
    # exist (apps query + one batched job load). The OLD N+1 would make q5 > q2 by ~3.
    assert q5 == q2, f"coach context query count grew with applications (N+1): {q2} -> {q5}"

    # And the context actually contains the jobs (eager-load returned the right data).
    ctx = coach._get_user_context(user5)
    assert "Engineer" in ctx and "Acme" in ctx
