"""Public-demo skill match — a single job description vs a résumé, KEY-FREE and deterministic.

This powers the pre-launch PUBLIC DEMO (FACTORY_STANDARD §34 / ROADMAP §34): the no-account
"aha" a visitor can try before signing up. It is a deliberately SINGLE-posting cousin of the
pipeline-wide ``skill_gaps.analyze_skill_gaps`` — paste ONE job description (+ optionally a
résumé) and see, instantly, which of the role's skills your résumé already shows and which it is
missing.

Why this is the demo (a DECISION COROLLARY call): the product's headline "aha" is a fit read on a
role. The full numeric fit-score blends semantic embeddings (60% weight), which require the
owner-only ``GEMINI_API_KEY``; exposing that publicly would either 503 when the key is absent (a
broken demo — forbidden by §34) or spend the owner's LLM budget on anonymous traffic (a
wallet-drain vector). The SKILLS half is the honest, compelling, fully-LOCAL slice: it reuses the
exact heuristic ``extract_skills`` vocabulary the real scorer + skill-gap heatmap use, so the
demo shows the SAME real signal the logged-in product does, needs NO third-party AI, sends NO data
off the server, costs nothing per call, and cannot be turned into an LLM-spend amplifier. It works
in production the moment the app deploys — no owner secret required.

Deterministic by construction (a pure function of its inputs): matches are the set intersection of
the two skill sets, gaps the set difference, both ordered ``(skill)`` alphabetically so the output
is trivially and reproducibly testable (the ROADMAP's "deterministic eval on the ranking math").
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


@dataclass
class DemoSkillMatch:
    """A single-role skill match: what the résumé already shows vs what the role also wants."""

    # Skills the role demands that the résumé ALSO shows (positive framing first).
    matching_skills: List[str]
    # Skills the role demands that the résumé is MISSING (the actionable gaps).
    missing_skills: List[str]
    # Total distinct skills the role's description demands (denominator of coverage).
    role_skill_count: int
    # Whether a non-empty résumé was supplied (drives honest "add your résumé" messaging).
    has_resume: bool

    @property
    def coverage(self) -> float:
        """Fraction of the role's demanded skills the résumé covers (0..1).

        Guards the no-detected-skill case: a role whose description surfaces zero known skills
        has an undefined coverage, so we report 0.0 rather than dividing by zero.
        """
        if self.role_skill_count == 0:
            return 0.0
        return round(len(self.matching_skills) / self.role_skill_count, 3)

    def to_dict(self) -> dict:
        return {
            "matching_skills": self.matching_skills,
            "missing_skills": self.missing_skills,
            "role_skill_count": self.role_skill_count,
            "matching_count": len(self.matching_skills),
            "missing_count": len(self.missing_skills),
            "coverage": self.coverage,
            "has_resume": self.has_resume,
        }


def analyze_demo_match(
    job_description: str,
    resume_text: str,
    extract: Callable[[str], List[str]],
) -> DemoSkillMatch:
    """Match ONE job description against a résumé using a shared, key-free skill vocabulary.

    ``extract`` is the skill-extraction callable (in production ``JobScorer(db).extract_skills``);
    injected — never imported here — so the demo shares the EXACT vocabulary the real scorer uses
    on both sides (a résumé "python" matches a JD "python") and tests can pin a deterministic
    extractor. No embeddings, no third-party AI, no personal data leaves the server.

    Returns matching skills (role demands ∩ résumé) and missing skills (role demands − résumé),
    each de-duplicated and sorted alphabetically for a deterministic, testable ordering. When the
    résumé is blank, every detected role skill is "missing" and ``has_resume`` is False so the
    caller can prompt for a résumé honestly instead of implying a real zero-coverage verdict.
    """
    role_skills = set(extract(job_description or ""))
    resume_skills = set(extract(resume_text or "")) if (resume_text or "").strip() else set()

    matching = sorted(role_skills & resume_skills)
    missing = sorted(role_skills - resume_skills)

    return DemoSkillMatch(
        matching_skills=matching,
        missing_skills=missing,
        role_skill_count=len(role_skills),
        has_resume=bool((resume_text or "").strip()),
    )
