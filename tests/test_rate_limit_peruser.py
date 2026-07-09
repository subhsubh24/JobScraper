"""Per-user rate limiting on authed endpoints (ROADMAP Track F; security A→A+).

The authed reads/writes (coach suggestions, skill-gaps, profile résumé, report, job
create/update, enrichment, ai-consent) were IP-keyed, so MANY distinct users behind one
carrier-grade-NAT public IP shared a single limit — one busy user (or a stranger on the same
NAT) could false-429 everyone else, and a compromised token got no per-account bound. These
endpoints now key the limiter by USER id (``rate_limit_user``), so each account has its own
budget.

This regression proves the KEYING at the HTTP layer: once user A's per-user budget for an
endpoint is spent, A gets a 429 while user B on the SAME client IP is untouched. Reverting any
of these endpoints back to the IP-keyed ``rate_limit`` reddens this test — A's seeded
``user:<id>`` counter would be ignored (the endpoint would tally the shared client IP
instead), so A's first call would pass AND B would share A's IP tally.

The LLM/ingest/auth-preauth buckets are intentionally left IP-keyed as deliberate
wallet-drain / account-rotation defenses and are out of scope here.
"""
import asgi
from src.db.models import User


def _register(client, email):
    r = client.post("/api/auth/register", json={"email": email, "password": "hunter2pw"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _uid(db, email):
    return db.query(User).filter(User.email == email).one().id


def test_coach_suggestions_is_per_user_not_per_ip(client, db_session):
    token_a = _register(client, "peruser-a@example.com")
    token_b = _register(client, "peruser-b@example.com")
    uid_a = _uid(db_session, "peruser-a@example.com")

    # Spend user A's per-user "suggest" budget (limit 30) on the exact subject the endpoint
    # keys by. _consume_counter commits each increment to the shared rate_counters table.
    for _ in range(30):
        assert asgi._consume_counter(db_session, f"user:{uid_a}", "suggest", 30, 60) is True

    # User A is now over budget -> 429.
    ra = client.get(
        "/api/coach/suggestions", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert ra.status_code == 429, ra.text

    # User B shares the SAME TestClient IP but has an untouched per-user budget -> allowed.
    # (Under the reverted IP-keyed limiter, B would 429 off A's shared client-IP tally.)
    rb = client.get(
        "/api/coach/suggestions", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert rb.status_code == 200, rb.text


def test_job_create_budget_is_isolated_per_user(client, db_session):
    """A second authed endpoint (POST /api/jobs, "write" bucket) proves the migration holds
    for writes too: exhausting A's per-user write budget never blocks B on the same IP."""
    token_a = _register(client, "peruser-w-a@example.com")
    token_b = _register(client, "peruser-w-b@example.com")
    uid_a = _uid(db_session, "peruser-w-a@example.com")

    for _ in range(30):
        assert asgi._consume_counter(db_session, f"user:{uid_a}", "write", 30, 60) is True

    payload = {
        "title": "Backend Engineer",
        "company_name": "Acme",
        "description": "Build and operate Python services.",
    }
    ra = client.post(
        "/api/jobs", headers={"Authorization": f"Bearer {token_a}"}, json=payload
    )
    assert ra.status_code == 429, ra.text

    rb = client.post(
        "/api/jobs", headers={"Authorization": f"Bearer {token_b}"}, json=payload
    )
    assert rb.status_code != 429, rb.text
