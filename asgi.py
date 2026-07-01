"""FastAPI backend for Career Operator.

Talks to the real `src/` services and models. Designed to DEGRADE GRACEFULLY:
the core journey (auth + job tracking + scoring + pipeline analytics) works with NO
Gemini key via heuristic scoring; AI features (prep packs, coach) return a truthful
"needs configuration" response instead of crashing when the key is absent.
"""
import hmac
import logging
import os
import re
import time
import uuid
from datetime import datetime
from typing import Dict, List, Literal, Optional, Tuple

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.errors import error_body
from src.api.ip_extraction import get_client_ip
from src.api.logging_config import request_id_var, setup_logging

from src.ai_coach.career_coach import CareerCoach
from src.auth.auth_service import AuthService
from src.db import get_db
from src.db.models import (
    Application,
    ApplicationStatus,
    ATSType,
    ContentReport,
    JobPosting,
    PrepArtifact,
    RateCounter,
    User,
    UserTier,
    Waitlist,
)
from src.enrichment.llm_workflows import LLMWorkflows
from src.llm import llm_available
from src.ranking.scorer import JobScorer
from src import analytics
from src import billing
from src import mobile_billing
from src import referrals

load_dotenv()
setup_logging()
logger = logging.getLogger("career_operator")


def _assert_required_secrets() -> None:
    """DEEP_DIAGNOSIS rule (b): a critical-path secret must FAIL LOUD in production, never
    silently default. On Vercel, refuse to run with an unset / dev-default JWT_SECRET —
    otherwise auth tokens are forgeable (a silent security hole worse than an outage).
    """
    if os.getenv("VERCEL"):
        secret = os.getenv("JWT_SECRET", "")
        if not secret or secret == "dev-secret-change-in-production":
            raise RuntimeError(
                "JWT_SECRET is unset or the insecure dev default in production — set a "
                "strong JWT_SECRET in the deploy env (auth tokens are forgeable otherwise)."
            )
        # The TEST-ONLY rate-limit bypass must NEVER be live in production. If the deploy env
        # somehow carries it, refuse to boot rather than run wide-open to abuse.
        if os.getenv("E2E_DISABLE_RATE_LIMIT"):
            raise RuntimeError(
                "E2E_DISABLE_RATE_LIMIT is set in production — this test-only flag disables "
                "rate limiting and must never be set on Vercel. Unset it in the deploy env."
            )


_assert_required_secrets()

app = FastAPI(
    title="Career Operator API",
    description="AI-powered job search platform (web + mobile)",
    version="1.1.0",
)

# NOTE on routing: Vercel Services may deliver requests to this app with the "/api"
# routePrefix STRIPPED (e.g. "/api/auth/register" arrives as "/auth/register"). Rather
# than guess the transform (a scope-rewriting middleware was NOT honored by Vercel's ASGI
# adapter), we register every /api/* route ALSO at its bare path at the bottom of this
# file — so the SAME endpoint matches whether or not the prefix arrives. This mirrors how
# /health and /api/health already both work.

# CORS. Auth is Bearer-token (no cookies). We NEVER fall back to a wide-open ``*`` policy:
# the unified Vercel deploy is SAME-ORIGIN (the web app calls ``/api`` on its own domain) and
# the mobile app is NATIVE (CORS is a browser-only mechanism), so neither client needs a
# permissive cross-origin policy. Locking the default closes the wide-open-CORS hardening gap
# (Quality #94) without breaking any real client.
_LOCAL_DEV_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


def resolve_cors_origins(explicit: List[str], is_vercel: bool) -> List[str]:
    """Resolve the CORS allow-list. Returns explicit origins when configured; otherwise a
    SAFE default that is never ``*``:

    - explicit ``ALLOWED_ORIGINS`` set -> use exactly those (credentials are re-enabled by the
      caller, keyed on this being non-empty);
    - production (Vercel) with none set -> ``[]`` (same-origin web + native mobile both still
      work; no cross-origin browser reads are permitted — the hardened default);
    - local/dev with none set -> the localhost Next dev-server origins so ``next dev`` (and the
      cross-port E2E run) can call a locally-running API.
    """
    if explicit:
        return explicit
    return [] if is_vercel else list(_LOCAL_DEV_ORIGINS)


_explicit_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
_cors_origins = resolve_cors_origins(_explicit_origins, bool(os.getenv("VERCEL")))
if os.getenv("VERCEL") and not _explicit_origins:
    # Non-fatal (same-origin web + native mobile both still work), but worth surfacing: set
    # ALLOWED_ORIGINS to permit any ADDITIONAL browser origin (e.g. a separate marketing
    # domain). We warn rather than fail so a missing var can never take the live API down.
    logger.warning(
        "CORS is locked to same-origin in production (ALLOWED_ORIGINS unset). Set "
        "ALLOWED_ORIGINS to allow additional browser origins (this also re-enables "
        "credentialed requests)."
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=bool(_explicit_origins),  # credentials only with an explicit allow-list
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security headers on every response.
# CSP here is intentionally limited to frame-ancestors (clickjacking defense) rather than
# a restrictive default-src/script-src: this app also serves the Swagger UI at /docs, which
# loads its assets from a CDN — a strict CSP would break it. Responses are JSON anyway, so
# resource-loading CSP adds little; frame-ancestors complements X-Frame-Options. HSTS forces
# HTTPS for a year (Vercel serves TLS); harmless on localhost (browsers ignore it on http).
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "frame-ancestors 'none'",
    # Deny powerful browser capabilities by default. The API serves JSON (and the
    # Swagger UI at /docs), neither of which needs camera/mic/geolocation/etc., so a
    # blanket deny is free defense-in-depth — an embedded/abused response can never
    # prompt for these features.
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
        "magnetometer=(), gyroscope=(), accelerometer=(), browsing-topics=()"
    ),
}


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Assign a correlation id to every request and stamp security headers on the response.

    The id is exposed three ways: in `request.state` (for handlers), in the `request_id`
    log contextvar (so every log line during this request carries it), and back to the
    client as the `X-Request-ID` response header + inside the error envelope.
    """
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = rid
    token = request_id_var.set(rid)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    for k, v in SECURITY_HEADERS.items():
        response.headers[k] = v
    return response


def _request_id(request: Request) -> Optional[str]:
    return getattr(request.state, "request_id", None)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Return HTTPExceptions in the consistent envelope (keeps the native `detail`)."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.status_code, exc.detail, _request_id(request)),
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """422 body validation errors, wrapped in the same envelope (detail = field errors).

    `exc.errors()` can hold non-JSON-native objects (e.g. ValueError in `ctx`), so it goes
    through `jsonable_encoder` exactly like FastAPI's default handler does.
    """
    from fastapi.encoders import jsonable_encoder

    return JSONResponse(
        status_code=422,
        content=error_body(422, jsonable_encoder(exc.errors()), _request_id(request)),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Error hygiene: never leak stack traces / internals to clients."""
    logger.exception(
        "Unhandled error on %s",
        request.url.path,
        extra={"path": request.url.path, "method": request.method, "status": 500},
    )
    return JSONResponse(
        status_code=500,
        content=error_body(500, "Internal server error", _request_id(request)),
    )


# ---------------------------------------------------------------------------
# Rate limiting + per-user/day LLM spend ceiling.
# CROSS-INSTANCE (ROADMAP Track F): backed by the shared Postgres ``rate_counters`` table,
# NOT in-process state. On Vercel serverless each invocation may run on a fresh instance, so
# the previous in-memory dicts only slowed abuse within ONE warm instance — the LLM spend
# ceiling in particular multiplied per instance, defeating the wallet-drain defense. The DB
# counter makes the limit GLOBAL: every instance reads/writes the same tally.
# ---------------------------------------------------------------------------

# Per-user/day ceiling on expensive LLM operations (wallet-drain defense).
LLM_DAILY_CEILING = int(os.getenv("LLM_DAILY_CEILING", "25"))


def _consume_counter(
    db: Session, subject: str, bucket: str, limit: int, window_seconds: int
) -> bool:
    """Atomically count one hit against a fixed window; return False if over ``limit``.

    Cross-instance + durable: the tally lives in Postgres and is COMMITTED immediately, so
    it holds across serverless instances AND is not lost if the request later errors (an
    expensive LLM attempt still counts — no fake under-count). Runs on the request's own
    session (so it transparently uses the test DB under dependency overrides); the early
    commit only persists the counter row (and any already-valid pending write), which is
    safe because limiter checks run before the endpoint does its real work.

    Concurrency: ``SELECT ... FOR UPDATE`` serializes concurrent increments on Postgres
    (a no-op on SQLite, which serializes writes itself); a first-insert race surfaces as an
    IntegrityError on the unique window key and is retried as an update.
    """
    window_key = int(time.time() // window_seconds)

    # Prune stale windows for this subject+bucket so the table stays bounded. (On the rare
    # insert-race retry below this prune is rolled back with the failed INSERT and simply
    # runs again on the next call — harmless; the table is still bounded over time.)
    db.query(RateCounter).filter(
        RateCounter.subject == subject,
        RateCounter.bucket == bucket,
        RateCounter.window_key < window_key,
    ).delete(synchronize_session=False)

    for _attempt in (1, 2):
        row = (
            db.query(RateCounter)
            .filter(
                RateCounter.subject == subject,
                RateCounter.bucket == bucket,
                RateCounter.window_key == window_key,
            )
            .with_for_update()
            .first()
        )
        if row is None:
            db.add(
                RateCounter(
                    subject=subject, bucket=bucket, window_key=window_key, count=1
                )
            )
            try:
                db.commit()
            except IntegrityError:
                # A concurrent request inserted the same window first — retry as update.
                db.rollback()
                continue
            return 1 <= limit
        if row.count >= limit:
            db.commit()  # commit the stale-window prune + release the row lock; count unchanged
            return False
        row.count += 1
        db.commit()
        return True
    return False


# Per-ACCOUNT login lockout (defends one account against a distributed password
# brute-force that spreads across IPs, which the per-IP rate limit alone misses). In-memory
# like the rate limiter above, so it's per-instance on serverless. Keyed by email so it
# never reveals whether the account exists.
# KNOWN TRADEOFF (honest): a hard lockout is a targeted-DoS vector — someone who knows a
# victim's email can keep the account locked by failing 5 logins every window. Moving to a
# shared store (Track F) does NOT fix this (it would centralize the lock). The real fix is
# CAPTCHA on the auth form (Track F / PENDING_OPS, needs owner keys) so automated failure
# floods are stopped before they count. The short window (15 min) bounds the harm meanwhile.
_LOGIN_FAILURES: Dict[str, Tuple[int, float]] = {}  # email -> (consecutive_failures, locked_until_ts)
LOGIN_MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
LOGIN_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "900"))  # 15 min
_LOGIN_FAILURES_MAXSIZE = 50000  # bound memory: ghost-email floods can't grow this unbounded


def _login_locked(email: str) -> bool:
    record = _LOGIN_FAILURES.get(email)
    if not record:
        return False
    failures, locked_until = record
    if locked_until and time.time() < locked_until:
        return True
    if locked_until and time.time() >= locked_until:
        _LOGIN_FAILURES.pop(email, None)  # lockout expired — reset
    return False


def _sweep_login_failures() -> None:
    """Drop expired/decayed entries when the map gets large (ghost-email flood defense).
    Entries with no active lock and stale activity are evicted; if still too large after
    that, clear the whole map (correctness-safe: it only loosens lockouts, never tightens)."""
    now = time.time()
    for key in [k for k, (_, lu) in _LOGIN_FAILURES.items() if lu and now >= lu]:
        _LOGIN_FAILURES.pop(key, None)
    if len(_LOGIN_FAILURES) > _LOGIN_FAILURES_MAXSIZE:
        _LOGIN_FAILURES.clear()


def _record_login_failure(email: str) -> None:
    if len(_LOGIN_FAILURES) >= _LOGIN_FAILURES_MAXSIZE:
        _sweep_login_failures()
    failures = _LOGIN_FAILURES.get(email, (0, 0.0))[0] + 1
    locked_until = time.time() + LOGIN_LOCKOUT_SECONDS if failures >= LOGIN_MAX_FAILURES else 0.0
    _LOGIN_FAILURES[email] = (failures, locked_until)


def _clear_login_failures(email: str) -> None:
    _LOGIN_FAILURES.pop(email, None)


# TEST-ONLY rate-limit bypass. The functional-journey CI job replays every journey from a
# SINGLE runner IP and would trip the per-IP limiter (a false red). Gated on
# E2E_DISABLE_RATE_LIMIT, which production NEVER sets — and _assert_required_secrets() above
# refuses to boot if it is ever present alongside VERCEL. Evaluated once at import.
_RATE_LIMIT_DISABLED = bool(os.getenv("E2E_DISABLE_RATE_LIMIT")) and not os.getenv("VERCEL")


def rate_limit(bucket: str, limit: int, window_seconds: int = 60):
    """Fixed-window limiter dependency factory, keyed by client + bucket (cross-instance)."""
    def _dep(request: Request, db: Session = Depends(get_db)) -> None:
        if _RATE_LIMIT_DISABLED:
            return
        client = get_client_ip(request)
        if not _consume_counter(db, client, bucket, limit, window_seconds):
            raise HTTPException(status_code=429, detail="Too many requests. Slow down.")
    return _dep


def check_llm_ceiling(user: User, db: Session) -> None:
    # 86400s window keyed by user id — a per-user/day ceiling that holds across instances.
    if not _consume_counter(db, user.id, "llm_daily", LLM_DAILY_CEILING, 86400):
        raise HTTPException(
            status_code=429,
            detail="Daily AI usage limit reached. Try again tomorrow.",
        )


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=255)
    # Bounded server-side: ``resume_text`` is embedded verbatim into LLM prompts (the coach
    # system prompt + prep-pack generation). With only a per-day CALL ceiling, an unbounded
    # field lets one account drive the PER-CALL token cost (and bill) arbitrarily high — a
    # wallet-drain vector, especially while provider spend caps are owner-pending. 50k chars
    # (~8k words) is generous for any real resume while killing multi-MB abuse.
    resume_text: Optional[str] = Field(default=None, max_length=50000)
    referral_code: Optional[str] = Field(default=None, max_length=32)


class UserLogin(BaseModel):
    email: str
    password: str


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)
    location: Optional[str] = Field(default=None, max_length=255)
    # Salary bounds: reject negatives and absurd values (data integrity — a negative or
    # MAX_INT salary corrupts pipeline analytics and fit-score math). 10M is a generous ceiling.
    salary_min: Optional[int] = Field(default=None, ge=0, le=10_000_000)
    salary_max: Optional[int] = Field(default=None, ge=0, le=10_000_000)
    # ``description``/``requirements`` feed LLM prep-pack prompts verbatim — bounded for the
    # same wallet-drain reason as ``resume_text`` above. 20k chars (~3k words) covers any real
    # job description while capping the per-call token cost an attacker can force.
    description: Optional[str] = Field(default=None, max_length=20000)
    requirements: Optional[str] = Field(default=None, max_length=20000)
    url: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _check_salary_range(self) -> "JobCreate":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min must not exceed salary_max")
        return self


class JobUpdate(BaseModel):
    status: str


class PrepPackRequest(BaseModel):
    # A user job id (UUID, 36 chars). Bounded so a pathologically long string can't be sent
    # to the DB query / string ops; the endpoint additionally scopes the lookup to the caller.
    job_id: str = Field(min_length=1, max_length=64)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    # Bounded client-supplied ids (a UUID is 36 chars). job_id is only ever an equality
    # filter (JobPosting.id, String(36)) — an over-length value just misses, so the generous
    # 64 mirrors PrepPackRequest.job_id. session_id is INSERTED into ChatMessage.session_id
    # (String(36)), so it is bound to exactly 36: a 37–64-char value would pass Pydantic but
    # raise a DB string-truncation error surfaced as a misleading 502. 422 at the boundary
    # is the honest failure.
    job_id: Optional[str] = Field(default=None, max_length=64)
    session_id: Optional[str] = Field(default=None, max_length=36)


class ReportRequest(BaseModel):
    """A user report/flag of AI-generated content (store GenAI/UGC requirement).

    ``content_type``/``reason`` are constrained to known values (a 422 at the boundary, not a
    silent bad row). The free-text fields are bounded so a report can't be used as an
    unbounded write (they are stored verbatim, never fed back into an LLM prompt).
    """

    content_type: Literal["coach", "prep_pack"]
    reason: Literal["harmful", "inaccurate", "offensive", "other"]
    # Optional client reference to the specific item; equality/audit only, never a write key.
    content_ref: Optional[str] = Field(default=None, max_length=64)
    # A snapshot of the reported text so a moderator can review it (bounded).
    content_excerpt: Optional[str] = Field(default=None, max_length=5000)
    detail: Optional[str] = Field(default=None, max_length=1000)


class AppPurchase(BaseModel):
    receipt_data: str
    platform: str = "ios"


class CheckoutRequest(BaseModel):
    plan: str = Field(min_length=2, max_length=50)


class ImportPreviewRequest(BaseModel):
    careers_url: str = Field(min_length=4, max_length=500)


class WaitlistJoin(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    source: Optional[str] = Field(default=None, max_length=50)


# Cap the preview so one request can't fan out into a huge payload / long fetch.
ATS_PREVIEW_LIMIT = 50

# Pragmatic email shape check (we don't pull in the email-validator dep just for the
# waitlist form): one "@", a dot in the domain, no whitespace. Rejects obvious junk while
# staying permissive about real addresses.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------
def user_public(user: User, db: Session) -> dict:
    limits = AuthService(db).check_usage_limits(user)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "tier": user.tier.value if isinstance(user.tier, UserTier) else user.tier,
        "jobs_remaining": limits["jobs_remaining"],
        "prep_packs_remaining": limits["prep_packs_remaining"],
        "ai_coach": user.tier == UserTier.PREMIUM,
    }


def job_public(job: JobPosting) -> dict:
    status = job.application.status if job.application else ApplicationStatus.SAVED
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company_name or (job.company.name if job.company else None),
        "location": job.location,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "score": round(job.score.overall_score, 1) if job.score else None,
        "score_explanation": job.score.score_explanation if job.score else None,
        "status": status.value if hasattr(status, "value") else status,
        "url": job.url,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


def ats_listing_public(listing, company_slug: Optional[str]) -> dict:
    """Serialize a normalized ATS JobListing for the import-preview response.

    `company_slug` is the ATS board token (e.g. Greenhouse "acme"), NOT a display name —
    named accordingly so a UI doesn't render the slug where a company name belongs.
    """
    return {
        "external_id": listing.external_id,
        "title": listing.title,
        "company_slug": company_slug,
        "location": listing.location,
        "url": listing.url,
        "department": listing.department,
        "remote_type": listing.remote_type,
        "posted_at": listing.posted_at,
    }


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------
def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ", 1)[1]
    user = AuthService(db).get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@app.post("/api/auth/register", dependencies=[Depends(rate_limit("auth", 10))])
def register(data: UserCreate, db: Session = Depends(get_db)):
    auth = AuthService(db)
    try:
        user, token = auth.register(data.email, data.password, data.full_name)
    except ValueError:
        # Do NOT reveal whether the email already exists (enumeration defense).
        raise HTTPException(status_code=400, detail="Could not register with those details")
    if data.resume_text:
        user.resume_text = data.resume_text
    # Commit the signup FIRST so it is durable no matter what the referral step does.
    db.commit()
    db.refresh(user)
    # Referral handling is STRICTLY best-effort: give the new user a shareable code and (if
    # they arrived via someone's link) attribute the referral + grant both sides the real
    # bonus. It runs in its own transaction and ANY failure (e.g. a rare code-collision race)
    # is swallowed so it can NEVER block or fail a signup — the user is already in the app.
    try:
        referrals.ensure_code(db, user)
        referrals.apply_referral(db, data.referral_code, user)
        db.commit()
    except Exception:  # noqa: BLE001 — referral is non-critical; never surface to signup
        db.rollback()
        logger.warning("referral processing failed during signup; continuing", exc_info=True)
        db.refresh(user)
    # Privacy-safe aggregate metric (best-effort, post-commit; counts only, no PII).
    analytics.record_event(db, "signup")
    return {"success": True, "token": token, "user": user_public(user, db)}


@app.post("/api/auth/login", dependencies=[Depends(rate_limit("auth", 10))])
def login(data: UserLogin, db: Session = Depends(get_db)):
    email_key = (data.email or "").lower()
    # Per-account lockout. Same generic 429 whether or not the account exists, so it can't
    # be used to enumerate emails.
    if _login_locked(email_key):
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Try again in about {LOGIN_LOCKOUT_SECONDS // 60} minutes.",
        )
    auth = AuthService(db)
    try:
        user, token = auth.login(data.email, data.password)
    except ValueError:
        _record_login_failure(email_key)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    _clear_login_failures(email_key)
    db.commit()
    return {"success": True, "token": token, "user": user_public(user, db)}


@app.get("/api/auth/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "user": user_public(user, db)}


@app.get("/api/referrals/me")
def referrals_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The caller's referral code, how many friends joined with it, and bonus earned."""
    stats = referrals.referral_stats(db, user)
    db.commit()  # ensure_code may have lazily assigned a code on first read
    return {"success": True, "referral": stats}


@app.delete("/api/auth/me", dependencies=[Depends(rate_limit("auth", 10))])
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Permanently delete the signed-in user and all their data.

    Required by Apple (App Store Review 5.1.1(v)) and Google Play for any app with account
    creation. A REAL deletion: cascades remove the user's jobs, scores, applications, prep
    artifacts, and chat history (see the relationship cascades on the User/JobPosting models),
    so nothing user-owned is left orphaned. Honest by design — we only report success after
    the row is actually gone.
    """
    AuthService(db).delete_user(user)
    db.commit()
    _clear_login_failures((user.email or "").lower())
    return {"success": True, "deleted": True}


# ---------------------------------------------------------------------------
# Waitlist (pre-launch growth capture — Track G/H)
# ---------------------------------------------------------------------------
# A generic, identical response for both new and already-present emails: the endpoint must
# never reveal whether an address is already on the list (enumeration defense, same posture
# as register/login).
_WAITLIST_OK = {"success": True, "message": "You're on the list — we'll be in touch."}


@app.post("/api/waitlist/join", dependencies=[Depends(rate_limit("waitlist", 5, 3600))])
def join_waitlist(data: WaitlistJoin, db: Session = Depends(get_db)):
    """Capture a pre-launch waitlist signup.

    NO email is sent (no provider is wired — gating on an unbuilt email loop would dead-end
    the visitor; DECISION COROLLARY). The DB row IS the real, verifiable side-effect, which
    makes visitor->signup measurable. Double-opt-in (confirmation email round-trip) lands
    with a real/sandbox email provider under Track H / F4.1.
    """
    email = (data.email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    if db.query(Waitlist).filter(Waitlist.email == email).first():
        return _WAITLIST_OK  # already on the list — indistinguishable from a fresh signup
    source = ((data.source or "").strip() or "organic")[:50]
    full_name = ((data.full_name or "").strip() or None)
    db.add(Waitlist(email=email, full_name=full_name, source=source))
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request won the unique-email slot between the check and the insert.
        # Still a success for the user, still no enumeration signal.
        db.rollback()
    return _WAITLIST_OK


@app.post("/api/auth/verify-purchase", dependencies=[Depends(rate_limit("auth", 10))])
def verify_purchase(
    data: AppPurchase,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upgrade to premium after a VERIFIED store purchase.

    SIDE-EFFECT INTEGRITY (FACTORY_STANDARD §6): a client-supplied receipt is NOT trusted to
    grant entitlement — that would be a client-trusted unlock. Mobile purchases are verified
    server-side out-of-band by RevenueCat, which POSTs a shared-secret-authenticated webhook
    to ``/api/billing/revenuecat-webhook`` (the only path that flips a mobile user to
    Premium). This client endpoint therefore never grants anything; it refuses honestly (501)
    so the app relies on the verified webhook + a ``/me`` refresh, never a self-reported
    unlock. Tracked in ROADMAP Track C + PENDING_OPS.
    """
    raise HTTPException(
        status_code=501,
        detail="Purchase verification is not available yet. No charge was applied and "
        "your plan is unchanged.",
    )


# ---------------------------------------------------------------------------
# Billing (web subscriptions via Stripe Checkout) — Track C.
# ---------------------------------------------------------------------------
def _web_base_url(request: Request) -> str:
    """Origin to send the user back to after Checkout. On the unified Vercel deployment the
    web app and API share an origin, so the request origin is correct; WEB_APP_URL overrides
    it (e.g. when the API runs on a separate origin from the site)."""
    explicit = os.getenv("WEB_APP_URL")
    if explicit:
        return explicit.rstrip("/")
    return str(request.base_url).rstrip("/")


@app.post("/api/billing/checkout", dependencies=[Depends(rate_limit("billing", 10))])
def billing_checkout(
    data: CheckoutRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Create a real Stripe Checkout session and return its hosted URL.

    SIDE-EFFECT INTEGRITY: this makes a REAL stripe.checkout.Session.create call. When
    Stripe isn't configured (no owner keys) it returns an HONEST 503 and applies no charge —
    never a fake success. Entitlement is granted only later, by the signed webhook.
    """
    if user.tier == UserTier.PREMIUM:
        raise HTTPException(status_code=400, detail="You're already on a Premium plan.")
    base = _web_base_url(request)
    try:
        url = billing.create_checkout_session(
            user,
            data.plan,
            success_url=f"{base}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/billing/cancel",
        )
    except billing.UnknownPlan:
        raise HTTPException(status_code=400, detail="Unknown plan.")
    except billing.BillingNotConfigured:
        raise HTTPException(
            status_code=503,
            detail="Subscriptions aren't available yet. No charge was made.",
        )
    return {"url": url}


@app.post("/api/billing/webhook")
async def billing_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive Stripe webhook events, VERIFY the signature, and persist entitlement.

    The raw request body is required for signature verification. We grant/revoke Premium
    only from a signature-verified event — an unsigned or forged payload changes nothing.
    """
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = billing.construct_event(payload, sig)
    except billing.BillingNotConfigured:
        raise HTTPException(status_code=503, detail="Billing webhook is not configured.")
    except Exception:
        # Invalid signature / malformed payload — grant NOTHING.
        raise HTTPException(status_code=400, detail="Invalid signature.")
    billing.apply_event(event, db)
    db.commit()
    return {"received": True}


@app.post("/api/billing/revenuecat-webhook")
async def revenuecat_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive RevenueCat (mobile IAP) webhook events, VERIFY the shared secret, and persist
    entitlement.

    SIDE-EFFECT INTEGRITY: a mobile user becomes Premium ONLY here, from a webhook whose
    ``Authorization`` header matches the owner-configured shared secret. A forged / missing
    header grants NOTHING (401); when the secret isn't set we refuse honestly (503). The app
    never self-reports entitlement — ``users.tier`` is flipped solely by a verified event.
    """
    auth = request.headers.get("authorization")
    try:
        mobile_billing.verify_authorization(auth)
    except mobile_billing.MobileBillingNotConfigured:
        raise HTTPException(status_code=503, detail="Mobile billing webhook is not configured.")
    except mobile_billing.InvalidWebhookAuth:
        # Wrong/missing secret — grant NOTHING.
        raise HTTPException(status_code=401, detail="Invalid webhook authorization.")
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed webhook payload.")
    mobile_billing.apply_event(payload, db)
    db.commit()
    return {"received": True}


# ---------------------------------------------------------------------------
# Job endpoints
# ---------------------------------------------------------------------------
@app.post("/api/jobs", dependencies=[Depends(rate_limit("write", 30))])
def create_job(
    data: JobCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth = AuthService(db)
    limits = auth.check_usage_limits(user)
    if not limits["can_add_job"]:
        raise HTTPException(
            status_code=403,
            detail="Free tier is limited to 5 tracked jobs. Upgrade to Pro for unlimited.",
        )

    job = JobPosting(
        user_id=user.id,
        title=data.title,
        company_name=data.company_name,
        location=data.location,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        description=data.description,
        requirements=data.requirements,
        url=data.url,
    )
    db.add(job)
    db.flush()

    # Score (heuristic fallback when no Gemini key — never crashes).
    scored = False
    try:
        JobScorer(db).score_job(job, user)
        scored = True
    except Exception:
        logger.exception("Scoring failed for job %s; continuing unscored", job.id)

    # Track it: create the pipeline Application row in SAVED.
    db.add(Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.SAVED))
    auth.increment_job_usage(user)
    db.commit()
    db.refresh(job)
    # Privacy-safe aggregate metrics (best-effort, post-commit; counts only, no PII). The
    # signup→job_added→fit_score_generated funnel is the activation ("aha") leading indicator.
    analytics.record_event(db, "job_added")
    if scored:
        analytics.record_event(db, "fit_score_generated")
    return {"success": True, "job": job_public(job)}


@app.get("/api/jobs")
def list_jobs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(None, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    # Eager-load the relationships ``job_public`` reads (application/score/company) so the
    # serializer never lazy-loads per row: one query per relationship instead of 3N+1.
    # ``limit`` is OPTIONAL and additive — omitting it preserves the original "return all"
    # contract (no client truncation); supplying it lets a client page an unbounded list.
    query = (
        db.query(JobPosting)
        .filter(JobPosting.user_id == user.id)
        .options(
            selectinload(JobPosting.application),
            selectinload(JobPosting.score),
            selectinload(JobPosting.company),
        )
        .order_by(JobPosting.created_at.desc())
    )
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    jobs = query.all()
    return {"success": True, "jobs": [job_public(j) for j in jobs]}


@app.get("/api/jobs/{job_id}")
def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = (
        db.query(JobPosting)
        .filter(JobPosting.id == job_id, JobPosting.user_id == user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "job": job_public(job)}


VALID_STATUSES = {s.value for s in ApplicationStatus}


@app.patch("/api/jobs/{job_id}", dependencies=[Depends(rate_limit("write", 60))])
def update_job_status(
    job_id: str,
    data: JobUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Must be one of: {sorted(VALID_STATUSES)}",
        )
    job = (
        db.query(JobPosting)
        .filter(JobPosting.id == job_id, JobPosting.user_id == user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    application = job.application
    if not application:
        application = Application(user_id=user.id, job_id=job.id)
        db.add(application)
    application.status = ApplicationStatus(data.status)
    application.last_activity_at = datetime.utcnow()
    if data.status == ApplicationStatus.APPLIED.value and not application.applied_at:
        application.applied_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return {"success": True, "job": job_public(job)}


# ---------------------------------------------------------------------------
# ATS ingestion — import open roles from a company's Greenhouse/Lever board.
# Preview-only (no side effects): we return REAL listings or a TRUTHFUL empty/
# unreachable state, and the user adds the ones they want via POST /api/jobs.
# We never fabricate jobs and never claim "no jobs" when the board was unreachable.
# ---------------------------------------------------------------------------
@app.post("/api/jobs/import-preview", dependencies=[Depends(rate_limit("ingest", 6))])
def import_jobs_preview(
    data: ImportPreviewRequest,
    user: User = Depends(get_current_user),
):
    from src.ingestion.detector import ATSDetector
    from src.ingestion.url_guard import assert_public_http_url, UnsafeURLError

    # SSRF defense: refuse to fetch internal/non-public targets before any network call.
    try:
        assert_public_http_url(data.careers_url)
    except UnsafeURLError:
        raise HTTPException(
            status_code=400,
            detail="Enter a public http(s) careers URL (internal/private addresses are not allowed).",
        )

    detector = ATSDetector()
    try:
        ats_type, identifier = detector.detect_from_careers_page(data.careers_url)
    except Exception:
        logger.exception("ATS detection raised for %s", data.careers_url)
        ats_type, identifier = ATSType.UNKNOWN, None

    supported = {ATSType.GREENHOUSE, ATSType.LEVER}
    if ats_type not in supported or not identifier:
        # Honest: no SUPPORTED board to fetch. Distinguish "found an unsupported board"
        # (Ashby/Workday) from "found nothing", and never imply an empty board.
        if ats_type in (ATSType.ASHBY, ATSType.WORKDAY):
            message = (
                f"We detected a {ats_type.value.title()} job board, but only Greenhouse and "
                "Lever are supported right now. Add the role manually for now."
            )
        else:
            message = (
                "We couldn't find a supported job board (Greenhouse or Lever) at that link. "
                "Paste the company's Greenhouse or Lever careers URL, or add the role manually."
            )
        return {
            "success": True,
            "ats": ats_type.value,
            "supported": False,
            "jobs": [],
            "truncated": False,
            "message": message,
        }

    # ats_type is GREENHOUSE/LEVER here, so get_client_for_company never raises.
    client = detector.get_client_for_company(ats_type, identifier)
    try:
        listings = client.fetch_jobs()
    except Exception:
        logger.exception("ATS fetch raised for %s/%s", ats_type.value, identifier)
        listings, client.last_error = [], "fetch raised"

    # fetch_jobs() swallows network errors and returns []; last_error tells us whether the
    # empty result is "unreachable" (a real failure) vs "genuinely no open roles" (truthful).
    if not listings and client.last_error:
        return {
            "success": True, "ats": ats_type.value, "supported": True, "reachable": False,
            "jobs": [], "truncated": False,
            "message": "That job board was temporarily unreachable. Please try again shortly.",
        }

    capped = listings[:ATS_PREVIEW_LIMIT]
    return {
        "success": True,
        "ats": ats_type.value,
        "supported": True,
        "reachable": True,
        "jobs": [ats_listing_public(j, identifier) for j in capped],
        "truncated": len(listings) > ATS_PREVIEW_LIMIT,
        "message": None if capped else "No open roles are posted on that board right now.",
    }


# ---------------------------------------------------------------------------
# Prep packs (LLM — degrades gracefully)
# ---------------------------------------------------------------------------
@app.post("/api/prep-packs/generate", dependencies=[Depends(rate_limit("llm", 10))])
def generate_prep_pack(
    data: PrepPackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth = AuthService(db)
    limits = auth.check_usage_limits(user)
    if not limits["can_generate_prep"]:
        raise HTTPException(
            status_code=403,
            detail="Free tier is limited to 1 prep pack/month. Upgrade to Pro for more.",
        )

    job = (
        db.query(JobPosting)
        .filter(JobPosting.id == data.job_id, JobPosting.user_id == user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not llm_available():
        # Truthful graceful degradation — not a crash, not a fake result.
        raise HTTPException(
            status_code=503,
            detail="AI prep packs require the server's GEMINI_API_KEY to be configured.",
        )

    check_llm_ceiling(user, db)
    try:
        artifact: PrepArtifact = LLMWorkflows(db).generate_prep_pack(job, user)
    except Exception:
        logger.exception("Prep pack generation failed")
        raise HTTPException(status_code=502, detail="AI provider error generating prep pack")

    auth.increment_prep_usage(user)
    db.commit()
    analytics.record_event(db, "prep_pack_generated")  # aggregate metric (best-effort, no PII)
    return {
        "success": True,
        "prep_pack": {
            "id": artifact.id,
            "title": artifact.title,
            "content": artifact.content,
        },
        "prep_packs_remaining": auth.check_usage_limits(user)["prep_packs_remaining"],
    }


# ---------------------------------------------------------------------------
# AI coach (Premium; LLM — degrades gracefully)
# ---------------------------------------------------------------------------
@app.post("/api/coach/chat", dependencies=[Depends(rate_limit("llm", 20))])
def coach_chat(
    data: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.tier != UserTier.PREMIUM:
        raise HTTPException(
            status_code=403,
            detail="The AI Career Coach is a Premium feature. Upgrade to unlock it.",
        )
    if not CareerCoach.available():
        raise HTTPException(
            status_code=503,
            detail="The AI Coach requires the server's GEMINI_API_KEY to be configured.",
        )

    check_llm_ceiling(user, db)
    job = None
    if data.job_id:
        job = (
            db.query(JobPosting)
            .filter(JobPosting.id == data.job_id, JobPosting.user_id == user.id)
            .first()
        )
    try:
        reply = CareerCoach(db).chat(
            user=user,
            message=data.message,
            session_id=data.session_id,
            job_context=job,
        )
    except Exception:
        logger.exception("Coach chat failed")
        raise HTTPException(status_code=502, detail="AI provider error in coach chat")
    db.commit()
    analytics.record_event(db, "coach_message")  # aggregate metric (best-effort, no PII)
    return {"success": True, "message": reply}


@app.get("/api/coach/suggestions", dependencies=[Depends(rate_limit("suggest", 30))])
def coach_suggestions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Rate-limited (was the only coach endpoint without one): it runs a per-user context
    # query on every call, so an authed client shouldn't be able to hammer it unbounded.
    # Works without an LLM key — deterministic, context-aware suggestions.
    suggestions = CareerCoach(db).get_suggested_questions(user)
    return {"success": True, "suggestions": suggestions}


# ---------------------------------------------------------------------------
# Report AI-generated content (Apple/Google 2026 GenAI/UGC requirement)
# ---------------------------------------------------------------------------
@app.post("/api/report", dependencies=[Depends(rate_limit("report", 20))])
def report_content(
    data: ReportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a signed-in user's report of an AI-generated coach reply or prep pack.

    SIDE-EFFECT INTEGRITY: the only success we report is the one we can back — a committed
    row a moderator can review. We commit FIRST, then return success; there is NO claim of
    any downstream notification (no email/alert pipeline is wired, so we don't pretend one
    is — DECISION COROLLARY). Rate-limited so the endpoint can't be used to flood the table.
    """
    report = ContentReport(
        user_id=user.id,
        content_type=data.content_type,
        reason=data.reason,
        content_ref=data.content_ref,
        content_excerpt=data.content_excerpt,
        detail=data.detail,
    )
    db.add(report)
    db.commit()
    return {"success": True, "message": "Thanks — this response has been flagged for review."}


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@app.get("/api/analytics/pipeline")
def pipeline_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Eager-load application + score so the aggregate loop (and the top-5 sort, which both
    # read job.score) never lazy-loads per row; also company, which job_public() reads when
    # building the top_jobs payload (company_name may be empty for ATS-scraped jobs). Fully
    # batched: 3 queries instead of 2N+1.
    jobs = (
        db.query(JobPosting)
        .filter(JobPosting.user_id == user.id)
        .options(
            selectinload(JobPosting.application),
            selectinload(JobPosting.score),
            selectinload(JobPosting.company),
        )
        .all()
    )
    status_counts: Dict[str, int] = {}
    scores = []
    for job in jobs:
        status = job.application.status.value if job.application else ApplicationStatus.SAVED.value
        status_counts[status] = status_counts.get(status, 0) + 1
        if job.score:
            scores.append(job.score.overall_score)
    avg = round(sum(scores) / len(scores), 1) if scores else 0.0
    top = sorted(
        (j for j in jobs if j.score),
        key=lambda j: j.score.overall_score,
        reverse=True,
    )[:5]
    return {
        "success": True,
        "stats": {
            "total_jobs": len(jobs),
            "status_breakdown": status_counts,
            "average_score": avg,
            "top_jobs": [job_public(j) for j in top],
        },
    }


@app.get("/api/analytics/summary", dependencies=[Depends(rate_limit("analytics", 30))])
def analytics_summary(request: Request, db: Session = Depends(get_db)):
    """Privacy-safe AGGREGATE product metrics for the owner's growth dashboard (counts only —
    no PII, no per-user data). Gated by a SERVER-SIDE shared secret (``ANALYTICS_READ_TOKEN``),
    NOT any authenticated user, so aggregate counts can never leak to end users. Returns an
    honest 503 when the token is unset (the endpoint is opt-in ops tooling, not a product
    feature — the app is fully functional without it).
    """
    token = os.getenv("ANALYTICS_READ_TOKEN")
    if not token:
        raise HTTPException(status_code=503, detail="Analytics read API is not configured.")
    provided = request.headers.get("authorization", "")
    # Constant-time compare so the token can't be recovered by timing.
    if not hmac.compare_digest(provided, f"Bearer {token}"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"success": True, "analytics": analytics.summary(db)}


@app.get("/")
def root():
    """Friendly landing payload so the base URL isn't a bare 404 (it's an API)."""
    return {
        "name": "Career Operator API",
        "status": "ok",
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
@app.get("/api/health")
def health():
    # /api/health is reachable in the unified Vercel deployment (backend mounted at /api);
    # /health is for local/container runs where the app owns the root.
    return {"status": "healthy", "version": app.version, "llm_enabled": llm_available()}


def _ensure_schema() -> None:
    """Create any missing tables on cold start (idempotent).

    Runs once per process import, which on Vercel serverless means once per cold
    start — guaranteed regardless of whether the ASGI adapter fires lifespan events.
    Safe: create_all only adds missing tables, never drops/alters. Disable by setting
    AUTO_CREATE_TABLES=0 once you adopt real alembic migrations. Wrapped so a slow/down
    DB never crashes the import (the request would surface the error instead).
    """
    if os.getenv("AUTO_CREATE_TABLES", "1") != "1":
        return
    try:
        from src.db import engine
        from src.db.models import Base

        Base.metadata.create_all(bind=engine)
    except Exception:
        logger.exception("AUTO_CREATE_TABLES: schema init skipped (DB unreachable?)")


_ensure_schema()


def _mirror_api_routes_at_bare_path() -> None:
    """Register every /api/* route ALSO at its bare path (drop the leading /api).

    Vercel Services may strip the "/api" routePrefix before the request reaches this app,
    so the same endpoint must match whether the prefix arrives or not. This is the
    routing-layer equivalent of /health + /api/health both existing — proven to work.
    """
    from fastapi.routing import APIRoute

    # Dedup by (path, method) — NOT path alone — so multi-method paths (e.g. /api/jobs has
    # GET+POST, /api/jobs/{id} has GET+PATCH) get ALL their methods mirrored. Keying by
    # path-only left the 2nd method 405ing on Vercel.
    existing = {
        (r.path, m)
        for r in app.router.routes
        if isinstance(r, APIRoute)
        for m in (r.methods or [])
    }
    for r in list(app.router.routes):
        if isinstance(r, APIRoute) and r.path.startswith("/api/"):
            bare = r.path[len("/api"):]  # "/api/jobs" -> "/jobs"
            methods = [m for m in (r.methods or []) if (bare, m) not in existing]
            if bare and methods:
                app.router.add_api_route(
                    bare,
                    r.endpoint,
                    methods=methods,
                    response_model=r.response_model,
                    status_code=r.status_code,
                    dependencies=r.dependencies,
                    include_in_schema=False,
                )
                for m in methods:
                    existing.add((bare, m))


_mirror_api_routes_at_bare_path()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
