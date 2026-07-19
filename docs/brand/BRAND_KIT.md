# BRAND KIT — Career Operator

> **A committed asset that codifies the brand as it already exists in code** — the palette
> in `mobile/src/theme.ts` + `web/app/globals.css`, the type stack wired in
> `web/app/layout.tsx`, the voice in `docs/store/ASO_COPY.md`, and the design bar in
> [VISION.md](../../VISION.md). This is the single reference for any external surface (web
> landing, app stores, legal pages, outreach) so they stay consistent. It does **not**
> invent new brand values — where a value isn't decided yet, it says so. Keep it in sync
> with the tokens; the tokens win on any conflict.

## Essence

**Career Operator turns a messy job search into a system you can run.** The product gives a
job seeker the operator's toolkit — fit scoring, role-specific interview prep, an AI coach,
and a pipeline CRM — over a web app and a native mobile app on one Python API.

- **Promise (the line):** *Run your job search like an operator.*
- **Audience:** active mid-to-senior tech / knowledge workers in a high-stakes, time-boxed
  search who value time and outcomes (see [BUSINESS_CASE](../BUSINESS_CASE.md)).
- **Category:** subscription job-search platform (not a one-off tool, not a job board).

## Voice & tone

Per VISION.md and the shipped store copy: **operator-grade, calm, outcome-focused — not
hypey.** Honest over flashy is a hard rule (VISION §4): never fabricate a metric, a result,
or store-readiness.

- **We sound like:** a competent operator/chief-of-staff — direct, concrete, confidence
  without hype. Lead with the outcome ("score how well you match and why"), name limits
  plainly ("works without an AI key — it degrades gracefully").
- **We avoid:** growth-hack hype ("$350K!", "quit your job money"), exclamation spam,
  emoji-as-decoration, vague superlatives, fake urgency, invented social proof.
- **Reading level:** plain, skimmable. Short sentences. Verbs first.

## Color palette (from the code — source of truth)

Dark-first. Tokens live in `mobile/src/theme.ts` (`colors`) and `web/app/globals.css`
(CSS vars + Tailwind `slate`/`indigo`). The shared surface/text values are identical
across web + mobile, and the **accent is now converged** on a single canonical value
(`#6366F1`) across both platforms.

| Role | Hex | Where | Use |
|---|---|---|---|
| Background | `#0B1020` | mobile `bg` / web `--background` | App canvas |
| Surface | `#151B2E` | mobile `surface` | Cards / raised panels |
| Surface (alt) | `#1E2740` | mobile `surfaceAlt` | Inputs / nested surfaces |
| Border | `#2A3554` | mobile `border` (web: `slate-700/800`) | Hairlines, dividers |
| Text | `#F4F6FB` | mobile `text` / web `--foreground` | Primary text |
| Text (muted) | `#9AA6C2` | mobile `textMuted` (web: `slate-400/500`) | Secondary text, labels |
| **Accent (canonical)** | `#6366F1` | mobile `primary` + web `web/components/ui.tsx` `bg-indigo-500` (Tailwind `indigo-500`) | Primary actions, links, focus ring |
| Success | `#34D399` | mobile `success` (web: `emerald`) | Good fit, positive state |
| Warning | `#FBBF24` | mobile `warning` (web: `amber`) | Moderate fit, caution |
| Danger | `#F87171` | mobile `danger` (web: `red-4xx/6xx`) | Weak fit, destructive, errors |

**Fit-score scale (real, from `theme.ts scoreColor`):** ≥ 75 → success (green), ≥ 50 →
warning (amber), else → danger (red). Reuse this mapping anywhere a 0–100 fit score is
shown so the signal reads the same everywhere.

**Accent restraint (VISION DESIGN BAR):** one accent, used to direct attention, not to
decorate. No rainbow accents, no decorative gradients/glows.

## Typography

- **Web:** **Geist Sans** (UI/body) + **Geist Mono** (numerals/code), loaded via
  `next/font/google` in `web/app/layout.tsx` (`--font-geist-sans` / `--font-geist-mono`).
- **Mobile:** the system font stack (San Francisco on iOS, Roboto on Android) — no custom
  font is bundled, which keeps the app native-feeling and light.
- **Hierarchy:** one focal point per screen; a real type-scale with deliberate weight
  contrast (e.g. screen titles ~26–30px / 700–800 weight, muted subtitles, 13–16px body).
  Match the existing screens rather than inventing new sizes.

## Logo, icon & imagery

- **Wordmark:** "Career Operator" set in Geist Sans, bold — used as the header brand on
  web (`web/app/app/layout.tsx`, landing, waitlist) and the auth header on mobile.
- **App icon / splash:** `mobile/app.json` points at `mobile/assets/images/icon.png` +
  adaptive-icon layers + `splash-icon.png`. **Honest status:** the committed `icon.png` is a
  **bespoke** brand mark — a chevron-"A" on a blueprint-grid field, NOT the Expo template
  (independently rendered + confirmed by the Quality Auditor, `docs/quality/QUALITY_SCORECARD.md`
  2026-07-16; reflected in [ACCEPTANCE_AUDIT](../store/ACCEPTANCE_AUDIT.md) G7). The feature
  graphic is likewise committed (`docs/store/assets/feature-graphic.png`). The one remaining
  store-listing artifact is **screenshots**, which require a signed native build (Human-Core,
  not producible on the Linux host — tracked in ACCEPTANCE_AUDIT A3/G7 + PENDING_OPS).
- **Iconography:** real icon sets only — `@expo/vector-icons` (Ionicons) on mobile, inline
  SVG on web. **No emoji as iconography** (VISION avoid-list).

## Design bar (the standard every surface clears)

This kit defers to the binding **DESIGN BAR in [VISION.md](../../VISION.md)** — THE DESIGNER
QUESTION, the AI-slop avoid-list (card spam, eyeballed spacing, decorative gradients,
emoji-as-icon, centered-everything, rainbow accents, fake depth), and the GENERATE-BETTER
targets (clear hierarchy, consistent whitespace from the scale, accent restraint,
content-first layouts, calm motion). One line: *simplicity without blandness; functionality
without visual clutter.*

## Consistency items (flagged honestly)

The primary **accent is now converged**: mobile `primary` was changed from `#5B8CFF` to
`#6366F1` (`mobile/src/theme.ts`) to match the web `indigo-500`, so both platforms use the
one canonical accent above. The app **icon/splash** are the committed **bespoke** chevron-"A"
mark (`mobile/assets/images/icon.png`), NOT the Expo template — see the "App icon / splash"
row above and [ACCEPTANCE_AUDIT](../store/ACCEPTANCE_AUDIT.md) G7. The one remaining
store-listing artifact gap is **screenshots**, which need a signed native build (Human-Core,
not producible on the Linux host — tracked in ACCEPTANCE_AUDIT A3/G7 + PENDING_OPS).
