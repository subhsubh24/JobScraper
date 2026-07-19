# Career Operator (JobScraper)

An AI career operator that takes a job seeker from "found a role" to "you're the strongest
candidate for it": a job pipeline/CRM, fit-scoring, tailored résumés + cover letters, skill-gap
analysis, prep packs, a mock-interview engine + readiness loop, and an AI career coach — with
honest subscription monetization. This is a **mature, pre-launch product**, not a scaffold.

> This file is a short orientation pointer. The authoritative docs win on any specific — do not
> duplicate their content here.

## Read these first (sources of truth)
- **`AGENTS.md`** — operating rules for AI agents (commands/the gate, stack conventions, LLM/cost
  rules, the design bar, hard don'ts). Start here.
- **`FACTORY_STANDARD.md`** — the shared, product-agnostic factory discipline (STABLE ANCHOR; never
  edit as loop work).
- **`ROADMAP.md`** — what to build next (the convergence anchor: tracks A–H, Definition of Done,
  standing standards).
- **`VISION.md`** — the north star + the quality bar (THE DESIGNER QUESTION).
- **`README.md`** — product overview + local run instructions.
- **`docs/quality/QUALITY_SCORECARD.md`** — the independent quality grade (CONSUME as data; never
  self-grade). Business math: `docs/BUSINESS_CASE.md`. Growth signal: `docs/growth/GROWTH_STATUS.md`.

## Stack (see `AGENTS.md` for conventions)
- **Backend:** FastAPI in `asgi.py` (the Vercel Services entrypoint) + business logic in `src/`;
  SQLAlchemy (`src/db`) over Neon Postgres in prod. Tests in `tests/` (+ journeys, evals).
- **Web:** Next.js (App Router, TypeScript, Tailwind) in `web/`.
- **Mobile:** Expo / React Native / TypeScript in `mobile/` (native build = EAS/owner).
- One Vercel project: web at `/`, API at `/api` (same-origin).

## The gate (must be green to merge)
`bash scripts/preflight.sh ci` — backend deps + `flake8` + `pytest` (coverage floor in
`setup.cfg`) + asgi import smoke, and mobile `tsc --noEmit` + `expo lint`. The full readiness gate
(`bash scripts/preflight.sh`) stays red until the product is actually done — that is the correct
pre-launch state.

## Hard don'ts
Never edit `.claude/` or `.github/`. Never commit secrets (`.env` is gitignored; env is
server-side only). Never weaken a guard/test to go green. See `AGENTS.md` for the full list.
