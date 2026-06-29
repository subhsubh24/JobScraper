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
