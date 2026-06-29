"""Golden-expectation evals for the heuristic job scorer (Track E).

These pin the DETERMINISTIC, key-free scoring path — the one that runs in CI and in prod when
no Gemini key is set. With embeddings unavailable the scorer falls back to a fixed semantic
score of 0.5 (weight 60%) plus a skills-overlap score (weight 40%), so:

    overall = (0.5 * 0.6 + skills_score * 0.4) * 100  =  30 + 40 * skills_score

Golden values follow directly:
    • all job skills present in résumé  -> skills_score 1.0 -> 70.0
    • no overlap                        -> skills_score 0.0 -> 30.0
    • no detectable job skills          -> skills_score 0.5 -> 50.0

If these drift, either the weighting or the skill extraction changed — a deliberate decision
that should update this eval, not slip through silently.
"""
import math

import pytest

from src.db.models import JobPosting, User, UserTier
from src.ranking.scorer import JobScorer


def _user(db, resume_text: str) -> User:
    u = User(email="eval@example.com", password_hash="x", tier=UserTier.FREE, resume_text=resume_text)
    db.add(u)
    db.flush()
    return u


def _job(db, user_id: str, description: str) -> JobPosting:
    j = JobPosting(user_id=user_id, title="Engineer", company_name="Acme", description=description)
    db.add(j)
    db.flush()
    return j


def test_extract_skills_is_deterministic_and_correct(db_session):
    scorer = JobScorer(db_session)
    found = set(scorer.extract_skills("I work with Python, React and PostgreSQL daily."))
    assert {"python", "react", "postgresql"} <= found
    assert "java" not in found


@pytest.mark.parametrize(
    "resume,description,expected",
    [
        # all job skills present in résumé -> 70
        ("python react sql", "We need python, react and sql experience", 70.0),
        # no overlap -> 30
        ("python developer", "Looking for a java and c# engineer", 30.0),
        # no detectable skills in the JD -> skills_score defaults to 0.5 -> 50
        ("python react", "We want a great teammate who loves a challenge", 50.0),
        # partial overlap (2 of 3 JD skills) -> skills_score 0.667 -> 30 + 26.67 = 56.67.
        # Pins the 60/40 weighting via a NON-degenerate skills_score (unlike the 0.5 case).
        ("python react", "need python, react and kubernetes", 56.67),
    ],
)
def test_heuristic_overall_score_golden(db_session, resume, description, expected):
    user = _user(db_session, resume)
    job = _job(db_session, user.id, description)
    score = JobScorer(db_session).score_job(job, user)
    assert score.overall_score == pytest.approx(expected, abs=0.01)
    assert 0 <= score.overall_score <= 100


def test_matching_and_missing_skills_are_correct(db_session):
    user = _user(db_session, "python and react")
    job = _job(db_session, user.id, "need python, react, kubernetes and aws")
    score = JobScorer(db_session).score_job(job, user)
    assert set(score.matching_skills) == {"python", "react"}
    assert set(score.missing_skills) == {"kubernetes", "aws"}


def test_scoring_is_reproducible_and_updates_in_place(db_session):
    from src.db.models import JobScore

    user = _user(db_session, "python react sql")
    job = _job(db_session, user.id, "python react sql role")
    s1 = JobScorer(db_session).score_job(job, user).overall_score
    s2 = JobScorer(db_session).score_job(job, user).overall_score  # re-score same rows
    assert s1 == s2
    # Re-scoring must UPDATE the existing JobScore row, not insert a duplicate.
    assert db_session.query(JobScore).filter(JobScore.job_id == job.id).count() == 1


# --- Explanation rating + formatting ---------------------------------------------------
# The explanation string is user-facing (it renders on the job-detail screen). The four
# rating bands and the list truncation (top 5 matching, top 3 to-highlight) are tested
# directly because the key-free heuristic path caps overall at 70 — so the "Excellent"
# (>=80) band is only reachable when embeddings are available in prod. A direct unit test
# pins every band + truncation so a threshold/weight drift can't silently change the copy.
@pytest.mark.parametrize(
    "score,expected_rating",
    [
        (100, "Excellent match!"),
        (80, "Excellent match!"),   # lower bound of the band
        (79.99, "Good match"),
        (60, "Good match"),         # lower bound
        (59.99, "Moderate match"),
        (40, "Moderate match"),     # lower bound
        (39.99, "Low match"),
        (0, "Low match"),
    ],
)
def test_explanation_rating_bands(db_session, score, expected_rating):
    # No skills passed -> the explanation is exactly the rating (no " | " segments).
    assert JobScorer(db_session)._generate_explanation(score, [], []) == expected_rating


def test_explanation_truncates_skill_lists(db_session):
    matching = [f"m{i}" for i in range(8)]   # > 5
    missing = [f"x{i}" for i in range(6)]     # > 3
    expl = JobScorer(db_session)._generate_explanation(85, matching, missing)
    assert expl.startswith("Excellent match!")
    assert "Matching skills: m0, m1, m2, m3, m4" in expl
    assert "m5" not in expl                    # 6th matching skill dropped
    assert "Skills to highlight: x0, x1, x2" in expl
    assert "x3" not in expl                    # 4th missing skill dropped


# A degenerate embedding (all zeros) makes cosine similarity undefined: the naive
# dot/(norm*norm) is 0/0 == nan, which is NOT an exception and would slip past the
# scorer's try/except to surface as a `nan` fit score. The guard must return a neutral
# 0.5 so a bad embedding can never corrupt a user-visible score.
@pytest.mark.parametrize(
    "v1,v2",
    [
        ([0.0, 0.0, 0.0], [1.0, 2.0, 3.0]),   # left zero vector
        ([1.0, 2.0, 3.0], [0.0, 0.0, 0.0]),   # right zero vector
        ([0.0, 0.0], [0.0, 0.0]),             # both zero
    ],
)
def test_cosine_similarity_zero_vector_returns_neutral_not_nan(db_session, v1, v2):
    # isfinite is the real property under test — the old code returned nan here, which is
    # not an exception and so slipped past score_job()'s try/except into the fit score.
    sim = JobScorer(db_session).cosine_similarity(v1, v2)
    assert math.isfinite(sim)
    assert sim == 0.5
