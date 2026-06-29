"""Eval for the prep-pack generator's persistence path (Track E).

generate_prep_pack is a monetized feature (gated behind the Pro/Premium prep limit) but had no
test on its STRUCTURE/persistence. The LLM call is the only non-deterministic part, so we patch
it with a fake client and assert the PrepArtifact is persisted with the right shape — fully
deterministic, no Gemini key. This guards the artifact contract (type/title/content/model).
"""
from src.db.models import JobPosting, PrepArtifact, User, UserTier
from src.enrichment.llm_workflows import LLMWorkflows


class _FakeLLM:
    def __init__(self, content: str):
        self._content = content
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        class _M:
            content = self._content

        class _C:
            message = _M()

        class _R:
            choices = [_C()]

        return _R()


def _seed(db):
    user = User(email="prep@example.com", password_hash="x", tier=UserTier.PREMIUM, resume_text="python react")
    db.add(user)
    db.flush()
    job = JobPosting(user_id=user.id, title="Backend Engineer", company_name="Acme", description="python role")
    db.add(job)
    db.flush()
    return user, job


def test_generate_prep_pack_persists_artifact(db_session):
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("## 1. Company Research\nAcme builds things.\n## 4. Technical Questions\n...")

    artifact = wf.generate_prep_pack(job, user)

    assert isinstance(artifact, PrepArtifact)
    assert artifact.artifact_type == "prep_pack"
    assert artifact.job_id == job.id
    assert "Backend Engineer" in artifact.title and "Acme" in artifact.title
    assert artifact.content and "Company Research" in artifact.content
    assert artifact.model_used  # records which model produced it

    # It is actually persisted (queryable on the same session), exactly once.
    rows = db_session.query(PrepArtifact).filter(PrepArtifact.job_id == job.id).all()
    assert len(rows) == 1 and rows[0].artifact_type == "prep_pack"


# A realistic, complete prep pack matching the 7-section contract the generator prompts for.
_GOLDEN_PREP = """## 1. Company Research Summary
Acme builds developer tooling. Recently raised a Series B.

## 2. Role Analysis
Owns the backend platform; must-have Python, nice-to-have Go.

## 3. Your Fit Story
Lead with your FastAPI + Postgres experience; address the Kubernetes gap.

## 4. Technical Interview Questions (10 questions)
1. Explain DB indexing. 2. Design a rate limiter. ... 10. Debug a deadlock.

## 5. Behavioral Interview Questions (8 questions)
1. Tell me about a conflict. ... 8. A time you failed.

## 6. Questions to Ask Them (5 questions)
1. What does success look like in 90 days? ... 5. How is on-call handled?

## 7. 48-Hour Study Plan
Day 1: systems design. Day 2: behavioral + company research.
"""


def test_generate_prep_pack_content_has_all_seven_sections(db_session):
    """Golden CONTENT eval (not just persistence): a complete prep pack must contain every
    one of the 7 prompted sections. Guards a regression where the artifact persists but the
    content is truncated/missing sections — the structure the monetized feature promises."""
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(_GOLDEN_PREP)

    artifact = wf.generate_prep_pack(job, user)

    required_sections = [
        "Company Research Summary",
        "Role Analysis",
        "Your Fit Story",
        "Technical Interview Questions",
        "Behavioral Interview Questions",
        "Questions to Ask Them",
        "48-Hour Study Plan",
    ]
    for section in required_sections:
        assert section in artifact.content, f"prep pack missing section: {section}"
    # All seven numbered markdown headers are present (## 1. .. ## 7.).
    for n in range(1, 8):
        assert f"## {n}." in artifact.content
