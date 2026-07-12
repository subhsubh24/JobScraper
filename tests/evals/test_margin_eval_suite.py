"""CI guard for the Margin cost-per-outcome eval suite (scripts/margin_eval.py).

Runs KEY-FREE and NETWORK-FREE (conftest blanks GEMINI_API_KEY), so it belongs in the normal
per-PR gate — it makes NO Gemini call. It pins three properties the on-demand runner relies on:

  1. The case matrix is well-formed + balanced across the full fit spectrum.
  2. The grader is CALIBRATED: every case's REAL deterministic heuristic fit score
     (score_job with embeddings off) lands in its assigned band window.
  3. The grader is GENUINE, not always-pass: a degenerate constant scorer would MISGRADE the
     strong and mismatch cases (so passing the suite actually means the scorer separates fits).

The live, metered embeddings path (real Gemini cost -> real cost-per-outcome) is exercised
on demand, never here — see evals/margin/README.md.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from src.db.models import JobPosting, User, UserTier
from src.ranking.scorer import JobScorer

ROOT = Path(__file__).resolve().parents[2]

# Import the runner module (scripts/ is not a package) to reuse its grader — one source of truth.
_spec = importlib.util.spec_from_file_location("margin_eval", ROOT / "scripts" / "margin_eval.py")
margin_eval = importlib.util.module_from_spec(_spec)
sys.modules["margin_eval"] = margin_eval
_spec.loader.exec_module(margin_eval)

CASES = margin_eval.load_cases()
BANDS = margin_eval.load_bands()
BAND_NAMES = ("strong", "partial", "weak", "mismatch")


def _real_heuristic_score(db, case) -> float:
    u = User(email=f"suite-{case['id']}@example.com", password_hash="x",
             tier=UserTier.FREE, resume_text=case["resume_text"])
    db.add(u)
    db.flush()
    j = JobPosting(user_id=u.id, title=case["job_title"], company_name="Acme",
                   description=case["job_description"], requirements=case.get("job_requirements", ""))
    db.add(j)
    db.flush()
    return float(JobScorer(db).score_job(j, u, use_embeddings=False).overall_score)


# --- 1. structure -------------------------------------------------------------------- #
def test_case_matrix_is_wellformed_and_balanced():
    assert len(CASES) >= 40, "want a representative matrix (>=40 cases)"
    from collections import Counter
    per_band = Counter(c["expected_band"] for c in CASES)
    assert set(per_band) == set(BAND_NAMES), "all four fit bands must be represented"
    # Balanced enough to be statistically meaningful per band.
    assert min(per_band.values()) >= 10
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids)), "case ids must be unique"
    required = {"id", "expected_band", "job_title", "job_description", "resume_text"}
    for c in CASES:
        assert required <= set(c), f"case {c.get('id')} missing fields"
    # Genuine variety, not one role/industry repeated.
    assert len({c["role"] for c in CASES}) >= 8
    assert len({c["industry"] for c in CASES}) >= 6


def test_bands_are_nonoverlapping_and_ordered():
    windows = [(BANDS[b][0], BANDS[b][1]) for b in BAND_NAMES]
    for name, (lo, hi) in BANDS.items():
        assert lo < hi, f"{name} window is empty"
    # mismatch < weak < partial < strong, non-overlapping.
    order = sorted(windows)
    for (lo1, hi1), (lo2, hi2) in zip(order, order[1:]):
        assert hi1 <= lo2, "band windows must not overlap"


# --- 2. calibration (real scorer, deterministic, key-free) --------------------------- #
def test_no_gemini_key_so_this_runs_network_free(db_session):
    # conftest blanks GEMINI_API_KEY -> the scorer's client is None -> pure heuristic, no calls.
    assert JobScorer(db_session).client is None


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_every_case_lands_in_its_expected_band(db_session, case):
    score = _real_heuristic_score(db_session, case)
    passed, landed = margin_eval.grade(case["expected_band"], score, BANDS)
    assert passed, (f"{case['id']}: real heuristic score {score} landed in {landed!r}, "
                    f"expected {case['expected_band']} {BANDS[case['expected_band']]}")


# --- 3. genuineness (the grader is not always-pass) ---------------------------------- #
def test_grader_distinguishes_good_from_bad():
    # A degenerate scorer that returns a constant 50 for EVERY case must fail the whole
    # strong and mismatch cohorts — proving the grader actually measures fit quality.
    const = 50.0
    strong = [c for c in CASES if c["expected_band"] == "strong"]
    mismatch = [c for c in CASES if c["expected_band"] == "mismatch"]
    assert all(not margin_eval.grade(c["expected_band"], const, BANDS)[0] for c in strong)
    assert all(not margin_eval.grade(c["expected_band"], const, BANDS)[0] for c in mismatch)
    # And it is not trivially fail-all: the true band's own midpoint passes.
    for band, (lo, hi) in BANDS.items():
        mid = (lo + min(hi, 100.0)) / 2
        assert margin_eval.grade(band, mid, BANDS)[0]


def test_band_for_score_maps_correctly():
    assert margin_eval.band_for_score(70.0, BANDS) == "strong"
    assert margin_eval.band_for_score(50.0, BANDS) == "partial"
    assert margin_eval.band_for_score(40.0, BANDS) == "weak"
    assert margin_eval.band_for_score(30.0, BANDS) == "mismatch"
