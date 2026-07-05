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

pytestmark = pytest.mark.live


def setup_module(module):
    # §28: skip in local/dev (no key expected) but FAIL LOUD in the nightly lane
    # (REQUIRE_LIVE_TESTS=1) if the real key is unexpectedly absent — never skip-green.
    from tests.live_guard import require_live_key

    require_live_key(LIVE_KEY, "GEMINI_API_KEY")


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


def test_cover_letter_real_output_is_substantive_and_relevant(db_session, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)  # restore the real key (conftest blanked it)
    from src.enrichment.llm_workflows import LLMWorkflows

    user, job = _seed(db_session)
    artifact = LLMWorkflows(db_session).generate_cover_letter(job, user)
    content = artifact.content or ""

    assert isinstance(artifact, PrepArtifact) and artifact.artifact_type == "cover_letter"
    assert len(content) > 150, f"cover letter too short to be real output: {len(content)} chars"
    low = content.lower()
    assert any(t in low for t in ("acme", "backend", "python", "engineer", "role")), \
        f"cover letter reads off-topic (not about the role): {content[:200]!r}"


def test_study_plan_real_output_is_substantive_and_structured(db_session, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)
    from src.enrichment.llm_workflows import LLMWorkflows

    user, job = _seed(db_session)
    artifact = LLMWorkflows(db_session).generate_study_plan(job, days=5)
    content = artifact.content or ""

    assert isinstance(artifact, PrepArtifact) and artifact.artifact_type == "study_plan"
    assert len(content) > 200, f"study plan too short to be real output: {len(content)} chars"
    low = content.lower()
    assert "day" in low, f"study plan lacks any day-by-day structure: {content[:200]!r}"
    assert any(t in low for t in ("backend", "python", "system", "practice", "study", "interview")), \
        f"study plan reads off-topic: {content[:200]!r}"


def test_tailored_resume_real_output_is_grounded_and_structured(db_session, monkeypatch):
    """The tailored résumé must be substantive, structured, and — critically — GROUNDED in the
    candidate's REAL résumé (it references the genuine skills present in the source), not a
    fabricated history. The seeded résumé names Python/FastAPI/AWS/Kubernetes; a real tailored
    output surfaces those true skills for a matching backend role."""
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)
    from src.enrichment.llm_workflows import LLMWorkflows

    user, job = _seed(db_session)  # résumé: Python/FastAPI/PostgreSQL/AWS/Docker/Kubernetes
    artifact = LLMWorkflows(db_session).generate_tailored_resume(job, user)
    content = artifact.content or ""
    low = content.lower()

    assert isinstance(artifact, PrepArtifact) and artifact.artifact_type == "tailored_resume"
    assert len(content) > 200, f"tailored résumé too short to be real output: {len(content)} chars"
    # Grounded in the REAL résumé: at least two of the source's genuine skills survive the rewrite
    # (a fabricated or off-topic résumé would not echo the candidate's actual stack).
    real_skills = [s for s in ("python", "fastapi", "postgres", "aws", "docker", "kubernetes") if s in low]
    assert len(real_skills) >= 2, \
        f"tailored résumé does not reference the candidate's real skills (grounding check): {content[:200]!r}"


def test_learning_plan_real_output_is_substantive_and_covers_the_gaps(db_session, monkeypatch):
    """The AI learning plan must be substantive, structured markdown, and actually address the
    supplied skill gaps (not drift onto unrelated skills). Tolerant assertions (length / at least
    one gap skill named / a markdown heading) — a real regression that returns empty/off-topic
    output reddens, while normal phrasing variation does not."""
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)
    from src.enrichment.llm_workflows import LLMWorkflows

    user, _ = _seed(db_session)
    gap_skills = ["kubernetes", "terraform", "go"]
    content = LLMWorkflows(db_session).generate_learning_plan(
        gap_skills, ["Platform Engineer", "Site Reliability Engineer"], user
    )
    assert isinstance(content, str) and len(content) > 200, \
        f"learning plan too short to be real output: {len(content or '')} chars"
    low = content.lower()
    # At least one of the supplied gaps is actually addressed (not a generic off-topic essay).
    assert any(s in low for s in gap_skills), \
        f"learning plan does not name any of the supplied gap skills: {content[:200]!r}"
    assert "#" in content, "learning plan is not structured markdown (no heading)"


def test_salary_negotiation_real_output_is_substantive_and_on_topic(db_session, monkeypatch):
    """The Career+ salary-negotiation guide is the ONE generator that had no real-output eval.
    Its real Gemini output must be substantive, structured, and actually about negotiating the
    offer (scripts / counter-offer / compensation) — not off-topic filler. Tolerant assertions
    (length / a negotiation keyword / markdown) so normal wording variation doesn't flake."""
    monkeypatch.setenv("GEMINI_API_KEY", LIVE_KEY)  # restore the real key (conftest blanked it)
    from src.enrichment.llm_workflows import LLMWorkflows

    user, job = _seed(db_session)
    artifact = LLMWorkflows(db_session).generate_salary_negotiation(job, target_salary=180000)
    content = artifact.content or ""

    assert isinstance(artifact, PrepArtifact) and artifact.artifact_type == "salary_negotiation"
    assert len(content) > 200, f"salary guide too short to be real output: {len(content)} chars"
    low = content.lower()
    assert any(t in low for t in ("negotiat", "salary", "offer", "counter", "compensation")), \
        f"salary guide reads off-topic (not about negotiation): {content[:200]!r}"
    assert any(ch in content for ch in ("#", "-", "1.", "2.")), \
        "salary guide lacks any structure (no heading or list)"


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
    # This eval exists to exercise the REAL Gemini embedding path, so opt in explicitly.
    # (score_job now defaults use_embeddings=False — fail-closed for third-party-AI consent,
    # Apple 5.1.2(i) — so the embedding path must be requested deliberately, as the HTTP
    # create_job route does only after a consent check.)
    score = JobScorer(db_session).score_job(job, user, use_embeddings=True)

    assert score.overall_score is not None and 0 <= float(score.overall_score) <= 100, \
        f"invalid score: {score.overall_score!r}"
    # the REAL embedding path ran (not the heuristic-only fallback): a real resume vector was stored
    vec = user.resume_embedding
    if isinstance(vec, str):
        vec = json.loads(vec)
    assert isinstance(vec, list) and len(vec) > 100, "real embedding was not produced/stored during scoring"
    assert score.score_explanation and score.score_explanation.strip(), "empty score explanation"
