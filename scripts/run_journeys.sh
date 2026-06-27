#!/usr/bin/env bash
# Run the runtime FUNCTIONAL journey suite locally (BUILDS != WORKS gate).
# On success, prints E2E_JOURNEYS_PASSED=1 (consumed by CI / preflight).
set -uo pipefail
cd "$(dirname "$0")/.."
if python3 -m pytest -q tests/journeys; then
  echo "E2E_JOURNEYS_PASSED=1"
  exit 0
else
  echo "E2E_JOURNEYS_PASSED=0"
  exit 1
fi
