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
| `/app/insights` | Skill-gap heatmap + AI learning plan | `tests/test_skill_gaps.py` (API) | free heatmap renders; plan is Pro/consent-gated |
| `/app/settings` | Account/settings (incl. résumé view/edit, GitHub enrichment) | API gate (`/api/auth/me`, résumé, enrichment, delete) | — _browser coverage: follow-up_ |
| `/pricing` | Plans | — | _follow-up_ |
| `/waitlist` | Pre-launch capture | `tests/test_waitlist.py` (API) | join → row written; enumeration-safe; no fake-email claim; rate-limited |
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
- waitlist join: row persisted; already-present email returns identical body (no enumeration);
  no "email sent" claim (no provider wired); 6th/hr per IP → 429

### Additional authed API endpoints (dedicated in-process tests, outside the core journey)
- **résumé view/edit** — `GET`/`PATCH /api/profile/resume` (`tests/test_resume_profile.py`):
  the post-signup add/edit path (closes the résumé dead-end); end-to-end unblock proven (a
  résumé-less Premium user hits the tailored-résumé 400, adds a résumé, the guard clears).
- **GitHub profile enrichment** (`tests/test_github_enrichment.py`): `POST /api/profile/enrich/github`
  — Pro-gated; imports the user's OWN public repo language/topics from the fixed `api.github.com`
  host (SSRF-safe); degrades gracefully. `GET`/`DELETE /api/profile/enrichment` (a DIFFERENT path)
  — free, read/clear your own competencies.
- **skill-gap heatmap** — `GET /api/insights/skill-gaps` (`tests/test_skill_gaps.py`): FREE,
  key-free, honest empty state; the cross-pipeline retention hook.
- **AI learning plan** — `POST /api/insights/learning-plan` (`tests/test_skill_gaps.py`): Pro+;
  same tier→data→503→consent→ceiling→moderation gate chain as the other generators; gaps
  recomputed server-side (never client-trusted).
- **mock interview** — `POST /api/prep/mock-interview` (start), `POST /api/prep/mock-interview/{id}/answer`
  (score one answer), `GET /api/prep/mock-interview/{id}`, `GET /api/prep/mock-interviews?job_id=`
  (`tests/test_mock_interview.py`): Pro+; same tier→job→503→consent→ceiling→moderation gate chain;
  multi-turn state on one `MockInterview` row scoped to `user.id` (tenant-isolated); honest scoring
  (weak answer scores low, `overall` computed server-side); account-deletion cascade proven.
- **interview readiness** — `GET /api/jobs/{job_id}/readiness` (`tests/test_readiness.py`): FREE,
  fully-local (no LLM/consent); a readiness score (0–100) + the single next-best-action computed
  from the user's REAL signals (résumé-vs-JD skill coverage + answered/scored mock questions +
  completed prep artifacts); scoped to `user.id` (404 on another user's job); honest 0-state,
  climbs only on real practice. The math is pinned by `tests/evals/test_readiness_evals.py`.

## Mobile screens (`mobile/src/app/**`, jest-expo component/integration tests)
| Screen / unit | Covered by | Outcome asserted |
|---|---|---|
| API client (`services/api.ts`) | `__tests__/api.test.ts` | token attach, path/method/body, response unwrap, error→ApiError(status,detail), offline msg |
| Pipeline (`(tabs)/index.tsx`) | `__tests__/pipeline-screen.test.tsx` | real jobs + stats render; empty + error states; spinner replaced (no stuck spinner) |
| Job detail (`job/[id].tsx`) | `__tests__/job-detail-screen.test.tsx` | real job/score/explanation; free-tier prep label; 403 → `/paywall`; prep pack inline; load error |
| Prep markdown (`components/markdown.tsx`) | `__tests__/markdown.test.tsx` | headings/bold/lists render; markers stripped |

## Lint / static gates
- backend: `flake8` clean
- web: `eslint --max-warnings=0` (zero warnings) + `tsc --noEmit`
- mobile: `tsc --noEmit` + `eslint`

## Known follow-ups (coverage gaps — honest)
- Browser coverage for `/app/settings`, `/pricing`, billing return pages.
- Native (mobile) on-device/simulator functional journey via Expo (Track B). Component/
  integration coverage now exists (jest-expo, see the Mobile table above); the real device
  run + navigation E2E remain human/CI.
- Dual-axis visual verdict per screenshot (Track E) — screenshots are captured by the web
  E2E into `web/e2e/__screenshots__/` but the per-shot design verdict is not yet wired.
