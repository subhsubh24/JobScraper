"""Cross-pipeline skill-gap analysis — deterministic, key-free, no third-party AI.

The market's job-search tools score ONE posting at a time. This looks across a user's WHOLE
pipeline: which skills do their tracked jobs repeatedly demand, and which of those are missing
from their résumé? That "you're missing Kubernetes, and 8 of your 10 saved jobs want it" read is
a planning/retention surface a single fit-score can't give.

Deliberately LOCAL and deterministic:
- It reuses the SAME heuristic skill extractor the scorer uses (``JobScorer.extract_skills``) on
  BOTH the résumé and every job description, so the two sides share one vocabulary and the
  comparison is apples-to-apples (a résumé "python" matches a JD "python").
- No embeddings, no Gemini call, no personal data leaves the server — so the heatmap is FREE,
  needs no third-party-AI consent (nothing is sent to a third party), and works with no
  ``GEMINI_API_KEY``. The (Pro, LLM) learning plan built on top of it is a separate step.
- The ranking is a pure function of the inputs (sorted by demand DESC then name ASC), so it is
  trivially and deterministically testable — the ROADMAP's "deterministic eval on the ranking
  math".
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Callable, List

from src.db.models import JobPosting


@dataclass
class SkillStat:
    """One skill and how it relates to the pipeline + the résumé."""

    skill: str
    job_count: int  # how many tracked jobs demand this skill
    in_resume: bool

    def to_dict(self, total_jobs: int) -> dict:
        return {
            "skill": self.skill,
            "job_count": self.job_count,
            "total_jobs": total_jobs,
            # Fraction of the pipeline demanding this skill (0..1) — drives the heatmap
            # intensity in the UI. Guarded against a zero-job divide.
            "coverage": round(self.job_count / total_jobs, 3) if total_jobs else 0.0,
            "in_resume": self.in_resume,
        }


@dataclass
class SkillGapAnalysis:
    total_jobs: int
    has_resume: bool
    gaps: List[SkillStat]  # demanded skills NOT in the résumé, ranked by job_count DESC
    strengths: List[SkillStat]  # demanded skills the résumé HAS (positive framing)

    def to_dict(self) -> dict:
        return {
            "total_jobs": self.total_jobs,
            "has_resume": self.has_resume,
            "gaps": [g.to_dict(self.total_jobs) for g in self.gaps],
            "strengths": [s.to_dict(self.total_jobs) for s in self.strengths],
        }


def _jd_text(job: JobPosting) -> str:
    return f"{job.description or ''} {job.requirements or ''}"


def analyze_skill_gaps(
    jobs: List[JobPosting],
    resume_text: str,
    extract: Callable[[str], List[str]],
) -> SkillGapAnalysis:
    """Rank the pipeline's skill demand against the résumé — frequency × absence.

    ``extract`` is the skill-extraction callable (in production, ``JobScorer(db).extract_skills``);
    injected rather than imported so the SAME vocabulary is used on both sides and tests can pin a
    deterministic extractor. For each skill any job demands: ``job_count`` = the number of tracked
    jobs whose JD contains it (counted once per job), ``in_resume`` = whether the résumé contains
    it. Skills the résumé lacks are GAPS (ranked by demand, most-demanded first); skills it has are
    STRENGTHS. Ordering is deterministic: ``(-job_count, skill)`` so ties break alphabetically.
    """
    resume_skills = set(extract(resume_text or ""))
    total_jobs = len(jobs)

    demand: Counter = Counter()
    for job in jobs:
        # A set per job so a JD mentioning "python" three times still counts once.
        for skill in set(extract(_jd_text(job))):
            demand[skill] += 1

    gaps: List[SkillStat] = []
    strengths: List[SkillStat] = []
    for skill, count in demand.items():
        stat = SkillStat(skill=skill, job_count=count, in_resume=skill in resume_skills)
        (strengths if stat.in_resume else gaps).append(stat)

    gaps.sort(key=lambda s: (-s.job_count, s.skill))
    strengths.sort(key=lambda s: (-s.job_count, s.skill))

    return SkillGapAnalysis(
        total_jobs=total_jobs,
        has_resume=bool((resume_text or "").strip()),
        gaps=gaps,
        strengths=strengths,
    )
