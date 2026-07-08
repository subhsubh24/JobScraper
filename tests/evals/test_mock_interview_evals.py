"""Deterministic evals for the mock-interview engine (ROADMAP Track A surface 3).

Key-free, fake LLM. Pins the two contracts that must hold regardless of the model's wording:
  1. QUESTION SHAPE — the generated set is validated, category-normalized, and bounded.
  2. SCORING HONESTY + INTEGRITY — sub-scores are clamped 0-5 server-side, ``overall`` is COMPUTED
     from them (never trusted from the model), and a malformed/empty result FAILS LOUD (§6, no
     silent blank score). The honesty *ordering* on real output (strong > weak) is covered by the
     nightly real-output eval in test_ai_output_evals.py.
"""
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
    user = User(email="mieval@example.com", password_hash="x", tier=UserTier.PREMIUM)
    db.add(user)
    db.flush()
    job = JobPosting(user_id=user.id, title="Backend Engineer", company_name="Acme",
                     description="python services", requirements="python, sql, aws")
    db.add(job)
    db.flush()
    return user, job


def test_questions_are_shaped_normalized_and_bounded(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(json.dumps({"questions": [
        {"question": "Design a rate limiter.", "category": "Technical"},   # normalized lower
        {"question": "Describe a failure you owned.", "category": "nonsense"},  # -> behavioral
        {"question": "   ", "category": "technical"},                       # blank -> dropped
    ] + [{"question": f"Extra {i}?", "category": "behavioral"} for i in range(20)]}))
    _, job = _seed(db_session)
    qs = wf.generate_mock_interview_questions(job, num_questions=5)
    assert len(qs) == 5, "must be bounded to num_questions"
    assert qs[0]["category"] == "technical"
    assert qs[1]["category"] == "behavioral"  # invalid category defaults to behavioral
    assert all(q["question"].strip() for q in qs), "no blank question survives"


def test_score_overall_is_computed_not_trusted_and_clamped(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(json.dumps({
        "relevance": 4, "specificity": 2, "star": 3,
        "overall": 100,  # the model's own overall is IGNORED
        "feedback": "Add a measurable outcome.", "model_answer": "A strong answer would...",
    }))
    _, job = _seed(db_session)
    res = wf.score_mock_interview_answer(job, "Q?", "answer")
    # overall = (4 + 2 + 3) / 15 * 100 = 60.0, computed server-side (not the model's 100).
    assert res["overall"] == 60.0
    assert res["relevance"] == 4 and res["specificity"] == 2 and res["star"] == 3


def test_score_clamps_out_of_range_sub_scores(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(json.dumps({
        "relevance": 12, "specificity": -5, "star": 3,
        "feedback": "ok", "model_answer": "x",
    }))
    _, job = _seed(db_session)
    res = wf.score_mock_interview_answer(job, "Q?", "answer")
    assert res["relevance"] == 5 and res["specificity"] == 0


def test_score_empty_feedback_fails_loud(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(json.dumps({"relevance": 3, "specificity": 3, "star": 3, "feedback": ""}))
    _, job = _seed(db_session)
    with pytest.raises(RuntimeError):
        wf.score_mock_interview_answer(job, "Q?", "answer")
