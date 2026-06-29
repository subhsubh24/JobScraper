"""Coverage for LLMWorkflows paths the prep-pack eval didn't reach: structured JSON
parsing (parse_job_description, json_mode) and the key-absent guard in _call_llm.

The output-moderation safety net is already covered end-to-end with the REAL moderator in
tests/test_prep_moderation.py, so it is not re-tested here. Deterministic + key-free: the
LLM client is faked."""
import json

import pytest

from src.db.models import JobPosting, User, UserTier
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
