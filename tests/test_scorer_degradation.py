"""Guard on the scorer's CONFIGURED-BUT-FAILING embedding branch (a silent-failure path).

FACTORY_STANDARD §6: a whole class of bugs appears ONLY when an external dependency is
CONFIGURED but its call FAILS at runtime — a different code path than the keyless/degraded one.
The scorer's embedding branch is exactly this: when a client IS present, ``score_job`` calls
Gemini for embeddings, and if that call raises it must degrade to the neutral 0.5 semantic
baseline and still return a real, bounded score — never crash, never emit a ``nan`` fit score
(a swallowed failure the caller's try/except would not catch).

Prior coverage exercised the happy path (a live key, ``tests/evals/test_ai_output_evals.py``)
and the keyless path, but NOT a client that is present yet errors mid-call. These tests close
that gap with a client whose ``embeddings.create`` always raises.

(The zero-vector ``cosine_similarity`` NaN guard is already pinned directly in
``tests/evals/test_scoring_evals.py`` — not re-tested here.)
"""
import math

from src.db.models import Company, JobPosting, JobScore, User, UserTier
from src.ranking.scorer import JobScorer


def _user(db, email="scorer-degrade@example.com"):
    user = User(
        email=email,
        password_hash="x",
        tier=UserTier.FREE,
        full_name="Degrade User",
        # Every extracted skill here is also present in the JD below, so skills_score == 1.0
        # and the heuristic overall score is exactly 30 + 40*1.0 == 70.0 (semantic baseline
        # 0.5). That fixed number lets us assert "degraded to the baseline" precisely.
        resume_text="Experienced python sql aws engineer",
    )
    db.add(user)
    db.flush()
    return user


def _job(db, user):
    company = Company(name="Acme")
    db.add(company)
    db.flush()
    job = JobPosting(
        user_id=user.id,
        company_id=company.id,
        title="Backend Engineer",
        company_name="Acme",
        description="python sql aws backend role",
    )
    db.add(job)
    db.flush()
    return job


class _AlwaysRaisingEmbeddings:
    def create(self, *args, **kwargs):  # noqa: D401 - simulates a live provider error mid-call
        raise RuntimeError("simulated Gemini embeddings 502")


class _ErroringClient:
    """A CONFIGURED client (``client is not None``) whose embedding call always fails at
    runtime. This makes ``score_job`` take the embedding branch and hit the error INSIDE the
    call — the case a present-but-flaky provider produces in production."""

    embeddings = _AlwaysRaisingEmbeddings()


def test_score_job_degrades_when_configured_embedding_call_fails(db_session):
    """CONFIGURED-but-failing embedding path degrades to the neutral baseline, not a crash."""
    user = _user(db_session)
    job = _job(db_session, user)

    scorer = JobScorer(db_session)
    # Force the "provider configured" branch: a non-None client whose call raises at runtime.
    scorer.client = _ErroringClient()

    score = scorer.score_job(job, user, use_embeddings=True)

    assert isinstance(score, JobScore)
    # Bounded, real, and NOT nan despite the embedding failure.
    assert 0.0 <= score.overall_score <= 100.0
    assert not math.isnan(score.overall_score)
    # Degraded to the neutral 0.5 semantic baseline: 30 + 40*skills_score, skills_score == 1.0.
    assert score.overall_score == 70.0
    assert not math.isnan(score.skills_match)


def test_score_job_local_only_never_touches_configured_client(db_session):
    """use_embeddings=False must stay fully local even when a (failing) client is present —
    fail-closed: no personal data leaves the server, so the erroring provider is never called
    (if it were, ``_ErroringClient`` would raise and this test would error)."""
    user = _user(db_session, email="scorer-local@example.com")
    job = _job(db_session, user)

    scorer = JobScorer(db_session)
    scorer.client = _ErroringClient()  # a trap: any call to it raises

    score = scorer.score_job(job, user, use_embeddings=False)
    assert score.overall_score == 70.0
