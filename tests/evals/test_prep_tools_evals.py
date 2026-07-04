"""Evals for the newly-wired prep-tool generators — cover letter + study plan (issue #222).

Same discipline as test_prep_pack_evals.py: the LLM call is the only non-deterministic part, so
we patch it with a fake client and assert each PrepArtifact is persisted with the right shape
(type/title/content/model) — fully deterministic, no Gemini key. This guards the artifact
contract for the two generators that previously had ZERO direct coverage (they were unrouted).

It also pins the SIDE-EFFECT INTEGRITY behaviour of the shared ``_call_llm`` chokepoint:
BOTH an empty/blank completion AND clearly-unsafe (moderator-flagged) output FAIL LOUD (raise)
rather than becoming a persisted "generated" artifact — so the endpoint charges no usage and
claims no success on either. Both paths matter now that two more user-facing features flow
through them.
"""
import pytest

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
    user = User(
        email="tools@example.com",
        password_hash="x",
        tier=UserTier.PREMIUM,
        full_name="Ada Dev",
        resume_text="python react",
    )
    db.add(user)
    db.flush()
    job = JobPosting(user_id=user.id, title="Backend Engineer", company_name="Acme", description="python role")
    db.add(job)
    db.flush()
    return user, job


def test_generate_cover_letter_persists_artifact(db_session):
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("Dear Hiring Manager,\nI am excited to apply for the Backend Engineer role.")

    artifact = wf.generate_cover_letter(job, user)

    assert isinstance(artifact, PrepArtifact)
    assert artifact.artifact_type == "cover_letter"
    assert artifact.job_id == job.id
    assert "Backend Engineer" in artifact.title and "Acme" in artifact.title
    assert artifact.content and "Hiring Manager" in artifact.content
    assert artifact.model_used

    rows = db_session.query(PrepArtifact).filter(PrepArtifact.job_id == job.id).all()
    assert len(rows) == 1 and rows[0].artifact_type == "cover_letter"


def test_generate_study_plan_persists_artifact_with_day_count(db_session):
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("## Day 1\nMorning: data structures.\n## Day 2\nSystem design.")

    artifact = wf.generate_study_plan(job, days=10)

    assert isinstance(artifact, PrepArtifact)
    assert artifact.artifact_type == "study_plan"
    assert artifact.job_id == job.id
    assert "10-Day" in artifact.title  # the requested day count reaches the artifact title
    assert artifact.content and "Day 1" in artifact.content
    assert artifact.model_used

    rows = db_session.query(PrepArtifact).filter(PrepArtifact.job_id == job.id).all()
    assert len(rows) == 1 and rows[0].artifact_type == "study_plan"


def test_generate_tailored_resume_persists_artifact(db_session):
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("## Ada Dev\nSenior engineer — Python, React. Tailored for the Backend role.")

    artifact = wf.generate_tailored_resume(job, user)

    assert isinstance(artifact, PrepArtifact)
    assert artifact.artifact_type == "tailored_resume"
    assert artifact.job_id == job.id
    assert "Backend Engineer" in artifact.title and "Acme" in artifact.title
    assert artifact.content and "Ada Dev" in artifact.content
    assert artifact.model_used

    rows = db_session.query(PrepArtifact).filter(PrepArtifact.job_id == job.id).all()
    assert len(rows) == 1 and rows[0].artifact_type == "tailored_resume"


def test_tailored_resume_blank_completion_fails_loud(db_session):
    """An empty completion must raise (honest 502 upstream), never persist a blank 'tailored'
    résumé and report success — SIDE-EFFECT INTEGRITY (§6)."""
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("   ")  # whitespace-only == empty
    with pytest.raises(RuntimeError):
        wf.generate_tailored_resume(job, user)
    assert db_session.query(PrepArtifact).filter(PrepArtifact.job_id == job.id).count() == 0


def test_cover_letter_blank_completion_fails_loud(db_session):
    """An empty LLM completion must raise (honest 502 upstream), never persist a blank
    'generated' cover letter and report success — SIDE-EFFECT INTEGRITY (§6)."""
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("   ")  # whitespace-only == empty
    with pytest.raises(RuntimeError):
        wf.generate_cover_letter(job, user)
    # Nothing was persisted.
    assert db_session.query(PrepArtifact).filter(PrepArtifact.job_id == job.id).count() == 0
