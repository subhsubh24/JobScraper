"""Interview-readiness score + autonomous next-best-action (per target job).

The north-star differentiator (ROADMAP Track A, surface 3): not another tool, but an
*operator* that measures how ready a candidate is for ONE specific role and tells them the
SINGLE next best thing to do about it. This closes the arc from "found a role" → "you're the
strongest candidate for it".

Design — like ``skill_gaps.py``, deliberately PURE, deterministic, and KEY-FREE:
- The readiness read is a weighted composite of the user's REAL signals for this job — how well
  their résumé covers the role's demanded skills, how much they've practiced (answered + scored
  mock-interview questions), and which prep artifacts they've completed. Nothing is sent to a
  third party, no ``GEMINI_API_KEY`` is needed, so the read is FREE and works offline — the
  engagement/retention hook that drives users toward the Pro drills (mock interviews, prep gen).
- **It climbs ONLY on real practice** (VISION "honest > flashy"): every component is 0 in the
  honest 0-state and rises only as the user does real, verifiable work. It is never a vanity
  number and never fabricated.
- **Monotonic in real inputs:** answering another question, generating another artifact, or
  raising a mock-interview score never DECREASES readiness (each contributes a non-negative,
  capped term). This is the property the deterministic eval pins.
- The next-best-action is a pure, priority-ordered rule over the same real signals — so it is
  trivially and deterministically testable, and always points at one concrete, doable step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

# The prep artifacts that matter for being ready for an interview (a bounded, ordered set).
KEY_ARTIFACTS: tuple = ("prep_pack", "tailored_resume", "cover_letter")
_ARTIFACT_LABELS: Dict[str, str] = {
    "prep_pack": "interview prep pack",
    "tailored_resume": "tailored résumé",
    "cover_letter": "cover letter",
}
# How many strong (100-scored) mock answers max out the practice component. Practicing ~4 real
# questions well is the bar for "practiced"; more still counts but the component is capped at 1.
TARGET_PRACTICE_QUESTIONS: int = 4
# An answered question scoring below this (0–100) is a "weak answer" worth redoing.
WEAK_ANSWER_THRESHOLD: float = 60.0

# Component weights (interview practice is the core of interview-readiness). When a component is
# UNAVAILABLE (e.g. the JD has no extractable skills to measure coverage against) it is excluded
# and the remaining weights are renormalized — never a silent 0 that unfairly drags the score.
_WEIGHTS: Dict[str, float] = {"interview_practice": 0.5, "skill_coverage": 0.3, "artifacts": 0.2}


@dataclass
class NextAction:
    """The single next best action — one concrete, doable step, or the ready state."""

    action: str  # machine key: add_resume | start_mock_interview | answer_question |
    #              redo_answer | generate_artifact | study_skill | ready
    label: str   # short user-facing CTA
    detail: str  # one line of honest context (why this, from real signals)

    def to_dict(self) -> dict:
        return {"action": self.action, "label": self.label, "detail": self.detail}


@dataclass
class ReadinessReport:
    score: int  # 0–100, honest 0 when there is no signal
    components: Dict[str, Optional[float]]  # each 0..1 or None when unavailable
    next_action: NextAction
    signals: Dict[str, object] = field(default_factory=dict)  # raw counts for the UI

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "components": self.components,
            "next_action": self.next_action.to_dict(),
            "signals": self.signals,
        }


def _all_answers(sessions: Iterable[dict]) -> List[dict]:
    """Every scored answer across all of the job's mock-interview sessions."""
    out: List[dict] = []
    for s in sessions:
        for a in (s.get("answers") or []):
            if isinstance(a, dict):
                out.append(a)
    return out


def _overall(answer: dict) -> float:
    """A single answer's overall score (0–100), clamped and non-negative; 0 if malformed."""
    try:
        return max(0.0, min(100.0, float(answer.get("overall", 0.0))))
    except (TypeError, ValueError):
        return 0.0


def compute_readiness(
    jd_text: str,
    resume_text: str,
    artifact_types: Iterable[str],
    sessions: List[dict],
    extract: Callable[[str], List[str]],
) -> ReadinessReport:
    """Compute the readiness read + the next best action for ONE job from REAL signals.

    ``extract`` is the shared skill extractor (in production ``JobScorer(db).extract_skills``),
    injected so the résumé and the JD are compared with ONE vocabulary (same rationale as
    ``skill_gaps.analyze_skill_gaps``). ``sessions`` is a list of ``{"questions": [...],
    "answers": [...]}`` dicts (the job's mock-interview rows). ``artifact_types`` is the set of
    prep-artifact types already generated for this job. All inputs are the user's own, already
    persisted — this function neither calls an LLM nor mutates anything.
    """
    resume_text = resume_text or ""
    has_resume = bool(resume_text.strip())
    completed_artifacts = {t for t in (artifact_types or []) if t}

    # --- Component 1: skill coverage (résumé vs THIS job's demanded skills) -----------------
    jd_skills = set(extract(jd_text or ""))
    resume_skills = set(extract(resume_text))
    missing_skills = sorted(jd_skills - resume_skills)
    if jd_skills:
        skill_coverage: Optional[float] = len(jd_skills & resume_skills) / len(jd_skills)
    else:
        skill_coverage = None  # unavailable — no extractable skills to measure against

    # --- Component 2: interview practice (answered + scored mock questions) -----------------
    answers = _all_answers(sessions)
    # Sum of per-answer normalized scores, capped at the practice target → rises with BOTH more
    # answered questions AND higher scores; each term is non-negative (monotonic).
    practice_sum = sum(_overall(a) / 100.0 for a in answers)
    interview_practice = min(1.0, practice_sum / TARGET_PRACTICE_QUESTIONS)

    # --- Component 3: prep artifacts completed ---------------------------------------------
    artifacts = len(completed_artifacts & set(KEY_ARTIFACTS)) / len(KEY_ARTIFACTS)

    components: Dict[str, Optional[float]] = {
        "interview_practice": round(interview_practice, 3),
        "skill_coverage": round(skill_coverage, 3) if skill_coverage is not None else None,
        "artifacts": round(artifacts, 3),
    }

    # Weighted composite over AVAILABLE components (renormalize when one is excluded).
    num = 0.0
    den = 0.0
    for name, weight in _WEIGHTS.items():
        value = components[name]
        if value is None:
            continue
        num += value * weight
        den += weight
    score = int(round(100 * num / den)) if den else 0

    next_action = _next_action(
        has_resume=has_resume,
        missing_skills=missing_skills,
        sessions=sessions,
        completed_artifacts=completed_artifacts,
    )

    return ReadinessReport(
        score=score,
        components=components,
        next_action=next_action,
        signals={
            "has_resume": has_resume,
            "answered_questions": len(answers),
            "missing_skill_count": len(missing_skills),
            "artifacts_completed": sorted(completed_artifacts & set(KEY_ARTIFACTS)),
            "sessions": len(sessions),
        },
    )


def _first_unanswered(session: dict) -> Optional[int]:
    """Index of the first unanswered question in a session, or None if fully answered."""
    questions = session.get("questions") or []
    answered = {a.get("question_index") for a in (session.get("answers") or []) if isinstance(a, dict)}
    for i in range(len(questions)):
        if i not in answered:
            return i
    return None


def _weakest_answer(sessions: Iterable[dict]) -> Optional[dict]:
    """The answered question with the lowest overall score below the weak threshold, if any."""
    weakest: Optional[dict] = None
    for a in _all_answers(sessions):
        if _overall(a) < WEAK_ANSWER_THRESHOLD:
            if weakest is None or _overall(a) < _overall(weakest):
                weakest = a
    return weakest


def _next_action(
    has_resume: bool,
    missing_skills: List[str],
    sessions: List[dict],
    completed_artifacts: set,
) -> NextAction:
    """Priority-ordered next best action — the single most valuable step, from real signals."""
    # 1. No résumé → the foundational gap (feeds scoring, tailoring, skill coverage).
    if not has_resume:
        return NextAction(
            "add_resume",
            "Add your résumé",
            "Add your résumé in Settings so we can tailor prep and measure your fit for this role.",
        )

    # 2. No practice yet → start the core drill.
    if not sessions:
        return NextAction(
            "start_mock_interview",
            "Start a mock interview",
            "Practice role-specific questions and get scored, actionable feedback.",
        )

    # 3. An in-progress session with an unanswered question → finish it.
    for session in sessions:
        idx = _first_unanswered(session)
        if idx is not None:
            return NextAction(
                "answer_question",
                f"Answer question {idx + 1}",
                "Finish your in-progress mock interview to complete this practice round.",
            )

    # 4. A weak answered question → redo it (the readiness-loop redo path).
    weakest = _weakest_answer(sessions)
    if weakest is not None:
        qnum = int(weakest.get("question_index", 0)) + 1
        return NextAction(
            "redo_answer",
            f"Redo your weakest answer (question {qnum})",
            "Your lowest-scoring answer is the fastest way to raise your readiness — redo it.",
        )

    # 5. A key prep artifact missing → generate it.
    for artifact in KEY_ARTIFACTS:
        if artifact not in completed_artifacts:
            label = _ARTIFACT_LABELS[artifact]
            return NextAction(
                "generate_artifact",
                f"Generate your {label}",
                f"You haven't created a {label} for this role yet — it strengthens your application.",
            )

    # 6. Skill gaps remain → study the most relevant missing skill.
    if missing_skills:
        skill = missing_skills[0]
        return NextAction(
            "study_skill",
            f"Study {skill}",
            f"This role asks for {skill}, which isn't on your résumé — closing it lifts your fit.",
        )

    # 7. Everything strong → a final review.
    return NextAction(
        "ready",
        "You're interview-ready",
        "You've practiced, covered the role's skills, and prepared your materials — do a final review.",
    )
