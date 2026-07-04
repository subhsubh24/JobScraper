"""Deterministic eval for the cross-pipeline skill-gap RANKING MATH (ROADMAP Track A).

The ranking is a pure function of (jobs, résumé, extractor) — no LLM, no DB — so it is pinned
exactly here: frequency across the pipeline × absence from the résumé, ordered ``(-job_count,
skill)``. A regression in the ranking (wrong order, a résumé skill leaking into gaps, a
double-count when a JD repeats a skill) reddens this. The LLM learning plan built ON TOP of this
ranking is judged separately by the real-output eval (test_ai_output_evals.py, nightly ``live``).
"""
from types import SimpleNamespace

from src.insights.skill_gaps import analyze_skill_gaps

# A fixed vocabulary so the eval is fully deterministic and independent of the scorer's list.
_VOCAB = ["python", "react", "kubernetes", "aws", "docker", "terraform", "sql"]


def _extract(text: str):
    low = (text or "").lower()
    return [s for s in _VOCAB if s in low]


def _job(description="", requirements=""):
    return SimpleNamespace(description=description, requirements=requirements)


def test_gaps_ranked_by_pipeline_demand_desc():
    jobs = [
        _job("python kubernetes aws"),
        _job("kubernetes docker"),
        _job("python react"),
    ]
    a = analyze_skill_gaps(jobs, "python react", _extract)

    assert a.total_jobs == 3 and a.has_resume is True
    # Missing skills ranked by how many jobs demand them; ties break alphabetically.
    # kubernetes=2, then aws=1, docker=1 (alpha).
    assert [(g.skill, g.job_count) for g in a.gaps] == [
        ("kubernetes", 2),
        ("aws", 1),
        ("docker", 1),
    ]
    # Résumé skills are strengths, never gaps.
    assert [(s.skill, s.job_count) for s in a.strengths] == [("python", 2), ("react", 1)]


def test_resume_skill_never_appears_as_a_gap():
    jobs = [_job("python"), _job("python kubernetes")]
    a = analyze_skill_gaps(jobs, "python", _extract)
    gap_skills = {g.skill for g in a.gaps}
    assert "python" not in gap_skills
    assert gap_skills == {"kubernetes"}


def test_skill_counted_once_per_job_even_if_repeated():
    # A JD that mentions the same skill in both description AND requirements counts ONCE.
    jobs = [_job(description="kubernetes kubernetes", requirements="kubernetes")]
    a = analyze_skill_gaps(jobs, "", _extract)
    assert len(a.gaps) == 1
    assert a.gaps[0].skill == "kubernetes" and a.gaps[0].job_count == 1


def test_coverage_fraction_and_empty_states():
    a0 = analyze_skill_gaps([], "", _extract)
    assert a0.total_jobs == 0 and a0.has_resume is False and a0.gaps == []

    jobs = [_job("aws"), _job("aws"), _job("python"), _job("sql")]
    a = analyze_skill_gaps(jobs, "python", _extract)
    top = a.gaps[0]
    assert top.skill == "aws" and top.job_count == 2
    # 2 of 4 jobs demand aws → coverage 0.5 in the serialized payload.
    assert top.to_dict(a.total_jobs)["coverage"] == 0.5


def test_determinism_same_input_same_order():
    jobs = [_job("aws docker"), _job("docker terraform"), _job("aws terraform")]
    first = [g.skill for g in analyze_skill_gaps(jobs, "", _extract).gaps]
    second = [g.skill for g in analyze_skill_gaps(jobs, "", _extract).gaps]
    assert first == second  # stable, reproducible ordering
