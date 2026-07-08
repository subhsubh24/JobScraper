"""Deterministic eval for the interview-READINESS math (ROADMAP Track A, surface 3).

The readiness read is a pure function of (jd_text, résumé, artifact_types, mock sessions,
extractor) — no LLM, no DB — so it is pinned exactly here. The properties the ROADMAP names:
- **Honest 0-state:** no signal → 0, never a vanity number.
- **Monotonic in real inputs:** answering another question, raising a mock score, or completing
  another artifact never DECREASES readiness.
- **Priority-ordered next-best-action:** the single most valuable concrete step, from real signals.
A regression in any of these (a component that drops on more practice, a wrong action order,
a fabricated non-zero 0-state) reddens this.
"""
from src.insights.readiness import (
    KEY_ARTIFACTS,
    TARGET_PRACTICE_QUESTIONS,
    compute_readiness,
)

# A fixed vocabulary so the eval is fully deterministic and independent of the scorer's list.
_VOCAB = ["python", "react", "kubernetes", "aws", "docker", "sql"]


def _extract(text):
    low = (text or "").lower()
    return [s for s in _VOCAB if s in low]


def _session(questions, answers):
    return {"questions": questions, "answers": answers}


def _answer(index, overall):
    return {"question_index": index, "overall": overall}


def _compute(jd="", resume="", artifacts=(), sessions=()):
    return compute_readiness(jd, resume, list(artifacts), list(sessions), _extract)


def test_zero_state_is_zero():
    # No résumé, no practice, no artifacts, JD with skills → honest 0.
    r = _compute(jd="python react", resume="", artifacts=(), sessions=())
    assert r.score == 0
    assert r.next_action.action == "add_resume"
    assert r.signals["answered_questions"] == 0


def test_no_extractable_skills_excludes_coverage_component():
    # A JD with no vocabulary skills → skill_coverage is unavailable (None), not a silent 0.
    r = _compute(jd="we value curiosity", resume="curiosity", artifacts=(), sessions=())
    assert r.components["skill_coverage"] is None
    # With only practice+artifacts available and both empty, score is 0 (honest).
    assert r.score == 0


def test_more_answered_questions_raises_readiness():
    base = _compute(jd="python", resume="python", sessions=[_session(
        [{"question": "q1"}, {"question": "q2"}], [_answer(0, 80)])])
    more = _compute(jd="python", resume="python", sessions=[_session(
        [{"question": "q1"}, {"question": "q2"}], [_answer(0, 80), _answer(1, 80)])])
    assert more.score > base.score  # answering a second question climbs readiness


def test_higher_scores_raise_readiness():
    low = _compute(jd="python", resume="python", sessions=[_session(
        [{"question": "q1"}], [_answer(0, 20)])])
    high = _compute(jd="python", resume="python", sessions=[_session(
        [{"question": "q1"}], [_answer(0, 100)])])
    assert high.score > low.score  # a stronger answer scores higher readiness


def test_completing_an_artifact_raises_readiness():
    none = _compute(jd="python", resume="python", artifacts=())
    one = _compute(jd="python", resume="python", artifacts=(KEY_ARTIFACTS[0],))
    assert one.score > none.score


def test_practice_component_caps_and_is_bounded():
    # Many strong answers cap the practice component at 1.0 (never > 100 overall).
    answers = [_answer(i, 100) for i in range(TARGET_PRACTICE_QUESTIONS * 3)]
    questions = [{"question": f"q{i}"} for i in range(len(answers))]
    r = _compute(jd="python", resume="python", sessions=[_session(questions, answers)])
    assert r.components["interview_practice"] == 1.0
    assert 0 <= r.score <= 100


def test_skill_coverage_reflects_resume_vs_jd():
    # JD demands python+react+aws; résumé has python only → coverage 1/3.
    r = _compute(jd="python react aws", resume="python")
    assert r.components["skill_coverage"] == round(1 / 3, 3)


def test_next_action_priority_order():
    # (2) résumé present, no session → start a mock interview.
    r = _compute(jd="python", resume="python", sessions=())
    assert r.next_action.action == "start_mock_interview"

    # (3) an in-progress session with an unanswered question → answer it.
    r = _compute(jd="python", resume="python", sessions=[_session(
        [{"question": "q1"}, {"question": "q2"}], [_answer(0, 90)])])
    assert r.next_action.action == "answer_question"
    assert "2" in r.next_action.label  # question 2 is the unanswered one

    # (4) all answered but one is weak → redo the weakest.
    r = _compute(jd="python", resume="python", sessions=[_session(
        [{"question": "q1"}, {"question": "q2"}], [_answer(0, 90), _answer(1, 30)])])
    assert r.next_action.action == "redo_answer"
    assert "2" in r.next_action.label  # question 2 is the weakest

    # (5) strong answers, résumé covers the JD, but a key artifact is missing → generate it.
    strong = [_answer(i, 95) for i in range(TARGET_PRACTICE_QUESTIONS)]
    qs = [{"question": f"q{i}"} for i in range(TARGET_PRACTICE_QUESTIONS)]
    r = _compute(jd="python", resume="python", artifacts=(), sessions=[_session(qs, strong)])
    assert r.next_action.action == "generate_artifact"

    # (6) everything strong incl. all key artifacts, but a JD skill is missing → study it.
    r = _compute(jd="python kubernetes", resume="python", artifacts=KEY_ARTIFACTS,
                 sessions=[_session(qs, strong)])
    assert r.next_action.action == "study_skill"
    assert "kubernetes" in r.next_action.label

    # (7) everything strong and no missing skills → ready.
    r = _compute(jd="python", resume="python", artifacts=KEY_ARTIFACTS,
                 sessions=[_session(qs, strong)])
    assert r.next_action.action == "ready"


def test_malformed_answer_overall_does_not_crash_and_scores_zero():
    # A malformed/missing overall is treated as 0 (fail-safe), never a crash or a vanity number.
    r = _compute(jd="python", resume="python", sessions=[_session(
        [{"question": "q1"}], [{"question_index": 0, "overall": "not-a-number"}])])
    assert r.components["interview_practice"] == 0.0
