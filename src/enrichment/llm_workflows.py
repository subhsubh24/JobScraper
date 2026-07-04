"""LLM workflows for job enrichment and prep pack generation."""
import json
import logging
import os

from sqlalchemy.orm import Session

from src.ai_coach.moderation import ContentModerator
from src.db.models import JobPosting, PrepArtifact, User
from src.llm import get_llm_client, chat_model

logger = logging.getLogger("career_operator.llm_workflows")


def _refinement_enabled() -> bool:
    """The drafter→reviewer pass is ON by default; the owner can disable it for cost.

    It doubles the Gemini calls per generation (draft + one review-and-revise). The per-user/day
    LLM ceiling still bounds total GENERATIONS; this env flag is the COGS lever
    (FACTORY_STANDARD §24) to turn the extra call off wholesale if inference cost ever bites.
    """
    return os.getenv("ENABLE_ARTIFACT_REFINEMENT", "1").strip().lower() in ("1", "true", "yes", "on")


# The product-side maker≠checker pass (ROADMAP Track A). Before an AI artifact is returned to the
# user, ONE independent critique-and-revise improves it — mirroring how the FACTORY reviews its own
# code. The single hardest constraint is that "make it stronger" must NEVER become "make things up":
# a reviewer that adds an unsupported achievement to sound impressive would manufacture exactly the
# "obviously-AI / inaccurate" output real users penalise (GROWTH_STATUS counter-signal; VISION
# "honest > flashy"). So honesty is the reviewer's FIRST duty, above polish.
_REVIEWER_SYSTEM = """You are a meticulous senior editor doing a final quality pass on an \
AI-generated {kind} before it is shown to a job-seeker. Return the IMPROVED {kind} and nothing \
else — no preamble, no commentary, no notes about your changes.

YOUR FIRST DUTY IS HONESTY — it overrides every other goal:
- You may ONLY use facts supported by the SOURCE CONTEXT or already present in the draft. NEVER add,
  invent, or inflate an employer, job title, date, degree, certification, metric, number, or skill
  that is not supported by the source. If the draft contains an unsupported or exaggerated claim,
  REMOVE or soften it — do not "improve" it into something more impressive but false.
- "Improving" means: sharper and more specific wording, better structure and hierarchy, removing
  filler / robotic / generic phrasing, tightening the tailoring to THIS job, fixing tone so it reads
  as written by a thoughtful human — NOT adding invented substance.

Keep the draft's format (markdown structure, headings, length constraints). If the draft is already \
strong and honest, return it essentially unchanged rather than padding it. Output only the final \
{kind}."""


class ModeratedContentError(RuntimeError):
    """Raised when the safety moderator flags a user-facing generation.

    Unlike the AI coach (where a decline IS a valid conversational reply), these workflows
    produce a persisted ARTIFACT the user "generated" (and, for prep packs, spent a usage on).
    Substituting the safe-decline text as the artifact's content — persisting it, charging the
    usage, and reporting ``success: True`` — is a FAKE SUCCESS (FACTORY_STANDARD §6): the user
    asked for a prep pack / cover letter / study plan / negotiation script and got a decline
    message titled as their deliverable, while being charged for it. So a flagged generation
    must FAIL LOUD to the endpoint (no artifact persisted, no usage charged, no success claimed),
    never silently masquerade as the requested artifact. The endpoint maps this to an honest
    422. The ``safe_response`` is carried for the caller to surface if it wants.
    """

    def __init__(self, safe_response: str = ""):
        self.safe_response = safe_response
        super().__init__("Generated content was withheld by the safety filter.")


class LLMWorkflows:
    """Handles all LLM-powered workflows for job enrichment and prep generation."""

    MODEL = chat_model()  # Gemini model (env-overridable via GEMINI_MODEL)

    def __init__(self, db: Session):
        self.db = db
        self.client = get_llm_client()
        # Same conservative safety net the AI coach uses. Apple App Review §1.2 and Google's
        # UGC policy require apps that surface AI-generated content to moderate it; the coach
        # already did, but prep packs / cover letters / negotiation scripts were unmoderated.
        # We screen the model OUTPUT (the text shown to the user), never the JSON-parsing call.
        self.moderator = ContentModerator()

    def _call_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Make a call to the LLM."""
        if self.client is None:
            raise RuntimeError("GEMINI_API_KEY not configured")
        kwargs = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4000,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        try:
            content = response.choices[0].message.content
        except (IndexError, AttributeError):
            # A malformed/empty completion (no choices, no message) must FAIL LOUD here so
            # the caller surfaces an honest error — never silently produce a blank artifact.
            raise RuntimeError("LLM returned a malformed response (no message content).")

        # An empty/None completion is NOT a success. Returning it would either crash the
        # JSON parser (`json.loads(None)` in parse_job_description) or persist a blank
        # prep pack / cover letter and report it to the user as "generated" — a fake-success
        # side effect (FACTORY_STANDARD §6). Fail loud so the endpoint returns an honest 502.
        if not content or not content.strip():
            raise RuntimeError("LLM returned an empty response.")

        # Moderate the user-facing prose (prep packs, cover letters, study plans,
        # negotiation scripts). The structured JSON-parsing path is internal plumbing, not
        # shown to users, so we skip it to avoid false positives on field values. The
        # moderator is deliberately conservative — it only replaces CLEARLY unsafe output, so
        # a normal interview-prep answer is never swallowed. A flagged generation FAILS LOUD
        # (raises) rather than returning the safe-decline text: these callers persist the
        # result as the user's "generated" artifact and (for prep packs) charge a usage, so
        # returning the decline as content would be a fake-success side effect (§6). The
        # endpoint catches this and returns an honest error without charging or persisting.
        if not json_mode:
            verdict = self.moderator.check_output(content)
            if not verdict.allowed:
                raise ModeratedContentError(verdict.safe_response or "")
        return content

    def _refine(self, draft: str, kind: str, source_context: str) -> str:
        """Product-side maker≠checker: run ONE independent review-and-revise on a drafted artifact.

        The reviewer sees the SAME grounding context the drafter saw (so it can catch a fabricated
        claim the drafter is told never to make) plus the draft, and returns an improved version.
        Best-effort and fail-SAFE by design: the draft has ALREADY passed generation + moderation,
        so this pass can only make the artifact BETTER or leave it unchanged — it must never break a
        generation or make it worse. Any failure of the review call (provider error, empty response,
        or the refined output tripping the moderator) falls back to the clean draft. Routing through
        ``_call_llm`` means the refined prose is moderated too; a flagged refinement → fall back.
        """
        if not draft or not _refinement_enabled() or self.client is None:
            return draft
        system_prompt = _REVIEWER_SYSTEM.format(kind=kind)
        user_prompt = (
            "SOURCE CONTEXT (the sole basis of truth — do NOT add anything not supported here):\n"
            f"{source_context}\n\n"
            f"DRAFT {kind} TO REVIEW AND IMPROVE:\n{draft}\n\n"
            f"Return only the improved {kind}."
        )
        try:
            improved = self._call_llm(system_prompt, user_prompt)
        except Exception:
            # Fail SAFE: the draft is already a valid, moderated artifact. A refinement failure
            # (provider error / empty / moderator-flagged refinement) must never degrade it.
            logger.warning("Artifact refinement pass failed for %s; returning the draft.", kind)
            return draft
        improved = (improved or "").strip()
        return improved or draft

    def parse_job_description(self, job: JobPosting) -> dict:
        """Parse a job description to extract structured data."""
        system_prompt = """You are a job description parser. Extract structured information from job postings.
        Return a JSON object with these fields:
        - required_skills: list of required technical skills
        - preferred_skills: list of nice-to-have skills
        - experience_years: minimum years of experience (number or null)
        - education: required education level
        - responsibilities: list of key responsibilities
        - benefits: list of benefits mentioned
        - remote_policy: "remote", "hybrid", "onsite", or "unknown"
        - salary_range: object with min and max if mentioned, else null
        """

        user_prompt = f"""Parse this job posting:

Title: {job.title}
Company: {job.company_name}
Location: {job.location}

Description:
{job.description or 'N/A'}

Requirements:
{job.requirements or 'N/A'}
"""

        result = self._call_llm(system_prompt, user_prompt, json_mode=True)
        return json.loads(result)

    def generate_prep_pack(self, job: JobPosting, user: User) -> PrepArtifact:
        """Generate a comprehensive interview prep pack for a job."""
        system_prompt = """You are an expert interview coach. Create a comprehensive interview preparation pack.
        The prep pack should be practical, specific to the job, and actionable.
        Format your response in clear markdown sections."""

        user_prompt = f"""Create an interview prep pack for this job application:

JOB DETAILS:
Title: {job.title}
Company: {job.company_name}
Location: {job.location}
Description: {job.description or 'N/A'}
Requirements: {job.requirements or 'N/A'}

CANDIDATE RESUME:
{user.resume_text or 'No resume provided'}

Create a prep pack with these sections:

## 1. Company Research Summary
- What does the company do?
- Recent news/developments
- Company culture signals from the JD

## 2. Role Analysis
- Key responsibilities
- Must-have vs nice-to-have skills
- How this role fits in the org

## 3. Your Fit Story
- How to position your experience
- Key achievements to highlight
- Gaps to address proactively

## 4. Technical Interview Questions (10 questions)
- Mix of conceptual and practical
- Include suggested answer frameworks

## 5. Behavioral Interview Questions (8 questions)
- STAR format suggestions
- Specific examples to prepare

## 6. Questions to Ask Them (5 questions)
- Shows genuine interest
- Helps you evaluate the role

## 7. 48-Hour Study Plan
- Day 1 focus areas
- Day 2 focus areas
- Last-minute reminders
"""

        content = self._call_llm(system_prompt, user_prompt)
        content = self._refine(content, "interview prep pack", user_prompt)

        # Save as artifact
        artifact = PrepArtifact(
            job_id=job.id,
            artifact_type="prep_pack",
            title=f"Interview Prep: {job.title} at {job.company_name}",
            content=content,
            model_used=self.MODEL,
        )
        self.db.add(artifact)
        self.db.flush()

        return artifact

    def generate_study_plan(self, job: JobPosting, days: int = 7) -> PrepArtifact:
        """Generate a day-by-day study plan for interview prep."""
        system_prompt = """You are a technical interview coach. Create a detailed study plan.
        Be specific about what to study each day, with time estimates and resources."""

        user_prompt = f"""Create a {days}-day study plan for this job interview:

Title: {job.title}
Company: {job.company_name}
Requirements: {job.requirements or job.description or 'General software engineering'}

For each day, include:
- Morning focus (2 hours)
- Afternoon focus (2 hours)
- Evening review (1 hour)
- Specific topics, resources, and practice problems
"""

        content = self._call_llm(system_prompt, user_prompt)
        content = self._refine(content, "study plan", user_prompt)

        artifact = PrepArtifact(
            job_id=job.id,
            artifact_type="study_plan",
            title=f"{days}-Day Study Plan: {job.title}",
            content=content,
            model_used=self.MODEL,
        )
        self.db.add(artifact)
        self.db.flush()

        return artifact

    def generate_cover_letter(self, job: JobPosting, user: User) -> PrepArtifact:
        """Generate a tailored cover letter."""
        system_prompt = """You are a professional cover letter writer. Write concise, compelling cover letters.
        - Keep it under 300 words
        - Be specific about why this role and company
        - Highlight 2-3 relevant achievements
        - Sound human, not robotic"""

        user_prompt = f"""Write a cover letter for:

JOB:
Title: {job.title}
Company: {job.company_name}
Description: {job.description or 'N/A'}

CANDIDATE:
Name: {user.full_name or 'Candidate'}
Resume: {user.resume_text or 'Experienced professional'}
"""

        content = self._call_llm(system_prompt, user_prompt)
        content = self._refine(content, "cover letter", user_prompt)

        artifact = PrepArtifact(
            job_id=job.id,
            artifact_type="cover_letter",
            title=f"Cover Letter: {job.title} at {job.company_name}",
            content=content,
            model_used=self.MODEL,
        )
        self.db.add(artifact)
        self.db.flush()

        return artifact

    def generate_tailored_resume(self, job: JobPosting, user: User) -> PrepArtifact:
        """Rewrite the user's OWN résumé, tailored to a specific posting.

        The single hardest constraint here is HONESTY: a tailored résumé must reorder, emphasize,
        and rephrase the candidate's REAL experience to mirror the job's language — it must NEVER
        invent an employer, title, date, degree, or skill the source résumé doesn't contain.
        Fabricated experience is worse than useless: it gets the candidate caught (VISION "honest >
        flashy"; the real user complaint that AI output is "obviously AI"/inaccurate). The endpoint
        guarantees ``user.resume_text`` is present before calling this (you cannot tailor nothing —
        tailoring an empty résumé would force the model to fabricate a whole history), so the prompt
        can lean on it as the sole source of truth.
        """
        system_prompt = """You are an expert résumé editor. You rewrite a candidate's EXISTING
résumé so it is tailored to ONE specific job posting.

ABSOLUTE RULES — these are non-negotiable and override everything else:
- Use ONLY the experience, employers, job titles, dates, education, and skills that appear in the
  candidate's source résumé. NEVER invent, add, or exaggerate an employer, role, title, date,
  degree, certification, metric, or skill that is not already in the source. If the source does
  not contain something the job wants, DO NOT fabricate it — instead surface the genuinely-relevant
  experience the candidate DOES have.
- You may REORDER sections/bullets to put the most relevant experience first, REPHRASE bullets to
  mirror the job's language and keywords (only where the underlying fact is true), and TIGHTEN
  wording. That is the whole job.
- Keep it truthful and ATS-friendly: clear section headings, concise bullet points, real keywords
  from the posting that genuinely match the candidate.

Return the tailored résumé as clean, well-structured markdown (name/summary, skills, experience
with bullets, education). Do not add a preamble or commentary — output only the résumé."""

        user_prompt = f"""Tailor this candidate's résumé to the job below.

TARGET JOB:
Title: {job.title}
Company: {job.company_name}
Location: {job.location}
Description: {job.description or 'N/A'}
Requirements: {job.requirements or 'N/A'}

CANDIDATE'S CURRENT RÉSUMÉ (the ONLY source of truth — do not add anything not present here):
{user.resume_text}

Rewrite the résumé tailored to this posting, following the ABSOLUTE RULES. Emphasize the experience
and skills that match this role; mirror the posting's terminology where it is genuinely accurate;
never invent anything.
"""

        content = self._call_llm(system_prompt, user_prompt)
        content = self._refine(content, "tailored résumé", user_prompt)

        artifact = PrepArtifact(
            job_id=job.id,
            artifact_type="tailored_resume",
            title=f"Tailored Résumé: {job.title} at {job.company_name}",
            content=content,
            model_used=self.MODEL,
        )
        self.db.add(artifact)
        self.db.flush()

        return artifact

    def generate_learning_plan(
        self, gap_skills: list[str], job_titles: list[str], user: User
    ) -> str:
        """Generate a prioritised learning plan for the user's TOP cross-pipeline skill gaps.

        Returns the plan as markdown CONTENT — deliberately NOT persisted as a ``PrepArtifact``.
        A ``PrepArtifact`` is job-scoped (``job_id`` is required), but this plan is cross-pipeline
        (it spans ALL the user's jobs) and is cheaply regenerable from the deterministic heatmap,
        so we return it for the user to read / copy / download rather than storing a mislabelled
        job-scoped row. The endpoint computes ``gap_skills`` server-side (never trusted from the
        client) and bounds them (top ~10), and only skill NAMES + job TITLES are sent to the model
        — never the full résumé or JD text — so the third-party payload stays small and bounded.

        HONESTY on resources: the prompt names REPUTABLE, well-known resource TYPES + sources and
        is explicitly told NOT to fabricate specific URLs or invent course titles. A dead or
        invented link is exactly the "obviously-AI / inaccurate" output real users penalise
        (VISION "honest > flashy"); commonly-findable named resources are more useful and honest
        than confident fake URLs. Output is moderated by the shared ``_call_llm`` chokepoint, so a
        flagged plan FAILS LOUD (``ModeratedContentError``) instead of masquerading as a result.
        """
        system_prompt = """You are a pragmatic technical learning coach. Given a job-seeker's TOP
recurring skill gaps (skills their target jobs repeatedly demand but their résumé lacks), produce
a prioritised, realistic learning plan.

RULES — non-negotiable:
- Cover ONLY the skills provided. Do NOT invent additional skills, employers, or certifications.
- Order the skills by priority (most-demanded first, as given) and propose a sensible weekly
  sequence the reader can actually follow.
- For EACH skill give: (a) why it matters for their target roles, (b) a concrete learning path
  (fundamentals → hands-on practice → a small portfolio proof), and (c) a realistic time estimate
  to job-ready competence.
- Recommend REPUTABLE, widely-known resources by NAME and TYPE — e.g. "the official <tool> docs",
  "freeCodeCamp", "a well-reviewed Coursera or Udemy course on <topic>", "build a small project
  that <does X>". Do NOT fabricate specific URLs and do NOT invent exact course titles — name
  real, commonly-findable resource categories the reader can search for. Honesty over specificity.
Return clean, well-structured markdown with one heading per skill and a short intro. No preamble."""

        titles = ", ".join(t for t in job_titles[:8] if t) or "various roles"
        skills = ", ".join(gap_skills)
        user_prompt = f"""The candidate is targeting roles like: {titles}.
Their top recurring skill gaps, most-demanded first: {skills}.

Write the prioritised learning plan following the RULES."""

        content = self._call_llm(system_prompt, user_prompt)
        return self._refine(content, "learning plan", user_prompt)

    def generate_salary_negotiation(self, job: JobPosting, target_salary: int) -> PrepArtifact:
        """Generate salary negotiation scripts and strategies."""
        system_prompt = """You are a salary negotiation expert. Provide specific scripts and strategies.
        Be practical and give exact phrases to use."""

        user_prompt = f"""Create salary negotiation materials for:

Role: {job.title}
Company: {job.company_name}
Target Salary: ${target_salary:,}
Posted Range: ${job.salary_min or 'Not specified'} - ${job.salary_max or 'Not specified'}

Include:
1. Research talking points
2. Initial offer response script
3. Counter-offer script
4. Handling pushback responses
5. Negotiating beyond salary (equity, bonus, etc.)
6. Final acceptance script
"""

        content = self._call_llm(system_prompt, user_prompt)
        content = self._refine(content, "salary negotiation guide", user_prompt)

        artifact = PrepArtifact(
            job_id=job.id,
            artifact_type="salary_negotiation",
            title=f"Salary Negotiation: {job.title}",
            content=content,
            model_used=self.MODEL,
        )
        self.db.add(artifact)
        self.db.flush()

        return artifact
