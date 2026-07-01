"""Coverage for the scorer's batch/query helpers: ``score_all_jobs`` + ``get_top_jobs``.

These two public methods on ``JobScorer`` had ZERO test coverage despite sitting on the core
scoring path (``score_all_jobs`` is the "score everything new" entry point; ``get_top_jobs``
is the ranked-pipeline query). They run key-free here (heuristic scoring), so the assertions
are deterministic:
 - ``score_all_jobs`` scores ONLY the not-yet-scored jobs (the outerjoin/IS NULL filter), so a
   second call returns nothing — it must not re-score or duplicate.
 - ``get_top_jobs`` returns ``(JobPosting, JobScore)`` rows ordered by overall_score DESC and
   honours ``limit``.
"""
from src.db.models import Company, JobPosting, JobScore, User, UserTier
from src.ranking.scorer import JobScorer


def _user(db, email="scorer-wf@example.com"):
    user = User(
        email=email,
        password_hash="x",
        tier=UserTier.FREE,
        full_name="Scorer User",
        resume_text="Experienced python sql aws engineer",
    )
    db.add(user)
    db.flush()
    return user


def _job(db, user, title, description):
    company = Company(name="Acme")
    db.add(company)
    db.flush()
    job = JobPosting(
        user_id=user.id,
        company_id=company.id,
        title=title,
        company_name="Acme",
        description=description,
    )
    db.add(job)
    db.flush()
    return job


def test_score_all_jobs_scores_only_unscored(db_session):
    user = _user(db_session)
    _job(db_session, user, "Backend", "python sql backend role")
    _job(db_session, user, "Data", "python aws data role")

    scorer = JobScorer(db_session)
    first = scorer.score_all_jobs(user)
    assert len(first) == 2, "both unscored jobs should be scored on the first pass"
    for s in first:
        assert isinstance(s, JobScore)
        assert 0 <= s.overall_score <= 100  # heuristic score is a real bounded number

    # A second pass finds nothing new — score_all_jobs must skip already-scored jobs
    # (the outerjoin/IS NULL filter), not re-score or duplicate them.
    second = scorer.score_all_jobs(user)
    assert second == []
    assert db_session.query(JobScore).count() == 2  # no duplicate score rows


def test_score_all_jobs_empty_when_no_jobs(db_session):
    user = _user(db_session, email="scorer-empty@example.com")
    assert JobScorer(db_session).score_all_jobs(user) == []


def test_get_top_jobs_orders_desc_and_respects_limit(db_session):
    user = _user(db_session, email="scorer-top@example.com")
    # Three jobs with explicit, distinct scores so ordering is unambiguous.
    j_low = _job(db_session, user, "Low", "unrelated role")
    j_high = _job(db_session, user, "High", "python sql aws role")
    j_mid = _job(db_session, user, "Mid", "python role")
    db_session.add(JobScore(job_id=j_low.id, overall_score=20.0, score_explanation="Low match"))
    db_session.add(JobScore(job_id=j_high.id, overall_score=95.0, score_explanation="Excellent"))
    db_session.add(JobScore(job_id=j_mid.id, overall_score=60.0, score_explanation="Good match"))
    db_session.flush()

    scorer = JobScorer(db_session)
    top = scorer.get_top_jobs(user, limit=2)
    assert len(top) == 2, "limit must cap the result count"
    # Each row is (JobPosting, JobScore), ordered by overall_score DESC.
    assert [score.overall_score for _job_row, score in top] == [95.0, 60.0]
    assert top[0][0].title == "High"


def test_get_top_jobs_excludes_unscored_and_other_users(db_session):
    user = _user(db_session, email="scorer-iso@example.com")
    scored = _job(db_session, user, "Scored", "python role")
    _job(db_session, user, "Unscored", "python role")  # no JobScore row → excluded by the join
    db_session.add(JobScore(job_id=scored.id, overall_score=80.0, score_explanation="x"))

    other = _user(db_session, email="scorer-other@example.com")
    other_job = _job(db_session, other, "Other", "python role")
    db_session.add(JobScore(job_id=other_job.id, overall_score=99.0, score_explanation="x"))
    db_session.flush()

    top = JobScorer(db_session).get_top_jobs(user)
    # Only the current user's SCORED job is returned (unscored excluded by the inner join;
    # the other user's higher-scored job is never visible — per-user isolation).
    assert len(top) == 1
    assert top[0][0].id == scored.id


# ---------------------------------------------------------------------------
# Embedding RELOAD path (scorer.py ensure_user_embedding / ensure_job_embedding)
#
# When an embedding already EXISTS it is returned without a fresh API call. The stored
# value may be a JSON string (legacy/text storage) or a list (JSON column) — the isinstance
# check handles both. Key-free tests never populate embeddings (get_embedding raises before
# storing), so these defensive branches had ZERO coverage. A regression that drops the
# isinstance guard would call json.loads() on a list (TypeError, caught → silent 0.5 score)
# or skip parsing a stored string, silently DEGRADING scores for affected rows.
# ---------------------------------------------------------------------------
def test_ensure_user_embedding_parses_stored_json_string(db_session):
    user = _user(db_session, email="embed-user-str@example.com")
    user.resume_embedding = "[0.1, 0.2, 0.3]"  # stored as a JSON string
    db_session.flush()

    emb = JobScorer(db_session).ensure_user_embedding(user)
    assert emb == [0.1, 0.2, 0.3]  # parsed back to a list, no fresh embedding call


def test_ensure_user_embedding_returns_stored_list_as_is(db_session):
    user = _user(db_session, email="embed-user-list@example.com")
    user.resume_embedding = [0.4, 0.5]  # already a list (JSON column)
    db_session.flush()

    emb = JobScorer(db_session).ensure_user_embedding(user)
    assert emb == [0.4, 0.5]  # returned as-is — never json.loads()'d into a crash


def test_ensure_job_embedding_parses_stored_json_string(db_session):
    user = _user(db_session, email="embed-job-str@example.com")
    job = _job(db_session, user, "Backend", "python aws")
    job.jd_embedding = "[0.6, 0.7]"  # stored as a JSON string
    db_session.flush()

    emb = JobScorer(db_session).ensure_job_embedding(job)
    assert emb == [0.6, 0.7]


def test_ensure_job_embedding_returns_stored_list_as_is(db_session):
    user = _user(db_session, email="embed-job-list@example.com")
    job = _job(db_session, user, "Backend", "python aws")
    job.jd_embedding = [0.8, 0.9]  # already a list
    db_session.flush()

    emb = JobScorer(db_session).ensure_job_embedding(job)
    assert emb == [0.8, 0.9]
