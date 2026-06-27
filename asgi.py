"""FastAPI backend for Career Operator.

Talks to the real `src/` services and models. Designed to DEGRADE GRACEFULLY:
the core journey (auth + job tracking + scoring + pipeline analytics) works with NO
OpenAI key via heuristic scoring; AI features (prep packs, coach) return a truthful
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

app = FastAPI(
    title="Career Operator API",
    description="AI-powered job search platform (web + mobile)",
    version="1.1.0",
)

# CORS locked to known origins (override via ALLOWED_ORIGINS, comma-separated).
_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
allow_origins = [o.strip() for o in _origins.split(",") if o.strip()] or [
    "http://localhost",
    "http://localhost:8081",  # Expo dev
    "http://localhost:19006",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security headers on every response.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
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
    auth = AuthService(db)
    try:
        user, token = auth.login(data.email, data.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    db.commit()
    return {"success": True, "token": token, "user": user_public(user, db)}


@app.get("/api/auth/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "user": user_public(user, db)}


@app.post("/api/auth/verify-purchase")
def verify_purchase(
    data: AppPurchase,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upgrade to premium after a verified store purchase.

    NOTE: real receipt/signature verification (Apple/Google/RevenueCat) is Track C and
    NOT yet implemented — this endpoint trusts the client and must not ship to
    production as-is. Tracked in ROADMAP Track C + ACCEPTANCE_AUDIT (A4/G4).
    """
    AuthService(db).upgrade_to_premium(user, data.receipt_data)
    db.commit()
    db.refresh(user)
    return {"success": True, "user": user_public(user, db)}


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

    # Score (heuristic fallback when no OpenAI key — never crashes).
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
            detail="AI prep packs require the server's OPENAI_API_KEY to be configured.",
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
            detail="The AI Coach requires the server's OPENAI_API_KEY to be configured.",
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


@app.get("/health")
def health():
    return {"status": "healthy", "version": app.version, "llm_enabled": llm_available()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
