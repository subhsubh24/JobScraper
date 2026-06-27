"""Job scoring algorithm using embeddings and heuristics."""
import json
from typing import List
import numpy as np
from sqlalchemy.orm import Session

from src.db.models import JobPosting, JobScore, User
from src.llm import get_llm_client, embedding_model


class JobScorer:
    """Scores jobs based on resume match using embeddings and heuristics."""

    EMBEDDING_MODEL = embedding_model()

    def __init__(self, db: Session):
        self.db = db
        self.client = get_llm_client()

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
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

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

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using common patterns."""
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

    def score_job(self, job: JobPosting, user: User) -> JobScore:
        """Score a job for a user and save the result."""
        # Get embeddings
        try:
            resume_embedding = self.ensure_user_embedding(user)
            job_embedding = self.ensure_job_embedding(job)

            # Calculate semantic similarity (0-1)
            semantic_score = self.cosine_similarity(resume_embedding, job_embedding)
        except Exception as e:
            print(f"Embedding error: {e}")
            semantic_score = 0.5  # Default if API fails

        # Extract skills
        resume_skills = set(self.extract_skills(user.resume_text or ""))
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
        """Score all unscored jobs for a user."""
        # Get jobs without scores
        jobs = self.db.query(JobPosting).filter(
            JobPosting.user_id == user.id
        ).outerjoin(JobScore).filter(
            JobScore.id.is_(None)
        ).all()

        scores = []
        for job in jobs:
            try:
                score = self.score_job(job, user)
                scores.append(score)
            except Exception as e:
                print(f"Error scoring job {job.id}: {e}")

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
