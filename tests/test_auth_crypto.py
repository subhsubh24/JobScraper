"""Direct unit tests for AuthService's security-critical crypto primitives.

The password hashing (PBKDF2-HMAC-SHA256 + per-hash salt) and the signed-token
create/verify (HMAC-SHA256) are only exercised INDIRECTLY today, through the register/login
HTTP flow. That leaves the failure branches — a tampered signature, an expired token, a
malformed token, a wrong password — without a direct assertion, so a silent security
regression could pass the happy-path integration tests. These tests pin the primitives
themselves. Each is mutation-provable on the FUNCTIONAL contract: dropping (or short-circuiting)
the signature comparison in ``verify_token`` makes the tampered-signature/tampered-payload/
wrong-secret tests fail; dropping the expiry check makes the expired-token test fail; making the
hash non-salted makes the salted-hash test fail — all while the happy-path HTTP-flow tests stay
green. (These are functional assertions: they verify that tampering is REJECTED, not the
constant-time property of ``hmac.compare_digest`` — a timing characteristic a functional unit
test cannot observe.)
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

from src.auth.auth_service import AuthService
from src.db.models import UserTier


def _svc() -> AuthService:
    # The crypto methods never touch the DB, so a None session is fine here.
    return AuthService(None)


def _user(uid="user-1", email="crypto@example.com", tier=UserTier.FREE):
    return SimpleNamespace(id=uid, email=email, tier=tier)


# --------------------------------------------------------------------------- password hashing
def test_password_hash_round_trip():
    h = AuthService.hash_password("Sup3r-Secret!")
    assert AuthService.verify_password("Sup3r-Secret!", h) is True


def test_wrong_password_is_rejected():
    h = AuthService.hash_password("correct horse battery staple")
    assert AuthService.verify_password("wrong password", h) is False


def test_hash_is_salted_so_same_password_hashes_differently():
    # A per-hash random salt means two hashes of the SAME password must differ (no global
    # salt / plain digest) — yet both verify. Guards against a salt regression.
    a = AuthService.hash_password("same-password")
    b = AuthService.hash_password("same-password")
    assert a != b
    assert AuthService.verify_password("same-password", a)
    assert AuthService.verify_password("same-password", b)


def test_verify_password_on_garbage_hash_returns_false_not_raises():
    # A corrupt/non-base64 stored hash must fail closed (False), never throw (which would
    # surface as a 500 on login instead of a clean auth failure).
    assert AuthService.verify_password("whatever", "not-valid-base64!!") is False
    assert AuthService.verify_password("whatever", "") is False


def test_unicode_password_round_trips():
    h = AuthService.hash_password("pÄsswörd–🔐")
    assert AuthService.verify_password("pÄsswörd–🔐", h) is True
    assert AuthService.verify_password("passw0rd", h) is False


# --------------------------------------------------------------------------- token create/verify
def test_token_round_trip_carries_identity_claims():
    svc = _svc()
    token = svc.create_token(_user(uid="abc", email="me@example.com", tier=UserTier.PREMIUM))
    payload = svc.verify_token(token)
    assert payload is not None
    assert payload["user_id"] == "abc"
    assert payload["email"] == "me@example.com"
    assert payload["tier"] == "premium"


def test_tampered_signature_is_rejected():
    svc = _svc()
    token = svc.create_token(_user())
    header, payload, sig = token.split(".")
    # Flip the last character of the signature — a constant-time comparison must reject it.
    forged_sig = sig[:-1] + ("A" if sig[-1] != "A" else "B")
    assert svc.verify_token(f"{header}.{payload}.{forged_sig}") is None


def test_tampered_payload_is_rejected():
    """Re-encoding a modified payload without re-signing must fail — the signature covers it."""
    svc = _svc()
    token = svc.create_token(_user(uid="orig"))
    header, _payload, sig = token.split(".")
    forged_payload = svc._base64url_encode(b'{"user_id": "attacker", "exp": 9999999999}')
    assert svc.verify_token(f"{header}.{forged_payload}.{sig}") is None


def test_wrong_secret_cannot_verify():
    signer = _svc()
    token = signer.create_token(_user())
    verifier = _svc()
    verifier.JWT_SECRET = "a-different-secret"  # instance attr shadows the class default
    assert verifier.verify_token(token) is None


def test_malformed_tokens_return_none_not_raise():
    svc = _svc()
    for bad in ["", "onlyonepart", "two.parts", "a.b.c.d", "...", "not a token at all"]:
        assert svc.verify_token(bad) is None


def test_expired_token_is_rejected():
    svc = _svc()
    svc.JWT_EXPIRY_DAYS = -1  # issue a token that expired a day ago
    token = svc.create_token(_user())
    assert svc.verify_token(token) is None


def test_token_valid_just_before_expiry():
    """A token whose exp is still in the future verifies — guards against an off-by-one that
    would reject every live token (the inverse regression of the expiry check)."""
    svc = _svc()
    svc.JWT_EXPIRY_DAYS = 1
    token = svc.create_token(_user())
    payload = svc.verify_token(token)
    assert payload is not None
    # exp is ~1 day out (sanity bound, not a brittle exact match).
    assert payload["exp"] > (datetime.utcnow() + timedelta(hours=12)).timestamp()
