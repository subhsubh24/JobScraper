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
$PY -c "import api; assert hasattr(api, 'app'), 'api.app missing'" || fail "api import smoke failed"
ok "api:app imports"

sect "backend: tests (pytest)"
if [ -d tests ]; then
  $PY -m pytest -q tests || fail "pytest failed"
  ok "pytest green"
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
else
  fail "mobile/ Expo app missing (package.json)"
fi

if [ "$MODE" = "ci" ]; then
  echo ""; echo "PREFLIGHT(ci): mechanical gate GREEN"; exit 0
fi

# ---------------------------------------------------------------------------
# READINESS GATE (full) — these SHOULD fail until the product is actually done.
# ---------------------------------------------------------------------------
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

sect "billing wired (real, not stubs)"
grep -rqs "stripe.checkout.Session.create" . --include=*.py || fail "no real Stripe Checkout call found"
grep -rqs "RevenueCat\|Purchases" mobile/ 2>/dev/null || fail "mobile entitlement (RevenueCat) not wired"
ok "billing wired"

sect "security mechanisms present"
grep -rqs "rate" --include=*.py . || fail "no rate limiting found"
ok "security mechanisms present"

sect "runtime FUNCTIONAL journey suite ran green this attempt"
if $PY -m pytest -q tests/journeys >/tmp/journeys.out 2>&1; then
  E2E_JOURNEYS_PASSED=1
  ok "journey suite ran GREEN this attempt"
else
  cat /tmp/journeys.out >&2
  fail "journey suite did not pass this attempt"
fi
[ "${E2E_JOURNEYS_PASSED:-0}" = "1" ] || fail "E2E_JOURNEYS_PASSED != 1"

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
