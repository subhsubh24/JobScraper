"""Golden-expectation evals for the deterministic coach suggestions (Track E).

`get_suggested_questions` is the key-free, context-aware path: it returns different prompts
depending on the user's pipeline state (no applications vs interviewing vs applied). These
evals pin that the suggestions are non-empty, deterministic, and actually adapt to state —
so a regression that makes them generic/static is caught.
"""
from src.ai_coach.career_coach import CareerCoach
from src.db.models import Application, ApplicationStatus, JobPosting, User, UserTier


def _user(db) -> User:
    u = User(email="sugg@example.com", password_hash="x", tier=UserTier.PREMIUM)
    db.add(u)
    db.flush()
    return u


def _job_with_status(db, user_id: str, status: ApplicationStatus) -> None:
    job = JobPosting(user_id=user_id, title="Eng", company_name="Acme")
    db.add(job)
    db.flush()
    db.add(Application(user_id=user_id, job_id=job.id, status=status))
    db.flush()


def test_suggestions_nonempty_and_deterministic(db_session):
    user = _user(db_session)
    coach = CareerCoach(db_session)
    first = coach.get_suggested_questions(user)
    assert first and all(isinstance(s, str) and s for s in first)
    assert first == coach.get_suggested_questions(user)  # deterministic


def test_suggestions_adapt_to_pipeline_state(db_session):
    user = _user(db_session)
    coach = CareerCoach(db_session)

    no_apps = coach.get_suggested_questions(user)

    _job_with_status(db_session, user.id, ApplicationStatus.INTERVIEW)
    interviewing = coach.get_suggested_questions(user)

    # The interviewing user gets interview-prep prompts that the empty-pipeline user does not.
    assert interviewing != no_apps
    assert any("interview" in s.lower() for s in interviewing)


def test_suggestions_applied_branch(db_session):
    # The third branch: has applications but none interviewing -> follow-up/response prompts,
    # distinct from both the empty-pipeline and interviewing lists.
    user = _user(db_session)
    coach = CareerCoach(db_session)
    no_apps = coach.get_suggested_questions(user)

    _job_with_status(db_session, user.id, ApplicationStatus.APPLIED)
    applied = coach.get_suggested_questions(user)

    assert applied != no_apps
    assert any("follow up" in s.lower() or "response rate" in s.lower() for s in applied)
    assert not any("what should i wear" in s.lower() for s in applied)  # not the interview list
