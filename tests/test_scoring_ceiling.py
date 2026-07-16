"""Track F: the JOB-SCORING embedding call is metered by a per-user/day ceiling.

Every new job triggers a PAID Gemini embedding in ``score_job``. The feature LLM ceiling
(prep / coach / salary) does NOT cover this path, so an account with unlimited jobs could
drive unbounded embedding spend — a wallet-drain vector the other endpoints already defend.

``create_job`` now consumes a ``score_daily`` counter slot before scoring, but ONLY when a
real paid call would actually fire (a Gemini key is present); the keyless heuristic path is
free and is never metered. Over the ceiling a job is still created, just UNSCORED (the same
graceful outcome as a scoring error) — the add is never blocked. These tests pin that
contract so a regression that drops the meter (or meters the free heuristic path) fails LOUD.
"""
import asgi

OK_PW = "hunter2pw"


class _RecordingScorer:
    """Stand-in for ``JobScorer`` that records ``score_job`` calls WITHOUT any real Gemini
    call — so the test asserts the METERING decision, not embedding output."""

    calls = 0

    def __init__(self, db):  # noqa: D401 - matches JobScorer(db) construction
        # Mirror the real JobScorer contract: a SUCCESSFUL score leaves embedding_failed False,
        # so create_job does NOT refund the slot and the ceiling is enforced.
        self.embedding_failed = False

    def score_job(self, job, user, use_embeddings=True):
        # ``use_embeddings`` mirrors the real JobScorer signature (whether the paid Gemini
        # embedding path is used). The metering decision lives in create_job, not here, so we
        # count every invocation and let the tests assert how often create_job chose to score.
        _RecordingScorer.calls += 1
        return None


class _OutagingScorer:
    """Stand-in whose ``score_job`` simulates a paid embedding OUTAGE: it still returns a
    (degraded) score — score_job never re-raises — but sets ``embedding_failed=True`` on the
    paid path, exactly as the real ``JobScorer`` does when the Gemini embedding call fails and
    it degrades to the neutral baseline. create_job must then REFUND the up-front score_daily
    slot (no billable embedding succeeded), so an outage never burns the ceiling."""

    calls = 0

    def __init__(self, db):  # noqa: D401 - matches JobScorer(db) construction
        self.embedding_failed = False

    def score_job(self, job, user, use_embeddings=True):
        _OutagingScorer.calls += 1
        # Outage on the metered (paid) path only; a local heuristic score costs nothing anyway.
        self.embedding_failed = bool(use_embeddings)
        return None


def _register(client, email):
    r = client.post("/api/auth/register", json={"email": email, "password": OK_PW})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _add_job(client, token, i):
    return client.post(
        "/api/jobs",
        headers=_auth(token),
        json={"title": f"Role {i}", "company_name": "Acme", "description": "Build things."},
    )


def test_scoring_metered_over_ceiling_creates_job_unscored(client, monkeypatch):
    """With a Gemini key present and a low ceiling, the first N adds score (the paid call
    fires) and further adds are created UNSCORED (no scoring call) — the wallet-drain brake,
    while the job itself is always created."""
    _RecordingScorer.calls = 0
    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "JobScorer", _RecordingScorer)
    monkeypatch.setattr(asgi, "SCORE_DAILY_CEILING", 2)

    token = _register(client, "meter-cap@example.com")
    # Grant third-party-AI consent so the embedding (paid) path is actually used and metered —
    # without consent, scoring stays on the free local heuristic and is never metered.
    assert client.post("/api/ai-consent", headers=_auth(token)).status_code == 200
    # 3 adds, all within the free-tier 5-job cap so only the scoring ceiling (2) is exercised.
    for i in range(3):
        assert _add_job(client, token, i).status_code == 200

    # Only the first 2 fired a paid scoring call; the 3rd was created unscored.
    assert _RecordingScorer.calls == 2


def test_job_creation_stays_atomic_when_a_later_step_fails(client, db_session, monkeypatch):
    """Regression: the scoring meter must not split job creation into two transactions.

    ``_consume_counter`` commits immediately, so if it ran AFTER the job insert, a failure in
    a later step (here: ``increment_job_usage``) would leave an ORPHANED JobPosting with no
    Application/usage row. The fix moves the meter BEFORE any writes, so on such a failure the
    job insert rolls back cleanly. Load-bearing: against the pre-fix ordering the orphaned job
    would be committed and this count assertion fails."""
    import pytest

    from src.db.models import JobPosting

    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "JobScorer", _RecordingScorer)

    def _boom(self, user):
        raise RuntimeError("simulated failure after the scoring meter")

    monkeypatch.setattr(asgi.AuthService, "increment_job_usage", _boom)

    token = _register(client, "atomic@example.com")
    # The later step raises; the TestClient surfaces it (the add is not a success).
    with pytest.raises(RuntimeError):
        _add_job(client, token, 1)

    # The job insert must have rolled back — no orphaned JobPosting persisted (the meter's
    # earlier commit only persisted the counter row, never the job).
    assert db_session.query(JobPosting).count() == 0


def test_embedding_outage_refunds_the_scoring_slot(client, db_session, monkeypatch):
    """A Gemini embedding OUTAGE refunds the up-front score_daily slot — no burned ceiling.

    ``create_job`` consumes a score_daily slot BEFORE scoring, but ``score_job`` swallows an
    embedding failure and degrades to the neutral baseline WITHOUT re-raising, so the outer
    except never fires. Without a refund, an outage would silently burn a paid-ceiling slot for
    a call that cost nothing — contradicting the project's refund principle (count calls that
    actually cost money, not provider outages). This pins the refund: with the ceiling at 2 and
    an always-outaging scorer, MORE than 2 adds all still attempt scoring, because each consumed
    slot is returned. Load-bearing: drop the refund and adds 3+ are created UNSCORED
    (calls stays 2) and the counter climbs — this reddens.
    """
    _OutagingScorer.calls = 0
    monkeypatch.setattr(asgi, "llm_available", lambda: True)
    monkeypatch.setattr(asgi, "JobScorer", _OutagingScorer)
    monkeypatch.setattr(asgi, "SCORE_DAILY_CEILING", 2)

    token = _register(client, "outage-refund@example.com")
    # Consent so the embedding (paid, metered) path is chosen — else scoring stays free+local.
    assert client.post("/api/ai-consent", headers=_auth(token)).status_code == 200
    # 4 adds > ceiling 2, all within the free-tier 5-job cap. Every add attempts scoring only if
    # its slot keeps getting refunded after each outage.
    for i in range(4):
        assert _add_job(client, token, i).status_code == 200

    assert _OutagingScorer.calls == 4  # all 4 scored — the outage refund kept the ceiling clear

    # And the counter nets to 0 in the current window: consume +1 then refund -1 per add.
    import time

    from src.db.models import RateCounter, User

    user = db_session.query(User).filter(User.email == "outage-refund@example.com").one()
    window_key = int(time.time() // 86400)
    row = (
        db_session.query(RateCounter)
        .filter(
            RateCounter.subject == str(user.id),
            RateCounter.bucket == "score_daily",
            RateCounter.window_key == window_key,
        )
        .first()
    )
    # Every consume was matched by a refund → floor 0 (or no surviving positive count).
    assert row is None or row.count == 0


def test_scoring_not_metered_without_a_key(client, monkeypatch):
    """The keyless heuristic scoring path is FREE, so it must never be metered — every add
    scores even with the ceiling set to 1 (proves the ``not llm_available()`` short-circuit)."""
    _RecordingScorer.calls = 0
    # llm_available stays False (conftest forces a key-free env).
    monkeypatch.setattr(asgi, "JobScorer", _RecordingScorer)
    monkeypatch.setattr(asgi, "SCORE_DAILY_CEILING", 1)

    token = _register(client, "meter-nokey@example.com")
    for i in range(3):
        assert _add_job(client, token, i).status_code == 200

    # All 3 scored despite ceiling=1 — the free path is exempt from the meter.
    assert _RecordingScorer.calls == 3
