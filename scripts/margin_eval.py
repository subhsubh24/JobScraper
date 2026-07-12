#!/usr/bin/env python3
"""Repo-specific eval runner: statistical cost-per-outcome for `jobscraper-fit-scoring`.

Runs a representative INPUT MATRIX (evals/margin/fit_scoring_cases.jsonl) of diverse
job+candidate pairs across the full fit spectrum through the REAL scoring path
(`JobScorer.score_job`), grades each result against its expected fit band, and emits real
CALLS + graded OUTCOMES to Margin via the published `margin-meter` SDK. This is what gives
Margin an accurate, statistically-grounded cost-per-outcome for JobScraper's fit scoring —
not a single hand-picked request.

Two modes:
  * HEURISTIC (default, key-free): score_job runs locally (semantic baseline 0.5), so there is
    NO third-party LLM call and NO AI cost — an honest zero-cost baseline. Deterministic, so the
    grader is fully CALIBRATED (see evals/margin/bands.json + tests/evals/test_margin_eval_suite.py).
  * EMBEDDINGS (`--embeddings`, needs GEMINI_API_KEY): score_job uses REAL Gemini embeddings for
    the semantic half. The runner meters each embedding call (real tokens -> real cost) so the
    emitted cost-per-outcome reflects the actual paid path. Cost-capped via --max-embed-cases.

Fail-safe by construction:
  * No `margin-meter` / no MARGIN_INGEST_URL+MARGIN_INGEST_KEY -> telemetry is DISABLED; the run
    still scores + grades + prints a summary (emits nothing, no network).
  * No GEMINI_API_KEY -> heuristic mode (never errors on a missing key).
  * Eval batches are tagged session_id="eval:<run-id>" so eval traffic is separable from prod.

NOT run by the keyless CI gate (it is an on-demand / scheduled tool). CI verifies the suite's
integrity + heuristic calibration WITHOUT any network via tests/evals/test_margin_eval_suite.py.

Usage:
  python scripts/margin_eval.py                          # heuristic, dry unless MARGIN_* set
  python scripts/margin_eval.py --dry-run                # score+grade+print, emit nothing
  MARGIN_INGEST_URL=... MARGIN_INGEST_KEY=... python scripts/margin_eval.py
  GEMINI_API_KEY=... python scripts/margin_eval.py --embeddings --max-embed-cases 30
  python scripts/margin_eval.py --embeddings --embedding-model gemini-embedding-001  # config override
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WORKFLOW_ID = "jobscraper-fit-scoring"
CASES_PATH = ROOT / "evals" / "margin" / "fit_scoring_cases.jsonl"
BANDS_PATH = ROOT / "evals" / "margin" / "bands.json"


# --------------------------------------------------------------------------- #
# Grader (importable + reused by the CI test — single source of truth)
# --------------------------------------------------------------------------- #
def load_bands(path: Path = BANDS_PATH) -> dict:
    raw = json.loads(Path(path).read_text())
    return {k: tuple(v) for k, v in raw.items() if not k.startswith("_")}


def band_for_score(score: float, bands: dict) -> Optional[str]:
    """The band whose [lo, hi) window contains ``score`` (None if outside every band)."""
    for name, (lo, hi) in bands.items():
        if lo <= score < hi:
            return name
    return None


def grade(expected_band: str, score: float, bands: dict) -> tuple[bool, Optional[str]]:
    """A case PASSES iff its real fit score lands in its EXPECTED band's window."""
    lo, hi = bands[expected_band]
    landed = band_for_score(score, bands)
    return (lo <= score < hi), landed


def load_cases(path: Path = CASES_PATH) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


# --------------------------------------------------------------------------- #
# Scoring (real path) + metered embeddings
# --------------------------------------------------------------------------- #
@dataclass
class CaseResult:
    case_id: str
    expected_band: str
    score: float
    passed: bool
    landed_band: Optional[str]
    input_tokens: int = 0
    latency_ms: int = 0
    call_emitted: bool = False
    outcome_emitted: bool = False


@dataclass
class RunSummary:
    run_id: str
    mode: str
    total: int = 0
    passed: int = 0
    per_band_total: Counter = field(default_factory=Counter)
    per_band_passed: Counter = field(default_factory=Counter)
    scores: list = field(default_factory=list)
    total_input_tokens: int = 0
    calls_emitted: int = 0
    outcomes_emitted: int = 0
    telemetry_enabled: bool = False


def _metered_embedding(scorer, meter, text, run_id):  # pragma: no cover - live-only (needs a key)
    """Embed ``text`` via the real client; return (vector, prompt_tokens, latency_ms)."""
    t0 = time.perf_counter()
    resp = scorer.client.embeddings.create(model=scorer.EMBEDDING_MODEL, input=text[:8000])
    latency_ms = int((time.perf_counter() - t0) * 1000)
    usage = getattr(resp, "usage", None)
    tokens = int(getattr(usage, "prompt_tokens", 0) or getattr(usage, "total_tokens", 0) or 0)
    return resp.data[0].embedding, tokens, latency_ms


def score_case(db, case, scorer, use_embeddings, meter, run_id):
    """Run ONE case through the real score_job, grade it, emit call+outcome. Fail-safe."""
    from src.db.models import JobPosting, User, UserTier

    bands = scorer._eval_bands
    u = User(email=f"eval-{run_id}-{case['id']}@example.com", password_hash="x",
             tier=UserTier.FREE, resume_text=case["resume_text"])
    db.add(u)
    db.flush()
    j = JobPosting(user_id=u.id, title=case["job_title"], company_name="Acme",
                   description=case["job_description"], requirements=case.get("job_requirements", ""))
    db.add(j)
    db.flush()

    input_tokens = 0
    latency_ms = 0
    if use_embeddings and scorer.client is not None:  # pragma: no cover - live-only
        try:
            r_vec, r_tok, r_ms = _metered_embedding(scorer, meter, u.resume_text, run_id)
            jd_text = f"Title: {j.title}\n{j.description}\n{j.requirements}"
            j_vec, j_tok, j_ms = _metered_embedding(scorer, meter, jd_text, run_id)
            u.resume_embedding = r_vec  # cached -> score_job reuses, no extra API call
            j.jd_embedding = j_vec
            db.flush()
            input_tokens = r_tok + j_tok
            latency_ms = r_ms + j_ms
        except Exception as exc:
            print(f"  [warn] embedding failed for {case['id']}: {exc}; heuristic fallback",
                  file=sys.stderr)
            use_embeddings = False

    sc = scorer.score_job(j, u, use_embeddings=use_embeddings)
    score = float(sc.overall_score)
    passed, landed = grade(case["expected_band"], score, bands)

    res = CaseResult(case_id=case["id"], expected_band=case["expected_band"], score=score,
                     passed=passed, landed_band=landed, input_tokens=input_tokens,
                     latency_ms=latency_ms)

    if meter is not None:
        session = f"eval:{run_id}"
        # Emit the real AI COST (embeddings mode only — heuristic mode has no LLM call).
        # record_call carries the batch on session_id (supported on calls).
        if input_tokens > 0:  # pragma: no cover - live-only
            try:
                r = meter.record_call(workflow_id=WORKFLOW_ID, provider="google",
                                      model=scorer.EMBEDDING_MODEL, input_tokens=input_tokens,
                                      output_tokens=0, cache_read_tokens=0, latency_ms=latency_ms,
                                      status="ok", session_id=session)
                res.call_emitted = bool(getattr(r, "ok", False))
                if not res.call_emitted:
                    print(f"  [warn] call emit not ok for {case['id']}: {getattr(r, 'error', r)}",
                          file=sys.stderr)
            except Exception as exc:
                print(f"  [warn] call emit raised for {case['id']}: {exc}", file=sys.stderr)
        # Emit the GRADED outcome (both modes): quality = the real fit score, passed = in-band.
        # The batch id rides on `link` — record_outcome has no session_id in the SDK surface.
        try:
            r = meter.record_outcome(workflow_id=WORKFLOW_ID, passed=passed,
                                     quality_score=round(score / 100.0, 4),
                                     quality_method="eval-band-grader", link=session)
            res.outcome_emitted = bool(getattr(r, "ok", False))
            if not res.outcome_emitted:
                print(f"  [warn] outcome emit not ok for {case['id']}: {getattr(r, 'error', r)}",
                      file=sys.stderr)
        except Exception as exc:
            print(f"  [warn] outcome emit raised for {case['id']}: {exc}", file=sys.stderr)
    return res


# --------------------------------------------------------------------------- #
# Runner
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
    """A configured MarginMeter, or None (telemetry disabled) — never raises."""
    if dry_run:
        return None
    have_env = bool(os.getenv("MARGIN_INGEST_URL")) and bool(os.getenv("MARGIN_INGEST_KEY"))
    if not have_env:
        return None
    try:
        from margin_meter import MarginMeter
    except Exception:
        return None
    try:
        return MarginMeter(timeout=2.0)
    except Exception:
        return None


def run(cases, use_embeddings, meter, run_id, mode) -> tuple[RunSummary, list]:
    from src.ranking.scorer import JobScorer
    import src.ranking.scorer as scorer_mod
    import src.llm as llm_mod

    # The runner is the SOLE emitter: disable the in-app auto-emit so an eval batch does not
    # ALSO fire an ungraded, session-less outcome from inside score_job (no double counting).
    scorer_mod._meter = None
    llm_mod._meter = None

    db = _build_session()
    scorer = JobScorer(db)
    scorer._eval_bands = load_bands()

    summary = RunSummary(run_id=run_id, mode=mode, telemetry_enabled=meter is not None)
    results = []
    for case in cases:
        res = score_case(db, case, scorer, use_embeddings, meter, run_id)
        results.append(res)
        summary.total += 1
        summary.per_band_total[res.expected_band] += 1
        if res.passed:
            summary.passed += 1
            summary.per_band_passed[res.expected_band] += 1
        summary.scores.append(res.score)
        summary.total_input_tokens += res.input_tokens
        summary.calls_emitted += int(res.call_emitted)
        summary.outcomes_emitted += int(res.outcome_emitted)
    return summary, results


def _print_summary(s: RunSummary):
    print("")
    print(f"== margin_eval — {WORKFLOW_ID} ==")
    print(f"run_id={s.run_id}  mode={s.mode}  session_id=eval:{s.run_id}")
    print(f"cases={s.total}  passed={s.passed}  accuracy={s.passed / s.total * 100:.1f}%"
          if s.total else "cases=0")
    print("per-band pass rate (grader distinguishes fit quality — not always-pass):")
    for band in ("strong", "partial", "weak", "mismatch"):
        tot = s.per_band_total.get(band, 0)
        pas = s.per_band_passed.get(band, 0)
        if tot:
            print(f"  {band:9} {pas:>2}/{tot:<2}  ({pas / tot * 100:5.1f}%)")
    if s.scores:
        dist = dict(sorted(Counter(round(x) for x in s.scores).items()))
        print(f"score distribution: {dist}")
    print(f"telemetry={'ENABLED' if s.telemetry_enabled else 'DISABLED (no MARGIN_* env / dry-run)'}"
          f"  calls_emitted={s.calls_emitted}  outcomes_emitted={s.outcomes_emitted}"
          f"  total_input_tokens={s.total_input_tokens}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Margin cost-per-outcome eval for jobscraper-fit-scoring")
    ap.add_argument("--cases", default=str(CASES_PATH), help="path to the case matrix (jsonl)")
    ap.add_argument("--limit", type=int, default=0, help="cap total cases (0 = all)")
    ap.add_argument("--embeddings", action="store_true",
                    help="use REAL Gemini embeddings (needs GEMINI_API_KEY) — meters real cost")
    ap.add_argument("--max-embed-cases", type=int, default=40,
                    help="cost cap: max cases to run against the paid embedding API")
    ap.add_argument("--model", default=None, help="override GEMINI_MODEL (config re-run)")
    ap.add_argument("--embedding-model", default=None, help="override GEMINI_EMBEDDING_MODEL")
    ap.add_argument("--run-id", default=None, help="batch id (default: random); tags session_id")
    ap.add_argument("--dry-run", action="store_true", help="score + grade + print; emit nothing")
    args = ap.parse_args(argv)

    if args.model:
        os.environ["GEMINI_MODEL"] = args.model
    if args.embedding_model:
        os.environ["GEMINI_EMBEDDING_MODEL"] = args.embedding_model

    run_id = args.run_id or uuid.uuid4().hex[:12]
    cases = load_cases(Path(args.cases))
    if args.limit:
        cases = cases[: args.limit]

    use_embeddings = args.embeddings and bool(os.getenv("GEMINI_API_KEY"))
    if args.embeddings and not use_embeddings:
        print("[info] --embeddings requested but GEMINI_API_KEY is unset -> heuristic mode",
              file=sys.stderr)
    if use_embeddings and args.max_embed_cases and len(cases) > args.max_embed_cases:
        print(f"[info] cost cap: running first {args.max_embed_cases} of {len(cases)} cases "
              f"against the paid embedding API", file=sys.stderr)
        cases = cases[: args.max_embed_cases]

    mode = "embeddings" if use_embeddings else "heuristic"
    meter = _build_meter(args.dry_run)
    summary, _ = run(cases, use_embeddings, meter, run_id, mode)
    _print_summary(summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
