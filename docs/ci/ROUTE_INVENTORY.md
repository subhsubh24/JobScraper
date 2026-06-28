# Route / flow inventory — what the functional gate must cover

The functional-journey gate's job is to prove the REAL user journeys reach a working
outcome (BUILDS ≠ WORKS). This inventory is the checklist the journey suites are measured
against: every user-reachable route/flow below should be exercised by an outcome-asserting
test (browser for web, in-process for the API) — not merely return `<400`.

Keep this current as routes are added. A new route with no journey coverage is a gap.

## Web app routes (`web/app/**/page.tsx`)
| Route | Purpose | Covered by | Outcome asserted |
|---|---|---|---|
| `/` | Marketing landing | `e2e/core-journey.spec.ts` | landing renders, "Log in" link present |
| `/register` | Signup | `e2e/core-journey.spec.ts` | signup → lands in `/app` (no verify dead-end) |
| `/login` | Login | `e2e/core-journey.spec.ts` | login form renders |
| `/app` | Pipeline dashboard | `e2e/core-journey.spec.ts` | working dashboard; empty state, not an error |
| `/app` (add job) | Core product loop | `e2e/core-journey.spec.ts` | **fit SCORE (core output) renders as a real number** |
| `/app/jobs/[id]` | Job detail | `e2e/core-journey.spec.ts` | detail renders the job |
| `/app/coach` | AI coach | (API gate covers paywall/degrade) | free → truthful paywall, not 500 |
| `/app/settings` | Account/settings | API gate (`/api/auth/me`, delete) | — _browser coverage: follow-up_ |
| `/pricing` | Plans | — | _follow-up_ |
| `/privacy`, `/terms` | Legal | (marketing-exempt; static) | render |
| `/billing/success`, `/billing/cancel` | Stripe return | API gate (checkout/webhook) | — _follow-up_ |

## API flows (`tests/journeys/test_core_journey.py`, in-process ASGI + seeded throwaway DB)
- signup → login (case-insensitive) → `/auth/me` working dashboard state
- add job → **real heuristic score > 0** → list → detail → status update → pipeline analytics
- coach suggestions WITHOUT an LLM key (deterministic)
- paywall: free user → AI coach 403 (truthful), prep-pack 503 (no fake result)
- signup reaches a usable session immediately (no email-verification dead-end)
- verify-purchase 501 (no fake premium grant — side-effect integrity)
- auth failures safe (401 not 500; no email enumeration)
- free-tier job limit enforced (6th → 403 Upgrade)
- Vercel stripped-prefix mirror: every `/api/*` method also reachable at the bare path

## Lint / static gates
- backend: `flake8` clean
- web: `eslint --max-warnings=0` (zero warnings) + `tsc --noEmit`
- mobile: `tsc --noEmit` + `eslint`

## Known follow-ups (coverage gaps — honest)
- Browser coverage for `/app/settings`, `/pricing`, billing return pages.
- Native (mobile) functional journey via Expo + a device/simulator runner (Track B).
- Dual-axis visual verdict per screenshot (Track E) — screenshots are captured by the web
  E2E into `web/e2e/__screenshots__/` but the per-shot design verdict is not yet wired.
