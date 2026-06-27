# VISION — Career Operator

> North star, single source of truth for *why this exists and what "good" means*.
> Operational sequencing lives in [ROADMAP.md](./ROADMAP.md). The business math
> lives in [docs/BUSINESS_CASE.md](./docs/BUSINESS_CASE.md).

## What we are building

**Career Operator** is a real, sellable product that helps job seekers run their
search like an operator: ingest roles, score fit against their profile, generate
interview prep, and coach them through the pipeline. It ships as **both**:

- a **web product + API** (Python: FastAPI API, Flask web app), and
- a **native mobile app** (Expo / React Native, TypeScript, iOS + Android),

with the mobile app at **full parity** with the web product, talking to the same
Python backend API.

It is monetized by **subscription** (good-better-best + annual) and is intended to
earn **reliable revenue with ≥ $100K/yr ARR as the FLOOR, not the target** — we
maximize beyond it.

## The standing design / quality bar

Every change is judged against these. They do not move.

1. **THE DESIGNER QUESTION** — *"Would an experienced product designer intentionally
   choose this?"* If the honest answer is no, it is not done.
2. **No generated-looking slop.** No lorem ipsum, no placeholder cards, no "Coming
   soon" dead ends shipped as if real.
3. **No thin-wrapper mobile.** The app is a real native experience, not a webview of
   the site.
4. **Honest > flashy.** We never fabricate a metric, a "done", a revenue number, a
   user, a review, or store-readiness. A partial-but-honest result beats a
   complete-looking fake.
5. **Real data only, never placeholders.** Empty/loading/error states are designed
   and truthful.
6. **Degrade gracefully.** When a dependency is missing (e.g. no LLM key, no
   network), the product still does something useful and says what it can't do —
   it does not crash or lie.
7. **Trustworthy + App-Store-acceptable + polished.** Privacy, security, and
   compliance are features, not afterthoughts.

## Who pays and why

Active job seekers (especially mid-to-senior tech/knowledge workers) who value time
and outcomes during a high-stakes, time-boxed search. They pay a subscription for:
fit scoring that saves triage time, AI interview prep tied to specific roles, an AI
career coach, and a pipeline CRM that keeps the search organized. See
[docs/BUSINESS_CASE.md](./docs/BUSINESS_CASE.md) for the honest, sourced numbers.

## What "done" means

Done is **evidence-based**, never self-assessed. A capability is done only when there
is a verifiable artifact on the default branch and the gate is green. "It compiles /
the handler is wired" is **not** done — every flow must be validated at runtime, as a
user, asserting the intended outcome. See ROADMAP.md → *Definition of Done* and
*Standing Standards* for the full, binding rules.

## Honest current state (bootstrap)

As of the bootstrap run: the Python backend is an **architectural blueprint that does
not yet fully work** — `api.py` references service methods that do not exist in
`src/` with those signatures, so only `/health` is functionally real. The mobile app
is being re-platformed from a Flutter prototype to Expo/React Native. There is **no
revenue, no users, no live billing, and no store submission.** The business case is
**below the $100K floor** today; we say so plainly and list the buildable levers.
This file and the apparatus around it are the machine that converges the product
toward the vision over scheduled factory runs.
