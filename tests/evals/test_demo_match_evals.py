"""Deterministic eval for the public demo skill-match math (FACTORY_STANDARD §34 / ROADMAP §34).

The demo match is a pure function of (job_description, resume_text, extractor) — no LLM, no DB —
so its properties are pinned exactly here with a fixed extractor (independent of the scorer's
real list, so this eval never drifts if that list grows). The properties the demo relies on:
- **Correct split:** matching = role ∩ résumé, missing = role − résumé, both de-duplicated.
- **Deterministic ordering:** alphabetical, so the rendered result is stable + reproducible.
- **Honest coverage:** matching / role_skill_count, guarded against a zero-skill divide.
- **Honest no-résumé state:** blank résumé → has_resume False + every role skill missing
  (never a fabricated 0% "you match nothing" verdict).
A regression in any of these (a wrong split, non-deterministic order, a divide-by-zero NaN, a
dishonest no-résumé verdict) reddens this eval.
"""
from src.insights.demo_match import analyze_demo_match

# A fixed vocabulary so the eval is fully deterministic and independent of the scorer's list.
_VOCAB = ["python", "react", "kubernetes", "aws", "docker", "sql", "go"]


def _extract(text):
    low = (text or "").lower()
    return [s for s in _VOCAB if s in low]


def _match(jd, resume=""):
    return analyze_demo_match(jd, resume, _extract)


def test_correct_matching_and_missing_split():
    m = _match("python aws docker kubernetes", "python aws")
    assert m.matching_skills == ["aws", "python"]  # ∩, sorted
    assert m.missing_skills == ["docker", "kubernetes"]  # role − résumé, sorted
    assert m.role_skill_count == 4
    assert m.coverage == 0.5  # 2 of 4


def test_ordering_is_deterministic_alphabetical():
    # Same skills, different input order → identical, alphabetically-ordered output.
    a = _match("react python go aws", "go react")
    b = _match("aws go python react", "react go")
    assert a.matching_skills == b.matching_skills == ["go", "react"]
    assert a.missing_skills == b.missing_skills == ["aws", "python"]


def test_duplicates_counted_once():
    # A JD mentioning "python" many times still counts it once (set semantics).
    m = _match("python python python aws", "python")
    assert m.role_skill_count == 2
    assert m.matching_skills == ["python"]
    assert m.missing_skills == ["aws"]


def test_no_known_skills_is_zero_coverage_not_nan():
    m = _match("we value curiosity and teamwork", "curiosity")
    assert m.role_skill_count == 0
    assert m.coverage == 0.0  # guarded divide, never NaN
    assert m.matching_skills == []
    assert m.missing_skills == []


def test_blank_resume_is_honest():
    m = _match("python aws docker", "")
    assert m.has_resume is False
    assert m.matching_skills == []
    assert m.missing_skills == ["aws", "docker", "python"]
    assert m.coverage == 0.0


def test_whitespace_only_resume_is_treated_as_no_resume():
    m = _match("python aws", "   \n\t  ")
    assert m.has_resume is False
    assert m.matching_skills == []


def test_full_coverage():
    m = _match("python aws", "python aws go")
    assert m.coverage == 1.0
    assert m.missing_skills == []
    assert m.matching_skills == ["aws", "python"]
