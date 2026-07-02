#!/usr/bin/env bash
# preflight.sh — Career Operator readiness gate.
#
# Two modes:
#   ./scripts/preflight.sh ci    -> MECHANICAL per-change gate (must be green to merge):
#                                   backend deps+lint+test+import smoke, mobile tsc+lint.
#   ./scripts/preflight.sh       -> FULL readiness gate (must be green to SUBMIT):
#                                   ci gate + YAML invariants + journey suite green +
#                                   store audit zero FAILs + billing wired + security
#                                   mechanisms + DoD all [x] + business-case floor met.
#
# Exits non-zero on the FIRST gap. Honest by design: the full gate is RED until the
# product is actually done — that is the correct pre-launch state.
set -uo pipefail
cd "$(dirname "$0")/.."

# --- FACTORY_STANDARD §22: computation-integrity gate (fail-safe; vacuous until analysis/figures.json has entries) ---
if [ -f scripts/validate-computation.mjs ] && ! node scripts/validate-computation.mjs; then
  echo "PREFLIGHT FAIL: validate-computation (§22) — a committed figure is mis-computed or non-reproducible." >&2
  exit 1
fi
MODE="${1:-full}"
PY="${PYTHON:-python3}"

fail() { echo "PREFLIGHT FAIL: $*" >&2; exit 1; }
ok()   { echo "  ok: $*"; }
sect() { echo ""; echo "== $* =="; }

# ---------------------------------------------------------------------------
# MECHANICAL GATE (ci)
# ---------------------------------------------------------------------------
sect "backend: dependencies importable"
$PY -c "import fastapi, sqlalchemy, pydantic" 2>/dev/null || fail "backend deps not importable (pip install -r requirements.txt)"
ok "core backend deps import"

sect "backend: lint (flake8)"
if command -v flake8 >/dev/null 2>&1; then
  flake8 . || fail "flake8 reported issues"
  ok "flake8 clean"
else
  fail "flake8 not installed (in requirements.txt)"
fi

sect "backend: import/serve smoke"
$PY -c "import asgi; assert hasattr(asgi, 'app'), 'asgi.app missing'" || fail "asgi import smoke failed"
ok "asgi:app imports (Vercel Services entrypoint)"

sect "backend: tests (pytest) + coverage floor"
if [ -d tests ]; then
  # Enforce the coverage floor when pytest-cov is available; fall back to a plain run
  # otherwise so the gate still works without the plugin. The threshold lives ONLY in
  # setup.cfg ([coverage:report] fail_under) — coverage.py reads it automatically, so there
  # is no duplicated number here to drift out of sync.
  # `-m "not live"`: skip the REAL external-API tests (Gemini/Stripe) per-PR — they run
  # NIGHTLY (.github/workflows/nightly.yml) so PRs stay fast + make no live calls. The
  # deterministic evals still run here.
  if $PY -c "import pytest_cov" >/dev/null 2>&1; then
    $PY -m pytest -q -m "not live" --cov --cov-report=term-missing tests \
      || fail "pytest failed or coverage below the setup.cfg floor"
    ok "pytest green + coverage floor met (setup.cfg)"
  else
    $PY -m pytest -q -m "not live" tests || fail "pytest failed"
    ok "pytest green (coverage skipped: pytest-cov not installed)"
  fi
else
  fail "no tests/ directory"
fi

sect "mobile: present + typecheck"
if [ -d mobile ] && [ -f mobile/package.json ]; then
  if [ ! -d mobile/node_modules ]; then
    echo "  (mobile/node_modules missing — run: cd mobile && npm install)"
    fail "mobile deps not installed"
  fi
  ( cd mobile && npx tsc --noEmit ) || fail "mobile tsc --noEmit failed"
  ok "mobile tsc clean"
  if [ -f mobile/node_modules/.bin/eslint ]; then
    ( cd mobile && npm run -s lint ) || fail "mobile lint failed"
    ok "mobile lint clean"
  fi
  # Component/integration tests (jest-expo). Headless, no native build — guards that the
  # screens/components actually render their intended output (BUILDS != WORKS for mobile).
  # jest is a declared devDependency, so its ABSENCE is a gate FAILURE, never a silent skip
  # (unlike the optional eslint guard above).
  if [ -f mobile/node_modules/.bin/jest ]; then
    ( cd mobile && npx jest --ci --silent ) || fail "mobile jest tests failed"
    ok "mobile jest green"
  else
    fail "mobile jest not installed (declared devDep — run: cd mobile && npm ci)"
  fi
else
  fail "mobile/ Expo app missing (package.json)"
fi

sect "web: present + typecheck + lint (Next.js)"
if [ -d web ] && [ -f web/package.json ]; then
  if [ ! -d web/node_modules ]; then
    echo "  (web/node_modules missing — run: cd web && npm install)"
    fail "web deps not installed"
  fi
  ( cd web && npx tsc --noEmit ) || fail "web tsc --noEmit failed"
  ok "web tsc clean"
  ( cd web && npm run -s lint ) || fail "web lint failed"
  ok "web lint clean"
else
  fail "web/ Next.js app missing (package.json)"
fi

sect "source tracked in git (no gitignored-source foot-gun)"
# A local gate passes even when source is gitignored (files exist on disk) but a fresh
# clone / Vercel build fails. Assert critical source dirs actually have tracked files.
for d in web/lib web/app web/components mobile/src src; do
  [ "$(git ls-files "$d" | head -1)" != "" ] || fail "no tracked files under $d (gitignore foot-gun? deploy will fail)"
done
ok "web + mobile + backend source is tracked"

sect "visual-verification honest-tick guard"
# If the dual-axis visual-verification box is ticked, there MUST be real committed
# screenshots. No-op while it's [ ] so it never blocks current runs. (Completeness +
# the dual-axis verdict are enforced by the deep audit + readiness auditors; this guard
# just kills the egregious fake-tick.)
if grep -qE '^- \[x\] \*\*Visual verification' ROADMAP.md; then
  shots=$(find web/e2e/__screenshots__ mobile/__screenshots__ -type f \
            \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' \) -size +0c 2>/dev/null | wc -l | tr -d ' ')
  [ "${shots:-0}" -ge 5 ] || fail "Visual-verification box is [x] but only ${shots:-0} committed non-zero screenshots (<5) — capture them or un-tick the box"
  ok "visual-verification screenshots present ($shots)"
else
  ok "visual-verification not yet ticked — guard skipped (no-op)"
fi

sect "quality scorecard parse guard (auditor-owned; we never author it)"
$PY scripts/check_quality.py parse || fail "QUALITY_SCORECARD malformed"

sect "self-validation manifest (every external dep declared + validatable)"
$PY scripts/check_validation.py || fail "self-validation gate failed (see docs/ci/VALIDATION.md)"

sect "GTM honesty gate (no GROWTH_STATUS metric without a connected source)"
$PY scripts/validate_gtm.py || fail "validate-gtm failed (a GTM metric has no source, or GTM_SCORECARD invalid)"

sect "eval coverage (every AI-output module has a deterministic + real-output eval)"
$PY scripts/check_eval_coverage.py || fail "eval-coverage gate failed (see docs/ci/EVAL_COVERAGE.md)"

if [ "$MODE" = "ci" ]; then
  echo ""; echo "PREFLIGHT(ci): mechanical gate GREEN"; exit 0
fi

# ---------------------------------------------------------------------------
# READINESS GATE (full) — these SHOULD fail until the product is actually done.
# ---------------------------------------------------------------------------
sect "self-validation READINESS (no unvalidated capability may ship)"
$PY scripts/check_validation.py --readiness || fail "unvalidated capability (see docs/ci/VALIDATION.md + OWNER_ACTIONs)"

sect "GTM READINESS (graded GTM_SCORECARD, ship-critical dims >= A)"
$PY scripts/validate_gtm.py --readiness || fail "GTM not ready (needs a graded docs/growth/GTM_SCORECARD.md)"

sect "machine-readable YAML blocks"
BLOCK_OUT="$($PY scripts/check_blocks.py)" || fail "YAML block validation failed"
echo "$BLOCK_OUT" | sed 's/^/  /'
FLOOR_MET="$(echo "$BLOCK_OUT" | grep '^floor_met_year1=' | cut -d= -f2)"
ENGINE_PCT="$(echo "$BLOCK_OUT" | grep '^engine_pct=' | cut -d= -f2)"

sect "required rendered store assets (non-placeholder)"
for f in docs/store/assets/icon.png docs/store/assets/feature_graphic.png; do
  [ -s "$f" ] || fail "missing/empty store asset: $f (rendered image required)"
done
ok "store assets present"

sect "distribution/release config (real, artifact-backed)"
[ -f mobile/eas.json ] || fail "mobile/eas.json missing (EAS build+submit profiles)"
$PY -c "import json; d=json.load(open('mobile/eas.json')); assert 'build' in d and 'submit' in d, 'eas.json missing build/submit'" \
  || fail "mobile/eas.json invalid or missing build/submit profiles"
grep -q '"bundleIdentifier"' mobile/app.json || fail "app.json missing iOS bundleIdentifier"
grep -q '"buildNumber"' mobile/app.json || fail "app.json missing iOS buildNumber"
grep -q '"versionCode"' mobile/app.json || fail "app.json missing Android versionCode"
[ -f web/package.json ] && grep -q '"build"' web/package.json || fail "web build command missing"
ok "release/deploy config present"

sect "billing wired (real, not stubs)"
grep -rqs "stripe.checkout.Session.create" . --include=*.py || fail "no real Stripe Checkout call found"
grep -rqs "RevenueCat\|Purchases" mobile/ 2>/dev/null || fail "mobile entitlement (RevenueCat) not wired"
ok "billing wired"

sect "security mechanisms present"
grep -rqs "rate" --include=*.py . || fail "no rate limiting found"
# Per-user/day spend ceiling / circuit breaker (wallet-drain defense — LLM+scrape).
grep -rqiE 'ceiling|spend.?(cap|limit)|circuit.?breaker|daily.?(cap|limit)|quota' --include=*.py . \
  || fail "no per-user/day API spend ceiling — one abuser can run up the paid-API bill"
# Security headers / CORS lockdown (API or web).
grep -rqiE 'X-Content-Type-Options|X-Frame-Options|Strict-Transport-Security|Content-Security-Policy' asgi.py web/ 2>/dev/null \
  || fail "no security headers (X-Content-Type-Options/X-Frame-Options/CSP) found"
# CAPTCHA / bot-protection on public forms (signup/waitlist).
grep -rqiE 'turnstile|hcaptcha|recaptcha|captcha' asgi.py src/ web/ 2>/dev/null \
  || fail "no captcha/bot-protection on public forms"
ok "security mechanisms present"

sect "no stub/placeholder markers on critical paths (BUILDS != WORKS)"
if grep -rniE 'not (yet )?implemented|FIXME|placeholder|\bstub\b|\bTODO\b' asgi.py src --include=*.py \
   | grep -viE 'no .*stub|TODO\(P[0-9]\)'; then
  fail "stub/TODO/placeholder marker on a critical path — 'code exists' is not 'it works'"
fi
ok "no stub markers on critical paths"

sect "runtime FUNCTIONAL journey suite ran green this attempt"
if $PY -m pytest -q tests/journeys >/tmp/journeys.out 2>&1; then
  E2E_JOURNEYS_PASSED=1
  ok "journey suite ran GREEN this attempt"
else
  cat /tmp/journeys.out >&2
  fail "journey suite did not pass this attempt"
fi
[ "${E2E_JOURNEYS_PASSED:-0}" = "1" ] || fail "E2E_JOURNEYS_PASSED != 1"

sect "quality grade (independent auditor): A/A+ ship-critical, >= B elsewhere"
$PY scripts/check_quality.py readiness || fail "quality grade below bar (see docs/quality/QUALITY_SCORECARD.md)"
ok "quality grade meets the bar"

sect "store-acceptance audit: zero open FAILs"
if grep -q "FAIL" docs/store/ACCEPTANCE_AUDIT.md; then
  fail "ACCEPTANCE_AUDIT.md still has open FAILs"
fi
ok "no open FAILs"

sect "business-case floor met"
[ "$FLOOR_MET" = "true" ] || fail "business case floor not met (floor_met_year1=$FLOOR_MET)"
ok "floor met"

sect "growth engine built (engine_pct == 100)"
[ "$ENGINE_PCT" = "100" ] || fail "growth engine not complete (engine_pct=$ENGINE_PCT)"
ok "engine complete"

sect "DoD: every checkbox ticked"
if grep -qE '^\- \[ \]' ROADMAP.md; then
  fail "ROADMAP.md has unticked DoD/track boxes"
fi
ok "all boxes ticked"

echo ""; echo "PREFLIGHT(full): READINESS GATE GREEN — eligible for the auditor gate"
