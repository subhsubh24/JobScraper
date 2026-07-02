"""REAL-OUTPUT quality evals — judge the ACTUAL Gemini output of each AI feature.

The other eval suites are deterministic (they pin the heuristic math / prep-pack structure with
a FAKE LLM). These run ONLY when a real GEMINI_API_KEY is available in CI (conftest stashes it in
GEMINI_API_KEY_LIVE; see tests/test_llm_live.py), restore the key for their own calls, and assert
the REAL generated output is substantive, on-topic, and structured — so a prompt/parse/model
regression that DEGRADES real output is caught, not just a broken import. Assertions are tolerant
of model wording (no exact-string match) so this stays reliable as a required gate.

Every LLM-using module in src/ must be covered here (enforced by scripts/check_eval_coverage.py).
"""
import json
import os

import pytest

from src.db.models import JobPosting, PrepArtifact, User, UserTier

LIVE_KEY = os.getenv("GEMINI_API_KEY_LIVE") or os.getenv("GEMINI_API_KEY") or ""

pytestmark = pytest.mark.skipif(
    not LIVE_KEY,
    reason="No real GEMINI_API_KEY in CI — real-output evals skipped (degraded mode). "
    "See OWNER_ACTION validation-capability-gemini.",
)


def _seed(db, tier=UserTier.PREMIUM):
    user = User(
        email=f"eval-{tier.value}@example.com",
        password_hash="x",
        tier=tier,
        resume_text=("Senior Python engineer. FastAPI, PostgreSQL, AWS, Docker, Kubernetes; "
                     "led backend teams and designed distributed systems."),
    )
    db.add(user)
    db.flush()
    job = JobPosting(
        user_id=user.id,
        title="Senior Backend Engineer",
        company_name="Acme",
        location="Remote US",
        description="Build Python/FastAPI services on PostgreSQL and AWS. Kubernetes, Docker, CI/CD.",
        requirements="5+ years Python, SQL, AWS, distributed systems.",
    )
    db.add(job)
    db.flush()
    return user, job


def test_prep_pack_real_output_is_substantive_relevant_and_structured(db_session, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)  # restore the real key (conftest blanked it)
    from src.enrichment.llm_workflows import LLMWorkflows

    user, job = _seed(db_session)
    artifact = LLMWorkflows(db_session).generate_prep_pack(job, user)
    content = artifact.content or ""

    assert isinstance(artifact, PrepArtifact)
    assert len(content) > 400, f"prep pack too short to be real output: {len(content)} chars"
    low = content.lower()
    assert any(t in low for t in ("acme", "backend", "python", "interview")), \
        f"prep pack reads off-topic (not about the role): {content[:200]!r}"
    assert ("##" in content) or ("\n-" in content) or ("\n*" in content), \
        "prep pack lacks the requested markdown structure"


def test_coach_real_answer_is_substantive_and_on_topic(db_session, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)
    from src.ai_coach.career_coach import CareerCoach

    user, _ = _seed(db_session)
    answer = CareerCoach(db_session).chat(
        user, "How should I prepare for a senior backend engineer interview?"
    )
    assert isinstance(answer, str) and len(answer.strip()) > 80, f"coach answer too short/empty: {answer!r}"
    low = answer.lower()
    assert any(t in low for t in
               ("interview", "prepare", "experience", "skill", "system", "practice", "question", "role")), \
        f"coach answer reads off-topic: {answer[:200]!r}"


def test_fit_score_real_embedding_path_produces_a_valid_score(db_session, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)  # restore the real key so embeddings are real
    from src.ranking.scorer import JobScorer

    user, job = _seed(db_session)
    score = JobScorer(db_session).score_job(job, user)

    assert score.score is not None and 0 <= float(score.score) <= 100, f"invalid score: {score.score!r}"
    # the REAL embedding path ran (not the heuristic-only fallback): a real resume vector was stored
    vec = user.resume_embedding
    if isinstance(vec, str):
        vec = json.loads(vec)
    assert isinstance(vec, list) and len(vec) > 100, "real embedding was not produced/stored during scoring"
    assert score.score_explanation and score.score_explanation.strip(), "empty score explanation"
