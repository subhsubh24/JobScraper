# Career Operator

> Run your job search like an operator. AI fit scoring, interview prep, an AI career
> coach, and a pipeline CRM — across a Next.js web app and a native mobile app, on one
> Python API.

Career Operator is a subscription job-search platform for active mid-to-senior job
seekers. It scores how well each role fits your resume, generates role-specific
interview prep, answers career questions through an AI coach, and tracks your pipeline.

It ships as three surfaces over one backend:

- **Web app + API** — Next.js (App Router, TypeScript, Tailwind) front end and a Python
  **FastAPI** backend, deployed together on **Vercel** (Vercel Services: web at `/`, API
  at `/api`).
- **Native mobile app** — **Expo / React Native** (TypeScript), iOS + Android. Talks to
  the same `/api`. Not deployed to Vercel; ships through the App Store / Google Play.

> **Status:** pre-launch. The product is built and deployed; monetization code is wired
> (Stripe for web; mobile billing is in progress). It is **not** yet store-submitted. See
> [ROADMAP.md](./ROADMAP.md) for what's done and what's left, and
> [docs/BUSINESS_CASE.md](./docs/BUSINESS_CASE.md) for honest revenue math.

## Features

- **Fit scoring** — a 0–100 score for how well a job matches your resume, with a
  breakdown. Uses Google Gemini embeddings when a key is configured, and degrades
  gracefully to a deterministic heuristic when it isn't (the core loop works key-free).
- **Interview prep packs** — structured, role-specific prep generated for a job.
- **AI application tools (Pro)** — a **tailored résumé** rewritten to a specific posting
  (grounded in your real résumé, never fabricated), plus **cover letters** and **study
  plans**, each rendered as markdown with one-tap copy/download.
- **Salary-negotiation coaching (Career+)** — scripts and strategy for a specific offer.
- **AI career coach** — a chat coach with a conservative safety guardrail (Pro).
- **Cross-pipeline skill-gap heatmap** — across ALL your tracked jobs (not one posting),
  which skills they demand most that your résumé is missing, ranked by frequency. Free and
  fully local; a Pro AI **learning plan** turns the top gaps into a prioritised path.
- **Pipeline CRM** — track jobs through stages with fit scores surfaced inline.
- **ATS import preview** — preview live listings from a Greenhouse/Lever careers URL
  (SSRF-guarded), or an honest empty/unreachable state.

## Pricing

Subscription, good-better-best + annual (annual ≈ 2 months free). See
[docs/BUSINESS_CASE.md](./docs/BUSINESS_CASE.md) for the full model.

| Tier | Monthly | Annual | Who | Key gates |
|---|---|---|---|---|
| **Free** | $0 | — | Trial / casual | 5 tracked jobs, 1 prep pack/mo, no AI coach |
| **Pro** | $12 | $96 | Active seeker | Unlimited jobs, unlimited prep packs, AI tailored résumés + cover letters + study plans, AI coach (fair-use: 25 AI actions/day, shared across AI features) |
| **Career+** | $24 | $192 | Senior / urgent | Everything in Pro + AI salary-negotiation coaching |

> **Current state:** **Career+ is now a real, differentiated entitlement** (PRs #152/#153/#155).
> `UserTier` stays binary FREE/PREMIUM at the DB layer; the *level* (Pro vs Career+) is derived
> from the webhook-verified `Subscription.plan` prefix (`careerplus_*`), so Career+ is granted
> only by a signed Stripe event. Its exclusive is **AI salary-negotiation coaching** (additive —
> it had no endpoint at any tier before, so Pro loses nothing). Web checkout for Career+ is live;
> the on-device mobile *purchase* stays owner-blocked (RevenueCat keys/store accounts — see
> PENDING_OPS), though a Career+ user who subscribed on web uses the feature on mobile. Outreach/
> priority are not yet built and are no longer advertised. See [docs/BUSINESS_CASE.md](./docs/BUSINESS_CASE.md).

The honest Year-1 planning case is **~$57.5K ARR** (below the $100K factory floor —
stated plainly, not inflated). The path to the floor is the buildable lever list in the
business case, not a spreadsheet edit.

## Repository layout

```
JobScraper/
├── asgi.py                 # FastAPI app (`app`) — the Vercel Services API entrypoint
├── vercel.json             # Vercel Services: web at /, FastAPI at /api
├── src/                    # Backend business logic
│   ├── auth/               # Auth + JWT
│   ├── billing.py          # Stripe checkout + webhook + entitlement
│   ├── ai_coach/           # AI career coach + content moderation
│   ├── ranking/            # Fit-scoring algorithm (heuristic + embeddings)
│   ├── enrichment/         # LLM prep-pack workflows
│   ├── ingestion/          # Greenhouse/Lever ATS import
│   └── db/                 # SQLAlchemy models + session
├── web/                    # Next.js web app (App Router, TypeScript, Tailwind)
├── mobile/                 # Expo / React Native app (TypeScript) — iOS + Android
├── mobile-flutter-legacy/  # Retired Flutter prototype (reference only)
├── migrations/             # Alembic migrations (auto-applied on deploy)
├── tests/                  # Backend tests + outcome-asserting journey suite
│   └── journeys/           # Functional journey suite (E2E_JOURNEYS)
├── scripts/                # preflight.sh (gate), run_journeys.sh, db tools
├── docs/                   # BUSINESS_CASE, DEPLOY_VERCEL, store/, growth/, quality/, …
├── ROADMAP.md              # The convergence anchor — what to build, in what order
├── VISION.md               # North star + design/quality bar
└── FACTORY_STANDARD.md     # Shared operating discipline
```

## Quick start

### Backend API

```bash
pip install -r requirements.txt        # runtime deps (CI uses requirements-dev.txt)
cp .env.example .env                    # then edit .env (see below)
./start_api.sh                          # uvicorn asgi:app on http://0.0.0.0:8000
# Interactive API docs: http://0.0.0.0:8000/docs
```

`GEMINI_API_KEY` is **optional** — AI features degrade gracefully without it, so the core
journey runs key-free. `JWT_SECRET` should be set for anything beyond local play (the API
refuses to start in production with an unset/dev-default secret, by design).

### Web app

```bash
cd web
npm install
npm run dev                             # http://localhost:3000
# Point it at a local API:  NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Mobile app (Expo / React Native — not Flutter)

```bash
cd mobile
npm install
npm run start                           # `expo start` — open in Expo Go (scan the QR code)
# Point it at an API:  EXPO_PUBLIC_API_URL=<your API base>
```

## Deployment

Production is a **single Vercel project** using Vercel Services — Next.js at `/` and the
FastAPI app (`asgi:app`) at `/api`, same origin, shared env. External Postgres (Neon) is
required (no SQLite persistence on serverless). Full guide:
[docs/DEPLOY_VERCEL.md](./docs/DEPLOY_VERCEL.md). The mobile app is **not** on Vercel — it
points at the deployment's `/api` and ships through the app stores.

## Tech stack

- **Backend:** FastAPI (Python) on Vercel serverless · SQLAlchemy + Alembic · Neon
  Postgres · Google Gemini (via the OpenAI-compatible endpoint) · Stripe (web billing).
- **Web:** Next.js (App Router, TypeScript, Tailwind) on Vercel.
- **Mobile:** Expo / React Native / TypeScript (iOS + Android).

## Quality gate

`scripts/preflight.sh ci` is the per-change gate (backend lint + tests + import smoke,
mobile `tsc` + lint); `scripts/preflight.sh` is the full readiness gate. Both run in CI
as required checks on `main` (`preflight (lint + typecheck + tests)` + `functional
journeys (web E2E)`). The functional journey suite validates the core loop at runtime
(signup → dashboard → add job → fit score renders → detail), not just that the build
compiles.

## Key documents

- [VISION.md](./VISION.md) — product vision + design/quality bar
- [ROADMAP.md](./ROADMAP.md) — execution plan, tracks, Definition of Done
- [docs/BUSINESS_CASE.md](./docs/BUSINESS_CASE.md) — pricing, revenue projections, levers
- [docs/DEPLOY_VERCEL.md](./docs/DEPLOY_VERCEL.md) — production deployment (Vercel Services)
- [AGENTS.md](./AGENTS.md) — engineering conventions + the gate commands
