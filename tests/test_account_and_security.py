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
def test_delete_account_removes_user_and_data(client):
    reg = _reg(client, "del@example.com")
    h = _hdr(reg["token"])

    # Create a job so there is owned data to cascade-delete.
    r = client.post("/api/jobs", headers=h, json={"title": "Eng", "company_name": "Co", "description": "python"})
    assert r.status_code == 200, r.text

    # Delete the account.
    d = client.delete("/api/auth/me", headers=h)
    assert d.status_code == 200, d.text
    assert d.json()["deleted"] is True

    # The token no longer resolves to a user -> 401 (the row is gone, not just flagged).
    assert client.get("/api/auth/me", headers=h).status_code == 401
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
