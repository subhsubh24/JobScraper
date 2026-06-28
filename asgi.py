"""FastAPI backend for Career Operator.

Talks to the real `src/` services and models. Designed to DEGRADE GRACEFULLY:
the core journey (auth + job tracking + scoring + pipeline analytics) works with NO
Gemini key via heuristic scoring; AI features (prep packs, coach) return a truthful
"needs configuration" response instead of crashing when the key is absent.
"""
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.ai_coach.career_coach import CareerCoach
from src.auth.auth_service import AuthService
from src.db import get_db
from src.db.models import (
    Application,
    ApplicationStatus,
    ATSType,
    JobPosting,
    PrepArtifact,
    User,
    UserTier,
)
from src.enrichment.llm_workflows import LLMWorkflows
from src.llm import llm_available
from src.ranking.scorer import JobScorer

load_dotenv()
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

# CORS. Auth is Bearer-token (no cookies), so when no explicit allowlist is configured
# we allow any origin WITHOUT credentials — this lets the web app call the API from its
# own Vercel domain out of the box. Set ALLOWED_ORIGINS (comma-separated) to lock it
# down to specific origins (which also re-enables credentials).
_explicit_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_explicit_origins or ["*"],
    allow_credentials=bool(_explicit_origins),  # cannot combine credentials with "*"
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
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for k, v in SECURITY_HEADERS.items():
        response.headers[k] = v
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Error hygiene: never leak stack traces / internals to clients."""
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ---------------------------------------------------------------------------
# Rate limiting + per-user/day LLM spend ceiling.
# NOTE: in-memory state. On Vercel serverless each invocation may run on a fresh
# instance, so these limits are per-instance, NOT global — they slow abuse within a
# warm instance but are not a hard cross-instance guarantee. Track F: back these with
# a shared store (Upstash Redis / Postgres) before relying on them in production.
# ---------------------------------------------------------------------------
_RATE_BUCKET: Dict[Tuple[str, str], List[float]] = defaultdict(list)
_LLM_DAY_COUNT: Dict[Tuple[str, str], int] = defaultdict(int)

# Per-user/day ceiling on expensive LLM operations (wallet-drain defense).
LLM_DAILY_CEILING = int(os.getenv("LLM_DAILY_CEILING", "25"))

# Per-ACCOUNT login lockout (defends one account against a distributed password
# brute-force that spreads across IPs, which the per-IP rate limit alone misses). In-memory
# like the rate limiter above, so it's per-instance on serverless — Track F tracks moving
# both to a shared store. Keyed by email so it never reveals whether the account exists.
_LOGIN_FAILURES: Dict[str, Tuple[int, float]] = {}  # email -> (consecutive_failures, locked_until_ts)
LOGIN_MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
LOGIN_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "900"))  # 15 min


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


def _record_login_failure(email: str) -> None:
    failures = _LOGIN_FAILURES.get(email, (0, 0.0))[0] + 1
    locked_until = time.time() + LOGIN_LOCKOUT_SECONDS if failures >= LOGIN_MAX_FAILURES else 0.0
    _LOGIN_FAILURES[email] = (failures, locked_until)


def _clear_login_failures(email: str) -> None:
    _LOGIN_FAILURES.pop(email, None)


def rate_limit(bucket: str, limit: int, window_seconds: int = 60):
    """Fixed-window limiter dependency factory, keyed by client + bucket."""
    def _dep(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        key = (client, bucket)
        now = time.time()
        hits = [t for t in _RATE_BUCKET[key] if now - t < window_seconds]
        if len(hits) >= limit:
            raise HTTPException(status_code=429, detail="Too many requests. Slow down.")
        hits.append(now)
        _RATE_BUCKET[key] = hits
    return _dep


def check_llm_ceiling(user: User) -> None:
    key = (user.id, date.today().isoformat())
    if _LLM_DAY_COUNT[key] >= LLM_DAILY_CEILING:
        raise HTTPException(
            status_code=429,
            detail="Daily AI usage limit reached. Try again tomorrow.",
        )
    _LLM_DAY_COUNT[key] += 1


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None
    resume_text: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    url: Optional[str] = None


class JobUpdate(BaseModel):
    status: str


class PrepPackRequest(BaseModel):
    job_id: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    job_id: Optional[str] = None
    session_id: Optional[str] = None


class AppPurchase(BaseModel):
    receipt_data: str
    platform: str = "ios"


class ImportPreviewRequest(BaseModel):
    careers_url: str = Field(min_length=4, max_length=500)


# Cap the preview so one request can't fan out into a huge payload / long fetch.
ATS_PREVIEW_LIMIT = 50


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
    db.commit()
    db.refresh(user)
    return {"success": True, "token": token, "user": user_public(user, db)}


@app.post("/api/auth/login", dependencies=[Depends(rate_limit("auth", 10))])
def login(data: UserLogin, db: Session = Depends(get_db)):
    email_key = (data.email or "").lower()
    # Per-account lockout. Same generic 429 whether or not the account exists, so it can't
    # be used to enumerate emails.
    if _login_locked(email_key):
        raise HTTPException(
            status_code=429,
            detail="Too many failed attempts. Try again in a few minutes.",
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


@app.post("/api/auth/verify-purchase")
def verify_purchase(
    data: AppPurchase,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upgrade to premium after a VERIFIED store purchase.

    SIDE-EFFECT INTEGRITY (FACTORY_STANDARD §6): real receipt/signature verification
    (Apple/Google/RevenueCat) is Track C and NOT yet implemented. We must NOT fake-grant
    premium on an unverified receipt — a "purchase processed" the user can't trust is a
    LIE and a billing-path correctness bug. Until verification exists, this endpoint
    refuses honestly (501) and grants NOTHING. Tracked in ROADMAP Track C + PENDING_OPS.
    """
    raise HTTPException(
        status_code=501,
        detail="Purchase verification is not available yet. No charge was applied and "
        "your plan is unchanged.",
    )


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
    try:
        JobScorer(db).score_job(job, user)
    except Exception:
        logger.exception("Scoring failed for job %s; continuing unscored", job.id)

    # Track it: create the pipeline Application row in SAVED.
    db.add(Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.SAVED))
    auth.increment_job_usage(user)
    db.commit()
    db.refresh(job)
    return {"success": True, "job": job_public(job)}


@app.get("/api/jobs")
def list_jobs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    jobs = (
        db.query(JobPosting)
        .filter(JobPosting.user_id == user.id)
        .order_by(JobPosting.created_at.desc())
        .all()
    )
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

    check_llm_ceiling(user)
    try:
        artifact: PrepArtifact = LLMWorkflows(db).generate_prep_pack(job, user)
    except Exception:
        logger.exception("Prep pack generation failed")
        raise HTTPException(status_code=502, detail="AI provider error generating prep pack")

    auth.increment_prep_usage(user)
    db.commit()
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

    check_llm_ceiling(user)
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
    return {"success": True, "message": reply}


@app.get("/api/coach/suggestions")
def coach_suggestions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Works without an LLM key — deterministic, context-aware suggestions.
    suggestions = CareerCoach(db).get_suggested_questions(user)
    return {"success": True, "suggestions": suggestions}


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@app.get("/api/analytics/pipeline")
def pipeline_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    jobs = db.query(JobPosting).filter(JobPosting.user_id == user.id).all()
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
