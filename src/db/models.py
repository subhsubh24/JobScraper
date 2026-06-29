"""SQLAlchemy database models for Career Operator."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, DateTime,
    ForeignKey, Enum, JSON, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class UserTier(str, PyEnum):
    FREE = "free"
    PREMIUM = "premium"


class ApplicationStatus(str, PyEnum):
    SAVED = "saved"
    APPLIED = "applied"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ATSType(str, PyEnum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WORKDAY = "workday"
    UNKNOWN = "unknown"


# ============ USER & AUTH ============

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    tier = Column(Enum(UserTier), default=UserTier.FREE)

    # Usage tracking for free tier limits
    jobs_added_this_month = Column(Integer, default=0)
    prep_packs_this_month = Column(Integer, default=0)
    usage_reset_date = Column(DateTime, default=datetime.utcnow)

    # Profile
    full_name = Column(String(255))
    resume_text = Column(Text)
    resume_embedding = Column(JSON)  # Store as JSON array

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    jobs = relationship("JobPosting", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship(
        "Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


# ============ BILLING / SUBSCRIPTIONS ============

class Subscription(Base):
    """Durable Stripe subscription record for a user (Track C).

    One row per user. ``users.tier`` remains the single source of truth for entitlement
    gating; this table is the audit/renewal bookkeeping a Stripe webhook keeps in sync.
    A NEW table (not new columns on ``users``) so AUTO_CREATE_TABLES can create it safely.
    """
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    stripe_customer_id = Column(String(255), index=True)
    stripe_subscription_id = Column(String(255), index=True)

    plan = Column(String(50))    # pro_monthly | pro_annual | careerplus_* (our plan id)
    status = Column(String(50))  # Stripe status: active, trialing, past_due, canceled, ...
    current_period_end = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscription")


# ============ WAITLIST (pre-launch growth) ============

class Waitlist(Base):
    """Pre-launch waitlist signup (Track G/H).

    Capturing the row IS the real, verifiable side-effect — it makes visitor->signup
    measurable without sending anything. We intentionally do NOT send a confirmation email
    here: no email provider is wired yet, and gating signup on an unbuilt email loop would
    dead-end the user (DECISION COROLLARY). Double-opt-in (``confirmed_at``) lands once a
    real/sandbox email provider + a round-trip test exist (Track H / F4.1). A NEW table (not
    new columns on an existing one) so AUTO_CREATE_TABLES can create it safely on deploy.
    """
    __tablename__ = "waitlist"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    source = Column(String(50), default="organic")  # organic | referral | <campaign>
    confirmed_at = Column(DateTime, nullable=True)  # set when double-opt-in lands (Track H)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============ COMPANIES ============

class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, index=True)
    careers_url = Column(String(500))
    ats_type = Column(Enum(ATSType), default=ATSType.UNKNOWN)
    ats_identifier = Column(String(255))  # e.g., greenhouse board token

    # Company metadata
    industry = Column(String(100))
    size = Column(String(50))  # e.g., "50-200", "1000+"
    location = Column(String(255))
    description = Column(Text)

    # Scraping metadata
    last_scraped_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job_postings = relationship("JobPosting", back_populates="company")
    contacts = relationship("Contact", back_populates="company")


# ============ JOB POSTINGS ============

class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True)

    # Job details
    title = Column(String(255), nullable=False)
    company_name = Column(String(255))  # Denormalized for user-added jobs
    location = Column(String(255))
    remote_type = Column(String(50))  # remote, hybrid, onsite

    # Job description
    description = Column(Text)
    requirements = Column(Text)
    responsibilities = Column(Text)

    # Compensation
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(String(10), default="USD")

    # External links
    url = Column(String(500))
    external_id = Column(String(255))  # ID from ATS

    # Parsed/enriched data
    parsed_skills = Column(JSON)  # ["python", "react", ...]
    parsed_experience_years = Column(Integer)
    jd_embedding = Column(JSON)  # Store as JSON array

    # Timestamps
    posted_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="jobs")
    company = relationship("Company", back_populates="job_postings")
    score = relationship("JobScore", back_populates="job", uselist=False, cascade="all, delete-orphan")
    application = relationship("Application", back_populates="job", uselist=False, cascade="all, delete-orphan")
    prep_artifacts = relationship("PrepArtifact", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_job_user_company", "user_id", "company_name"),
    )


# ============ JOB SCORING ============

class JobScore(Base):
    __tablename__ = "job_scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("job_postings.id"), unique=True, nullable=False)

    # Scores (0-100)
    overall_score = Column(Float, nullable=False)
    skills_match = Column(Float)
    experience_match = Column(Float)
    salary_match = Column(Float)
    location_match = Column(Float)

    # Breakdown
    matching_skills = Column(JSON)  # ["python", "sql"]
    missing_skills = Column(JSON)   # ["kubernetes"]
    score_explanation = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("JobPosting", back_populates="score")


# ============ APPLICATIONS ============

class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("job_postings.id"), unique=True, nullable=False)

    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.SAVED)

    # Timeline
    applied_at = Column(DateTime)
    last_activity_at = Column(DateTime, default=datetime.utcnow)

    # Notes
    notes = Column(Text)
    next_step = Column(String(255))
    next_step_date = Column(DateTime)

    # Interview tracking
    interview_rounds = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="applications")
    job = relationship("JobPosting", back_populates="application")


# ============ PREP ARTIFACTS ============

class PrepArtifact(Base):
    __tablename__ = "prep_artifacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("job_postings.id"), nullable=False, index=True)

    artifact_type = Column(String(50), nullable=False)  # prep_pack, study_plan, cover_letter
    title = Column(String(255))
    content = Column(Text, nullable=False)  # JSON or markdown content

    # Metadata
    model_used = Column(String(100))
    tokens_used = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("JobPosting", back_populates="prep_artifacts")


# ============ AI COACH ============

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Context
    job_id = Column(String(36), ForeignKey("job_postings.id"), nullable=True)
    session_id = Column(String(36), index=True)  # Group messages in a conversation

    # Metadata
    tokens_used = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_messages")


# ============ CONTACTS (CRM) ============

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True)

    name = Column(String(255), nullable=False)
    email = Column(String(255))
    linkedin_url = Column(String(500))
    title = Column(String(255))

    # Outreach tracking
    last_contacted_at = Column(DateTime)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="contacts")
    outreach_sequences = relationship("OutreachSequence", back_populates="contact")


class OutreachSequence(Base):
    __tablename__ = "outreach_sequences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contact_id = Column(String(36), ForeignKey("contacts.id"), nullable=False)

    sequence_type = Column(String(50))  # cold_outreach, follow_up, thank_you
    status = Column(String(50), default="pending")  # pending, sent, replied

    subject = Column(String(255))
    body = Column(Text)

    scheduled_for = Column(DateTime)
    sent_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contact = relationship("Contact", back_populates="outreach_sequences")
