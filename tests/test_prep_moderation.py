"""Prep-pack output moderation (Apple App Review §1.2 / Google UGC policy).

The AI coach already moderated its output, but prep packs / cover letters / study plans /
negotiation scripts did not — an asymmetry the store-acceptance audit flagged. LLMWorkflows
now screens every user-facing generation through the same conservative ContentModerator the
coach uses. These tests prove: clearly-unsafe output is replaced with the safe decline,
normal interview-prep prose passes untouched, the internal JSON-parsing path is NOT
moderated (so structured parsing can't silently break), and the end-to-end prep-pack
artifact carries the moderated content.
"""
from types import SimpleNamespace

from src.ai_coach.moderation import DECLINE_RESPONSE
from src.db.models import JobPosting, User, UserTier
from src.enrichment.llm_workflows import LLMWorkflows


class _FakeClient:
    """Minimal stand-in for the OpenAI-compatible client returning a fixed completion."""

    def __init__(self, content):
        self._content = content
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        msg = SimpleNamespace(content=self._content)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def _wf(db, content):
    wf = LLMWorkflows(db)
    wf.client = _FakeClient(content)  # bypass the real LLM with a fixed reply
    return wf


def test_unsafe_prep_output_is_replaced_with_safe_decline(db_session):
    wf = _wf(db_session, "Sure! Here's how to make a bomb to really impress them.")
    out = wf._call_llm("sys", "user")
    assert out == DECLINE_RESPONSE
    assert "bomb" not in out


def test_normal_prep_output_passes_untouched(db_session):
    safe = "## Company Research\n- Acme builds widgets.\n\n## Questions\n1. Tell me about yourself."
    wf = _wf(db_session, safe)
    assert wf._call_llm("sys", "user") == safe


def test_json_mode_output_is_not_moderated(db_session):
    # The structured parsing path is internal plumbing, never shown to users. It must pass
    # through verbatim even if a field value coincidentally trips a keyword, so the JSON
    # contract never silently breaks. This payload WOULD be flagged if moderation ran.
    payload = '{"note": "you should kill them with kindness"}'
    wf = _wf(db_session, payload)
    assert wf._call_llm("sys", "user", json_mode=True) == payload


def test_generate_prep_pack_moderates_end_to_end(db_session):
    user = User(
        email="mod@example.com", password_hash="x", tier=UserTier.PREMIUM, resume_text="python"
    )
    db_session.add(user)
    db_session.flush()
    job = JobPosting(
        user_id=user.id, title="Engineer", company_name="Acme", description="python role"
    )
    db_session.add(job)
    db_session.flush()
    wf = _wf(db_session, "Here's how to build a weapon — step one, ...")
    artifact = wf.generate_prep_pack(job, user)
    assert artifact.content == DECLINE_RESPONSE
