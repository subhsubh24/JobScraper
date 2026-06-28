# PROPOSED CI — make the loop's quality gates REQUIRED checks

**Status:** STAGED. The autonomous loop authored everything here but **cannot push
`.github/`** (a workflow-scope, sensitive-file action that hangs the headless run). An owner
or an interactive workflow-scope session must apply the workflow file and mark the checks
required. Until then, the gates run locally / in the routine but do **not** block auto-merge.

**Why:** today a PR auto-merges on `gh pr merge --admin` without CI enforcing the gate, so a
BUILDS≠WORKS / lint-failing change *could* slip in. This resolves loop-health harness
proposal **"gates not enforced in CI"** (mirrors what GroceryManager shipped; adapted to this
Python + Next.js + Expo stack).

---

## What the loop already did (shipped through the normal gate)
- Browser-level **functional journey suite**: `web/e2e/core-journey.spec.ts` +
  `web/playwright.config.ts`. Boots a running Next.js build + a running FastAPI backend +
  a seeded throwaway SQLite DB and asserts the **outcome renders** — signup → working
  dashboard (no dead-end) → add job → **the fit SCORE (core-product output) renders as a
  real number** → job detail. Self-seeds (fresh account per run). Verified GREEN locally.
- In-process API journey suite (`tests/journeys/`) already asserts outcomes against a seeded
  throwaway DB (90 tests; gated by `preflight.sh`).
- **Lint at zero warnings**: `web` lint is now `eslint --max-warnings=0`; mobile + flake8
  already clean.
- **Route/flow inventory**: `docs/ci/ROUTE_INVENTORY.md`.
- **Test-only rate-limit bypass** (`E2E_DISABLE_RATE_LIMIT`) wired into `asgi.py`, **hard-
  refused on Vercel** (`_assert_required_secrets` raises if it's ever set in prod;
  regression test in `tests/test_hardening.py`).

## OWNER STEPS (apply the staged config)
1. **Add the workflow** below as `.github/workflows/ci.yml` (needs `workflow` scope — that's
   why the loop can't push it).
2. **Verify it goes GREEN** on a PR first — run the workflow on an open PR and confirm both
   jobs pass. **Do NOT mark a red/flaky check required** (that would block the loop).
3. **Mark the checks required**: repo → Settings → Branches → branch protection for `main` →
   *Require status checks to pass before merging* → add:
   - `preflight (lint + typecheck + tests)`
   - `functional journeys (web E2E)`
   Equivalent via API:
   ```bash
   gh api -X PUT repos/{owner}/JobScraper/branches/main/protection/required_status_checks \
     -f strict=true \
     -f 'checks[][context]=preflight (lint + typecheck + tests)' \
     -f 'checks[][context]=functional journeys (web E2E)'
   ```
4. Close the linked `loop: harness improvement proposal` issue once both checks are required
   and green. Flip `enforced_in_ci` once true (see LOOP_HEALTH / loop-memory).

## Two gotchas carried forward (so the first run is green)
- **(a) `NEXT_PUBLIC_*` is baked at BUILD time in Next.js.** The web app reads the API origin
  from `NEXT_PUBLIC_API_URL`; it must be set when `next build` runs, not at start. The
  workflow builds with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`. (No next-auth here — auth
  is Bearer-JWT in localStorage, so there's no trusted-host callback to configure; pointing
  the build at the local API is the equivalent knob.)
- **(b) One CI runner replays every journey from ONE IP → trips the per-IP rate limiter.** The
  API server is started by `playwright.config.ts` with `E2E_DISABLE_RATE_LIMIT=1` (test-only).
  Production NEVER sets it, and `asgi.py` refuses to boot if it sees it on Vercel.

---

## `.github/workflows/ci.yml` (copy verbatim)

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]

jobs:
  preflight-ci:
    name: preflight (lint + typecheck + tests)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: npm
          cache-dependency-path: |
            web/package-lock.json
            mobile/package-lock.json
      - run: cd web && npm ci
      - run: cd mobile && npm ci
      - run: bash scripts/preflight.sh ci

  functional-journeys:
    name: functional journeys (web E2E)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: npm
          cache-dependency-path: web/package-lock.json
      - run: cd web && npm ci
      - name: Install Playwright browser
        run: cd web && npx playwright install --with-deps chromium
      - name: Build web (GOTCHA a — NEXT_PUBLIC_API_URL baked at build time)
        run: cd web && NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run build
      - name: Run functional journeys
        # GOTCHA b — the API server (started by playwright.config.ts) gets the test-only
        # E2E_DISABLE_RATE_LIMIT=1 so the single-runner IP does not trip the limiter.
        # Prod never sets it; asgi.py refuses to boot with it on Vercel.
        run: cd web && CI=1 npm run e2e
      - name: Upload report + screenshots
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-and-screenshots
          path: |
            web/playwright-report/
            web/e2e/__screenshots__/
          retention-days: 14
```

## Required-checks list (for branch protection)
- `preflight (lint + typecheck + tests)`
- `functional journeys (web E2E)`
