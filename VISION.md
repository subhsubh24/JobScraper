# VISION — Career Operator

> North star, single source of truth for *why this exists and what "good" means*.
> Operational sequencing lives in [ROADMAP.md](./ROADMAP.md). The business math
> lives in [docs/BUSINESS_CASE.md](./docs/BUSINESS_CASE.md).

## What we are building

**Career Operator** is a real, sellable product that helps job seekers run their
search like an operator: ingest roles, score fit against their profile, generate
interview prep, and coach them through the pipeline. It ships as **both**:

- a **web product + API** (Next.js web app + Python FastAPI API), and
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

## The DESIGN BAR (must NOT look vibe-coded) — a STANDING loop standard

Read every run. **Reviewer B enforces this on every UI change (web + mobile); the deep
audit's DESIGN & ACCESSIBILITY lens applies it to the whole live UI.** The goal is an
intentional, hand-crafted product — NOT a generated-looking AI frontend. Use the existing
design system (web: `web/app/globals.css` + Tailwind tokens; mobile: `mobile/src/theme.ts`)
— never ad-hoc styles.

**THE DESIGNER QUESTION (the test every UI diff must pass):** *"Would an experienced
product designer intentionally make this decision?"* If it isn't a confident **yes** for
the layout, spacing, type, color, and component choices, it does not ship. "It renders /
it's technically correct" is not the bar; "a designer would have chosen this" is.
**Reviewer B REQUEST_CHANGES on any UI diff that can't answer yes.**

**AVOID BY DEFAULT (the AI-slop list — each is a smell to justify or remove):**
cookie-cutter SaaS layouts; default/un-themed Tailwind straight out of the box; **card
spam** (wrapping everything in a bordered card); arbitrary/eyeballed spacing (use the
scale); decorative gradients, glows, and blobs; **emoji used as icons** (use a real icon
set — `@expo/vector-icons` on mobile, an SVG/icon set on web); generic startup patterns
(hero + 3 feature cards + pricing table cloned from every landing page); centered-
everything; rainbow accent colors; fake depth (heavy drop-shadows everywhere). None are
banned outright — but each is a generator default, so it must be a *deliberate* choice or
it's removed.

**GENERATE BETTER (target instead):** a clear visual hierarchy (one focal point per
screen, a real type scale, deliberate weight contrast); generous, *consistent* whitespace
from the spacing scale; restraint with the single accent (mostly solid, used to direct
attention, not decorate); content-first layouts shaped by the actual data (not a card grid
by reflex); purposeful, calm motion; density that fits a focused daily-use tool; bespoke
touches that signal a human made deliberate calls. Match the cohesion of a well-designed
consumer app, not a template.

**RECURRING TASTE AUDIT (hook into the periodic deep audit's design lens):** each deep
audit, sweep the live UI for **generated-looking surfaces** (fail THE DESIGNER QUESTION or
hit the avoid list) and produce a PRIORITIZED list ranked by design impact (most-seen,
most-generic, most-conversion-relevant first: landing, auth, paywall, the pipeline/core
loop). Turn the top findings into value-bar-clearing UI work. **A surface that reads as
AI-generated is a design BUG.**

**The standard, in one line:** *simplicity without blandness; functionality without
visual clutter.*

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
