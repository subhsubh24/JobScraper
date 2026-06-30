"""Coverage for LLMWorkflows paths the prep-pack eval didn't reach: structured JSON
parsing (parse_job_description, json_mode) and the key-absent guard in _call_llm.

The output-moderation safety net is already covered end-to-end with the REAL moderator in
tests/test_prep_moderation.py, so it is not re-tested here. Deterministic + key-free: the
LLM client is faked."""
import json

import pytest

from src.db.models import JobPosting, PrepArtifact, User, UserTier
from src.enrichment.llm_workflows import LLMWorkflows


class _NoChoicesLLM:
    """A malformed completion with no choices (IndexError on choices[0])."""

    def __init__(self):
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        class _R:
            choices = []

        return _R()


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
    user = User(email="wf@example.com", password_hash="x", tier=UserTier.PREMIUM, resume_text="python aws")
    db.add(user)
    db.flush()
    job = JobPosting(user_id=user.id, title="Data Engineer", company_name="Globex", description="etl role")
    db.add(job)
    db.flush()
    return user, job


def test_parse_job_description_returns_parsed_json(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(json.dumps({"required_skills": ["python", "sql"], "experience_years": 5}))
    _, job = _seed(db_session)

    parsed = wf.parse_job_description(job)

    assert parsed["required_skills"] == ["python", "sql"]
    assert parsed["experience_years"] == 5


def test_call_llm_raises_without_configured_client(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = None
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        wf._call_llm("sys", "user")


# ---- Generator persistence contract (monetized features that had ZERO tests) ----

def test_generate_study_plan_persists_artifact(db_session):
    _, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("Day 1: Morning — algorithms.\nDay 2: Afternoon — system design.")

    artifact = wf.generate_study_plan(job, days=7)

    assert artifact.artifact_type == "study_plan"
    assert artifact.job_id == job.id
    assert "7-Day Study Plan" in artifact.title
    assert "Day 1" in artifact.content
    assert db_session.query(PrepArtifact).filter(PrepArtifact.job_id == job.id).count() == 1


def test_generate_cover_letter_persists_artifact(db_session):
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("Dear Hiring Manager,\n\nI am excited to apply...")

    artifact = wf.generate_cover_letter(job, user)

    assert artifact.artifact_type == "cover_letter"
    assert artifact.job_id == job.id
    assert "Cover Letter" in artifact.title and "Globex" in artifact.title
    assert "Hiring Manager" in artifact.content


def test_generate_salary_negotiation_persists_artifact(db_session):
    _, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("1. Research talking points\n2. Initial offer response script")

    artifact = wf.generate_salary_negotiation(job, target_salary=150000)

    assert artifact.artifact_type == "salary_negotiation"
    assert artifact.job_id == job.id
    assert artifact.content.startswith("1. Research")


# ---- Empty / malformed completions must FAIL LOUD, never a blank "success" ----

def test_empty_completion_fails_loud_not_a_blank_artifact(db_session):
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("   ")  # whitespace-only — not a real prep pack

    with pytest.raises(RuntimeError):
        wf.generate_prep_pack(job, user)
    assert db_session.query(PrepArtifact).filter(PrepArtifact.job_id == job.id).count() == 0


def test_none_completion_fails_loud(db_session):
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(None)

    with pytest.raises(RuntimeError):
        wf.generate_cover_letter(job, user)


def test_parse_job_description_empty_response_raises_not_crashes(db_session):
    _, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("")  # json.loads("") would ValueError without the guard

    with pytest.raises(RuntimeError):
        wf.parse_job_description(job)


def test_malformed_completion_no_choices_fails_loud(db_session):
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _NoChoicesLLM()

    with pytest.raises(RuntimeError):
        wf.generate_prep_pack(job, user)
