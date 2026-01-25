"""
FastAPI backend for Career Operator mobile app.
Optimized for $4.99 one-time purchase model.
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import os
from dotenv import load_dotenv

from src.db import get_session
from src.db.models import User, JobPosting, JobScore, Application, PrepArtifact, ChatMessage
from src.ranking.scorer import JobScorer
from src.enrichment.llm_workflows import LLMWorkflows
from src.ai_coach.career_coach import CareerCoach
from src.auth.auth_service import AuthService

load_dotenv()

app = FastAPI(
    title="Career Operator API",
    description="AI-powered job search platform for mobile apps",
    version="1.0.0"
)

# CORS for mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Request/Response Models
# ============================================================================

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    target_roles: List[str] = Field(default_factory=list)
    target_salary_min: float = 150000
    target_locations: List[str] = Field(default_factory=lambda: ["Remote US"])

class UserLogin(BaseModel):
    email: str
    password: str

class JobCreate(BaseModel):
    title: str
    company_name: str
    location: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    description: str
    apply_url: Optional[str] = None

class JobUpdate(BaseModel):
    status: Optional[str] = None

class PrepPackRequest(BaseModel):
    job_pk: str

class ChatRequest(BaseModel):
    message: str
    job_pk: Optional[str] = None
    context_type: str = "general"

class AppPurchase(BaseModel):
    receipt_data: str  # Apple/Google receipt
    device_id: str

# ============================================================================
# Authentication
# ============================================================================

def get_current_user(authorization: str = Header(None)):
    """Verify JWT token and return user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ")[1]
    payload = AuthService.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    db = get_session()
    user = db.query(User).filter_by(user_id=payload['user_id']).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user

# ============================================================================
# Auth Endpoints
# ============================================================================

@app.post("/api/auth/register")
def register(data: UserCreate):
    """Register new user (free tier)."""
    db = get_session()

    try:
        user = AuthService.create_user(
            session=db,
            email=data.email,
            password=data.password,
            full_name=data.full_name,
            subscription_tier='free'
        )

        # Set preferences
        user.target_salary_min = data.target_salary_min
        user.target_role_families = ','.join(data.target_roles)
        user.target_locations = ','.join(data.target_locations)
        db.commit()

        token = AuthService.generate_token(user)

        return {
            'success': True,
            'token': token,
            'user': {
                'user_id': user.user_id,
                'email': user.email,
                'full_name': user.full_name,
                'subscription_tier': user.subscription_tier,
                'prep_packs_remaining': 1 if user.subscription_tier == 'free' else 5,
                'ai_messages_remaining': 0 if user.subscription_tier == 'free' else 20
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
def login(data: UserLogin):
    """Login user."""
    db = get_session()

    user = AuthService.authenticate_user(db, data.email, data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = AuthService.generate_token(user)

    return {
        'success': True,
        'token': token,
        'user': {
            'user_id': user.user_id,
            'email': user.email,
            'full_name': user.full_name,
            'subscription_tier': user.subscription_tier,
            'prep_packs_remaining': max(0, (5 if user.subscription_tier == 'premium' else 1) - user.prep_packs_used_this_month),
            'ai_messages_remaining': max(0, (20 if user.subscription_tier == 'premium' else 0) - user.ai_messages_used_this_month)
        }
    }

@app.post("/api/auth/verify-purchase")
def verify_purchase(data: AppPurchase, user: User = Depends(get_current_user)):
    """Verify app store purchase and upgrade to premium."""
    db = get_session()

    # TODO: Implement actual receipt verification
    # For now, just upgrade user

    user.subscription_tier = 'premium'
    user.subscription_status = 'active'
    user.subscription_start_date = datetime.utcnow()
    db.commit()

    return {
        'success': True,
        'message': 'Purchase verified! You now have Premium access.',
        'user': {
            'subscription_tier': user.subscription_tier,
            'prep_packs_remaining': 5,
            'ai_messages_remaining': 20
        }
    }

# ============================================================================
# Job Endpoints
# ============================================================================

@app.post("/api/jobs")
def create_job(data: JobCreate, user: User = Depends(get_current_user)):
    """Add a new job to track."""
    db = get_session()

    # Check job limit (free: 5, premium: unlimited)
    job_count = db.query(JobPosting).filter_by(user_id=user.user_id).count()

    if user.subscription_tier == 'free' and job_count >= 5:
        raise HTTPException(
            status_code=403,
            detail="Free tier limited to 5 jobs. Upgrade to Premium for unlimited."
        )

    # Create job
    import uuid
    job = JobPosting(
        job_pk=str(uuid.uuid4()),
        user_id=user.user_id,
        source='manual',
        source_job_id=str(uuid.uuid4()),
        company_id=1,  # TODO: Create company if not exists
        title=data.title,
        location_raw=data.location,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        description_text=data.description,
        apply_url=data.apply_url,
        status='new'
    )

    db.add(job)

    # Score the job
    scorer = JobScorer()
    score_result = scorer.score_job(
        job={'title': data.title, 'description': data.description, 'salary_min': data.salary_min or 0},
        company={'name': data.company_name},
        user_resume=user.resume_text or ""
    )

    job_score = JobScore(
        job_pk=job.job_pk,
        total_score=score_result['total_score'],
        score_breakdown_json=str(score_result['breakdown']),
        mode='standard'
    )

    db.add(job_score)
    db.commit()

    return {
        'success': True,
        'job': {
            'job_pk': job.job_pk,
            'title': job.title,
            'company': data.company_name,
            'location': job.location_raw,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
            'score': score_result['total_score'],
            'status': job.status
        }
    }

@app.get("/api/jobs")
def get_jobs(user: User = Depends(get_current_user)):
    """Get all user's jobs."""
    db = get_session()

    jobs = db.query(JobPosting).filter_by(user_id=user.user_id).all()

    return {
        'success': True,
        'jobs': [{
            'job_pk': job.job_pk,
            'title': job.title,
            'company': job.company.name if job.company else 'Unknown',
            'location': job.location_raw,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
            'score': job.job_score.total_score if job.job_score else 0,
            'status': job.status,
            'created_at': job.created_at.isoformat()
        } for job in jobs]
    }

@app.patch("/api/jobs/{job_pk}")
def update_job(job_pk: str, data: JobUpdate, user: User = Depends(get_current_user)):
    """Update job status."""
    db = get_session()

    job = db.query(JobPosting).filter_by(job_pk=job_pk, user_id=user.user_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if data.status:
        job.status = data.status

    db.commit()

    return {
        'success': True,
        'job': {
            'job_pk': job.job_pk,
            'status': job.status
        }
    }

# ============================================================================
# Prep Pack Endpoints
# ============================================================================

@app.post("/api/prep-packs/generate")
def generate_prep_pack(data: PrepPackRequest, user: User = Depends(get_current_user)):
    """Generate AI interview prep pack."""
    db = get_session()

    # Check if user has credits
    if user.subscription_tier == 'free':
        if user.prep_packs_used_this_month >= 1:
            raise HTTPException(
                status_code=403,
                detail="Free tier limited to 1 prep pack/month. Upgrade to Premium for 5/month."
            )
    elif user.subscription_tier == 'premium':
        if user.prep_packs_used_this_month >= 5:
            raise HTTPException(
                status_code=403,
                detail="You've used all 5 prep packs this month. Resets in {} days.".format(
                    (user.usage_reset_date - datetime.utcnow()).days
                )
            )

    # Get job
    job = db.query(JobPosting).filter_by(job_pk=data.job_pk, user_id=user.user_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Generate prep pack (this will use OpenAI)
    workflows = LLMWorkflows()

    try:
        # This is simplified - in production, run all 6 workflows
        company_dossier = workflows.workflow_company_dossier(
            company_name=job.company.name if job.company else "Unknown",
            job_pk=job.job_pk
        )

        # Increment usage
        AuthService.increment_prep_pack_usage(db, user.user_id)

        # Save prep artifact
        prep = PrepArtifact(
            job_pk=job.job_pk,
            company_dossier_json=str(company_dossier)
        )
        db.add(prep)
        db.commit()

        return {
            'success': True,
            'prep_pack': {
                'company_dossier': company_dossier,
                'credits_remaining': max(0, (5 if user.subscription_tier == 'premium' else 1) - user.prep_packs_used_this_month)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prep pack: {str(e)}")

# ============================================================================
# AI Career Coach Endpoints
# ============================================================================

@app.post("/api/coach/chat")
def chat_with_coach(data: ChatRequest, user: User = Depends(get_current_user)):
    """Chat with AI Career Coach."""
    db = get_session()

    # Check tier
    if user.subscription_tier == 'free':
        raise HTTPException(
            status_code=403,
            detail="AI Career Coach is only available in Premium. Upgrade for $4.99!"
        )

    # Check credits
    if user.ai_messages_used_this_month >= 20:
        raise HTTPException(
            status_code=403,
            detail="You've used all 20 AI messages this month. Resets in {} days.".format(
                (user.usage_reset_date - datetime.utcnow()).days
            )
        )

    coach = CareerCoach()

    try:
        response = coach.chat(
            db=db,
            user=user,
            message=data.message,
            context_type=data.context_type,
            job_pk=data.job_pk
        )

        AuthService.increment_ai_message_usage(db, user.user_id)

        return {
            'success': True,
            'message': response['message'],
            'credits_remaining': max(0, 20 - user.ai_messages_used_this_month)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Coach error: {str(e)}")

@app.get("/api/coach/suggestions")
def get_coach_suggestions(user: User = Depends(get_current_user)):
    """Get suggested questions for AI Coach."""
    db = get_session()

    coach = CareerCoach()
    suggestions = coach.get_suggested_questions(user, db)

    return {
        'success': True,
        'suggestions': suggestions
    }

# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.get("/api/analytics/pipeline")
def get_pipeline_stats(user: User = Depends(get_current_user)):
    """Get pipeline statistics."""
    db = get_session()

    jobs = db.query(JobPosting).filter_by(user_id=user.user_id).all()

    status_counts = {}
    for job in jobs:
        status_counts[job.status] = status_counts.get(job.status, 0) + 1

    avg_score = sum(job.job_score.total_score for job in jobs if job.job_score) / max(len(jobs), 1)

    return {
        'success': True,
        'stats': {
            'total_jobs': len(jobs),
            'status_breakdown': status_counts,
            'average_score': round(avg_score, 1),
            'top_jobs': [{
                'job_pk': job.job_pk,
                'title': job.title,
                'company': job.company.name if job.company else 'Unknown',
                'score': job.job_score.total_score if job.job_score else 0
            } for job in sorted(jobs, key=lambda j: j.job_score.total_score if j.job_score else 0, reverse=True)[:5]]
        }
    }

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
