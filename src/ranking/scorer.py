"""Job scoring algorithm using embeddings and heuristics."""
import json
import logging
import threading
from typing import List
import numpy as np
from sqlalchemy.orm import Session

from src.db.models import JobPosting, JobScore, User
from src.llm import get_llm_client, embedding_model, _meter

logger = logging.getLogger("career_operator.scorer")


def _record_fit_outcome(score):  # pragma: no cover - non-blocking outcome telemetry; never affects scoring
    """Emit the finalized job-fit score to Margin as an outcome, NON-BLOCKING + fail-safe."""
    if not _meter:
        return
    try:
        threading.Thread(
            target=lambda: _meter.record_outcome(
                workflow_id="jobscraper-fit-scoring",
                passed=(score is not None),
                quality_score=round(score / 100, 4),
                quality_method="heuristic",
            ),
            daemon=True,
        ).start()
    except Exception:
        pass


class JobScorer:
    """Scores jobs based on resume match using embeddings and heuristics."""

    EMBEDDING_MODEL = embedding_model()

    def __init__(self, db: Session):
        self.db = db
        self.client = get_llm_client()
        # Per-instance cache of link-discovered competencies keyed by user id, so a bulk
        # re-score (one JobScorer, many jobs) loads a user's enrichment ONCE, not per job.
        self._enriched_cache: dict = {}

    def _enriched_skills(self, user: User) -> set:
        """The user's link-discovered competencies as a skill set (empty if none).

        Optional signal — never breaks scoring: a load failure degrades to an empty set. Lazily
        imported to avoid a circular import (github_enricher imports the models this module uses).
        """
        cached = self._enriched_cache.get(user.id)
        if cached is not None:
            return cached
        from src.enrichment.github_enricher import user_enriched_skills

        result = user_enriched_skills(self.db, user)
        self._enriched_cache[user.id] = result
        return result

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text."""
        if self.client is None:
            raise RuntimeError("GEMINI_API_KEY not configured; using heuristic fallback")
        response = self.client.embeddings.create(
            model=self.EMBEDDING_MODEL,
            input=text[:8000]  # Limit input length
        )
        return response.data[0].embedding

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Guards the zero-vector case: if either vector has zero magnitude the cosine is
        undefined and the naive ``dot / (norm * norm)`` yields ``nan`` (0/0) — which is NOT
        an exception, so it would slip past the caller's ``try/except`` and surface as a
        ``nan`` fit score to the user. We return a neutral 0.5 instead (the same value the
        scorer uses when embeddings are unavailable), so a degenerate embedding can never
        corrupt a score.
        """
        a = np.array(vec1, dtype=float)
        b = np.array(vec2, dtype=float)
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0.0:
            return 0.5
        return float(np.dot(a, b) / denom)

    def ensure_user_embedding(self, user: User) -> List[float]:
        """Ensure user has a resume embedding, create if missing."""
        if user.resume_embedding:
            if isinstance(user.resume_embedding, str):
                return json.loads(user.resume_embedding)
            return user.resume_embedding

        if not user.resume_text:
            raise ValueError("User has no resume text to create embedding")

        embedding = self.get_embedding(user.resume_text)
        user.resume_embedding = embedding
        self.db.flush()
        return embedding

    def ensure_job_embedding(self, job: JobPosting) -> List[float]:
        """Ensure job has a JD embedding, create if missing."""
        if job.jd_embedding:
            if isinstance(job.jd_embedding, str):
                return json.loads(job.jd_embedding)
            return job.jd_embedding

        # Combine job info for embedding
        jd_text = f"""
        Title: {job.title}
        Company: {job.company_name or ''}
        Location: {job.location or ''}

        Description:
        {job.description or ''}

        Requirements:
        {job.requirements or ''}

        Responsibilities:
        {job.responsibilities or ''}
        """

        embedding = self.get_embedding(jd_text)
        job.jd_embedding = embedding
        self.db.flush()
        return embedding

    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """Extract skills from text using common patterns.

        A pure function of ``text`` (no instance/DB/LLM state) — declared ``@staticmethod`` so a
        key-free, DB-free caller (e.g. the public no-account demo, FACTORY_STANDARD §34) can reuse
        the EXACT same skill vocabulary as the scorer without standing up a ``JobScorer(db)``.
        Still callable as ``self.extract_skills(...)`` from the scoring path, unchanged."""
        common_skills = [
            "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
            "react", "vue", "angular", "node", "django", "flask", "fastapi",
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
            "git", "ci/cd", "jenkins", "github actions",
            "machine learning", "deep learning", "nlp", "computer vision",
            "data science", "pandas", "numpy", "pytorch", "tensorflow",
            "agile", "scrum", "product management", "project management",
            "leadership", "communication", "problem solving",
        ]

        text_lower = text.lower()
        found_skills = []
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        return found_skills

    def score_job(
        self, job: JobPosting, user: User, use_embeddings: bool = False
    ) -> JobScore:
        """Score a job for a user and save the result.

        ``use_embeddings`` controls whether the semantic-similarity half uses the third-party
        AI (Gemini) embeddings. When it is False the scorer runs purely LOCALLY — no personal
        data leaves the server — using the neutral 0.5 semantic baseline plus the local skills
        match. Callers pass True ONLY after confirming the user consented to third-party AI
        sharing (Apple 5.1.2(i)) AND a key is present; the user still gets a real, honest fit
        score without embeddings, just heuristic-only.

        Default is False = FAIL CLOSED: a caller must OPT IN to sending data to the third party,
        so a new or forgotten call site can never leak personal data to Gemini by omission.
        """
        # Get embeddings (only when allowed — see ``use_embeddings``).
        if use_embeddings:
            try:
                resume_embedding = self.ensure_user_embedding(user)
                job_embedding = self.ensure_job_embedding(job)

                # Calculate semantic similarity (0-1)
                semantic_score = self.cosine_similarity(resume_embedding, job_embedding)
            except Exception:
                # Degrade to the neutral baseline, but LOG it (structured, request-id
                # correlated) instead of a bare print to stdout — a swallowed print is a
                # silent failure the same way the zero-vector nan would be.
                logger.warning(
                    "embedding failed during scoring; using neutral 0.5 baseline", exc_info=True
                )
                semantic_score = 0.5  # Default if API fails
        else:
            # Consent not granted (or no key): stay fully local, never call the third party.
            semantic_score = 0.5

        # Extract skills (résumé + optional link-discovered competencies).
        resume_skills = set(self.extract_skills(user.resume_text or ""))
        # Fold in competencies discovered from the user's linked public sources (GitHub) — an
        # ADDITIVE, honest signal (structured repo languages/topics, never invented) so a skill
        # the user has proven in public work but omitted from the résumé still matches roles that
        # require it. Memoized per scorer instance (§ perf: one query for a bulk re-score, not
        # N). Empty for users with no enrichment → existing scores (golden evals) are unchanged.
        resume_skills |= self._enriched_skills(user)
        jd_text = f"{job.description or ''} {job.requirements or ''}"
        job_skills = set(self.extract_skills(jd_text))

        matching_skills = list(resume_skills & job_skills)
        missing_skills = list(job_skills - resume_skills)

        # Calculate skills match (0-1)
        if job_skills:
            skills_score = len(matching_skills) / len(job_skills)
        else:
            skills_score = 0.5

        # Calculate overall score (0-100)
        # Weights: 60% semantic, 40% skills match
        overall_score = (semantic_score * 0.6 + skills_score * 0.4) * 100
        overall_score = min(100, max(0, overall_score))
        _record_fit_outcome(overall_score)  # pragma: no cover

        # Generate explanation
        explanation = self._generate_explanation(
            overall_score, matching_skills, missing_skills
        )

        # Check for existing score
        existing_score = self.db.query(JobScore).filter(
            JobScore.job_id == job.id
        ).first()

        if existing_score:
            existing_score.overall_score = overall_score
            existing_score.skills_match = skills_score * 100
            existing_score.matching_skills = matching_skills
            existing_score.missing_skills = missing_skills
            existing_score.score_explanation = explanation
            score = existing_score
        else:
            score = JobScore(
                job_id=job.id,
                overall_score=overall_score,
                skills_match=skills_score * 100,
                matching_skills=matching_skills,
                missing_skills=missing_skills,
                score_explanation=explanation,
            )
            self.db.add(score)

        self.db.flush()
        return score

    def _generate_explanation(
        self,
        score: float,
        matching: List[str],
        missing: List[str]
    ) -> str:
        """Generate a human-readable score explanation."""
        if score >= 80:
            rating = "Excellent match!"
        elif score >= 60:
            rating = "Good match"
        elif score >= 40:
            rating = "Moderate match"
        else:
            rating = "Low match"

        parts = [rating]

        if matching:
            parts.append(f"Matching skills: {', '.join(matching[:5])}")

        if missing:
            parts.append(f"Skills to highlight: {', '.join(missing[:3])}")

        return " | ".join(parts)

    def score_all_jobs(self, user: User) -> List[JobScore]:
        """Score all unscored jobs for a user.

        Consent-safe by construction: embeddings (a third-party Gemini call) are used ONLY when
        a key is present AND the user granted third-party-AI consent (Apple 5.1.2(i)); otherwise
        every job is scored with the fully-local heuristic. NOTE: this helper is not currently
        wired to an HTTP route; a future caller that exposes it MUST also enforce the per-user/day
        embedding spend ceiling (see ``create_job``'s ``_consume_counter`` in asgi.py) — this
        batch path deliberately does not meter, so it must not be exposed unmetered.
        """
        use_embeddings = self.client is not None and user.ai_consent_at is not None

        # Get jobs without scores
        jobs = self.db.query(JobPosting).filter(
            JobPosting.user_id == user.id
        ).outerjoin(JobScore).filter(
            JobScore.id.is_(None)
        ).all()

        scores = []
        for job in jobs:
            try:
                score = self.score_job(job, user, use_embeddings=use_embeddings)
                scores.append(score)
            except Exception:
                logger.warning("failed to score job %s; skipping", job.id, exc_info=True)

        return scores

    def get_top_jobs(self, user: User, limit: int = 10) -> List[tuple]:
        """Get top scored jobs for a user."""
        results = self.db.query(JobPosting, JobScore).join(
            JobScore, JobPosting.id == JobScore.job_id
        ).filter(
            JobPosting.user_id == user.id
        ).order_by(
            JobScore.overall_score.desc()
        ).limit(limit).all()

        return results
