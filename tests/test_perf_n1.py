"""Regression guard: the job-list + pipeline-analytics endpoints must NOT be N+1 queries.

``GET /api/jobs`` and ``GET /api/analytics/pipeline`` serialize every one of a user's jobs
via ``job_public`` / the aggregate loop, which read each job's ``application``, ``score`` and
``company``. Without eager-loading those are lazy relationships → one extra query PER job
(3N+1 for /api/jobs, 2N+1 for the analytics loop), unbounded for unlimited-tier users.

These tests seed users with different job counts and assert the query count is CONSTANT
(does not grow with the number of jobs), so the N+1 cannot silently come back. They call the
route functions directly against a real session so the count reflects actual DB round-trips.
"""
from sqlalchemy import event

import asgi
from src.db.models import (
    Application,
    ApplicationStatus,
    Company,
    JobPosting,
    JobScore,
    User,
    UserTier,
)


def _seed_user_with_jobs(db, n: int, email: str) -> User:
    """A user with ``n`` jobs, each carrying an application + score + a DISTINCT company.

    Crucially every job has ``company_name=None`` so ``job_public`` must dereference the
    ``company`` relationship (it short-circuits on a truthy ``company_name``). Distinct
    companies defeat the identity-map cache, so a missing ``selectinload(company)`` shows up
    as one extra lazy-load PER job — i.e. the query-count guard actually exercises the
    company path instead of silently skipping it."""
    user = User(email=email, password_hash="x", tier=UserTier.PREMIUM, full_name="Perf User")
    db.add(user)
    db.flush()
    for i in range(n):
        company = Company(name=f"Acme {i}")
        db.add(company)
        db.flush()
        job = JobPosting(
            user_id=user.id,
            company_id=company.id,
            title=f"Engineer {i}",
            company_name=None,
        )
        db.add(job)
        db.flush()
        db.add(Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.APPLIED))
        db.add(JobScore(job_id=job.id, overall_score=70.0 + i, score_explanation="Good match"))
    db.flush()
    return user


def _count_queries(db, fn):
    conn = db.connection()
    count = {"n": 0}

    def _on_exec(*_args, **_kwargs):
        count["n"] += 1

    event.listen(conn, "after_cursor_execute", _on_exec)
    try:
        result = fn()
    finally:
        event.remove(conn, "after_cursor_execute", _on_exec)
    return count["n"], result


def _count_engine_queries(db, fn):
    """Count DB statements across the WHOLE call, INCLUDING after an internal ``commit``.

    ``_count_queries`` binds its listener to a single ``Connection`` captured up front. An endpoint
    that commits mid-call (e.g. ``update_job_status`` / ``create_job``) checks out a NEW connection
    for its subsequent statements, which that listener never sees — so it silently under-counts and
    a POST-COMMIT N+1 (exactly what the re-read fixes) slips past. Listen on the ENGINE instead so
    every statement is counted regardless of which connection issues it."""
    engine = db.get_bind()
    count = {"n": 0}

    def _on_exec(*_args, **_kwargs):
        count["n"] += 1

    event.listen(engine, "after_cursor_execute", _on_exec)
    try:
        result = fn()
    finally:
        event.remove(engine, "after_cursor_execute", _on_exec)
    return count["n"], result


def test_list_jobs_is_not_n_plus_one(db_session):
    user2 = _seed_user_with_jobs(db_session, 2, "perf-jobs-a@example.com")
    db_session.expire_all()  # force fresh loads so the count reflects real fetches
    q2, _ = _count_queries(db_session, lambda: asgi.list_jobs(user=user2, db=db_session, limit=None, offset=0))

    user5 = _seed_user_with_jobs(db_session, 5, "perf-jobs-b@example.com")
    db_session.expire_all()
    q5, res5 = _count_queries(db_session, lambda: asgi.list_jobs(user=user5, db=db_session, limit=None, offset=0))

    # Constant query count regardless of job count (jobs + batched application/score/company).
    # The OLD 3N+1 would make q5 exceed q2 by ~9.
    assert q5 == q2, f"/api/jobs query count grew with job count (N+1): {q2} -> {q5}"

    # And the serialized output is real (eager-load returned the right data, not empty).
    assert len(res5["jobs"]) == 5
    assert res5["jobs"][0]["score"] is not None
    assert res5["jobs"][0]["status"] == ApplicationStatus.APPLIED.value


def test_get_job_detail_loads_relationships_in_one_query(db_session):
    """``GET /api/jobs/{id}`` serializes a SINGLE job via ``job_public``, which reads its
    application + score + company. Without eager-loading that's the object fetch plus three
    lazy-load round-trips (4 queries); ``joinedload`` pulls all three in ONE query. This pins
    the hot-path detail endpoint at a single DB round-trip so the lazy-loads can't creep back."""
    user = _seed_user_with_jobs(db_session, 1, "perf-detail@example.com")
    job_id = db_session.query(JobPosting).filter(JobPosting.user_id == user.id).first().id
    db_session.expire_all()  # force fresh loads so the count reflects real fetches
    _ = user.id  # reload the user OUTSIDE the measured region (in prod it's already loaded by
    #              the auth dependency) so the count reflects only the job-detail fetch
    n, res = _count_queries(db_session, lambda: asgi.get_job(job_id=job_id, user=user, db=db_session))

    assert n == 1, f"GET /api/jobs/{{id}} should load job + relationships in ONE query, got {n}"
    # And the eager-loaded data is real (the company path — company_name is None — resolved).
    assert res["job"]["score"] is not None
    assert res["job"]["status"] == ApplicationStatus.APPLIED.value
    assert res["job"]["company"] == "Acme 0"


def test_create_job_duplicate_resubmit_loads_relationships_in_one_query(db_session):
    """The ``POST /api/jobs`` idempotency guard re-serializes an ALREADY-tracked job via
    ``job_public`` (application + score) when the same posting is re-submitted (double-click /
    retry). Without eager-loading that's the lookup plus a lazy-load round-trip per relationship;
    ``joinedload`` pulls them in ONE LEFT JOIN. This pins the duplicate-add hot path at a single
    DB round-trip so the lazy-loads can't creep back (reverting to selectinload reddens it)."""
    user = User(email="perf-dup@example.com", password_hash="x", tier=UserTier.PREMIUM)
    db_session.add(user)
    db_session.flush()
    job = JobPosting(user_id=user.id, title="Staff Engineer", company_name="Acme", url=None)
    db_session.add(job)
    db_session.flush()
    db_session.add(Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.APPLIED))
    db_session.add(JobScore(job_id=job.id, overall_score=88.0, score_explanation="Strong"))
    db_session.flush()

    data = asgi.JobCreate(title="Staff Engineer", company_name="Acme")
    db_session.expire_all()  # force fresh loads so the count reflects real fetches
    _ = user.id  # reload the user OUTSIDE the measured region (in prod the auth dependency has
    #              already loaded it) so the count reflects only create_job's own round-trips
    n, res = _count_queries(
        db_session, lambda: asgi.create_job(data=data, user=user, db=db_session)
    )

    # Idempotent: the re-submit returns the EXISTING job, never inserts a duplicate.
    assert res["duplicate"] is True
    assert res["job"]["score"] == 88.0
    assert res["job"]["status"] == ApplicationStatus.APPLIED.value
    # ONE query: the joinedload lookup. The OLD selectinload issued the lookup + a separate
    # query per relationship (3–4 total). A regression to lazy/selectinload reddens this.
    assert n == 1, f"duplicate job re-submit should load in ONE query, got {n}"


def test_list_jobs_limit_is_additive_and_optional(db_session):
    """Omitting ``limit`` returns up to the default cap (bounded, never unbounded — see
    ``test_list_jobs_omitted_limit_is_bounded_not_unbounded``); supplying it pages the
    result. Here the 5 seeded jobs are well under the 500 default, so an omitted limit
    still returns all five."""
    user = _seed_user_with_jobs(db_session, 5, "perf-jobs-limit@example.com")
    db_session.expire_all()
    _, all_res = _count_queries(db_session, lambda: asgi.list_jobs(user=user, db=db_session, limit=None, offset=0))
    assert len(all_res["jobs"]) == 5  # 5 < default cap → all returned, no truncation

    db_session.expire_all()
    _, paged = _count_queries(
        db_session, lambda: asgi.list_jobs(user=user, db=db_session, limit=2, offset=0)
    )
    assert len(paged["jobs"]) == 2

    db_session.expire_all()
    _, offset_res = _count_queries(
        db_session, lambda: asgi.list_jobs(user=user, db=db_session, limit=2, offset=4)
    )
    assert len(offset_res["jobs"]) == 1  # 5 jobs, offset 4 -> the last one


def test_list_jobs_omitted_limit_is_bounded_not_unbounded(db_session, monkeypatch):
    """An omitted ``limit`` must NOT trigger an unbounded scan. Paid tiers have no job cap, so
    "return all" could load thousands of rows + serialize a multi-MB response on the dashboard
    hot path (every session restore), risking the serverless budget. Omitting ``limit`` now
    bounds to ``_JOBS_LIST_DEFAULT_LIMIT`` (the same ``le=500`` ceiling an explicit limit is
    capped at). Patched low here so the guard is fast + LOAD-BEARING: reverting the fix to an
    unbounded default (``if limit is not None: query = query.limit(limit)``) returns all 5 and
    reddens the first assertion."""
    monkeypatch.setattr(asgi, "_JOBS_LIST_DEFAULT_LIMIT", 3)
    user = _seed_user_with_jobs(db_session, 5, "perf-jobs-bounded@example.com")

    db_session.expire_all()
    _, res = _count_queries(
        db_session, lambda: asgi.list_jobs(user=user, db=db_session, limit=None, offset=0)
    )
    assert len(res["jobs"]) == 3, "omitted limit must be bounded by the default cap, not unbounded"

    # An explicit limit still overrides the default (and is itself route-capped at le=500).
    db_session.expire_all()
    _, res2 = _count_queries(
        db_session, lambda: asgi.list_jobs(user=user, db=db_session, limit=5, offset=0)
    )
    assert len(res2["jobs"]) == 5


def test_pipeline_stats_is_not_n_plus_one(db_session):
    user2 = _seed_user_with_jobs(db_session, 2, "perf-pipe-a@example.com")
    db_session.expire_all()
    q2, _ = _count_queries(db_session, lambda: asgi.pipeline_stats(user=user2, db=db_session))

    user5 = _seed_user_with_jobs(db_session, 5, "perf-pipe-b@example.com")
    db_session.expire_all()
    q5, res5 = _count_queries(db_session, lambda: asgi.pipeline_stats(user=user5, db=db_session))

    assert q5 == q2, f"/api/analytics/pipeline query count grew with job count (N+1): {q2} -> {q5}"

    # Aggregate is correct: 5 jobs, all APPLIED, avg of 70..74 = 72.0, top 5 returned.
    stats = res5["stats"]
    assert stats["total_jobs"] == 5
    assert stats["status_breakdown"][ApplicationStatus.APPLIED.value] == 5
    assert stats["average_score"] == 72.0
    assert len(stats["top_jobs"]) == 5


def test_pipeline_status_breakdown_and_avg_are_db_aggregated_correctly(db_session):
    """The DB-aggregated pipeline stats must preserve the EXACT semantics of the old in-Python
    loop: a job with NO application counts as SAVED, statuses group correctly, the average is
    over SCORED jobs only, and top_jobs is the score-DESC top 5. Reverting the GROUP BY to a
    naive query or dropping the NULL→SAVED coalesce reddens this."""
    user = User(email="pipe-agg@example.com", password_hash="x", tier=UserTier.PREMIUM)
    db_session.add(user)
    db_session.flush()

    def _job(title, *, status=None, score=None):
        job = JobPosting(user_id=user.id, title=title, company_name="Acme")
        db_session.add(job)
        db_session.flush()
        if status is not None:
            db_session.add(Application(user_id=user.id, job_id=job.id, status=status))
        if score is not None:
            db_session.add(JobScore(job_id=job.id, overall_score=score, score_explanation="ok"))
        return job

    # 2 jobs with NO application (→ SAVED), 1 explicitly SAVED, 2 APPLIED, 1 INTERVIEWING.
    _job("no-app-1")  # no application → SAVED
    _job("no-app-2", score=40.0)  # no application → SAVED, and scored
    _job("saved-1", status=ApplicationStatus.SAVED, score=90.0)
    _job("applied-1", status=ApplicationStatus.APPLIED, score=80.0)
    _job("applied-2", status=ApplicationStatus.APPLIED)  # unscored → excluded from avg
    _job("interview-1", status=ApplicationStatus.INTERVIEW, score=100.0)
    db_session.flush()

    stats = asgi.pipeline_stats(user=user, db=db_session)["stats"]

    assert stats["total_jobs"] == 6
    # The two application-less jobs fold into SAVED alongside the explicit one → 3 SAVED.
    assert stats["status_breakdown"] == {
        ApplicationStatus.SAVED.value: 3,
        ApplicationStatus.APPLIED.value: 2,
        ApplicationStatus.INTERVIEW.value: 1,
    }
    # Average over the 4 SCORED jobs only: (40 + 90 + 80 + 100) / 4 = 77.5 (unscored excluded).
    assert stats["average_score"] == 77.5
    # Top jobs are score-DESC: 100, 90, 80, 40 (the two unscored jobs never appear).
    top_titles = [j["title"] for j in stats["top_jobs"]]
    assert top_titles == ["interview-1", "saved-1", "applied-1", "no-app-2"]


def test_pipeline_stats_empty_user_is_zeroed_not_errored(db_session):
    """A user with zero jobs returns an honest zero state (no divide-by-zero on the average)."""
    user = User(email="pipe-empty@example.com", password_hash="x", tier=UserTier.PREMIUM)
    db_session.add(user)
    db_session.flush()
    stats = asgi.pipeline_stats(user=user, db=db_session)["stats"]
    assert stats["total_jobs"] == 0
    assert stats["status_breakdown"] == {}
    assert stats["average_score"] == 0.0
    assert stats["top_jobs"] == []


def test_update_job_status_does_not_n_plus_one_on_serialization(db_session):
    """``PATCH /api/jobs/{id}`` re-serializes the updated job via ``job_public`` (application +
    score + company). ``commit`` expires those relationships, so without an eager re-read the
    response lazy-loads all three — 3 extra round-trips on the hot pipeline-tracking write path.
    The fix re-reads the row with ``joinedload`` (one LEFT JOIN). This pins the endpoint's total
    query count well below the OLD lazy-load path so the N+1 cannot silently return."""
    user = _seed_user_with_jobs(db_session, 1, "perf-patch@example.com")
    job_id = db_session.query(JobPosting).filter(JobPosting.user_id == user.id).first().id
    data = asgi.JobUpdate(status=ApplicationStatus.INTERVIEW.value)
    db_session.expire_all()  # force fresh loads so the count reflects real fetches
    _ = user.id  # reload the user OUTSIDE the measured region (the auth dependency already
    #              loaded it in prod) so the count reflects only the PATCH's own round-trips
    # ENGINE-level count: the endpoint commits mid-call, so a connection-scoped listener would
    # stop seeing statements right where the N+1 lives (post-commit serialization). This spans it.
    n, res = _count_engine_queries(
        db_session,
        lambda: asgi.update_job_status(job_id=job_id, data=data, user=user, db=db_session),
    )

    # Correct outcome: the new status persisted and the eager-loaded relationships are real.
    assert res["job"]["status"] == ApplicationStatus.INTERVIEW.value
    assert res["job"]["score"] is not None
    assert res["job"]["company"] == "Acme 0"  # company_name is None → dereferences the relationship
    # fetch job + load its application + the UPDATE + ONE joinedload re-read = 4. The OLD
    # refresh()+lazy path issued a refresh SELECT plus a lazy application/score/company load each
    # (7). Reverting to db.refresh + lazy job_public (or filtering the re-read on the expired
    # job.id, which adds a refresh SELECT) pushes n back over 4 and reddens this.
    assert n <= 4, f"PATCH /api/jobs/{{id}} N+1 on job_public serialization: {n} queries"


def test_create_job_new_job_serialization_is_eager_not_lazy(db_session):
    """``POST /api/jobs`` (the NEW-job path, not the dedup early-return) commits, then serializes
    the created job via ``job_public``. The old tail was ``db.refresh(job)`` + lazy ``job_public``
    — a wasted refresh SELECT plus a lazy load per read relationship AFTER the commit. The fix
    captures the PK before committing and re-reads once with ``joinedload``. The engine-level count
    (which spans the internal commit — a connection-scoped counter would miss the tail entirely)
    pins the total so reverting to the refresh()+lazy tail reddens it."""
    user = User(
        email="perf-create@example.com", password_hash="x", tier=UserTier.PREMIUM,
        resume_text="python react",
    )
    db_session.add(user)
    db_session.flush()
    data = asgi.JobCreate(title="Engineer", description="python and react role", company_name="Acme")
    db_session.expire_all()  # force fresh loads so the count reflects real fetches
    _ = user.id  # reload the user OUTSIDE the measured region (auth dependency loads it in prod)

    n, res = _count_engine_queries(
        db_session, lambda: asgi.create_job(data=data, user=user, db=db_session)
    )

    # The created job is returned with real data from the eager re-read (SAVED application + score).
    assert res.get("duplicate") is not True
    assert res["job"]["status"] == ApplicationStatus.SAVED.value
    assert res["job"]["score"] is not None  # heuristic score present (no key needed)
    # Load-bearing bound: the fixed tail is ONE joinedload re-read (measured: 12 statements for the
    # whole add path). The OLD tail (db.refresh + job_public lazy-loading application + score — the
    # company path short-circuits on the truthy company_name) issues SEVERAL more after the commit
    # (a refresh SELECT + one lazy load per read relationship), pushing n over this bound on revert.
    assert n <= 12, f"create_job N+1 on the add path: {n} statements (a refresh()+lazy tail adds ≥2)"


def _capture_user_selects(db, fn):
    """Run ``fn`` and return (count of ``SELECT ... FROM users`` statements, result).

    ``recompute_user_tier`` reads a user's entitlement from the SUBSCRIPTIONS and
    ORGANIZATION_MEMBERS tables — never the ``users`` table — so the ONLY ``FROM users`` reads
    during ``_recompute_all_member_tiers`` are the member-user loads. Counting them isolates
    the exact N+1 the bulk load fixes, independent of recompute's own per-user query cost."""
    engine = db.get_bind()
    selects = {"n": 0}

    def _on_exec(_conn, _cur, statement, *_a, **_k):
        s = statement.lower()
        if s.startswith("select") and "from users" in s:
            selects["n"] += 1

    event.listen(engine, "after_cursor_execute", _on_exec)
    try:
        result = fn()
    finally:
        event.remove(engine, "after_cursor_execute", _on_exec)
    return selects["n"], result


def _seed_org_with_members(db, n: int, label: str):
    """An ACTIVE org (enough seats) with an owner + ``n`` active members, each a distinct user."""
    from src.db.models import Organization, OrganizationMember

    owner = User(email=f"org-owner-{label}@example.com", password_hash="x", tier=UserTier.FREE)
    db.add(owner)
    db.flush()
    org = Organization(
        name=f"Acme {label}", owner_id=owner.id, plan="team_annual",
        status="active", seats_purchased=n + 1,
    )
    db.add(org)
    db.flush()
    for i in range(n):
        m = User(email=f"org-member-{label}-{i}@example.com", password_hash="x", tier=UserTier.FREE)
        db.add(m)
        db.flush()
        db.add(OrganizationMember(org_id=org.id, user_id=m.id, role="member", active=True))
    db.flush()
    return org


def test_recompute_all_member_tiers_bulk_loads_users_not_n_plus_one(db_session):
    """The org-webhook tier reconciliation must load its member users in ONE query, not one per
    member. It runs on the synchronous Stripe org-webhook path (seat created/updated/deleted), so a
    per-member ``SELECT ... FROM users`` is an N+1 that scales with the org (up to MAX_SEATS) against
    the serverless budget. Counting ONLY ``FROM users`` statements isolates the member-user load
    (``recompute_user_tier`` reads subscriptions/org_members, never users), so this reddens the moment
    the bulk ``User.id.in_(...)`` load reverts to a per-member ``User.id == m.user_id`` query."""
    import src.org_billing as org_billing

    org2 = _seed_org_with_members(db_session, 2, "a")
    db_session.expire_all()
    u2, _ = _capture_user_selects(
        db_session, lambda: org_billing._recompute_all_member_tiers(db_session, org2)
    )

    org5 = _seed_org_with_members(db_session, 5, "b")
    db_session.expire_all()
    u5, _ = _capture_user_selects(
        db_session, lambda: org_billing._recompute_all_member_tiers(db_session, org5)
    )

    # CONSTANT: exactly one bulk user load regardless of member count. The OLD per-member query
    # made this equal the member count (2 then 5), so reverting the bulk load reddens both asserts.
    assert u2 == 1, f"expected 1 bulk user load for 2 members, got {u2} (per-member N+1?)"
    assert u5 == 1, f"expected 1 bulk user load for 5 members, got {u5} (per-member N+1?)"
