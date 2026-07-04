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


class _SequenceFakeLLM:
    """Returns queued completions in order — so a generation's DRAFT call and its subsequent
    REVIEW-and-revise call can return DIFFERENT content, letting the tests prove the
    drafter→reviewer pass actually runs and the REFINED text is what gets persisted."""

    def __init__(self, *contents):
        self._contents = list(contents)
        self.calls = 0
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        idx = min(self.calls, len(self._contents) - 1)
        content = self._contents[idx]
        self.calls += 1

        class _M:
            pass

        _M.content = content

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


# ---------------------------------------------------------------------------
# Drafter→reviewer pass (product-side maker≠checker, ROADMAP Track A). The generator makes TWO
# LLM calls per artifact: a DRAFT, then one review-and-revise. These evals pin that the REFINED
# text is what's persisted, that the pass is fail-SAFE (any refine failure falls back to the clean
# draft — it can only improve, never break), that it's togglable for COGS, and that the internal
# JSON-parsing path is NOT refined.
# ---------------------------------------------------------------------------


def test_refinement_pass_persists_the_reviewed_version_not_the_draft(db_session, monkeypatch):
    monkeypatch.setenv("ENABLE_ARTIFACT_REFINEMENT", "1")
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    # 1st call = the weaker DRAFT; 2nd call = the improved REVIEWED version.
    wf.client = _SequenceFakeLLM(
        "Dear Hiring Manager, I want the job. I am good.",
        "Dear Hiring Manager,\nHaving shipped Python and React systems, I'm excited to bring that "
        "to the Backend Engineer role at Acme.",
    )

    artifact = wf.generate_cover_letter(job, user)

    assert wf.client.calls == 2  # draft + one review-and-revise
    assert "excited to bring that" in artifact.content  # the REVIEWED text was persisted
    assert artifact.content != "Dear Hiring Manager, I want the job. I am good."


def test_refinement_falls_back_to_draft_when_review_call_fails(db_session, monkeypatch):
    """Fail-SAFE: if the review-and-revise call errors, the already-valid, already-moderated
    draft is what's persisted — the pass never breaks or worsens a generation."""
    monkeypatch.setenv("ENABLE_ARTIFACT_REFINEMENT", "1")
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    draft = "## Ada Dev\nSenior engineer — Python, React. Solid, honest draft."
    wf.client = _FakeLLM(draft)

    original_call = wf._call_llm
    calls = {"n": 0}

    def flaky(system_prompt, user_prompt, json_mode=False):
        calls["n"] += 1
        if calls["n"] == 1:
            return original_call(system_prompt, user_prompt, json_mode=json_mode)  # draft OK
        raise RuntimeError("provider 503 on the review pass")

    monkeypatch.setattr(wf, "_call_llm", flaky)

    artifact = wf.generate_tailored_resume(job, user)

    assert calls["n"] == 2  # draft succeeded, review attempted then failed
    assert artifact.content == draft  # fell back to the clean draft — no break, no worse output


def test_refinement_can_be_disabled_for_cost(db_session, monkeypatch):
    """The COGS lever (§24): with the flag off, exactly ONE call is made and the draft is used."""
    monkeypatch.setenv("ENABLE_ARTIFACT_REFINEMENT", "0")
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _SequenceFakeLLM(
        "## Day 1\nDraft plan.",
        "## Day 1\nThis reviewed version must NOT appear when refinement is disabled.",
    )

    artifact = wf.generate_study_plan(job, days=5)

    assert wf.client.calls == 1  # no second (review) call
    assert "Draft plan" in artifact.content
    assert "must NOT appear" not in artifact.content


def test_refined_blank_falls_back_to_draft(db_session, monkeypatch):
    """A review pass that returns blank must not blank the artifact — fall back to the draft."""
    monkeypatch.setenv("ENABLE_ARTIFACT_REFINEMENT", "1")
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    draft = "Dear Hiring Manager,\nA genuine, specific cover letter about the Backend role."
    # Draft is real; the review call returns whitespace (which _call_llm would itself reject) —
    # _refine swallows that and keeps the draft.
    wf.client = _SequenceFakeLLM(draft, "   ")

    artifact = wf.generate_cover_letter(job, user)

    assert artifact.content == draft


def test_json_parsing_path_is_not_refined(db_session, monkeypatch):
    """parse_job_description is internal JSON plumbing (json_mode), never shown to the user, so it
    must make exactly one call and skip the prose review pass."""
    monkeypatch.setenv("ENABLE_ARTIFACT_REFINEMENT", "1")
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _SequenceFakeLLM('{"required_skills": ["python"]}', '{"required_skills": ["nope"]}')

    result = wf.parse_job_description(job)

    assert wf.client.calls == 1  # json_mode path is not refined
    assert result == {"required_skills": ["python"]}
