"""Direct guards on the scorer's two silent-failure branches.

These branches are the ones that can corrupt a user-facing fit score WITHOUT raising — so a
plain ``try/except`` around scoring would never catch them. They had no direct unit assertion
(QUALITY_SCORECARD correctness top_gap: "zero-vector scorer guard has no direct unit
assertion on the NaN/0.5 branch"). Both are pinned here:

1. ``cosine_similarity`` on a zero-magnitude vector: the naive ``dot / (norm*norm)`` is 0/0 =
   ``nan`` (NOT an exception), which would surface as a ``nan`` fit score. The guard must
   return the neutral 0.5 instead.
2. The DEPENDENCY-CONFIGURED-BUT-FAILING embedding path (FACTORY_STANDARD §6): a client IS
   present but ``embeddings.create`` throws at runtime. ``score_job(use_embeddings=True)`` must
   degrade to the neutral 0.5 semantic baseline and still return a real, bounded score — never
   crash, never emit ``nan``. The keyless path passing is NOT evidence this configured-but-
   erroring path degrades; we exercise it with a client whose call always raises.
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
    def create(self, *args, **kwargs):  # noqa: D401 - simulates a live provider error
        raise RuntimeError("simulated Gemini embeddings 502")


class _ErroringClient:
    """A CONFIGURED client whose embedding call always fails at runtime (§6 configured-but-
    failing path). ``client is not None`` so the scorer takes the embedding branch and must
    catch the error, not the keyless short-circuit."""

    embeddings = _AlwaysRaisingEmbeddings()


def test_cosine_similarity_zero_vector_returns_neutral_not_nan(db_session):
    scorer = JobScorer(db_session)
    # A zero-magnitude vector makes the denominator 0 -> naive cosine is nan.
    result = scorer.cosine_similarity([0.0, 0.0, 0.0], [1.0, 2.0, 3.0])
    assert result == 0.5
    assert not math.isnan(result)
    # Symmetric: zero vector on the other side, and both-zero, are equally guarded.
    assert scorer.cosine_similarity([1.0, 2.0, 3.0], [0.0, 0.0, 0.0]) == 0.5
    assert scorer.cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.5


def test_cosine_similarity_normal_vectors_unaffected(db_session):
    scorer = JobScorer(db_session)
    # Identical unit-direction vectors -> cosine 1.0; orthogonal -> 0.0. The guard only fires
    # on the zero-magnitude case, so real vectors are untouched.
    assert scorer.cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert scorer.cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


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
    fail-closed: no personal data leaves the server, so the erroring provider is never called."""
    user = _user(db_session, email="scorer-local@example.com")
    job = _job(db_session, user)

    scorer = JobScorer(db_session)
    scorer.client = _ErroringClient()  # would raise if the local path ever called it

    # No exception => the local branch never invoked the client.
    score = scorer.score_job(job, user, use_embeddings=False)
    assert score.overall_score == 70.0
