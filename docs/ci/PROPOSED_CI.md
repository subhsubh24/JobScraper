# PROPOSED CI — make the loop's quality gates REQUIRED checks

**Status:** APPLIED (workflow file). `.github/workflows/ci.yml` was created on 2026-06-28 in an
interactive session at the owner's explicit request. **Still owner-only to finish:** (1) mark
the two gate checks REQUIRED in branch protection (after confirming they're green on a PR), and
(2) the Part B secrets/PITR/stamp/Vercel steps below. Until the checks are *required*, the
workflow runs but does not yet *block* auto-merge.

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

  # PART B — auto-migrate on deploy. Runs ONLY on push to main, ONLY after both gate jobs
  # pass, forward-only (`alembic upgrade head` — NEVER downgrade/reset). See "Part B" below
  # for the safety rails + the one-time baseline stamp the owner must do first.
  migrate:
    name: migrate (alembic upgrade head — main only)
    needs: [preflight-ci, functional-journeys]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - name: Apply forward-only migrations to production
        env:
          # Neon pooled connection string — set as a GitHub Actions SECRET, never inline.
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          if [ -z "$DATABASE_URL" ]; then
            echo "DATABASE_URL secret not set — skipping auto-migrate (see OWNER_ACTION auto-migrate)."
            exit 0
          fi
          alembic upgrade head
```

## Required-checks list (for branch protection)
- `preflight (lint + typecheck + tests)`
- `functional journeys (web E2E)`

(The `migrate` job is NOT a required PR check — it runs post-merge on `main` only. Do not add
it to required checks; PRs never run it.)

---

# Part B — auto-migrate on deploy (`alembic upgrade head`)

**Goal:** schema changes stop being a manual `python scripts/init_db.py` / `db push` after
every model change. The loop adds a migration in the same PR as the model change (enforced by
`tests/test_migrations.py` — see below); once merged, the `migrate` job applies it to
production automatically.

## What the loop already did (shipped through the gate)
- Stood up **real Alembic migrations**: `alembic.ini`, `migrations/env.py` (reads `DATABASE_URL`
  from the env — no committed creds; normalizes `postgres://`), and the initial migration
  `migrations/versions/*_initial_schema.py` (all 10 tables). Verified: `alembic upgrade head`
  on a fresh DB builds the full schema with **zero drift** vs the models.
- **Drift guard in the gate**: `tests/test_migrations.py` fails the build if the models change
  without a matching migration (the "forgot the migration" mistake). This is what makes
  auto-apply safe — a schema that doesn't match the code can't reach `main`.

## Safety rails (auto-applying to prod replaces the manual human checkpoint — apply consciously)
- **Migrations still pass the full gate + 2-reviewer + security review BEFORE merge.** Auto-apply
  only runs on what already cleared review.
- **Default-branch + post-gate only**: `if: push && ref == main` and `needs: [preflight-ci,
  functional-journeys]`. PRs never migrate; a red gate blocks the migrate job.
- **Forward-only**: `alembic upgrade head` only. No downgrade/reset in CI, ever.
- **TRADEOFF (state it to the owner):** this removes the manual schema checkpoint that a human
  `db push` provided. The recoverability net replacing it is **PITR / backups — enable them
  FIRST** (below). A destructive migration that passes review will auto-apply; PITR is how you
  undo it.

## Owner one-time setup (tracked as OWNER_ACTION `auto-migrate`)
1. **Enable Neon PITR / daily backups FIRST** (the recoverability net). Do not enable the job
   until this is on.
2. **Baseline the EXISTING DB** (it was bootstrapped via `create_all`, so the tables already
   exist): run **once** against prod so the initial migration isn't re-applied:
   ```bash
   DATABASE_URL='<neon pooled url>' alembic stamp head
   ```
   (Skip the stamp on a brand-new empty DB — there `alembic upgrade head` creates everything.)
3. **Add the secret**: repo → Settings → Secrets and variables → Actions → `DATABASE_URL` =
   the Neon pooled connection string. (The `migrate` job reads `secrets.DATABASE_URL`.)
4. **Cut over auto-create**: set `AUTO_CREATE_TABLES=0` in the Vercel env so the app stops
   `create_all`-ing on boot and Alembic is the single source of schema truth.
5. Apply the workflow (same `.github/` push as Part A) and confirm the `migrate` job goes
   green on the next push to `main`.

> **Never** put the real `DATABASE_URL` in a commit, an issue, or this file — only in GitHub
> Actions secrets / the Vercel env.
