"""Mock interview engine (ROADMAP Track A surface 3 — the interview-coaching pillar).

Two layers:
- ENDPOINT wiring (fake LLMWorkflows, no key): Pro gate, consent gate, honest 503 degradation,
  session persistence, per-answer scoring + completion, re-answer overwrite, tenant isolation,
  moderated-decline no-persist, the PMF funnel events, and account-deletion cascade.
- GENERATOR logic (real LLMWorkflows + a fake LLM client): question-shape validation/bounds,
  server-side score clamping + computed ``overall``, and fail-loud on malformed/empty output.
"""
import json
from types import SimpleNamespace

import pytest

import asgi
from src.db.models import MockInterview, User, UserTier
from src.enrichment.llm_workflows import LLMWorkflows, ModeratedContentError


# --------------------------------------------------------------------------- helpers
def _register(client, email="mi@example.com", password="hunter2pw"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _add_job(client, token):
    r = client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": "Staff Engineer", "company_name": "Acme", "description": "python etl"},
    )
    assert r.status_code == 200, r.text
    return r.json()["job"]["id"]


def _make_pro(db_session, user_id):
    db_session.query(User).filter(User.id == user_id).update({User.tier: UserTier.PREMIUM})
    db_session.commit()


def _consent(client, token):
    assert client.post("/api/ai-consent", headers=_auth(token)).status_code == 200


class _FakeMockWorkflows:
    """Deterministic stand-in for LLMWorkflows — returns realistic question/score shapes."""

    MODEL = "fake-model"

    def __init__(self, db):
        self._db = db

    def generate_mock_interview_questions(self, job, num_questions):
        return [
            {"question": f"Question {i}: tell me about X?",
             "category": "technical" if i % 2 else "behavioral"}
            for i in range(num_questions)
        ]

    def score_mock_interview_answer(self, job, question, answer):
        return {
            "relevance": 4, "specificity": 3, "star": 5, "overall": 80.0,
            "feedback": "Solid structure; add a concrete metric to strengthen it.",
            "model_answer": "A strong answer would open with the situation, then the result.",
        }


class _ModeratedWorkflows(_FakeMockWorkflows):
    def generate_mock_interview_questions(self, job, num_questions):
        raise ModeratedContentError("declined")

    def score_mock_interview_answer(self, job, question, answer):
        raise ModeratedContentError("declined")


@pytest.fixture()
def _llm_on(monkeypatch):
    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "LLMWorkflows", _FakeMockWorkflows)


@pytest.fixture()
def _llm_moderated(monkeypatch):
    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "LLMWorkflows", _ModeratedWorkflows)


def _start(client, token, job_id, num_questions=4):
    return client.post(
        "/api/prep/mock-interview",
        headers=_auth(token),
        json={"job_id": job_id, "num_questions": num_questions},
    )


# --------------------------------------------------------------------------- endpoint: gating
def test_start_blocked_for_free(client):
    _, token = _register(client)
    job_id = _add_job(client, token)
    r = _start(client, token, job_id)
    assert r.status_code == 403
    assert "pro" in r.json()["detail"].lower()


def test_start_requires_llm_key(client, db_session):
    """A Pro user with consent but no GEMINI key gets an HONEST 503 (gate passed), not a fake
    session — proving the entitlement gate cleared and degradation is truthful (§6)."""
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)
    r = _start(client, token, job_id)
    assert r.status_code == 503
    assert "gemini_api_key" in r.json()["detail"].lower()


def test_start_requires_consent(client, db_session, _llm_on):
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    r = _start(client, token, job_id)  # no consent granted
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "ai_consent_required"


def test_start_foreign_job_is_404(client, db_session, _llm_on):
    uid, token = _register(client)
    _make_pro(db_session, uid)
    _consent(client, token)
    r = _start(client, token, "not-a-real-job")
    assert r.status_code == 404


# --------------------------------------------------------------------------- endpoint: happy path
def test_start_persists_session_and_returns_questions(client, db_session, _llm_on):
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)

    r = _start(client, token, job_id, num_questions=4)
    assert r.status_code == 200, r.text
    iv = r.json()["interview"]
    assert iv["status"] == "in_progress"
    assert iv["total"] == 4
    assert len(iv["questions"]) == 4
    assert iv["answered_count"] == 0
    # Persisted, scoped to the user + job.
    row = db_session.query(MockInterview).filter_by(id=iv["id"]).first()
    assert row is not None
    assert row.user_id == uid and row.job_id == job_id
    assert len(row.questions) == 4


def test_answer_scores_persists_and_computes_overall(client, db_session, _llm_on):
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)
    iv = _start(client, token, job_id, num_questions=4).json()["interview"]

    r = client.post(
        f"/api/prep/mock-interview/{iv['id']}/answer",
        headers=_auth(token),
        json={"question_index": 0, "answer": "I led an ETL migration that cut latency 40%."},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["result"]["overall"] == 80.0
    assert body["result"]["feedback"].strip()
    assert body["status"] == "in_progress"  # 1 of 4 answered
    assert body["answered_count"] == 1
    # Persisted on the session.
    db_session.expire_all()
    row = db_session.query(MockInterview).filter_by(id=iv["id"]).first()
    assert len(row.answers) == 1
    assert row.answers[0]["question_index"] == 0
    assert row.answers[0]["overall"] == 80.0


def test_answer_completes_session_when_all_answered(client, db_session, _llm_on):
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)
    iv = _start(client, token, job_id, num_questions=3).json()["interview"]

    last = None
    for i in range(3):
        last = client.post(
            f"/api/prep/mock-interview/{iv['id']}/answer",
            headers=_auth(token),
            json={"question_index": i, "answer": f"Answer number {i} with detail."},
        )
        assert last.status_code == 200, last.text
    assert last.json()["status"] == "completed"
    assert last.json()["answered_count"] == 3
    db_session.expire_all()
    row = db_session.query(MockInterview).filter_by(id=iv["id"]).first()
    assert row.status == "completed"


def test_reanswer_overwrites_not_duplicates(client, db_session, _llm_on):
    """Re-answering a question (the readiness-loop 'redo the weak answer' path) OVERWRITES its
    prior score rather than appending a duplicate — one entry per question index."""
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)
    iv = _start(client, token, job_id, num_questions=4).json()["interview"]

    for _ in range(2):
        r = client.post(
            f"/api/prep/mock-interview/{iv['id']}/answer",
            headers=_auth(token),
            json={"question_index": 1, "answer": "A revised, stronger answer."},
        )
        assert r.status_code == 200, r.text
    db_session.expire_all()
    row = db_session.query(MockInterview).filter_by(id=iv["id"]).first()
    idxs = [a["question_index"] for a in row.answers]
    assert idxs == [1]  # one entry, not two


def test_answer_index_out_of_range_is_422(client, db_session, _llm_on):
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)
    iv = _start(client, token, job_id, num_questions=3).json()["interview"]
    r = client.post(
        f"/api/prep/mock-interview/{iv['id']}/answer",
        headers=_auth(token),
        json={"question_index": 5, "answer": "out of range"},
    )
    assert r.status_code == 422


# --------------------------------------------------------------------------- tenant isolation
def test_cannot_read_or_answer_another_users_interview(client, db_session, _llm_on):
    uid_a, tok_a = _register(client, "a-mi@example.com")
    job_a = _add_job(client, tok_a)
    _make_pro(db_session, uid_a)
    _consent(client, tok_a)
    iv = _start(client, tok_a, job_a).json()["interview"]

    uid_b, tok_b = _register(client, "b-mi@example.com")
    _make_pro(db_session, uid_b)
    _consent(client, tok_b)

    assert client.get(f"/api/prep/mock-interview/{iv['id']}", headers=_auth(tok_b)).status_code == 404
    r = client.post(
        f"/api/prep/mock-interview/{iv['id']}/answer",
        headers=_auth(tok_b),
        json={"question_index": 0, "answer": "not mine"},
    )
    assert r.status_code == 404


def test_get_and_list_interviews(client, db_session, _llm_on):
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)
    iv = _start(client, token, job_id).json()["interview"]

    g = client.get(f"/api/prep/mock-interview/{iv['id']}", headers=_auth(token))
    assert g.status_code == 200
    assert g.json()["interview"]["id"] == iv["id"]

    lst = client.get(
        "/api/prep/mock-interviews", headers=_auth(token), params={"job_id": job_id}
    )
    assert lst.status_code == 200
    ids = [i["id"] for i in lst.json()["interviews"]]
    assert iv["id"] in ids


# --------------------------------------------------------------------------- moderation / §6
def test_moderated_questions_return_422_and_persist_nothing(client, db_session, _llm_moderated):
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)
    r = _start(client, token, job_id)
    assert r.status_code == 422
    assert db_session.query(MockInterview).count() == 0  # no fake session persisted


def test_moderated_answer_returns_422_and_scores_nothing(client, db_session, monkeypatch):
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)
    # Start with the clean fake, then swap in the moderated one for the answer scoring.
    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "LLMWorkflows", _FakeMockWorkflows)
    iv = _start(client, token, job_id, num_questions=3).json()["interview"]
    monkeypatch.setattr(asgi, "LLMWorkflows", _ModeratedWorkflows)
    r = client.post(
        f"/api/prep/mock-interview/{iv['id']}/answer",
        headers=_auth(token),
        json={"question_index": 0, "answer": "an answer"},
    )
    assert r.status_code == 422
    db_session.expire_all()
    row = db_session.query(MockInterview).filter_by(id=iv["id"]).first()
    assert row.answers == []  # nothing scored/persisted on a moderated decline


# --------------------------------------------------------------------------- PMF funnel events
def test_start_and_answer_record_pmf_events(client, db_session, _llm_on):
    from src.db.models import AggregateEvent

    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)
    iv = _start(client, token, job_id, num_questions=3).json()["interview"]
    client.post(
        f"/api/prep/mock-interview/{iv['id']}/answer",
        headers=_auth(token),
        json={"question_index": 0, "answer": "an answer with detail"},
    )
    started = (
        db_session.query(AggregateEvent).filter_by(event_type="mock_interview_started").count()
    )
    answered = (
        db_session.query(AggregateEvent).filter_by(event_type="mock_interview_answered").count()
    )
    assert started >= 1 and answered >= 1


# --------------------------------------------------------------------------- content report surface
def test_report_accepts_mock_interview_content_type(client):
    _, token = _register(client)
    r = client.post(
        "/api/report",
        headers=_auth(token),
        json={"content_type": "mock_interview", "reason": "inaccurate",
              "content_excerpt": "the feedback was wrong"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True


# --------------------------------------------------------------------------- account deletion cascade
def test_account_deletion_purges_mock_interviews(client, db_session, _llm_on):
    uid, token = _register(client)
    job_id = _add_job(client, token)
    _make_pro(db_session, uid)
    _consent(client, token)
    _start(client, token, job_id)
    assert db_session.query(MockInterview).count() == 1

    d = client.delete("/api/auth/me", headers=_auth(token))
    assert d.status_code == 200, d.text
    db_session.expire_all()
    assert db_session.query(MockInterview).count() == 0  # Apple 5.1.1(v): nothing left orphaned


# =========================================================================== generator logic
class _FakeLLM:
    def __init__(self, content):
        self._content = content
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._content))]
        )


def _seed(db):
    user = User(email="wfmi@example.com", password_hash="x", tier=UserTier.PREMIUM)
    db.add(user)
    db.flush()
    from src.db.models import JobPosting
    job = JobPosting(user_id=user.id, title="Data Engineer", company_name="Globex",
                     description="etl", requirements="python, sql")
    db.add(job)
    db.flush()
    return user, job


def test_generate_questions_parses_normalizes_and_bounds(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(json.dumps({"questions": [
        {"question": "Explain a data pipeline you built.", "category": "TECHNICAL"},
        {"question": "Tell me about a conflict.", "category": "weird"},  # -> behavioral
        {"question": "", "category": "technical"},  # blank -> skipped
        {"question": "One more?", "category": "behavioral"},
    ]}))
    _, job = _seed(db_session)
    qs = wf.generate_mock_interview_questions(job, num_questions=5)
    assert len(qs) == 3  # the blank one is dropped
    assert qs[0]["category"] == "technical"  # normalized lower
    assert qs[1]["category"] == "behavioral"  # invalid -> default behavioral


def test_generate_questions_malformed_json_raises(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("not json at all")
    _, job = _seed(db_session)
    with pytest.raises(RuntimeError):
        wf.generate_mock_interview_questions(job)


def test_generate_questions_no_valid_items_raises(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(json.dumps({"questions": [{"question": "  "}]}))
    _, job = _seed(db_session)
    with pytest.raises(RuntimeError):
        wf.generate_mock_interview_questions(job)


def test_score_answer_clamps_and_computes_overall(db_session):
    wf = LLMWorkflows(db_session)
    # Out-of-range sub-scores must be clamped 0..5; overall is computed server-side, not trusted.
    wf.client = _FakeLLM(json.dumps({
        "relevance": 9, "specificity": -3, "star": 5,
        "overall": 999,  # the model's own overall is IGNORED
        "feedback": "Good but be specific.", "model_answer": "A strong answer would...",
    }))
    _, job = _seed(db_session)
    res = wf.score_mock_interview_answer(job, "Q?", "my answer")
    assert res["relevance"] == 5 and res["specificity"] == 0 and res["star"] == 5
    # overall = (5 + 0 + 5) / 15 * 100 = 66.7, NOT the model's fabricated 999.
    assert res["overall"] == 66.7


def test_score_answer_empty_feedback_raises(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(json.dumps({"relevance": 3, "specificity": 3, "star": 3, "feedback": " "}))
    _, job = _seed(db_session)
    with pytest.raises(RuntimeError):
        wf.score_mock_interview_answer(job, "Q?", "answer")


def test_score_answer_malformed_json_raises(db_session):
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("garbage")
    _, job = _seed(db_session)
    with pytest.raises(RuntimeError):
        wf.score_mock_interview_answer(job, "Q?", "answer")
