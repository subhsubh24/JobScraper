"""SQLAlchemy database models for Career Operator."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Text, Boolean, DateTime, Date,
    ForeignKey, Enum, JSON, Index, UniqueConstraint
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

    # Referral invite loop (Track G/H — lowest-CAC growth lever). ``referral_code`` is the
    # user's unique shareable code; ``bonus_prep_packs`` is the REAL, grantable-now reward
    # (extra free-tier prep packs) earned when someone signs up with the code — no fake
    # billing promise, so it never dead-ends on an unbuilt grant (DECISION COROLLARY).
    referral_code = Column(String(16), unique=True, index=True, nullable=True)
    bonus_prep_packs = Column(Integer, nullable=False, server_default="0", default=0)

    # Third-party-AI consent (Apple App Review 5.1.2(i) / privacy). NULL = never consented
    # (the default): the app must NOT send this user's personal data (resume / job text /
    # coach messages) to the third-party AI provider (Gemini) until they grant explicit,
    # revocable consent. Set to the grant timestamp on consent, back to NULL on revoke, so
    # the column doubles as an audit trail of WHEN consent was given.
    ai_consent_at = Column(DateTime, nullable=True)

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
    content_reports = relationship(
        "ContentReport", back_populates="user", cascade="all, delete-orphan"
    )
    enriched_competencies = relationship(
        "EnrichedCompetency", back_populates="user", cascade="all, delete-orphan"
    )
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


# ============ ORGANIZATIONS / TEAM SEATS (B2B2C tier — Track C / business-case lever 2) ============

class Organization(Base):
    """A team/organization that buys a POOL of seats and assigns them to member users.

    The B2B2C floor-lever (docs/BUSINESS_CASE.md lever 2): bootcamps, outplacement firms, and
    employers resell/allocate seats to their members (higher ARPA, lower CAC per seat than
    individual acquisition). Billing mirrors the individual Stripe path exactly (SIDE-EFFECT
    INTEGRITY): a signature-verified, QUANTITY-based Stripe subscription is the ONLY thing that
    sets ``status``/``seats_purchased`` — never a client-supplied flag. Entitlement is granted
    to a member ONLY while the org is active AND the member occupies a seat; ``users.tier``
    stays the single gating source of truth (``src.billing.recompute_user_tier`` reconciles an
    individual sub OR an active org seat into it), so EVERY existing paid-endpoint gate applies
    to seat members with ZERO gate changes. A team seat grants the base paid (Pro) level;
    Career+ remains an individual-only upsell (no seat plan grants it), so seats never silently
    unlock the higher tier. A NEW table (AUTO_CREATE_TABLES-safe) + the Alembic migration.
    """
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    # The user who created + administers the org (buys seats, adds/removes members). FK without
    # an ORM cascade — account deletion purges owned orgs explicitly (see auth_service), same
    # posture as referrals, so a Postgres FK constraint never blocks a user delete.
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Our plan id (e.g. ``team_annual``) — DERIVED entitlement level maps via billing, never
    # trusted from the client. NULL until a verified checkout completes.
    plan = Column(String(50))
    status = Column(String(50))  # Stripe subscription status: active, trialing, canceled, ...
    # Seat pool size = the verified Stripe subscription QUANTITY. Only a signed webhook writes
    # this; the seat-assignment endpoint refuses to exceed it (no unpaid entitlement).
    seats_purchased = Column(Integer, nullable=False, server_default="0", default=0)

    stripe_customer_id = Column(String(255), index=True)
    stripe_subscription_id = Column(String(255), index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = relationship(
        "OrganizationMember", back_populates="organization", cascade="all, delete-orphan"
    )


class OrganizationMember(Base):
    """One row per seat occupant in an organization.

    Owner privilege is NOT stored here — it is derived from ``Organization.owner_id``; every seat
    row is written with ``role="member"`` (the administrator claims a seat like anyone else, and
    the API synthesizes an ``"owner"`` display role from ``owner_id``). ``active`` members within
    an active org receive the org's paid entitlement. The invariant
    ``count(active members) <= organizations.seats_purchased`` is enforced at assignment time
    (you cannot add a member with no paid seat) and re-enforced on a webhook seat REDUCTION
    (oldest members keep their seats; the newest are deactivated) so an org never grants more
    entitlement than it pays for. ``user_id`` is globally UNIQUE — a user belongs to at most one
    org — which keeps entitlement reconciliation unambiguous. FK to users without an ORM cascade;
    account deletion purges these rows explicitly.
    """
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_org_member_user"),
        Index("ix_org_member_org_active", "org_id", "active"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="member")  # owner | member
    # Soft seat-occupancy flag: a removed/deactivated member keeps the row (audit) but frees the
    # seat and loses entitlement. Only ``active`` rows count against the seat pool + grant tier.
    active = Column(Boolean, nullable=False, server_default="1", default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="members")


# ============ REFERRALS (invite loop — growth) ============

class Referral(Base):
    """One row per successful referral attribution (Track G/H invite loop).

    Created when a NEW user signs up with another user's ``referral_code``. ``referred_id``
    is UNIQUE so a user can be attributed to at most one referrer (idempotent — a second
    attempt is a no-op). Both sides receive a real ``bonus_prep_packs`` grant at creation,
    so the reward is immediate and verifiable, never a promise against unbuilt billing. A
    NEW table (not new columns on an existing one) is AUTO_CREATE_TABLES-safe; the column
    adds on ``users`` ride the Alembic migration (auto-applied on deploy, drift-gated).
    """
    __tablename__ = "referrals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    referrer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    code = Column(String(16), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============ WAITLIST (pre-launch growth) ============

class Waitlist(Base):
    """Pre-launch waitlist signup (Track G/H).

    Capturing the row IS the primary, always-present side-effect — it makes visitor->signup
    measurable and is stored regardless of email deliverability. Double-opt-in shipped (Track H
    / F4.1): ``POST /api/waitlist/join`` best-effort dispatches a confirmation email via the
    email abstraction (``src/email``), and clicking the HMAC-signed link stamps ``confirmed_at``
    (``GET /api/waitlist/confirm``). Signup is NEVER gated on the email (DECISION COROLLARY):
    with the default dry-run backend / no connected provider nothing is delivered, the visitor
    is not dead-ended, and no false 'check your email' claim is made. A NEW table (not new
    columns on an existing one) so AUTO_CREATE_TABLES can create it safely on deploy.
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
    mock_interviews = relationship("MockInterview", back_populates="job", cascade="all, delete-orphan")

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

    # values: prep_pack, study_plan, cover_letter, salary_negotiation, tailored_resume
    artifact_type = Column(String(50), nullable=False)
    title = Column(String(255))
    content = Column(Text, nullable=False)  # JSON or markdown content

    # Metadata
    model_used = Column(String(100))
    tokens_used = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("JobPosting", back_populates="prep_artifacts")


# ============ MOCK INTERVIEW (interview coaching — north-star pillar) ============

class MockInterview(Base):
    """A text-first, role-specific mock interview session (ROADMAP Track A, surface 3).

    The differentiator is an *operator* that drills a candidate to interview-ready, not just
    another content tool. One row is ONE interview session for ONE tracked job: the coach
    generates JD-derived questions up front, then the user answers them one at a time and each
    answer is independently SCORED with concrete feedback + a model answer.

    Design notes:
    - **Job-scoped, like PrepArtifact.** ``job_id`` owns the row; deleting the job (or the user,
      whose ``jobs`` cascade reaches here) removes the session — so account deletion leaves ZERO
      rows (Apple 5.1.1(v) / Google). ``user_id`` is ALSO stored as an indexed FK so every
      endpoint can scope the lookup to the caller server-side (tenant isolation, never trust the
      client) without joining through the job.
    - **Multi-turn state as JSON, not a second table.** ``questions`` is the fixed generated set;
      ``answers`` is a list of per-question scored results appended/overwritten by index as the
      user answers. Keeping both as JSON on the one row keeps the whole session in a single read
      (no N+1) and avoids a second migration — the session is small and bounded (≤8 questions).
    - **Honest scoring only.** Each score reflects the REAL answer: a blank/evasive answer scores
      low. The score climbs only on real practice (VISION "honest > flashy") — never a vanity
      number. The user-facing feedback/model-answer prose is moderated at generation time.
    """

    __tablename__ = "mock_interviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    # Stored for direct, server-side ownership scoping on every endpoint (tenant isolation).
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    # The owning relationship: cascade deletes the session when the job (or user) is removed.
    job_id = Column(String(36), ForeignKey("job_postings.id"), nullable=False, index=True)

    # Generated questions: [{"question": str, "category": "technical"|"behavioral"}] (≤8).
    questions = Column(JSON, nullable=False)
    # Scored answers, keyed by "question_index": [{"question_index": int, "answer": str,
    #   "relevance": int(0-5), "specificity": int(0-5), "star": int(0-5), "overall": float(0-100),
    #   "feedback": str, "model_answer": str}]. Empty until the user answers.
    answers = Column(JSON, nullable=False, default=list)

    status = Column(String(20), nullable=False, default="in_progress")  # in_progress | completed
    model_used = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (job owns the cascade; user_id is a scoping column, no dual-cascade).
    job = relationship("JobPosting", back_populates="mock_interviews")


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


class ContentReport(Base):
    """A user's report/flag of AI-generated content (Apple App Review + Google Play 2026
    GenAI/UGC requirement: apps that surface generative-AI output must give users a way to
    report a specific response).

    The app already moderates LLM output server-side; this is the *user-facing* half. A
    report is a REAL side-effect — a persisted row a moderator reviews — so the UI never
    claims anything it can't back (it says "flagged for review", not "our team has been
    notified"), and it introduces NO dependency on an unbuilt notification/email pipeline
    (DECISION COROLLARY). ``content_excerpt`` snapshots the reported text so a moderator can
    still review it even if the source message/artifact is later deleted.
    """

    __tablename__ = "content_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Which AI surface produced the reported content.
    content_type = Column(String(20), nullable=False)  # coach | prep_pack
    # Optional client-supplied reference to the specific item (e.g. an artifact/message id).
    content_ref = Column(String(64), nullable=True)
    # Moderator-review snapshot of the reported text (bounded; survives source deletion).
    content_excerpt = Column(Text, nullable=True)

    reason = Column(String(30), nullable=False)  # harmful | inaccurate | offensive | other
    detail = Column(Text, nullable=True)  # optional free-text note from the reporter

    status = Column(String(20), nullable=False, server_default="open", default="open")

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="content_reports")


class EnrichedCompetency(Base):
    """A competency discovered from a user's linked public source (Track A profile enrichment).

    OPTIONAL, source-tagged metadata: the user provides a public link (today GitHub; portfolio /
    Scholar are named follow-ups) and we pull STRUCTURED, factual signals from it — never
    invented. For GitHub that is the repos' own ``language`` + ``topics`` fields via the public
    REST API (a FIXED trusted host, like the ATS clients), so there is no arbitrary-URL fetch /
    SSRF surface and nothing is scraped or hallucinated. Each row is one (skill, source_type)
    pair with an ``evidence`` note, so a user can see WHY a skill was attributed. It NEVER blocks
    the core flow — a failed import degrades to zero rows and scoring/generation are unchanged
    when there are none. Cascades on account deletion (owned by the user).
    """

    __tablename__ = "enriched_competencies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Normalized (lowercased) skill/competency name — matches the scorer's skill vocabulary.
    skill = Column(String(100), nullable=False)
    # Which kind of source it came from (today only "github").
    source_type = Column(String(30), nullable=False)  # github | portfolio | scholar
    # The public source URL the user authorized (audit trail + UI attribution).
    source_url = Column(String(500), nullable=False)
    # Short human-readable provenance, e.g. "Primary language in 4 repositories". Bounded.
    evidence = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="enriched_competencies")

    # A skill from a given source is recorded once — a re-import replaces the source's set.
    __table_args__ = (
        UniqueConstraint(
            "user_id", "skill", "source_type", name="uq_enriched_user_skill_source"
        ),
    )


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


class RateCounter(Base):
    """Cross-instance fixed-window abuse counter (rate limit + per-user/day LLM spend
    ceiling). On Vercel serverless each request may run on a fresh instance, so the old
    in-process dicts only slowed abuse within ONE warm instance — the LLM spend ceiling
    in particular multiplied per instance, defeating the wallet-drain defense. Persisting
    the counter to the shared Postgres makes the limit GLOBAL (ROADMAP Track F).

    A row is one (subject, bucket, window) tally. ``subject`` is the client IP (rate limit)
    or the user id (spend ceiling); ``window_key`` is ``floor(epoch / window_seconds)`` so
    each fixed window gets its own row. Stale windows are pruned opportunistically on write,
    so the table stays bounded to roughly the number of currently-active (subject, bucket)
    pairs rather than growing forever.
    """

    __tablename__ = "rate_counters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(255), nullable=False)
    bucket = Column(String(64), nullable=False)
    window_key = Column(BigInteger, nullable=False)
    count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # The unique constraint already creates the B-tree index that serves the only query
    # pattern (exact match on all three columns), so no separate Index is needed.
    __table_args__ = (
        UniqueConstraint("subject", "bucket", "window_key", name="uq_rate_counter_window"),
    )


class AggregateEvent(Base):
    """Privacy-safe aggregate product analytics — counts ONLY, no PII, no raw per-user
    events, no user ids. One row is a single ``(event_type, event_date)`` daily tally, so the
    table stays tiny (a handful of event types × days) and can NEVER be used to reconstruct an
    individual's behaviour. This is the PMF-measurement foundation: aggregate ACTIVATION and
    ENGAGEMENT counts are derived from these tallies (see ``src/analytics.py``). Per-user
    RETENTION cohorts are deliberately NOT derivable here — that needs a per-user dimension we
    intentionally do not store. It keeps counts only; writes are best-effort and never block a
    user request.
    """

    __tablename__ = "aggregate_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(64), nullable=False)
    event_date = Column(Date, nullable=False)  # UTC date bucket
    count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # The unique constraint creates the B-tree index that serves the only query patterns
    # (exact match on both columns for the upsert; group-by event_type for the summary), so
    # no separate Index is needed.
    __table_args__ = (
        UniqueConstraint("event_type", "event_date", name="uq_aggregate_event_day"),
    )


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
