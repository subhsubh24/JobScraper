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
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.errors import error_body
from src.api.ip_extraction import get_client_ip
from src.api.logging_config import request_id_var, setup_logging
from src.security.captcha import verify_captcha

from src.ai_coach.career_coach import CareerCoach
from src.auth.auth_service import AuthService
from src.db import get_db
from src.db.models import (
    Application,
    ApplicationStatus,
    ATSType,
    ContentReport,
    EnrichedCompetency,
    JobPosting,
    JobScore,
    MockInterview,
    PrepArtifact,
    RateCounter,
    User,
    UserTier,
    Waitlist,
)
from src.enrichment.llm_workflows import LLMWorkflows, ModeratedContentError
from src.enrichment.github_enricher import (
    discover_github_competencies,
    parse_github_username,
    replace_github_competencies,
)
from src.insights.demo_match import analyze_demo_match
from src.insights.readiness import compute_readiness
from src.insights.skill_gaps import analyze_skill_gaps
from src.llm import llm_available
from src.ranking.scorer import JobScorer
from src import analytics
from src import billing
from src import mobile_billing
from src import referrals
from src.email import EmailMessage, email_enabled, send_email
from src.email.tokens import make_confirm_token, verify_confirm_token

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

# Per-user/day ceiling on the JOB-SCORING embedding call (a SEPARATE, more generous brake).
# Every new job triggers a paid Gemini embedding of its description in ``score_job`` — a path
# the feature ceiling above does NOT cover, so an account with unlimited jobs (any paid tier)
# could drive unbounded embedding spend. This caps the number of PAID scoring calls per user
# per day; over the cap a job is still created but left UNSCORED (the same graceful outcome as
# a scoring error) rather than blocking the add or burning money. Kept well above any real
# daily job-add volume so it never bites a genuine user — only runaway/scripted abuse.
SCORE_DAILY_CEILING = int(os.getenv("SCORE_DAILY_CEILING", "100"))


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


def rate_limit_user(bucket: str, limit: int, window_seconds: int = 60):
    """Per-USER fixed-window limiter for AUTHED endpoints — keyed by user id, not client IP.

    Authed reads (session restore, the pipeline list, job detail) are hit on every app launch
    and pull-to-refresh, and behind carrier-grade NAT many distinct users share ONE public IP,
    so an IP-keyed limit (``rate_limit``) would false-429 legitimate mobile users the moment a
    busy NAT crossed the threshold. Keying by user id — like ``check_llm_ceiling`` — removes
    that shared-IP hazard AND gives real per-account abuse protection: a single compromised
    token can't hammer these DB-reading endpoints unbounded. The subject is prefixed ``user:``
    so its counter rows never collide with the IP-keyed limiter's, even in a shared bucket.
    """
    def _dep(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        if _RATE_LIMIT_DISABLED:
            return
        if not _consume_counter(db, f"user:{user.id}", bucket, limit, window_seconds):
            raise HTTPException(status_code=429, detail="Too many requests. Slow down.")
    return _dep


def check_llm_ceiling(user: User, db: Session) -> None:
    # 86400s window keyed by user id — a per-user/day ceiling that holds across instances.
    if not _consume_counter(db, user.id, "llm_daily", LLM_DAILY_CEILING, 86400):
        raise HTTPException(
            status_code=429,
            detail="Daily AI usage limit reached. Try again tomorrow.",
        )


def ai_consent_ok(user: User) -> bool:
    """True once the user has granted third-party-AI consent (Apple 5.1.2(i))."""
    return user.ai_consent_at is not None


def require_ai_consent(user: User) -> None:
    """Gate any path that sends personal data to the third-party AI (Gemini).

    Apple App Review 5.1.2(i) requires EXPLICIT, revocable consent BEFORE personal data is
    shared with a third-party AI — a blanket privacy-policy/account acceptance does not
    satisfy it. Raises a 403 with a machine-readable ``code`` the clients key on to surface
    the consent prompt (never a dead-end): granting it and retrying completes the flow. The
    check is enforced server-side on EVERY generative AI endpoint; the client flag is only a
    UX hint. (Job scoring degrades to a fully-local heuristic instead of blocking — see
    ``create_job`` — so the core loop still works before consent, with no third-party share.)
    """
    if not ai_consent_ok(user):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ai_consent_required",
                "message": (
                    "Enable AI features to use this. We'll send the relevant text to our AI "
                    "provider (Google Gemini) to generate this for you — you can turn this "
                    "off anytime in Settings."
                ),
            },
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
    # Cloudflare Turnstile solution from the client widget. Optional at the schema layer so the
    # seam stays a no-op until the owner connects Turnstile (see src/security/captcha.py); once
    # TURNSTILE_SECRET is set the endpoint rejects a request whose token is missing/invalid.
    captcha_token: Optional[str] = Field(default=None, max_length=4096)


class ResumeUpdate(BaseModel):
    # Same 50k bound + wallet-drain rationale as UserCreate.resume_text above: this text is
    # embedded verbatim into LLM prompts (scoring, prep packs, tailored résumé, cover letters).
    resume_text: str = Field(default="", max_length=50000)


class UserLogin(BaseModel):
    email: str
    password: str
    captcha_token: Optional[str] = Field(default=None, max_length=4096)


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

    content_type: Literal["coach", "prep_pack", "mock_interview"]
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


class SalaryNegotiationRequest(BaseModel):
    job_id: str = Field(min_length=1, max_length=64)
    # gt=0 (not ge=0): a target of 0 is not a real negotiation goal — it would burn a paid
    # LLM call (and a slot of the user's daily ceiling) generating a nonsensical "$0" guide
    # and return success:true. Reject it server-side so a direct API caller can't do that; the
    # web client already guards, but the server is the source of truth (Track F input bounds).
    target_salary: int = Field(gt=0, le=10_000_000)


class CoverLetterRequest(BaseModel):
    # Same bounded job id contract as PrepPackRequest — the endpoint scopes the lookup to the
    # caller, so an over-length value just misses; 422 at the boundary is the honest failure.
    job_id: str = Field(min_length=1, max_length=64)


class StudyPlanRequest(BaseModel):
    job_id: str = Field(min_length=1, max_length=64)
    # A day-by-day study plan. Bounded 1–30: <1 is meaningless and >30 would inflate the LLM
    # prompt/response without adding value (an interview is never 30+ days of daily cramming) —
    # the bound is an honest abuse guard on a paid, LLM-backed generation, not a product limit.
    days: int = Field(default=7, ge=1, le=30)


class TailoredResumeRequest(BaseModel):
    # Same bounded job id contract as the other prep tools — the endpoint scopes the lookup to
    # the caller, so an over-length value just misses; 422 at the boundary is the honest failure.
    job_id: str = Field(min_length=1, max_length=64)


class MockInterviewStartRequest(BaseModel):
    # Same bounded job id contract as the other prep tools.
    job_id: str = Field(min_length=1, max_length=64)
    # 3–8 questions: <3 is not a real interview, >8 inflates the LLM prompt/response and the
    # session without adding practice value. Bounded as an honest abuse guard on a paid call.
    num_questions: int = Field(default=5, ge=3, le=8)


class MockInterviewAnswerRequest(BaseModel):
    # Which question is being answered (0-based; the endpoint bounds it to the session's set).
    question_index: int = Field(ge=0, le=7)
    # The candidate's answer. Bounded so one scored answer can't be an unbounded LLM prompt;
    # min_length 1 so a blank submission is a 422 at the boundary, not a burned paid call.
    answer: str = Field(min_length=1, max_length=8000)


class ImportPreviewRequest(BaseModel):
    careers_url: str = Field(min_length=4, max_length=500)


class WaitlistJoin(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    source: Optional[str] = Field(default=None, max_length=50)
    captcha_token: Optional[str] = Field(default=None, max_length=4096)


class DemoSkillMatchRequest(BaseModel):
    """Public, no-account demo input (FACTORY_STANDARD §34). Bounded to cap request size — the
    skills match is KEY-FREE + local, so there is no LLM-spend risk, only body-spam to fence."""

    job_description: str = Field(min_length=1, max_length=25000)
    resume_text: Optional[str] = Field(default=None, max_length=30000)
    captcha_token: Optional[str] = Field(default=None, max_length=4096)


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
    # ``plan_level`` (free | pro | career_plus) is DERIVED from the webhook-verified
    # Subscription.plan (see src/billing.py) — clients use it to gate the Career+ surface, but
    # the server RE-CHECKS it on every Career+ endpoint (never trust the client flag).
    plan_level = billing.current_plan_level(user, user.subscription)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "tier": user.tier.value if isinstance(user.tier, UserTier) else user.tier,
        "plan_level": plan_level,
        "jobs_remaining": limits["jobs_remaining"],
        "prep_packs_remaining": limits["prep_packs_remaining"],
        "ai_coach": user.tier == UserTier.PREMIUM,
        "career_plus": plan_level == "career_plus",
        # Third-party-AI consent (Apple 5.1.2(i)). Clients read ``ai_consent`` to decide
        # whether to PROMPT for consent before an AI action; the server RE-CHECKS it on every
        # AI path (never trusts the client flag). ``ai_consent_at`` is the audit timestamp.
        "ai_consent": user.ai_consent_at is not None,
        "ai_consent_at": user.ai_consent_at.isoformat() if user.ai_consent_at else None,
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
# Bot/abuse protection for public forms (Track F). No-op until the owner connects Turnstile
# (see src/security/captcha.py); once enabled, a request whose captcha token is missing or
# invalid is rejected with a generic 403 (never reveals account existence — enumeration-safe,
# same posture as the auth error responses).
# ---------------------------------------------------------------------------
def _enforce_captcha(token: Optional[str], request: Request) -> None:
    if not verify_captcha(token, get_client_ip(request)):
        raise HTTPException(status_code=403, detail="Captcha verification failed. Please try again.")


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@app.post("/api/auth/register", dependencies=[Depends(rate_limit("auth", 10))])
def register(data: UserCreate, request: Request, db: Session = Depends(get_db)):
    _enforce_captcha(data.captcha_token, request)
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
    # Defense-in-depth (FACTORY_STANDARD §32): the account is already committed above, so NO
    # non-essential side-effect may turn a successful signup into a 500. record_event() is
    # already contractually never-raising, but we also guard the call site so a future
    # regression in it can never hard-block account creation.
    try:
        analytics.record_event(db, "signup")
    except Exception:  # noqa: BLE001 — analytics is non-critical; never surface to signup
        # Mirror the referral block: a failed statement poisons the Postgres transaction, so
        # ROLL BACK before returning — otherwise the very next query (user_public → usage
        # limits, below) would raise on the dirty transaction and 500 the request anyway,
        # re-introducing the exact hard-block this guard exists to prevent. refresh() re-loads
        # the (already-committed) user onto the clean session.
        db.rollback()
        logger.warning("analytics record_event failed during signup; continuing", exc_info=True)
        db.refresh(user)
    return {"success": True, "token": token, "user": user_public(user, db)}


@app.post("/api/auth/login", dependencies=[Depends(rate_limit("auth", 10))])
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    _enforce_captcha(data.captcha_token, request)
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


@app.get("/api/auth/me", dependencies=[Depends(rate_limit_user("user_read", 120))])
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "user": user_public(user, db)}


@app.post("/api/ai-consent", dependencies=[Depends(rate_limit_user("auth", 10))])
def grant_ai_consent(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Record explicit, revocable third-party-AI consent (Apple 5.1.2(i)).

    Idempotent: re-granting refreshes the timestamp. This is the ONLY thing that unlocks the
    generative AI paths (prep packs, salary coaching, AI coach) and the embedding-based
    scorer; the server checks ``ai_consent_at`` on every one of them.
    """
    user.ai_consent_at = datetime.utcnow()
    db.commit()
    return {"success": True, "user": user_public(user, db)}


@app.delete("/api/ai-consent", dependencies=[Depends(rate_limit_user("auth", 10))])
def revoke_ai_consent(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke third-party-AI consent (Apple 5.1.2(i) requires consent be revocable).

    After revoke, generative AI endpoints return 403 ``ai_consent_required`` again and job
    scoring drops back to the local heuristic — no further personal data is sent to Gemini.
    """
    user.ai_consent_at = None
    db.commit()
    return {"success": True, "user": user_public(user, db)}


@app.get("/api/referrals/me", dependencies=[Depends(rate_limit_user("user_read", 120))])
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
def _trusted_public_base() -> Optional[str]:
    """The OWNER-CONFIGURED public origin (``WEB_APP_URL``), or None if unset.

    SECURITY: links embedded in an email sent to a third party must NEVER be derived from the
    request ``Host`` header (attacker-controlled, no TrustedHostMiddleware here) — a spoofed
    Host on ``/api/waitlist/join`` would send a victim a genuine-looking confirmation email
    whose link points at an attacker domain (a phishing primitive). So outbound-email links use
    ONLY this trusted, owner-set origin — never ``request.base_url``."""
    base = os.getenv("WEB_APP_URL")
    return base.rstrip("/") if base else None


def _waitlist_confirm_operational() -> bool:
    """True only when the confirmation email can actually be sent AND its link is safe to build:
    a delivering provider is connected (``email_enabled()``) AND a trusted public origin is
    configured (``WEB_APP_URL``). Both the user-facing copy and the send guard on this, so we
    never promise a confirmation email we won't (safely) send."""
    return email_enabled() and _trusted_public_base() is not None


def _waitlist_response() -> dict:
    """Generic, enumeration-safe success. The message is IDENTICAL for new and existing
    signups (never reveals membership) and only promises a confirmation email when one will
    actually be sent (``_waitlist_confirm_operational()``) — otherwise it would be a
    fake-success claim for an email that never leaves the system (SIDE-EFFECT INTEGRITY)."""
    if _waitlist_confirm_operational():
        return {"success": True, "message": "You're on the list — check your email to confirm your spot."}
    return {"success": True, "message": "You're on the list — we'll be in touch."}


def _send_waitlist_confirm(email: str) -> None:
    """Best-effort double-opt-in email. NEVER raises — the captured row is the real
    side-effect, and email must not be able to break signup (mirrors analytics.record_event).
    The link is built from the TRUSTED owner-configured origin only (never the request Host —
    see ``_trusted_public_base``); when no provider/origin is configured nothing is delivered,
    the visitor is NOT dead-ended, and the response makes no false 'check your email' claim."""
    try:
        base = _trusted_public_base()
        if base is None or not email_enabled():
            # No trusted public origin and/or no delivering provider: do not build a
            # Host-derived link or fake a send. The row is already captured.
            return
        token = make_confirm_token(email)
        url = f"{base}/api/waitlist/confirm?email={quote(email)}&token={token}"
        send_email(EmailMessage(
            to=email,
            subject="Confirm your Career Operator waitlist spot",
            text_body=(
                "Thanks for joining the Career Operator waitlist.\n\n"
                f"Confirm your spot: {url}\n\n"
                "If you didn't request this, you can ignore this email."
            ),
            html_body=(
                "<p>Thanks for joining the <strong>Career Operator</strong> waitlist.</p>"
                f'<p><a href="{url}">Confirm your spot</a></p>'
                "<p>If you didn't request this, you can ignore this email.</p>"
            ),
        ))
    except Exception:  # pragma: no cover - defensive: email is never allowed to break signup
        logger.warning("waitlist confirm email dispatch failed", exc_info=True)


@app.post("/api/waitlist/join", dependencies=[Depends(rate_limit("waitlist", 5, 3600))])
def join_waitlist(data: WaitlistJoin, request: Request, db: Session = Depends(get_db)):
    """Capture a pre-launch waitlist signup + send a double-opt-in confirmation (Track H / F4.1).

    The DB row IS the primary, always-present side-effect (makes visitor->signup measurable);
    it is stored regardless of email deliverability. A confirmation email is then dispatched
    best-effort via the email abstraction: when a real provider is connected the recipient can
    click the HMAC-signed link to set ``confirmed_at`` (double-opt-in); with the default
    dry-run backend nothing is delivered, the visitor is NOT dead-ended, and the response makes
    no false claim (DECISION COROLLARY — we never gate signup on an email that didn't send).
    """
    _enforce_captcha(data.captcha_token, request)
    email = (data.email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    if db.query(Waitlist).filter(Waitlist.email == email).first():
        # Already on the list — indistinguishable from a fresh signup; no resend (avoids an
        # enumeration timing signal + a repeat-submit email-spam vector). The first email's
        # confirm link still works.
        return _waitlist_response()
    source = ((data.source or "").strip() or "organic")[:50]
    full_name = ((data.full_name or "").strip() or None)
    db.add(Waitlist(email=email, full_name=full_name, source=source))
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request won the unique-email slot between the check and the insert.
        # Still a success for the user, still no enumeration signal, and the winning request
        # already dispatched the confirm email.
        db.rollback()
        return _waitlist_response()
    _send_waitlist_confirm(email)
    return _waitlist_response()


@app.get("/api/waitlist/confirm", dependencies=[Depends(rate_limit("waitlist_confirm", 30, 3600))])
def confirm_waitlist(
    email: str = Query(..., max_length=255),
    token: str = Query(..., max_length=128),
    db: Session = Depends(get_db),
):
    """Complete waitlist double-opt-in from the emailed link, then redirect to a thank-you page.

    Verifies the stateless HMAC token (bound to the email — a tampered address invalidates it),
    then idempotently stamps ``confirmed_at``. A malformed email or invalid/forged token
    redirects with ``status=invalid`` and grants nothing; an otherwise-valid token redirects
    with ``status=ok`` (no membership enumeration beyond the identical redirect — a valid token
    for a non-existent row is a harmless no-op, and forging one needs the server secret)."""
    # Redirect target uses the TRUSTED owner-configured origin, or a HOST-RELATIVE path when
    # unset — NEVER request.base_url (the attacker-controlled Host, no TrustedHostMiddleware
    # here). A relative Location is same-origin by construction, so a spoofed Host can't turn
    # this branded "confirm" endpoint into an open redirect (CWE-601) to attacker infra.
    dest = (_trusted_public_base() or "") + "/waitlist/confirmed"
    e = (email or "").strip().lower()
    if not _EMAIL_RE.match(e) or not verify_confirm_token(e, token):
        return RedirectResponse(dest + "?status=invalid", status_code=303)
    row = db.query(Waitlist).filter(Waitlist.email == e).first()
    if row is not None and row.confirmed_at is None:
        row.confirmed_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(dest + "?status=ok", status_code=303)


# ---------------------------------------------------------------------------
# Public, no-account DEMO of the core "aha" (FACTORY_STANDARD §34 / ROADMAP §34).
# Lets a visitor try the real fit read before signing up: paste a job description
# (+ optionally a résumé) and see, instantly, which of the role's skills their résumé
# already shows and which it is missing — the SAME key-free signal the logged-in
# skill-gap heatmap uses. Deliberately the LOCAL half of the fit read (no embeddings /
# no Gemini): it needs NO owner secret (works the moment the app deploys — a DECISION
# COROLLARY call so the demo can never 503 on a missing key), sends NO data to a third
# party, and is deterministic + O(text) so it cannot be turned into an LLM-spend or
# compute amplifier. HARDENED like a live public surface (Track H / §12): bounded input
# (the Pydantic model), a burst + a daily IP rate limit, and the captcha seam (a no-op
# until the owner connects Turnstile, then fail-closed). No auth, no DB write, no PII.
# ---------------------------------------------------------------------------
@app.post(
    "/api/demo/skill-match",
    dependencies=[
        Depends(rate_limit("demo", 20, 60)),
        Depends(rate_limit("demo_daily", 200, 86400)),
    ],
)
def demo_skill_match(data: DemoSkillMatchRequest, request: Request):
    """Return a KEY-FREE skills match for one job description vs an optional résumé.

    No account, no DB, no third-party AI. The captcha seam runs first (enumeration-safe 403
    when the owner has connected Turnstile; a pure no-op otherwise), then the match is computed
    from the shared heuristic vocabulary. The response makes no false claim: when no résumé is
    supplied, ``has_resume`` is False and every detected role skill is reported as missing so the
    UI can honestly invite the visitor to paste a résumé rather than imply a real 0% verdict.
    """
    _enforce_captcha(data.captcha_token, request)
    result = analyze_demo_match(
        data.job_description,
        data.resume_text or "",
        JobScorer.extract_skills,
    )
    return result.to_dict()


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
@app.post("/api/jobs", dependencies=[Depends(rate_limit_user("write", 30))])
def create_job(
    data: JobCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth = AuthService(db)

    # Idempotency guard: a re-submit of an IDENTICAL posting (same user + title + company + url)
    # returns the EXISTING job instead of inserting a duplicate row. Without this, a double-click
    # / network retry / offline replay creates duplicate JobPostings AND double-fires every
    # side-effect — a wasted paid re-score against the daily ceiling, a double usage-count against
    # the free-tier cap, and a corrupted analytics funnel (job_added counted twice). Placed BEFORE
    # the usage-limit check so re-submitting a job you already track never trips the cap (you are
    # not adding a NEW job). ``url`` may be NULL — SQLAlchemy renders ``== None`` as ``IS NULL``.
    # job_public() reads application + score + company. This is a SINGLE-row lookup (``.first()``),
    # so joinedload pulls all three in ONE LEFT JOIN instead of the object plus three extra
    # per-relationship queries — 4 queries → 1 on the job-add hot path — exactly as ``get_job``
    # does for the same single-row/job_public() pattern (selectinload only wins for many rows).
    existing = (
        db.query(JobPosting)
        .options(
            joinedload(JobPosting.application),
            joinedload(JobPosting.score),
            joinedload(JobPosting.company),
        )
        .filter(
            JobPosting.user_id == user.id,
            JobPosting.title == data.title,
            JobPosting.company_name == data.company_name,
            JobPosting.url == data.url,
        )
        .first()
    )
    if existing is not None:
        return {"success": True, "job": job_public(existing), "duplicate": True}

    limits = auth.check_usage_limits(user)
    if not limits["can_add_job"]:
        raise HTTPException(
            status_code=403,
            detail="Free tier is limited to 5 tracked jobs. Upgrade to Pro for unlimited.",
        )

    # Decide scoring eligibility BEFORE any DB writes. The embedding-based scorer makes a PAID
    # Gemini call per job, so meter it under a per-user/day ceiling — unlimited job-adds must
    # not drive unbounded embedding spend (wallet-drain defense). ``_consume_counter`` commits
    # immediately (its cross-instance contract requires "check before real work"), so it MUST
    # run BEFORE the job/Application writes below: otherwise its commit would split job
    # creation into two transactions, and a failure in between (e.g. a slow Gemini call killed
    # by the serverless budget) could orphan a JobPosting with no Application/usage row.
    #
    # We use the Gemini embeddings ONLY when a key is present AND the user has granted
    # third-party-AI consent (Apple 5.1.2(i)) — otherwise scoring stays fully LOCAL (the
    # skills-match heuristic), sending nothing to Gemini. The per-day ceiling slot is consumed
    # ONLY when a real paid embedding call will actually fire; the local heuristic is free and
    # always allowed, so the core loop still produces a real fit score before consent. (Note:
    # the very first embedding-scored job makes 2 calls — resume + JD — but consumes 1 slot;
    # harmless, the resume embedding is cached thereafter.)
    use_embeddings = llm_available() and ai_consent_ok(user)
    if use_embeddings:
        may_score = _consume_counter(
            db, user.id, "score_daily", SCORE_DAILY_CEILING, 86400
        )
    else:
        may_score = True

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

    # Score (heuristic fallback when no Gemini key — never crashes). Over the ceiling the job
    # is still created, just UNSCORED (the same graceful outcome as a scoring error) — never a
    # blocked add. A False ``may_score`` here always means "key present but over the ceiling".
    scored = False
    if may_score:
        try:
            JobScorer(db).score_job(job, user, use_embeddings=use_embeddings)
            scored = True
        except Exception:
            logger.exception("Scoring failed for job %s; continuing unscored", job.id)
    else:
        logger.warning(
            "Per-day scoring ceiling reached for user %s; job %s created unscored",
            user.id,
            job.id,
        )

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


@app.get("/api/jobs", dependencies=[Depends(rate_limit_user("user_read", 120))])
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


@app.get("/api/jobs/{job_id}", dependencies=[Depends(rate_limit_user("user_read", 120))])
def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # job_public() reads application + score + company. For a SINGLE row, joinedload pulls all
    # three in ONE query (a LEFT JOIN) instead of the object plus three lazy-load round-trips —
    # 4 queries → 1 on the most-hit authed endpoint. (selectinload wouldn't help here: it issues
    # a separate query per relationship regardless of row count, so for one row it's still 3+1.)
    job = (
        db.query(JobPosting)
        .options(
            joinedload(JobPosting.application),
            joinedload(JobPosting.score),
            joinedload(JobPosting.company),
        )
        .filter(JobPosting.id == job_id, JobPosting.user_id == user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "job": job_public(job)}


@app.get(
    "/api/jobs/{job_id}/readiness",
    dependencies=[Depends(rate_limit_user("user_read", 120))],
)
def job_interview_readiness(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Interview-readiness read + next-best-action for one tracked job — FREE, fully local.

    Computes a readiness score (0–100) and the SINGLE next best action from the user's REAL
    signals for this job: résumé-vs-JD skill coverage, answered + scored mock-interview
    questions, and completed prep artifacts. No LLM, no third-party call, no consent needed —
    the read is free and works with no ``GEMINI_API_KEY``. It climbs only on real practice
    (never a vanity number). Scoped to the caller server-side (tenant isolation — never trust
    the client); 404 when the job isn't theirs. ``prep_artifacts`` + ``mock_interviews`` are
    eager-loaded so the whole read is a bounded, N+1-free set of queries.
    """
    job = (
        db.query(JobPosting)
        .options(
            selectinload(JobPosting.prep_artifacts),
            selectinload(JobPosting.mock_interviews),
        )
        .filter(JobPosting.id == job_id, JobPosting.user_id == user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    jd_text = f"{job.description or ''} {job.requirements or ''}"
    artifact_types = [a.artifact_type for a in job.prep_artifacts]
    sessions = [
        {"questions": mi.questions or [], "answers": mi.answers or []}
        for mi in job.mock_interviews
    ]
    report = compute_readiness(
        jd_text=jd_text,
        resume_text=user.resume_text or "",
        artifact_types=artifact_types,
        sessions=sessions,
        extract=JobScorer(db).extract_skills,
    )
    return {"success": True, "readiness": report.to_dict()}


VALID_STATUSES = {s.value for s in ApplicationStatus}


@app.patch("/api/jobs/{job_id}", dependencies=[Depends(rate_limit_user("write", 60))])
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


# Honest response when the safety moderator withholds a user-facing generation. A moderated
# decline is NOT the artifact the user requested, so the LLMWorkflows endpoints surface it as a
# 422 (no artifact persisted, no usage charged, no success claimed) rather than dressing the
# decline text up as the deliverable — see ModeratedContentError (§6, no fake success).
_MODERATED_DECLINE_DETAIL = (
    "The generated content was withheld by a safety filter and could not be returned. "
    "Please try again or revise the job details."
)


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

    # Apple 5.1.2(i): explicit consent BEFORE sending the resume/job text to Gemini.
    require_ai_consent(user)
    check_llm_ceiling(user, db)
    try:
        artifact: PrepArtifact = LLMWorkflows(db).generate_prep_pack(job, user)
    except ModeratedContentError:
        # A rare safety-filter decline is NOT a generated pack: do not persist it, do not
        # charge the monthly usage below, do not claim success (§6, no fake success). The
        # raise happens before any artifact is added and before increment_prep_usage.
        logger.info("Prep pack withheld by content moderation")
        raise HTTPException(status_code=422, detail=_MODERATED_DECLINE_DETAIL)
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
# Salary negotiation coaching (Career+ EXCLUSIVE; LLM — degrades gracefully)
# ---------------------------------------------------------------------------
@app.post("/api/prep/salary-negotiation", dependencies=[Depends(rate_limit("llm", 10))])
def generate_salary_negotiation_guide(
    data: SalaryNegotiationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate salary-negotiation scripts for a tracked job — a Career+ EXCLUSIVE feature.

    Career+ is a REAL, verified entitlement, not a client flag: the gate reads
    ``current_plan_level`` (derived from the signature-verified-webhook-written
    ``Subscription.plan``). This feature is ADDITIVE — it had no endpoint before, so gating it
    to Career+ takes nothing away from Pro/Premium users (no dark pattern). Honest degradation:
    no LLM key -> 503, never a fake or blank script (SIDE-EFFECT INTEGRITY §6). The gate is
    checked BEFORE any LLM work so a non-Career+ user always gets a clean 403, never a 503.
    """
    if billing.current_plan_level(user, user.subscription) != "career_plus":
        raise HTTPException(
            status_code=403,
            detail="Salary negotiation coaching is a Career+ feature. Upgrade to Career+ to unlock it.",
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
            detail="AI salary-negotiation coaching requires the server's GEMINI_API_KEY to be configured.",
        )

    # Apple 5.1.2(i): explicit consent BEFORE sending the resume/job text to Gemini.
    require_ai_consent(user)
    check_llm_ceiling(user, db)
    try:
        artifact: PrepArtifact = LLMWorkflows(db).generate_salary_negotiation(
            job, data.target_salary
        )
    except ModeratedContentError:
        # A moderated decline is not a generated script — return honestly, don't persist it
        # or claim success (§6, no fake success).
        logger.info("Salary negotiation guide withheld by content moderation")
        raise HTTPException(status_code=422, detail=_MODERATED_DECLINE_DETAIL)
    except Exception:
        logger.exception("Salary negotiation generation failed")
        raise HTTPException(status_code=502, detail="AI provider error generating negotiation guide")

    db.commit()
    analytics.record_event(db, "salary_negotiation_generated")  # aggregate metric (best-effort, no PII)
    return {
        "success": True,
        "artifact": {
            "id": artifact.id,
            "title": artifact.title,
            "content": artifact.content,
        },
    }


# ---------------------------------------------------------------------------
# Cover letter generation (Pro+; LLM — degrades gracefully)
# ---------------------------------------------------------------------------
@app.post("/api/prep/cover-letter", dependencies=[Depends(rate_limit("llm", 10))])
def generate_cover_letter_endpoint(
    data: CoverLetterRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a tailored cover letter for a tracked job — a Pro+ feature.

    This is ADDITIVE: the generator (``LLMWorkflows.generate_cover_letter``) existed but had no
    endpoint, so exposing it at Pro takes nothing from any existing user (no dark pattern). The
    gate is ``user.tier != PREMIUM`` (Pro AND Career+ are both PREMIUM), checked BEFORE any LLM
    work so a free user always gets a clean 403, never a 503. Honest degradation: no LLM key ->
    503, never a fake/blank letter (SIDE-EFFECT INTEGRITY §6). Consent (Apple 5.1.2(i)) + the
    per-user/day LLM ceiling are enforced before the resume/JD is sent to Gemini.
    """
    if user.tier != UserTier.PREMIUM:
        raise HTTPException(
            status_code=403,
            detail="Cover letters are a Pro feature. Upgrade to Pro or Career+ to unlock them.",
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
            detail="AI cover-letter generation requires the server's GEMINI_API_KEY to be configured.",
        )

    require_ai_consent(user)
    check_llm_ceiling(user, db)
    try:
        artifact: PrepArtifact = LLMWorkflows(db).generate_cover_letter(job, user)
    except ModeratedContentError:
        # A moderated decline is not a generated letter — return honestly, don't persist it
        # or claim success (§6, no fake success).
        logger.info("Cover letter withheld by content moderation")
        raise HTTPException(status_code=422, detail=_MODERATED_DECLINE_DETAIL)
    except Exception:
        logger.exception("Cover letter generation failed")
        raise HTTPException(status_code=502, detail="AI provider error generating cover letter")

    db.commit()
    analytics.record_event(db, "cover_letter_generated")  # aggregate metric (best-effort, no PII)
    return {
        "success": True,
        "artifact": {
            "id": artifact.id,
            "title": artifact.title,
            "content": artifact.content,
        },
    }


# ---------------------------------------------------------------------------
# Study plan generation (Pro+; LLM — degrades gracefully)
# ---------------------------------------------------------------------------
@app.post("/api/prep/study-plan", dependencies=[Depends(rate_limit("llm", 10))])
def generate_study_plan_endpoint(
    data: StudyPlanRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a day-by-day interview study plan for a tracked job — a Pro+ feature.

    Distinct from the prep pack's fixed 48-hour section: ``days`` (1–30) lets a candidate with a
    week or more before the interview get a paced plan the cram sheet can't give. Same Pro+ gate,
    consent, ceiling, and honest-degradation contract as the cover-letter endpoint above.
    """
    if user.tier != UserTier.PREMIUM:
        raise HTTPException(
            status_code=403,
            detail="Study plans are a Pro feature. Upgrade to Pro or Career+ to unlock them.",
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
            detail="AI study-plan generation requires the server's GEMINI_API_KEY to be configured.",
        )

    require_ai_consent(user)
    check_llm_ceiling(user, db)
    try:
        artifact: PrepArtifact = LLMWorkflows(db).generate_study_plan(job, data.days)
    except ModeratedContentError:
        # A moderated decline is not a generated plan — return honestly, don't persist it
        # or claim success (§6, no fake success).
        logger.info("Study plan withheld by content moderation")
        raise HTTPException(status_code=422, detail=_MODERATED_DECLINE_DETAIL)
    except Exception:
        logger.exception("Study plan generation failed")
        raise HTTPException(status_code=502, detail="AI provider error generating study plan")

    db.commit()
    analytics.record_event(db, "study_plan_generated")  # aggregate metric (best-effort, no PII)
    return {
        "success": True,
        "artifact": {
            "id": artifact.id,
            "title": artifact.title,
            "content": artifact.content,
        },
    }


# ---------------------------------------------------------------------------
# Tailored résumé generation (Pro+; LLM — degrades gracefully)
# ---------------------------------------------------------------------------
@app.post("/api/prep/tailored-resume", dependencies=[Depends(rate_limit("llm", 10))])
def generate_tailored_resume_endpoint(
    data: TailoredResumeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rewrite the user's résumé tailored to a tracked job — a Pro+ feature.

    Same Pro+ gate / consent / ceiling / honest-degradation contract as the cover-letter and
    study-plan endpoints. One EXTRA guard unique to this feature: it requires a saved résumé.
    Unlike a cover letter (which can be written from a name), a "tailored résumé" with no source
    résumé would force the model to FABRICATE an entire work history — the exact dishonesty this
    feature must never produce (VISION "honest > flashy"). So a paid user with an empty
    ``resume_text`` gets an honest 400 telling them to add their résumé first, never an invented
    one. The generator's prompt then treats the saved résumé as the sole source of truth.
    """
    if user.tier != UserTier.PREMIUM:
        raise HTTPException(
            status_code=403,
            detail="Tailored résumés are a Pro feature. Upgrade to Pro or Career+ to unlock them.",
        )

    job = (
        db.query(JobPosting)
        .filter(JobPosting.id == data.job_id, JobPosting.user_id == user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not (user.resume_text or "").strip():
        # Cannot tailor a résumé that doesn't exist — refuse honestly rather than fabricate one.
        raise HTTPException(
            status_code=400,
            detail="Add your résumé in Settings before generating a tailored résumé.",
        )

    if not llm_available():
        # Truthful graceful degradation — not a crash, not a fake result.
        raise HTTPException(
            status_code=503,
            detail="AI résumé tailoring requires the server's GEMINI_API_KEY to be configured.",
        )

    require_ai_consent(user)
    check_llm_ceiling(user, db)
    try:
        artifact: PrepArtifact = LLMWorkflows(db).generate_tailored_resume(job, user)
    except ModeratedContentError:
        # A moderated decline is not a generated résumé — return honestly, don't persist it
        # or claim success (§6, no fake success).
        logger.info("Tailored résumé withheld by content moderation")
        raise HTTPException(status_code=422, detail=_MODERATED_DECLINE_DETAIL)
    except Exception:
        logger.exception("Tailored résumé generation failed")
        raise HTTPException(status_code=502, detail="AI provider error generating tailored résumé")

    db.commit()
    analytics.record_event(db, "tailored_resume_generated")  # aggregate metric (best-effort, no PII)
    return {
        "success": True,
        "artifact": {
            "id": artifact.id,
            "title": artifact.title,
            "content": artifact.content,
        },
    }


# ---------------------------------------------------------------------------
# Mock interview engine (Pro+; LLM — the interview-coaching pillar, ROADMAP Track A surface 3)
#
# A realistic, role-specific text mock interview: the coach asks JD-derived questions, the user
# answers one at a time, and each answer is SCORED (relevance / specificity / STAR) with concrete
# feedback + a model answer. Multi-turn state lives on ONE ``MockInterview`` row. Every endpoint
# scopes the session to ``user.id`` server-side (tenant isolation — never trust the client).
# ---------------------------------------------------------------------------
def _mock_interview_public(interview: MockInterview) -> dict:
    """Serialize a session for the client: questions + any scored answers + status."""
    questions = interview.questions or []
    answers = interview.answers or []
    return {
        "id": interview.id,
        "job_id": interview.job_id,
        "status": interview.status,
        "questions": questions,
        "answers": answers,
        "answered_count": len(answers),
        "total": len(questions),
        "created_at": interview.created_at.isoformat() if interview.created_at else None,
    }


@app.post("/api/prep/mock-interview", dependencies=[Depends(rate_limit("llm", 10))])
def start_mock_interview(
    data: MockInterviewStartRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a mock interview for a tracked job — a Pro+ feature.

    Same Pro+ gate / consent / ceiling / honest-degradation contract as the other AI generators.
    Generates the JD-derived question set up front and persists an ``in_progress`` session; the
    user then answers each question via the ``/answer`` endpoint. A keyless server refuses
    honestly (503, no fake session); a moderated generation returns 422 and persists nothing (§6).
    """
    if user.tier != UserTier.PREMIUM:
        raise HTTPException(
            status_code=403,
            detail="Mock interviews are a Pro feature. Upgrade to Pro or Career+ to unlock them.",
        )

    job = (
        db.query(JobPosting)
        .filter(JobPosting.id == data.job_id, JobPosting.user_id == user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not llm_available():
        raise HTTPException(
            status_code=503,
            detail="Mock interviews require the server's GEMINI_API_KEY to be configured.",
        )

    require_ai_consent(user)
    check_llm_ceiling(user, db)
    try:
        questions = LLMWorkflows(db).generate_mock_interview_questions(job, data.num_questions)
    except ModeratedContentError:
        logger.info("Mock-interview questions withheld by content moderation")
        raise HTTPException(status_code=422, detail=_MODERATED_DECLINE_DETAIL)
    except Exception:
        logger.exception("Mock-interview question generation failed")
        raise HTTPException(status_code=502, detail="AI provider error starting the mock interview")

    interview = MockInterview(
        user_id=user.id,
        job_id=job.id,
        questions=questions,
        answers=[],
        status="in_progress",
        model_used=LLMWorkflows.MODEL,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    analytics.record_event(db, "mock_interview_started")  # aggregate metric (best-effort, no PII)
    return {"success": True, "interview": _mock_interview_public(interview)}


@app.post(
    "/api/prep/mock-interview/{interview_id}/answer",
    dependencies=[Depends(rate_limit("llm", 20))],
)
def answer_mock_interview(
    interview_id: str,
    data: MockInterviewAnswerRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit an answer to one question and get it scored — a Pro+ feature.

    Scores the answer (relevance / specificity / STAR) with concrete feedback + a model answer,
    then persists the result on the session (keyed by ``question_index``; re-answering a question
    OVERWRITES its prior score — the readiness-loop "redo the weak answer" path). When every
    question has been answered the session flips to ``completed``. Honest scoring only: a weak
    answer scores low. A moderated result returns 422 and persists nothing (§6).
    """
    if user.tier != UserTier.PREMIUM:
        raise HTTPException(
            status_code=403,
            detail="Mock interviews are a Pro feature. Upgrade to Pro or Career+ to unlock them.",
        )

    interview = (
        db.query(MockInterview)
        .filter(MockInterview.id == interview_id, MockInterview.user_id == user.id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Mock interview not found")

    questions = interview.questions or []
    if data.question_index >= len(questions):
        raise HTTPException(status_code=422, detail="Question index out of range for this interview.")

    job = (
        db.query(JobPosting)
        .filter(JobPosting.id == interview.job_id, JobPosting.user_id == user.id)
        .first()
    )
    if not job:
        # The owning job was deleted (which would cascade-delete the interview) — defensive.
        raise HTTPException(status_code=404, detail="Job not found")

    if not llm_available():
        raise HTTPException(
            status_code=503,
            detail="Mock interviews require the server's GEMINI_API_KEY to be configured.",
        )

    require_ai_consent(user)
    check_llm_ceiling(user, db)
    question_text = questions[data.question_index].get("question", "")
    try:
        result = LLMWorkflows(db).score_mock_interview_answer(job, question_text, data.answer)
    except ModeratedContentError:
        logger.info("Mock-interview answer feedback withheld by content moderation")
        raise HTTPException(status_code=422, detail=_MODERATED_DECLINE_DETAIL)
    except Exception:
        logger.exception("Mock-interview answer scoring failed")
        raise HTTPException(status_code=502, detail="AI provider error scoring your answer")

    entry = {"question_index": data.question_index, "answer": data.answer, **result}
    # Reassign a NEW list so SQLAlchemy marks the JSON column dirty (in-place mutation isn't
    # tracked). Overwrite any prior answer at this index (re-answer / redo the weak one).
    existing = [a for a in (interview.answers or []) if a.get("question_index") != data.question_index]
    existing.append(entry)
    existing.sort(key=lambda a: a.get("question_index", 0))
    interview.answers = existing
    answered_indexes = {a.get("question_index") for a in existing}
    if len(answered_indexes) >= len(questions):
        interview.status = "completed"
    db.commit()
    db.refresh(interview)
    analytics.record_event(db, "mock_interview_answered")  # aggregate metric (best-effort, no PII)
    return {
        "success": True,
        "result": {"question_index": data.question_index, **result},
        "status": interview.status,
        "answered_count": len(answered_indexes),
        "total": len(questions),
    }


@app.get(
    "/api/prep/mock-interview/{interview_id}",
    dependencies=[Depends(rate_limit_user("user_read", 120))],
)
def get_mock_interview(
    interview_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch a full mock-interview session (questions + scored answers) — the caller's own only."""
    interview = (
        db.query(MockInterview)
        .filter(MockInterview.id == interview_id, MockInterview.user_id == user.id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Mock interview not found")
    return {"success": True, "interview": _mock_interview_public(interview)}


@app.get(
    "/api/prep/mock-interviews",
    dependencies=[Depends(rate_limit_user("user_read", 120))],
)
def list_mock_interviews(
    job_id: str = Query(..., min_length=1, max_length=64),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the caller's mock-interview sessions for one tracked job (most recent first)."""
    interviews = (
        db.query(MockInterview)
        .filter(MockInterview.user_id == user.id, MockInterview.job_id == job_id)
        .order_by(MockInterview.created_at.desc())
        .all()
    )
    return {
        "success": True,
        "interviews": [
            {
                "id": i.id,
                "status": i.status,
                "total": len(i.questions or []),
                "answered_count": len(i.answers or []),
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in interviews
        ],
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
            detail="The AI Career Coach is a Pro feature. Upgrade to unlock it.",
        )
    if not CareerCoach.available():
        raise HTTPException(
            status_code=503,
            detail="The AI Coach requires the server's GEMINI_API_KEY to be configured.",
        )

    # Apple 5.1.2(i): explicit consent BEFORE sending resume/coach text to Gemini.
    require_ai_consent(user)
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


@app.get("/api/coach/suggestions", dependencies=[Depends(rate_limit_user("suggest", 30))])
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
@app.post("/api/report", dependencies=[Depends(rate_limit_user("report", 20))])
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
# Cross-pipeline insights: skill-gap heatmap (free) + AI learning plan (Pro)
# ---------------------------------------------------------------------------
# How many of the user's jobs the analysis considers. The heatmap is fully local (no LLM), so
# this is a CPU/allocation guard against a pathological account with thousands of jobs, not a
# wallet-drain guard — the LLM learning plan only ever receives the top ~10 skill NAMES + ≤8 job
# titles (never JD/résumé text), so its third-party payload is bounded regardless of this cap.
_SKILL_GAP_JOB_CAP = 500


@app.get("/api/insights/skill-gaps", dependencies=[Depends(rate_limit_user("suggest", 30))])
def skill_gap_heatmap(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cross-pipeline skill-gap heatmap — FREE, fully local (no LLM, no data leaves the server).

    Reuses the scorer's heuristic skill extractor on BOTH the résumé and every tracked JD, so the
    two sides share one vocabulary. Honest empty states: "no jobs yet" / "no résumé yet" are
    surfaced in the payload (``total_jobs`` / ``has_resume``), never errored — this is the free
    retention hook, and the (Pro, LLM) learning plan is a separate call.
    """
    jobs = (
        db.query(JobPosting)
        .filter(JobPosting.user_id == user.id)
        .order_by(JobPosting.created_at.desc())
        .limit(_SKILL_GAP_JOB_CAP)
        .all()
    )
    analysis = analyze_skill_gaps(jobs, user.resume_text or "", JobScorer(db).extract_skills)
    return {"success": True, "analysis": analysis.to_dict()}


@app.post("/api/insights/learning-plan", dependencies=[Depends(rate_limit("llm", 10))])
def generate_learning_plan_endpoint(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate an AI learning plan for the user's TOP cross-pipeline skill gaps — a Pro+ feature.

    Same Pro+ gate / consent / ceiling / honest-degradation contract as the other AI generators.
    The gaps are recomputed SERVER-SIDE from the user's own jobs (never trusted from the client),
    and only the top-10 gap skill names + job titles reach the model. NOT persisted: the plan is
    cross-pipeline (not job-scoped) and cheaply regenerable, so it is returned for copy/download.
    Guard order puts the actionable 400s (no jobs / no résumé / no gaps — states the user can fix)
    BEFORE the 503 key check and BEFORE consuming a daily LLM slot.
    """
    if user.tier != UserTier.PREMIUM:
        raise HTTPException(
            status_code=403,
            detail="AI learning plans are a Pro feature. Upgrade to Pro or Career+ to unlock them.",
        )

    jobs = (
        db.query(JobPosting)
        .filter(JobPosting.user_id == user.id)
        .order_by(JobPosting.created_at.desc())
        .limit(_SKILL_GAP_JOB_CAP)
        .all()
    )
    if not jobs:
        raise HTTPException(
            status_code=400,
            detail="Track some jobs first — your learning plan is built from the skills your saved jobs demand.",
        )
    if not (user.resume_text or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Add your résumé in Settings first — the plan compares your skills against your tracked jobs.",
        )

    analysis = analyze_skill_gaps(jobs, user.resume_text or "", JobScorer(db).extract_skills)
    top_gaps = [g.skill for g in analysis.gaps[:10]]
    if not top_gaps:
        raise HTTPException(
            status_code=400,
            detail="No skill gaps found — your résumé already covers the skills your tracked jobs demand.",
        )

    if not llm_available():
        raise HTTPException(
            status_code=503,
            detail="AI learning plans require the server's GEMINI_API_KEY to be configured.",
        )

    require_ai_consent(user)
    check_llm_ceiling(user, db)
    job_titles = [j.title for j in jobs if j.title]
    try:
        content = LLMWorkflows(db).generate_learning_plan(top_gaps, job_titles, user)
    except ModeratedContentError:
        # A moderated decline is not a learning plan — return honestly, persist nothing (§6).
        logger.info("Learning plan withheld by content moderation")
        raise HTTPException(status_code=422, detail=_MODERATED_DECLINE_DETAIL)
    except Exception:
        logger.exception("Learning plan generation failed")
        raise HTTPException(status_code=502, detail="AI provider error generating learning plan")

    analytics.record_event(db, "learning_plan_generated")  # aggregate metric (best-effort, no PII)
    return {
        "success": True,
        "artifact": {
            "title": "Your cross-pipeline learning plan",
            "content": content,
            "skills": top_gaps,
        },
    }


# ---------------------------------------------------------------------------
# Profile enrichment (Track A — the market's /expand)
# ---------------------------------------------------------------------------
class GithubEnrichRequest(BaseModel):
    # A GitHub username or github.com profile URL. Bounded (we only ever extract a validated
    # username from it and hit the FIXED host api.github.com — no arbitrary-URL fetch).
    github: str = Field(min_length=1, max_length=200)


def _enrichment_payload(db: Session, user: User) -> list:
    rows = (
        db.query(EnrichedCompetency)
        .filter(EnrichedCompetency.user_id == user.id)
        .order_by(EnrichedCompetency.skill)
        .all()
    )
    return [
        {"skill": r.skill, "source_type": r.source_type, "evidence": r.evidence}
        for r in rows
    ]


@app.get("/api/profile/resume", dependencies=[Depends(rate_limit_user("read", 60))])
def get_resume(user: User = Depends(get_current_user)):
    """Return the signed-in user's saved résumé text (their OWN data) so Settings can show + edit it.

    Empty string (never null) when none is saved, so the client renders an editable field either
    way. The résumé is core input for fit scoring, the tailored-résumé generator, cover letters,
    and the skill-gap heatmap — several of those explicitly tell the user to "add your résumé in
    Settings," so a read+write path here is what makes that instruction reachable.
    """
    return {"success": True, "resume_text": user.resume_text or ""}


@app.patch("/api/profile/resume", dependencies=[Depends(rate_limit_user("write", 20))])
def update_resume(
    data: ResumeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save (or clear) the user's résumé text — the update path that was missing after signup.

    Bounded server-side (50k chars, see ResumeUpdate). A blank/whitespace-only body CLEARS the
    résumé (stored as NULL) so a user can remove it; anything else is stored trimmed. Returns
    ``has_resume`` so the client can reflect the real saved state without a second round-trip.
    """
    text = (data.resume_text or "").strip()
    user.resume_text = text or None
    db.commit()
    return {"success": True, "has_resume": bool(text)}


@app.post("/api/profile/enrich/github", dependencies=[Depends(rate_limit_user("write", 20))])
def enrich_profile_github(
    data: GithubEnrichRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Import competencies from the user's public GitHub profile — a Pro+ feature (/expand).

    Honest, structured enrichment: we validate the username and call the PUBLIC GitHub REST API
    (fixed host api.github.com — no arbitrary-URL fetch, no SSRF, nothing scraped or invented).
    The repos' own language + topics become source-tagged competencies that feed fit-scoring +
    cover-letter generation. A re-import REPLACES the prior GitHub set (reflects current repos).
    No consent gate / LLM ceiling: no third-party AI is called and the user's own data is not
    sent anywhere — we only read their OWN public GitHub. Degrades honestly: an unknown user /
    private-only account / API error returns 200 with found=0 and an honest message, never a lie.
    """
    if user.tier != UserTier.PREMIUM:
        raise HTTPException(
            status_code=403,
            detail="Profile enrichment is a Pro feature. Upgrade to Pro or Career+ to unlock it.",
        )
    username = parse_github_username(data.github)
    if not username:
        raise HTTPException(
            status_code=400,
            detail="Enter a valid GitHub username or profile URL (e.g. github.com/yourname).",
        )
    discovered = discover_github_competencies(username)
    source_url = f"https://github.com/{username}"
    added = replace_github_competencies(db, user, source_url, discovered)
    db.commit()
    if added:
        analytics.record_event(db, "profile_enriched")  # aggregate metric (best-effort, no PII)
    return {
        "success": True,
        "found": added,
        "username": username,
        "competencies": _enrichment_payload(db, user),
        "message": (
            f"Imported {added} skill{'' if added == 1 else 's'} from github.com/{username}."
            if added
            else f"No public repositories with detectable skills found for github.com/{username}."
        ),
    }


@app.get("/api/profile/enrichment", dependencies=[Depends(rate_limit_user("user_read", 120))])
def get_profile_enrichment(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """The user's current link-discovered competencies (free; read your own data)."""
    return {"success": True, "competencies": _enrichment_payload(db, user)}


@app.delete("/api/profile/enrichment", dependencies=[Depends(rate_limit_user("write", 20))])
def clear_profile_enrichment(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Remove ALL of the user's imported competencies (data control — real cascade-free delete)."""
    deleted = (
        db.query(EnrichedCompetency)
        .filter(EnrichedCompetency.user_id == user.id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"success": True, "deleted": int(deleted)}


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@app.get("/api/analytics/pipeline", dependencies=[Depends(rate_limit_user("user_read", 120))])
def pipeline_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Aggregate in the DATABASE, not in Python — a CONSTANT number of queries regardless of how
    # many jobs the user has, and only the 5 top jobs are ever hydrated into objects. Previously
    # this loaded EVERY job (with 3 selectinloads) into memory just to count statuses + sort for
    # the top 5, so memory + transfer grew linearly with the pipeline. The query COUNT was already
    # constant (no N+1), but the working set was O(jobs); this makes it O(distinct statuses + 5).
    uid = user.id

    total_jobs = db.query(func.count(JobPosting.id)).filter(JobPosting.user_id == uid).scalar() or 0

    # Status breakdown via GROUP BY. A job with no Application row has no status and defaults to
    # SAVED (the same rule the old Python loop applied) — the NULL bucket from the outer join is
    # merged into SAVED here rather than in SQL, so the enum coalescing stays in one place.
    status_rows = (
        db.query(Application.status, func.count(JobPosting.id))
        .outerjoin(Application, Application.job_id == JobPosting.id)
        .filter(JobPosting.user_id == uid)
        .group_by(Application.status)
        .all()
    )
    status_counts: Dict[str, int] = {}
    for status, count in status_rows:
        # SQLAlchemy's Enum result-processor hands back an ApplicationStatus member (or None for
        # the outer-joined application-less rows); the None bucket folds into SAVED, matching the
        # old Python default. A non-enum value would AttributeError here (fail loud) rather than
        # silently produce a wrong key.
        key = ApplicationStatus.SAVED.value if status is None else status.value
        status_counts[key] = status_counts.get(key, 0) + count

    # Average score over SCORED jobs only — the INNER JOIN to JobScore excludes unscored jobs
    # entirely (overall_score is NOT NULL), matching the old ``if j.score`` filter — rounded to
    # match the previous Python round(mean, 1); 0.0 when the user has no scored jobs.
    avg_raw = (
        db.query(func.avg(JobScore.overall_score))
        .join(JobPosting, JobPosting.id == JobScore.job_id)
        .filter(JobPosting.user_id == uid)
        .scalar()
    )
    avg = round(float(avg_raw), 1) if avg_raw is not None else 0.0

    # Only the top 5 scored jobs are hydrated (with the relationships job_public() reads):
    # ORDER BY score DESC LIMIT 5 in SQL instead of sorting the whole pipeline in Python.
    top = (
        db.query(JobPosting)
        .join(JobScore, JobScore.job_id == JobPosting.id)
        .filter(JobPosting.user_id == uid)
        .options(
            selectinload(JobPosting.application),
            selectinload(JobPosting.score),
            selectinload(JobPosting.company),
        )
        .order_by(JobScore.overall_score.desc())
        .limit(5)
        .all()
    )
    return {
        "success": True,
        "stats": {
            "total_jobs": total_jobs,
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
