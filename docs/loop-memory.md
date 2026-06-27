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
