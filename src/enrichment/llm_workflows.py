"""LLM workflows for job enrichment and prep pack generation."""
import json
from sqlalchemy.orm import Session

from src.ai_coach.moderation import ContentModerator
from src.db.models import JobPosting, PrepArtifact, User
from src.llm import get_llm_client, chat_model


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
        content = response.choices[0].message.content

        # Moderate the user-facing prose (prep packs, cover letters, study plans,
        # negotiation scripts). The structured JSON-parsing path is internal plumbing, not
        # shown to users, so we skip it to avoid false positives on field values. The
        # moderator is deliberately conservative — it only replaces CLEARLY unsafe output, so
        # a normal interview-prep answer is never swallowed. A flagged generation returns the
        # safe decline text instead of surfacing unsafe content to the user.
        if not json_mode:
            verdict = self.moderator.check_output(content or "")
            if not verdict.allowed:
                return verdict.safe_response or ""
        return content

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
