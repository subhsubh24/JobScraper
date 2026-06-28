# LOOP MEMORY — Career Operator (cross-run lessons)

Durable lessons for the factory loop. Append dated entries. Keep it honest and short.

---

### 2026-06-27 — Bootstrap lesson
- **The repo wins over assumptions.** The bootstrap charter assumed "Python SaaS, NO
  mobile app." Reality: a **Flutter** prototype existed in `/mobile`. Owner chose to
  re-platform to **Expo/React Native + TypeScript** (matches the apparatus: preflight
  `tsc`, mobile CI). Flutter was moved to `/mobile-flutter-legacy` for reference, not
  deleted blindly. **Always orient against the real tree before building.**
- **BUILDS ≠ WORKS is not theoretical here.** `import api` exits 0, but `api.py` calls
  `AuthService.create_user/generate_token/authenticate_user`, `JobScorer().score_job(job=dict)`,
  `workflows.workflow_company_dossier`, `coach.chat(db=...)` — **none exist with those
  signatures** in `src/`. Only `/health` is functionally real. Import-success and
  HTTP-200 prove nothing; assert the user-visible outcome.
- **Graceful degradation is a release gate, not a nicety.** Scoring/prep/coach hard-fail
  with no `GEMINI_API_KEY`. The core journey must work (heuristic fallback) in a seeded
  env with no paid key, so the journey suite can run anywhere.
- **No CI exists and the loop may not add it** (`.github/` is off-limits). The gate is
  `scripts/preflight.sh` run locally + the two-gate readiness audit. CI wiring is an
  owner action (workflow scope) in PENDING_OPS.
- **Honest baseline beats a green-looking fake.** DoD starts all `[ ]`; business case is
  honestly below the $100K floor (`floor_met_year1: false`); growth is `pre_launch`,
  engine 0%. Convergence happens over scheduled runs, not by ticking boxes early.

### 2026-06-28 — Unpinned transitive httpx silently broke the whole test suite
A fresh container install floated the (unpinned, transitive-via-openai) `httpx` to 0.28.1.
httpx 0.28 dropped the `Client(app=...)` shortcut that starlette 0.35.1's `TestClient`
still passes, so `TestClient(app=...)` raised `TypeError` at construction — EVERY test in
`tests/journeys` errored before running. The preflight CI gate and the Track E journey suite
(`E2E_JOURNEYS_PASSED`) could not run at all, while a production deploy looked fine because
`TestClient` is test-only. Same local-green/repo-or-prod-broken family as the
gitignored-source foot-gun. Fix: pin `httpx==0.27.2` in `requirements.txt` (prod==dev, zero
drift; `requirements-dev.txt` inherits via `-r`). openai 1.59.6 supports httpx >=0.23,<1, so
the old `proxies` crash stays fixed. LESSONS: (1) on a fresh clone the gate runs against
LATEST floating transitives — pin anything whose major/minor API your tooling depends on,
even transitive ones; (2) a green local checkout with stale wheels hides this — the bug only
appears on a clean install, so treat "fresh-container CI red" as signal, not noise. Upgrade
path: lift the pin once fastapi/starlette are bumped to a TestClient that uses ASGITransport
(bumping fastapi from 0.109.0 risks asgi.py route-mirroring internals — deferred).

### 2026-06-27 — Cloud routines + dashboard wired (handoff)
The three scheduled cloud routines that drive this repo (source = this GitHub repo,
env FactoryDashboard) are LIVE. Future runs: do not recreate them; update via the
schedule skill if needed.
- **product factory** — `trig_01E9AFM1m7ZVJXHSzFswhYUD`, cron `0 */6 * * *`, Opus.
- **Growth Agent** — `trig_01PntigzEpuhp7wBxQNHzJvy`, cron `0 14 * * *`, Sonnet + Gmail.
- **daily digest** — `trig_01XfvH9BbgDNzEau6jBU7QRa`, cron `0 13 * * *`, Sonnet + Gmail.
JobScraper is registered in subhsubh24/AutoFactoryDashboard `config/projects.ts`
(slug `jobscraper`, kind `web+mobile`). Manage routines at
https://claude.ai/code/routines. Owner-only (Human-Core) steps remain in PENDING_OPS —
spend caps are 🔴 urgent before any live traffic.

### 2026-06-27 — Reconciled ROADMAP track ticks to real verified state (dashboard 0%)
AutoFactoryDashboard showed JobScraper at 0%. Diagnosis: the dashboard's headline % =
percentToSubmission = the Definition-of-Done checkboxes (submission readiness). DoD is
0/9 ticked — ACCURATE: the product is built + deployed + live-E2E-verified, but NOT
submission-ready (no monetization, no store assets, business case below $100K floor,
no independent A/A+ quality grade). Separately, build progress also read 0 because the
bootstrap left ALL Track boxes unticked — that understated reality. Fixed: ticked 19
Track boxes that are genuinely done WITH on-branch artifacts + this-session live
verification (backend e2e, Next.js web live, Neon, Gemini scoring+prep, gates green).
Left partial items (web SEO/polish, mobile device screens, auth lockout, CORS-locked,
migrations, evals, coverage, visual screenshots) and ALL DoD boxes unticked. Headline
stays 0% until the two-gate readiness passes — correct.

### 2026-06-27 — Marketing maturity gate + pre-launch SITE GATE
Growth markets autonomously but never before the product is ready, and never exposes a
half-baked app. Added: (1) ANALYSIS_PLAYBOOK marketing maturity gate (pre_launch
WAITLIST-ONLY with a HARD BLOCK on execute-mode until a channel is connected AND
GROWTH_STATUS.site_gate_up==true; launching; post_launch) — gated on the independent
QUALITY_SCORECARD + readiness, never eagerness. (2) GROWTH_STATUS.site_gate_up: false
(preflight check_blocks now requires it as a bool). (3) web/middleware.ts SITE GATE:
SITE_GATE_PASSWORD set -> Basic-auth the web app, EXEMPT marketing/legal routes (/,
/waitlist, /coming-soon, /privacy, /terms, /legal); ROADMAP Track G item (BLOCKING note)
+ PENDING_OPS site-gate owner action (set SITE_GATE_PASSWORD=deepster pre-launch, unset at
launch; mobile via TestFlight). (4) Growth Agent ROUTINE reinforced via /schedule:
execute-mode requires engine+channel AND (pre_launch => site_gate_up==true), else stay
PREPARE / zero external traffic; routine also writes site_gate_up each run. The SITE GATE
gates the Next.js web only; the FastAPI /api is a separate Vercel service (own JWT auth);
mobile pre-launch via TestFlight. Follow-up (Track G): build the waitlist landing + legal
pages the gate exempts, and repoint the pre-launch landing CTA to the waitlist.

### 2026-06-27 — Synced FACTORY_STANDARD.md to canonical (visual verification)
Canonical sync (kept byte-identical across factories): added visual-verification to the
shared standard — §6 "SEE WHAT THE USER SEES" (journey suite captures + commits a
screenshot of every page/state; design-audit + readiness gate VISUALLY review them on a
vision model; blank/broken/unstyled/off-brand/"vibe-coded" = release-blocking FAIL even if
DOM assertions pass; bounded to deep-audit + readiness, not every micro-change), §7 Gate-2
functional-reality lens now includes visually reviewing the screenshots, §10 design/taste
lens now visually reviews the screenshots. This is a deliberate canonical sync, NOT loop
work — FACTORY_STANDARD.md remains a stable anchor. FOLLOW-UP for the factory (ROADMAP/
product work, not this file): make the journey suite actually capture + commit page
screenshots (web: Playwright/screenshot; mobile: component snapshots) so the new lenses
have artifacts to judge.

### 2026-06-27 — Adopted the shared FACTORY_STANDARD.md (stable anchor)
Created `FACTORY_STANDARD.md` at the repo root with the canonical, product-agnostic
operating standard — copied BYTE-IDENTICAL (no paraphrase/trim/reorder/adaptation) so it
stays the same across every factory repo. Added the "Operating standard (read every run)"
pointer under the ROADMAP intro and a STABLE ANCHORS / do-not-churn entry. Referenced it in
the orient-read set of docs/autonomous-loop/PROMPT.md + AGENTS.md.
RULE: FACTORY_STANDARD.md is READ-ONLY context every run — NEVER edit or paraphrase it to
fit this product (product-specifics live in ROADMAP/VISION, which win on any specific). It
changes ONLY by a deliberate canonical cross-factory sync, never as loop work.

### 2026-06-27 — Factory-process parity with the sibling products
Aligned JobScraper's FACTORY (not product) to AptDesignerAI / GroceryManager /
HighlightMagic so all four run the identical process, building different things. Ported:
the full DESIGN BAR into VISION.md (THE DESIGNER QUESTION + AVOID-BY-DEFAULT AI-slop list +
GENERATE-BETTER + RECURRING TASTE AUDIT + "a surface that reads as AI-generated is a design
BUG"), enforced by Reviewer B + the deep-audit design lens; preflight security guards
(spend-ceiling/circuit-breaker, security headers, captcha) + a stub/placeholder-marker guard
on critical paths; the loop charter `docs/autonomous-loop/PROMPT.md` (ORIENT→HILL-CLIMB→
BOOTSTRAP→PICK ONE→IMPLEMENT→VERIFY→REVIEW(maker≠checker)→MERGE→RECORD→STOP); `AGENTS.md`
(gate commands + conventions + the ratchet); `IMPROVEMENT_LOG.md`. Documented the canonical
quality-rubric dimension set in check_quality.py.
DELIBERATELY NOT done (maker ≠ checker): did NOT create docs/quality/QUALITY_RUBRIC.md or
QUALITY_SCORECARD.md — the independent Quality Auditor routine owns/bootstraps them. Our
guard already handles their absence. The sibling AptDesignerAI ships the rubric because its
grader bootstrapped it there; ours will appear when the auditor runs.

### 2026-06-27 — Gitignored-source foot-gun broke the Vercel build
The first Vercel deploy failed: `Can't resolve @/lib/api|auth|types`. Cause: the root
.gitignore's Python `lib/` pattern (unanchored) ALSO matched `web/lib/`, so those 3 web
source files were never committed. It built locally (files on disk) but Vercel clones a
repo missing them — a local-green-but-repo-broken trap, same family as BUILDS ≠ WORKS.
Fix: anchored the Python packaging ignores to repo root (`/lib/`, `/lib64/`, `/build/`,
`/dist/`), committed `web/lib/*`, and verified with a CLEAN-ROOM build from `git archive
HEAD` (committed files only) — the real replica of a Vercel clone. Added a preflight
guard asserting critical source dirs (web/lib, web/app, web/components, mobile/src, src)
have tracked files. LESSON: a local gate can pass while the repo is missing gitignored
source; validate from a clean checkout, and never use unanchored generic ignore patterns
(`lib/`, `build/`, `dist/`) in a polyglot repo.

### 2026-06-27 — Consume the independent Quality grade (maker ≠ checker)
A separate Quality Auditor routine grades the product A+→F and OWNS
docs/quality/{QUALITY_RUBRIC,QUALITY_SCORECARD}.md — the factory must NOT author or
overwrite them (it would be self-grading). We only CONSUME: read the scorecard as DATA,
and when a ship-critical dimension is below A, turn its `top_gaps` into named
value-bar-clearing work and drive to A/A+. Wiring added:
- `scripts/check_quality.py`: `parse` (CI — OK if absent, FAIL if present+malformed;
  grades ∈ {A+,A,B,C,D,F,null}) and `readiness` (full gate — require present, ship-critical
  A/A+, others ≥ B). Tested absent/valid/failing/malformed; the throwaway scorecard used
  for testing was deleted, NOT committed (the grader owns that file).
- preflight: parse guard in CI; grade requirement in the full readiness gate.
- ROADMAP: QUALITY RUBRIC (A+→F) note, a DoD box (A/A+ ship-critical, ≥ B else,
  mechanically backed), and the deep audit must reconcile against the scorecard (lower
  view wins). Bounded drive-to-A+ (named fixes only; converge when no value-bar lever left).
Rule: never self-grade; never tick the quality DoD box unless the independent scorecard +
`check_quality.py readiness` back it.

### 2026-06-27 — Distribution/release config must be REAL (checkbox blind spot)
A checkbox-driven loop won't fix a build/deploy-readiness gap hidden under a parent box
that already reads done (ticked-box-not-backed-by-artifact / BUILDS ≠ WORKS). Defenses
added: explicit UNCHECKED ROADMAP items for (a) mobile release config and (b) web deploy
config, each requiring an ARTIFACT, not self-assessment. Built the buildable parts:
`mobile/eas.json` (build+submit profiles), `mobile/app.config.ts` (env overlay:
EAS_PROJECT_ID, EXPO_PUBLIC_API_URL), app.json bundle id + buildNumber/versionCode +
runtimeVersion. Validated WITHOUT a signed build: `expo config` resolves the merged
config, `eas.json` parses, env overlay overrides confirmed; web `next build` produces
`.next`. Signed cloud build + store submit stay Human-Core (PENDING_OPS: eas-build-submit).
Rule: never tick a "build/deploy-ready" box unless an artifact backs it; un-tick otherwise.

### 2026-06-27 — ONE Vercel deployment via Vercel Services (web + API together)
Owner wants a single Vercel project (like the other products), not two. Implemented with
**Vercel Services** (`experimentalServices` in vercel.json): `web` (Next.js) at routePrefix
`/` + `api` (FastAPI, entrypoint asgi.py) at routePrefix `/api`, one domain, shared env.
Vercel does NOT strip the route prefix, so FastAPI's existing `/api/*` routes match as-is.
Web app calls `/api/*` same-origin (api base URL = ''), so no CORS needed. Removed the
old `api/index.py` single-function shim (Services loads `asgi.py:app` directly) and added
`/api/health`. Caveat: Services is experimental/permission-gated — if unavailable, fall
back to two projects. The owner must set the project's Framework Preset to "Services".
Mobile (Expo) is NOT in this project — it points at the deployment's `/api`.
LESSON (process): always `git checkout -b <branch>` BEFORE editing — a prior run committed
to main then `git reset --hard origin/main` and lost the work. Branch first, then edit.

### 2026-06-27 — Frontend split: Next.js web (/web) + Expo mobile (/mobile)
Owner chose a Next.js web app over the React-Native-Web export. Architecture now:
- `/web` = Next.js (App Router, TS, Tailwind) → Vercel project #2 (Root Directory = web),
  the real website + web app. Reads NEXT_PUBLIC_API_URL (defaults to live API).
- `/mobile` = Expo → App Store / Play only (NOT Vercel). Removed mobile/vercel.json.
- API stays as Vercel project #1. Three surfaces, one FastAPI backend.
- preflight `ci` now gates web too (tsc + lint). CORS opened (Bearer-token API: any
  origin, no credentials, unless ALLOWED_ORIGINS is set) so the web app calls the API
  cross-origin. Two frontends = the cost; each best-in-class per platform = the benefit.

### 2026-06-27 — Provider/DB choices: Gemini (LLM) + Neon (Postgres) + Vercel
- LLM = Google Gemini via the OpenAI-compatible endpoint (key GEMINI_API_KEY). No OpenAI.
- DB = Neon Postgres (pooled endpoint). Supabase was dropped (per-instance charges).

### 2026-06-27 — Deploy target = Vercel (serverless), NOT Railway
Owner chose Vercel-for-everything (serverless Python API). Consequences baked into the
repo (see docs/DEPLOY_VERCEL.md):
- `api.py` → renamed `asgi.py` (FastAPI `app`), Vercel entry at `api/index.py`,
  `vercel.json` rewrites all routes there. The `/api` dir is the Vercel functions dir,
  hence the rename to avoid a package/module clash.
- `requirements.txt` slimmed to LEAN runtime deps (Vercel ~250MB function limit);
  full set moved to `requirements-dev.txt` (CI installs that). Removed unused heavy
  deps (sentence-transformers/torch, celery, redis, pandas, etc.) — they had ZERO
  imports and would blow the size limit.
- Serverless realities: external **Postgres required** (no SQLite persistence);
  `src/db` uses NullPool on serverless+Postgres; in-memory rate-limit/spend-ceiling are
  per-instance (Track F: move to shared store); watch the 60s function timeout for LLM
  calls. Railway/Docker configs kept as a fallback in `docs/legacy/`.
