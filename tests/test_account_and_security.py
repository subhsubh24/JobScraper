"""Track D (account deletion) + Track F (login lockout, security headers) guards.

Each asserts the INTENDED OUTCOME at runtime, not just a status code: deletion really
removes the user's data, lockout actually blocks, headers are actually present.
"""


def _reg(client, email="u@example.com", pw="supersecret123"):
    r = client.post("/api/auth/register", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return r.json()


def _hdr(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Account deletion (Apple/Google requirement) — a REAL delete, not a stub.
# ---------------------------------------------------------------------------
def test_delete_account_removes_user_and_data(client, db_session):
    from src.db.models import Application, ChatMessage, JobPosting, JobScore, PrepArtifact, User

    reg = _reg(client, "del@example.com")
    h = _hdr(reg["token"])
    user_id = reg["user"]["id"]

    # Create a job via the API (auto-creates an Application + JobScore).
    r = client.post("/api/jobs", headers=h, json={"title": "Eng", "company_name": "Co", "description": "python"})
    assert r.status_code == 200, r.text
    job_id = r.json()["job"]["id"]

    # Seed a prep artifact + chat message directly (the API paths are LLM-gated/premium),
    # so we can prove they too are cascade-deleted — not just the easy rows.
    db_session.add(PrepArtifact(job_id=job_id, artifact_type="prep_pack", title="P", content="x"))
    db_session.add(ChatMessage(user_id=user_id, role="user", content="hi"))
    db_session.commit()
    assert db_session.query(PrepArtifact).count() == 1
    assert db_session.query(ChatMessage).count() == 1

    # Delete the account.
    d = client.delete("/api/auth/me", headers=h)
    assert d.status_code == 200, d.text
    assert d.json()["deleted"] is True

    # The token no longer resolves to a user -> 401 (the row is gone, not just flagged).
    assert client.get("/api/auth/me", headers=h).status_code == 401
    # Every user-owned table is empty — nothing orphaned.
    db_session.expire_all()
    assert db_session.query(User).count() == 0
    assert db_session.query(JobPosting).count() == 0
    assert db_session.query(JobScore).count() == 0
    assert db_session.query(Application).count() == 0
    assert db_session.query(PrepArtifact).count() == 0
    assert db_session.query(ChatMessage).count() == 0
    # Re-registering the same email succeeds (no leftover unique-email row).
    again = client.post("/api/auth/register", json={"email": "del@example.com", "password": "supersecret123"})
    assert again.status_code == 200, again.text


def test_delete_account_requires_auth(client):
    assert client.delete("/api/auth/me").status_code == 401


# ---------------------------------------------------------------------------
# Per-account login lockout (brute-force defense).
# ---------------------------------------------------------------------------
def test_login_locks_after_repeated_failures(client):
    _reg(client, "lock@example.com", "correct-horse-battery")

    # 5 wrong passwords -> each 401.
    for _ in range(5):
        r = client.post("/api/auth/login", json={"email": "lock@example.com", "password": "wrong-pass-xx"})
        assert r.status_code == 401

    # 6th attempt is locked out (429) — even with the CORRECT password.
    locked = client.post("/api/auth/login", json={"email": "lock@example.com", "password": "correct-horse-battery"})
    assert locked.status_code == 429
    assert "too many" in locked.json()["detail"].lower()


def test_lockout_tally_is_db_backed_cross_instance(client, db_session):
    """The whole point of the fix: the failure tally lives in the shared ``rate_counters``
    table, NOT a per-instance in-memory dict (which never accumulated on serverless because a
    distributed brute-force hits a different instance each time). ``db_session`` is a SEPARATE
    session on the same DB — standing in for a second serverless instance — and it must SEE the
    failures recorded through the API and observe the lock. A regression back to in-memory state
    would make this assertion fail (the second 'instance' would see zero failures).
    """
    from src.db.models import RateCounter
    import asgi

    _reg(client, "cross@example.com", "correct-horse-battery")
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "cross@example.com", "password": "wrong-pass-xx"})

    # A different session (a different "instance") sees the durable tally in the shared table.
    rows = (
        db_session.query(RateCounter)
        .filter(RateCounter.bucket == "login_fail", RateCounter.subject == "login:cross@example.com")
        .all()
    )
    assert rows and rows[0].count >= asgi.LOGIN_MAX_FAILURES
    # …and the lockout gate, evaluated on that second session, agrees the account is locked.
    assert asgi._login_locked(db_session, "cross@example.com") is True
    # There is no in-memory lockout dict left to leak between instances.
    assert not hasattr(asgi, "_LOGIN_FAILURES")


def test_login_lockout_does_not_enumerate_emails(client):
    # An email that was never registered locks out exactly the same way (no signal that
    # the account doesn't exist).
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "whatever-123"})
    r = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "whatever-123"})
    assert r.status_code == 429


def test_successful_login_clears_failure_counter(client):
    _reg(client, "reset@example.com", "right-password-1")
    # A few failures, then a success, then a few more failures must NOT be locked
    # (success reset the counter).
    for _ in range(3):
        client.post("/api/auth/login", json={"email": "reset@example.com", "password": "nope-nope-1"})
    ok = client.post("/api/auth/login", json={"email": "reset@example.com", "password": "right-password-1"})
    assert ok.status_code == 200
    for _ in range(3):
        r = client.post("/api/auth/login", json={"email": "reset@example.com", "password": "nope-nope-1"})
        assert r.status_code == 401  # still not locked — counter was cleared


# ---------------------------------------------------------------------------
# Security headers present on every response (incl. errors).
# ---------------------------------------------------------------------------
def test_security_headers_present(client):
    r = client.get("/api/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "no-referrer"
    assert "max-age=31536000" in r.headers.get("Strict-Transport-Security", "")
    assert "frame-ancestors 'none'" in r.headers.get("Content-Security-Policy", "")


def test_security_headers_on_auth_error(client):
    r = client.get("/api/jobs")  # 401, no token
    assert r.status_code == 401
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert "max-age=31536000" in r.headers.get("Strict-Transport-Security", "")
