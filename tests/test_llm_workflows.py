"""Coverage for LLMWorkflows paths the prep-pack eval didn't reach: structured JSON
parsing, the key-absent guard, and — crucially for store review (Apple §1.2 / Google UGC) —
the OUTPUT-moderation safety net that swallows unsafe model output before a user sees it.

Deterministic + key-free: the LLM client is faked, and the moderation WIRING is tested by
swapping in a fake moderator (so the assertion isn't coupled to the regex internals, which
are tested directly in tests/test_coach_safety.py)."""
import json

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


class _Verdict:
    def __init__(self, allowed, safe_response=None):
        self.allowed = allowed
        self.safe_response = safe_response


class _FakeModerator:
    def __init__(self, verdict):
        self._verdict = verdict

    def check_output(self, _content):
        return self._verdict


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


def test_unsafe_prep_output_is_replaced_with_safe_response(db_session):
    """The OUTPUT moderation net must replace clearly-unsafe model output with the safe
    decline text — a user must never see unmoderated unsafe AI content (store requirement)."""
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("...unsafe model output...")
    wf.moderator = _FakeModerator(_Verdict(allowed=False, safe_response="[blocked: see guidelines]"))

    artifact = wf.generate_prep_pack(job, user)

    assert artifact.content == "[blocked: see guidelines]"
    # And it's the swapped-in safe text that is persisted, not the unsafe output.
    row = db_session.query(PrepArtifact).filter(PrepArtifact.job_id == job.id).first()
    assert row is not None and "unsafe" not in (row.content or "")


def test_safe_prep_output_passes_through(db_session):
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("## 1. Company Research Summary\nGlobex builds ETL tools.")
    wf.moderator = _FakeModerator(_Verdict(allowed=True))

    artifact = wf.generate_prep_pack(job, user)

    assert "Company Research Summary" in artifact.content


def test_call_llm_raises_without_configured_client(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = None
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        wf._call_llm("sys", "user")
