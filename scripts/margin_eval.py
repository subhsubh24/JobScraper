#!/usr/bin/env python3
"""Repo-specific eval runner: statistical cost-per-outcome for JobScraper's AI workflows.

Runs representative INPUT MATRICES (evals/margin/*_cases.jsonl) through the REAL metered paths,
grades each result against a GENUINE success signal, and emits real CALLS + graded OUTCOMES to
Margin via the published `margin-meter` SDK. That is what gives Margin an accurate,
statistically-grounded cost-per-outcome per workflow — not a single hand-picked request.

Workflows (see evals/margin/COVERAGE.md for the full frontier map):
  * fit-scoring            — JobScore.overall_score band grader. Has a DETERMINISTIC key-free
                             path, so it is CI-calibrated and runs keyless.
  * mock-interview-scoring — the real numeric answer score (relevance+specificity+STAR). LLM-only:
                             bimodal grader (strong answers score high, weak/blank/off-topic low).
  * cover-letter           — structural grader on the generated letter (grounded in the company +
                             a JD skill, right length, no placeholder). LLM-only.

Modes / fail-safe:
  * `--workflow {fit-scoring,mock-interview-scoring,cover-letter,all}` (default: all).
  * LLM-only workflows are SKIPPED without a GEMINI_API_KEY (and are never in the keyless CI gate).
  * No `margin-meter` / no MARGIN_INGEST_URL+MARGIN_INGEST_KEY -> telemetry DISABLED (still
    scores + grades + prints; emits nothing, no network).
  * Eval batches are tagged session_id="eval:<run-id>" (calls) / link="eval:<run-id>" (outcomes).

For chat workflows the runner RE-TAGS the app's in-request `record_call` (src/llm.py) to the
correct workflow_id + eval session_id, so emitted cost is the true paid path.

Usage:
  python scripts/margin_eval.py --dry-run
  MARGIN_INGEST_URL=... MARGIN_INGEST_KEY=... python scripts/margin_eval.py --workflow fit-scoring
  GEMINI_API_KEY=... MARGIN_INGEST_URL=... MARGIN_INGEST_KEY=... \
      python scripts/margin_eval.py --workflow all --embeddings --max-llm-cases 20
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MARGIN_DIR = ROOT / "evals" / "margin"
CASES_PATH = MARGIN_DIR / "fit_scoring_cases.jsonl"           # fit-scoring (default) — back-compat
BANDS_PATH = MARGIN_DIR / "bands.json"
MOCK_CASES_PATH = MARGIN_DIR / "mock_interview_scoring_cases.jsonl"
COVER_CASES_PATH = MARGIN_DIR / "cover_letter_cases.jsonl"

FIT_WORKFLOW_ID = "jobscraper-fit-scoring"
MOCK_WORKFLOW_ID = "jobscraper-mock-interview-scoring"
COVER_WORKFLOW_ID = "jobscraper-cover-letter"

# Mock-interview scoring is bimodal by design (the scorer floors vague/empty answers): a strong
# answer must score HIGH, a weak/blank/off-topic answer LOW. The 42-58 gap is deliberately unused.
MOCK_BANDS = {"strong": (58.0, 100.01), "weak": (0.0, 42.0)}


# --------------------------------------------------------------------------- #
# Graders (importable + reused by the CI test — single source of truth)
# --------------------------------------------------------------------------- #
def load_bands(path: Path = BANDS_PATH) -> dict:
    raw = json.loads(Path(path).read_text())
    return {k: tuple(v) for k, v in raw.items() if not k.startswith("_")}


def band_for_score(score: float, bands: dict) -> Optional[str]:
    for name, (lo, hi) in bands.items():
        if lo <= score < hi:
            return name
    return None


def grade(expected_band: str, score: float, bands: dict) -> tuple[bool, Optional[str]]:
    """A case PASSES iff its real score lands in its EXPECTED band's window."""
    lo, hi = bands[expected_band]
    return (lo <= score < hi), band_for_score(score, bands)


def grade_cover_letter(text: str, case: dict) -> tuple[bool, float, list]:
    """Genuine STRUCTURAL success signal for a generated cover letter.

    Passes only a usable, grounded letter: mentions the company, references >=1 required JD skill,
    is a real length, and has no unfilled placeholder. quality_score = fraction of checks passed,
    so a template/placeholder/empty/off-topic generation genuinely FAILS.
    """
    t = (text or "").strip()
    tl = t.lower()
    company_ok = bool(case.get("company")) and case["company"].lower() in tl
    skills_ok = any(str(s).lower() in tl for s in case.get("jd_skills", []) or [])
    length_ok = 200 <= len(t) <= 8000
    placeholder_ok = not re.search(
        r"\[[^\]]{1,40}\]|\{\{.*?\}\}|xxxx|lorem ipsum|your name here|\bcompany name\b|\[company\]", tl)
    checks = {"company": company_ok, "jd_skill": skills_ok,
              "length": length_ok, "no_placeholder": placeholder_ok}
    reasons = [k for k, v in checks.items() if not v]
    passed = all(checks.values())
    return passed, round(sum(checks.values()) / len(checks), 4), reasons


def load_cases(path: Path = CASES_PATH) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


# --------------------------------------------------------------------------- #
# Results
# --------------------------------------------------------------------------- #
@dataclass
class CaseResult:
    case_id: str
    expected_band: str
    score: float
    passed: bool
    landed_band: Optional[str] = None
    input_tokens: int = 0
    latency_ms: int = 0
    call_emitted: bool = False
    outcome_emitted: bool = False
    skipped: bool = False


@dataclass
class RunSummary:
    workflow: str
    run_id: str
    mode: str
    total: int = 0
    passed: int = 0
    skipped: int = 0
    per_band_total: Counter = field(default_factory=Counter)
    per_band_passed: Counter = field(default_factory=Counter)
    scores: list = field(default_factory=list)
    total_input_tokens: int = 0
    calls_emitted: int = 0
    outcomes_emitted: int = 0
    telemetry_enabled: bool = False


# --------------------------------------------------------------------------- #
# Telemetry plumbing
# --------------------------------------------------------------------------- #
def _build_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from src.db.models import Base

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _build_meter(dry_run: bool):
    if dry_run:
        return None
    if not (os.getenv("MARGIN_INGEST_URL") and os.getenv("MARGIN_INGEST_KEY")):
        return None
    try:
        from margin_meter import MarginMeter
        return MarginMeter(timeout=2.0)
    except Exception:
        return None


class _RetagMeter:
    """Wraps the real meter so the app's in-request record_call (src/llm.py) is re-tagged to THIS
    workflow_id + eval session_id — turning the app's own cost telemetry into correctly-attributed
    eval cost. record_outcome is a no-op here (the runner emits the graded outcome itself)."""

    def __init__(self, real, workflow_id: str, session_id: str, sink: list):
        self._real, self._wf, self._sid, self._sink = real, workflow_id, session_id, sink

    def record_call(self, **kw):  # pragma: no cover - live-only (needs a key)
        kw["workflow_id"] = self._wf
        kw["session_id"] = self._sid
        r = self._real.record_call(**kw)
        self._sink.append((int(kw.get("input_tokens", 0) or 0), bool(getattr(r, "ok", False))))
        return r

    def record_outcome(self, **kw):  # pragma: no cover
        return None


def _emit_outcome(meter, workflow_id, run_id, passed, quality_score, method, res, case_id):
    if meter is None:
        return
    try:
        r = meter.record_outcome(workflow_id=workflow_id, passed=passed,
                                 quality_score=round(quality_score, 4),
                                 quality_method=method, link=f"eval:{run_id}")
        res.outcome_emitted = bool(getattr(r, "ok", False))
        if not res.outcome_emitted:
            print(f"  [warn] outcome emit not ok for {case_id}: {getattr(r, 'error', r)}",
                  file=sys.stderr)
    except Exception as exc:
        print(f"  [warn] outcome emit raised for {case_id}: {exc}", file=sys.stderr)


# --------------------------------------------------------------------------- #
# Per-workflow runners
# --------------------------------------------------------------------------- #
def run_one_fit(ctx, case, meter, run_id, use_embeddings):
    from src.db.models import JobPosting, User, UserTier

    db, scorer, bands = ctx["db"], ctx["scorer"], ctx["bands"]
    u = User(email=f"eval-{run_id}-{case['id']}@example.com", password_hash="x",
             tier=UserTier.FREE, resume_text=case["resume_text"])
    db.add(u)
    db.flush()
    j = JobPosting(user_id=u.id, title=case["job_title"], company_name="Acme",
                   description=case["job_description"], requirements=case.get("job_requirements", ""))
    db.add(j)
    db.flush()

    input_tokens = latency_ms = 0
    if use_embeddings and scorer.client is not None:  # pragma: no cover - live-only
        try:
            t0 = time.perf_counter()
            u.resume_embedding = scorer.get_embedding(u.resume_text)
            jt = f"Title: {j.title}\n{j.description}\n{j.requirements}"
            j.jd_embedding = scorer.get_embedding(jt)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            db.flush()
        except Exception as exc:
            print(f"  [warn] embedding failed for {case['id']}: {exc}; heuristic", file=sys.stderr)
            use_embeddings = False

    sc = scorer.score_job(j, u, use_embeddings=use_embeddings)
    score = float(sc.overall_score)
    passed, landed = grade(case["expected_band"], score, bands)
    res = CaseResult(case["id"], case["expected_band"], score, passed, landed,
                     input_tokens=input_tokens, latency_ms=latency_ms)
    _emit_outcome(meter, FIT_WORKFLOW_ID, run_id, passed, score / 100.0, "eval-band-grader",
                  res, case["id"])
    return res


def _new_job(db, case):
    from src.db.models import JobPosting
    j = JobPosting(user_id=None, title=case.get("role", "Engineer"),
                   company_name=case.get("company", "Acme"),
                   description=case.get("job_description", case.get("role", "")),
                   requirements=case.get("requirements", case.get("job_requirements", "")))
    db.add(j)
    db.flush()
    return j


def run_one_mock(ctx, case, meter, run_id, use_llm):  # pragma: no cover - live-only
    if not use_llm or ctx["llm"] is None:
        return CaseResult(case["id"], case["expected_band"], 0.0, False, skipped=True)
    import src.llm as llm_mod
    sink = []
    prev = llm_mod._meter
    if meter is not None:
        llm_mod._meter = _RetagMeter(meter, MOCK_WORKFLOW_ID, f"eval:{run_id}", sink)
    try:
        job = _new_job(ctx["db"], case)
        result = ctx["llm"].score_mock_interview_answer(job, case["question"], case["answer"])
        overall = float(result["overall"])
    finally:
        llm_mod._meter = prev
    passed, landed = grade(case["expected_band"], overall, MOCK_BANDS)
    res = CaseResult(case["id"], case["expected_band"], overall, passed, landed)
    res.input_tokens = sum(t for t, _ in sink)
    res.call_emitted = any(ok for _, ok in sink)
    _emit_outcome(meter, MOCK_WORKFLOW_ID, run_id, passed, overall / 100.0,
                  "eval-answer-score", res, case["id"])
    return res


def run_one_cover(ctx, case, meter, run_id, use_llm):  # pragma: no cover - live-only
    if not use_llm or ctx["llm"] is None:
        return CaseResult(case["id"], case.get("expected_band", "valid"), 0.0, False, skipped=True)
    from src.db.models import User, UserTier
    import src.llm as llm_mod
    sink = []
    prev = llm_mod._meter
    if meter is not None:
        llm_mod._meter = _RetagMeter(meter, COVER_WORKFLOW_ID, f"eval:{run_id}", sink)
    try:
        db = ctx["db"]
        u = User(email=f"eval-{run_id}-{case['id']}@example.com", password_hash="x",
                 tier=UserTier.PREMIUM, resume_text=case["resume_text"])
        db.add(u)
        db.flush()
        job = _new_job(db, case)
        job.user_id = u.id
        db.flush()
        artifact = ctx["llm"].generate_cover_letter(job, u)
        text = getattr(artifact, "content", "") or ""
    finally:
        llm_mod._meter = prev
    passed, quality, reasons = grade_cover_letter(text, case)
    res = CaseResult(case["id"], case.get("expected_band", "valid"), quality * 100, passed)
    res.input_tokens = sum(t for t, _ in sink)
    res.call_emitted = any(ok for _, ok in sink)
    if not passed:
        print(f"  [grade] cover {case['id']} FAILED: {reasons}", file=sys.stderr)
    _emit_outcome(meter, COVER_WORKFLOW_ID, run_id, passed, quality, "eval-structural", res, case["id"])
    return res


# --------------------------------------------------------------------------- #
# Registry + dispatch
# --------------------------------------------------------------------------- #
@dataclass
class WorkflowSpec:
    slug: str
    workflow_id: str
    cases_file: Path
    requires_llm: bool
    run_one: Callable


WORKFLOWS = {
    "fit-scoring": WorkflowSpec("fit-scoring", FIT_WORKFLOW_ID, CASES_PATH, False, run_one_fit),
    "mock-interview-scoring": WorkflowSpec(
        "mock-interview-scoring", MOCK_WORKFLOW_ID, MOCK_CASES_PATH, True, run_one_mock),
    "cover-letter": WorkflowSpec("cover-letter", COVER_WORKFLOW_ID, COVER_CASES_PATH, True, run_one_cover),
}


def run_workflow(spec, meter, run_id, use_embeddings, use_llm, limit, max_llm) -> RunSummary:
    from src.ranking.scorer import JobScorer
    from src.enrichment.llm_workflows import LLMWorkflows
    from src.llm import get_llm_client
    import src.ranking.scorer as scorer_mod
    import src.llm as llm_mod

    # The runner is the SOLE emitter: silence the in-app auto-emit so an eval batch never fires an
    # ungraded, session-less outcome from inside score_job (chat cost is re-tagged per case instead).
    scorer_mod._meter = None
    llm_mod._meter = None

    cases = load_cases(spec.cases_file)
    if limit:
        cases = cases[:limit]

    llm_active = use_llm and get_llm_client() is not None
    if spec.requires_llm and llm_active and max_llm and len(cases) > max_llm:
        print(f"[info] cost cap: {spec.slug} first {max_llm}/{len(cases)} cases against the paid API",
              file=sys.stderr)
        cases = cases[:max_llm]

    db = _build_session()
    ctx = {"db": db}
    if not spec.requires_llm:
        sc = JobScorer(db)
        sc._eval_bands = None
        ctx.update(scorer=sc, bands=load_bands())
    ctx["llm"] = LLMWorkflows(db) if (spec.requires_llm and llm_active) else None

    mode = ("embeddings" if (spec.slug == "fit-scoring" and use_embeddings and ctx.get("scorer")
            and ctx["scorer"].client) else ("llm" if (spec.requires_llm and llm_active) else "heuristic"))
    s = RunSummary(workflow=spec.slug, run_id=run_id, mode=mode, telemetry_enabled=meter is not None)
    for case in cases:
        if spec.requires_llm:
            res = spec.run_one(ctx, case, meter, run_id, llm_active)
        else:
            res = spec.run_one(ctx, case, meter, run_id, use_embeddings)
        s.total += 1
        if res.skipped:
            s.skipped += 1
            continue
        s.per_band_total[res.expected_band] += 1
        if res.passed:
            s.passed += 1
            s.per_band_passed[res.expected_band] += 1
        s.scores.append(res.score)
        s.total_input_tokens += res.input_tokens
        s.calls_emitted += int(res.call_emitted)
        s.outcomes_emitted += int(res.outcome_emitted)
    return s


def _print_summary(s: RunSummary):
    graded = s.total - s.skipped
    print("")
    print(f"== margin_eval — {s.workflow} (id={WORKFLOWS[s.workflow].workflow_id}) ==")
    print(f"run_id={s.run_id}  mode={s.mode}  session=eval:{s.run_id}")
    if s.skipped:
        print(f"SKIPPED {s.skipped}/{s.total} (LLM-only workflow, no GEMINI_API_KEY)")
    if graded:
        print(f"graded={graded}  passed={s.passed}  accuracy={s.passed / graded * 100:.1f}%")
        for band in ("strong", "partial", "weak", "mismatch", "valid"):
            tot = s.per_band_total.get(band, 0)
            if tot:
                pas = s.per_band_passed.get(band, 0)
                print(f"  {band:9} {pas:>2}/{tot:<2} ({pas / tot * 100:5.1f}%)")
        if s.scores:
            print(f"score distribution: {dict(sorted(Counter(round(x) for x in s.scores).items()))}")
    print(f"telemetry={'ENABLED' if s.telemetry_enabled else 'DISABLED'}"
          f"  calls_emitted={s.calls_emitted}  outcomes_emitted={s.outcomes_emitted}"
          f"  total_input_tokens={s.total_input_tokens}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Margin cost-per-outcome eval for JobScraper AI workflows")
    ap.add_argument("--workflow", default="all",
                    choices=list(WORKFLOWS) + ["all"], help="which workflow suite to run")
    ap.add_argument("--limit", type=int, default=0, help="cap cases per workflow (0 = all)")
    ap.add_argument("--embeddings", action="store_true",
                    help="fit-scoring: use REAL Gemini embeddings (meters real cost)")
    ap.add_argument("--max-llm-cases", type=int, default=40,
                    help="cost cap: max cases/workflow against the paid LLM API")
    ap.add_argument("--model", default=None, help="override GEMINI_MODEL")
    ap.add_argument("--embedding-model", default=None, help="override GEMINI_EMBEDDING_MODEL")
    ap.add_argument("--run-id", default=None, help="batch id (default: random)")
    ap.add_argument("--dry-run", action="store_true", help="score + grade + print; emit nothing")
    args = ap.parse_args(argv)

    if args.model:
        os.environ["GEMINI_MODEL"] = args.model
    if args.embedding_model:
        os.environ["GEMINI_EMBEDDING_MODEL"] = args.embedding_model

    run_id = args.run_id or uuid.uuid4().hex[:12]
    meter = _build_meter(args.dry_run)
    use_llm = bool(os.getenv("GEMINI_API_KEY"))
    slugs = list(WORKFLOWS) if args.workflow == "all" else [args.workflow]

    for slug in slugs:
        spec = WORKFLOWS[slug]
        s = run_workflow(spec, meter, run_id, args.embeddings, use_llm,
                         args.limit, args.max_llm_cases)
        _print_summary(s)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
