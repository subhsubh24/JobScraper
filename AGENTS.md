# AGENTS.md — Career Operator / JobScraper

Operating rules for AI agents in this repo. Short on purpose — every line traces to a real
failure or a hard constraint (the ratchet). **Success is silent; failures are verbose.**
Same factory process as the sibling products; only the product differs.

## Commands (the gate)
- Backend deps: `pip install -r requirements-dev.txt` (Vercel installs lean `requirements.txt`)
- Lint: `flake8 .` · Tests: `python -m pytest -q tests` · Journeys: `./scripts/run_journeys.sh`
- Web: `cd web && npx tsc --noEmit && npm run lint && npm run build`
- Mobile: `cd mobile && npx tsc --noEmit && npx expo lint` (native build = EAS/owner)
- **Full gate:** `bash scripts/preflight.sh ci` (must be green to merge) ·
  `bash scripts/preflight.sh` (full readiness — stays red until the product is done)

## Stack / conventions
- FastAPI app is `asgi.py` (the Vercel Services entrypoint); business logic in `src/`.
  Web = Next.js (App Router, TS, Tailwind) in `web/`; mobile = Expo/RN/TS in `mobile/`.
- DB access via SQLAlchemy (`src/db`); Neon Postgres in prod (pooled endpoint, NullPool on
  serverless). Never commit secrets; env is server-side only (`.env` is gitignored).
- One Vercel project (Vercel Services): web at `/`, API at `/api`. Web calls `/api/*`
  same-origin.
- **Never use unanchored generic ignore patterns** (`lib/`, `build/`, `dist/`) in
  `.gitignore` — they hid `web/lib` and broke a deploy. Anchor to root (`/lib/`).

## LLM / AI rules (cost + graceful degradation)
- LLM only via `src/llm.py` (Gemini through its OpenAI-compatible endpoint). Override the model
  via env (`GEMINI_MODEL`, default the floating alias `gemini-flash-latest`) — never inline a
  model string elsewhere.
- **Cheapest tier by default; the app DEGRADES GRACEFULLY with no key** (scoring →
  heuristics; prep/coach → truthful 503). Never let a missing key crash a flow.
- Per-user/day spend ceiling (`LLM_DAILY_CEILING`) is load-bearing wallet-drain defense —
  add capacity, never remove the ceiling.

## The DESIGN BAR (UI must not look vibe-coded)
Every UI change passes THE DESIGNER QUESTION and avoids the AI-slop list in `VISION.md`
(no card spam, no emoji-as-icons, no eyeballed spacing, no default-Tailwind). Reviewer B
rejects UI diffs that can't answer "a designer would choose this" with a yes.

## Quality grade (maker ≠ checker)
An independent Quality Auditor owns `docs/quality/QUALITY_RUBRIC.md` +
`QUALITY_SCORECARD.md`. We CONSUME the grade (read as DATA), never author/overwrite those
files, never self-grade. Readiness requires A/A+ on every ship-critical dimension, ≥ B else.

## The ratchet
When an agent slips: add a rule here, add a deterministic guard (preflight check / test),
and record the lesson in `docs/loop-memory.md` so it can't recur. Remove a rule only when a
guard makes it redundant.

## Shared standard
`FACTORY_STANDARD.md` (repo root) is the shared, product-agnostic factory discipline — read
it every run; it is a STABLE ANCHOR (never edit/paraphrase it to fit this product; it syncs
canonically across all factory repos). Product-specifics live in ROADMAP/VISION.

## Hard don'ts
Never edit `.claude/` or `.github/`. Never commit secrets. Never weaken a guard/test to go
green. Always branch before editing; one merged change per loop run. Never edit
`FACTORY_STANDARD.md` as loop work.
