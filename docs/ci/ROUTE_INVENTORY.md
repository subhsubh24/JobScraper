# Route / flow inventory — what the functional gate must cover

The functional-journey gate's job is to prove the REAL user journeys reach a working
outcome (BUILDS ≠ WORKS). This inventory is the checklist the journey suites are measured
against: every user-reachable route/flow below should be exercised by an outcome-asserting
test (browser for web, in-process for the API) — not merely return `<400`.

Keep this current as routes are added. A new route with no journey coverage is a gap. The
**Complete API route → coverage matrix** below is the authoritative, exhaustive list of every
route in `asgi.py` (all 50) and the test that exercises it — so completeness is verifiable, not
asserted. The web/mobile tables and the API-flow narrative give the richer per-flow context.

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
| `/demo` | Public no-account skill-match demo (§34 aha) | `e2e/demo-journey.spec.ts` | paste JD+résumé → real matching/missing skills + coverage % RENDER; no-résumé + no-skills + backend-500 all degrade honestly (no fake 0%, no dead-end); → waitlist CTA |
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
- **ATS import preview** — `POST /api/jobs/import-preview` (`tests/test_ingestion_endpoint.py`):
  authed, unmetered; previews a live Greenhouse/Lever careers-page's job listings (or honest
  unsupported / unreachable / no-roles states); SSRF-hardened (public HTTP(S) only, per-hop
  redirect guard); mocked in E2E for CI determinism (a live board can't be reached repeatably).
  `web/e2e/import-journey.spec.ts` exercises the full flow: preview → select → pre-fill → create
  a real job (incl. the degraded states).
- **interview readiness** — `GET /api/jobs/{job_id}/readiness` (`tests/test_readiness.py`): FREE,
  fully-local (no LLM/consent); a readiness score (0–100) + the single next-best-action computed
  from the user's REAL signals (résumé-vs-JD skill coverage + answered/scored mock questions +
  completed prep artifacts); scoped to `user.id` (404 on another user's job); honest 0-state,
  climbs only on real practice. The math is pinned by `tests/evals/test_readiness_evals.py`.
- **public demo skill-match** — `POST /api/demo/skill-match` (`tests/test_demo_skill_match.py`,
  `tests/evals/test_demo_match_evals.py`): PUBLIC (no account), KEY-FREE + local (no LLM/DB/PII);
  paste one JD (+ optional résumé) → matching/missing skills + coverage % from the shared
  `extract_skills` vocabulary. Hardened like a live public surface (§12): bounded input, a burst
  (20/min) + daily (200/day) per-IP rate limit, captcha seam (no-op until owner connects). Honest
  no-résumé state (has_resume=false, no fake 0%). The §34 pre-launch "aha" funnel driver.

- **team / organization seats (B2B2C tier)** — `POST /api/org` (create), `GET /api/org` (mine),
  `POST /api/org/checkout` (buy N seats — a REAL quantity-based Stripe call), `POST /api/org/members`
  (assign a seat by email), `DELETE /api/org/members/{user_id}` (free a seat)
  (`tests/test_org_billing.py`, 21): the named business-case floor-lever. Entitlement is reconciled
  into `users.tier` by `billing.recompute_user_tier` (active individual Stripe sub OR active org
  seat OR active mobile/RevenueCat entitlement — the single authority over all three sources), so
  every existing paid gate applies to seat members unchanged; a team seat grants the base Pro level
  (Career+ stays an individual upsell). SIDE-EFFECT INTEGRITY: `status`/`seats_purchased` move ONLY
  on a signature-verified webhook (a forged event grants nothing); the paid-seat invariant
  (`active members <= seats_purchased`) is enforced on assignment AND on a webhook seat reduction
  (newest freed first); checkout refuses honestly (503) when Stripe isn't configured. Authz +
  tenant isolation (owner-only management; a member never sees the roster) + account-deletion purge
  (no orphaned org rows) are all tested. Web/mobile management surface is a follow-up (backend-first,
  like the Career+ tier PR #152). Live Stripe team Price ID is owner-only (PENDING_OPS).

### Complete API route → coverage matrix (all 50 routes in `asgi.py`)
Exhaustive by construction: every `@app.<verb>` route in `asgi.py` appears exactly once with the
test that exercises it. If a new route is added to `asgi.py` without a row here (and a real test),
the inventory is out of date — that is the gap this matrix makes visible. Auth/tier is the
server-enforced gate; "public" means no bearer token required.

| Method | Route | Auth / tier | Covered by |
|---|---|---|---|
| POST | `/api/auth/register` | public | `journeys/test_core_journey.py`, `test_account_and_security.py`, `test_signup_resilience.py` |
| POST | `/api/auth/login` | public | `journeys/test_core_journey.py`, `test_account_and_security.py` (lockout/enumeration) |
| GET | `/api/auth/me` | authed | `journeys/test_core_journey.py`, `test_auth_eager_load.py` |
| DELETE | `/api/auth/me` | authed | `test_account_and_security.py`, `test_content_report.py` (deletion cascade) |
| POST | `/api/ai-consent` | authed | `test_ai_consent.py` |
| DELETE | `/api/ai-consent` | authed | `test_ai_consent.py` (revoke) |
| GET | `/api/referrals/me` | authed | `test_referral.py` |
| POST | `/api/waitlist/join` | public | `test_waitlist.py`, `journeys/test_waitlist_double_optin.py` |
| GET | `/api/waitlist/confirm` | public (token) | `journeys/test_waitlist_double_optin.py` |
| POST | `/api/demo/skill-match` | public | `test_demo_skill_match.py`, `evals/test_demo_match_evals.py` |
| POST | `/api/auth/verify-purchase` | authed | `journeys/test_core_journey.py` (501, no fake grant), `test_api_input_hardening.py` |
| POST | `/api/billing/checkout` | authed | `test_billing.py`, `test_billing_timeout.py` |
| POST | `/api/billing/portal` | authed | `test_billing.py` (real portal call fires; honest 503 unconfigured; 400 no-subscription) |
| POST | `/api/billing/webhook` | public (Stripe sig) | `test_billing.py`, `test_org_billing.py` |
| POST | `/api/billing/revenuecat-webhook` | public (RC sig) | `test_mobile_billing.py`, `test_org_billing.py` |
| POST | `/api/org` | authed | `test_org_billing.py`, `test_org_hardening.py` |
| GET | `/api/org` | authed | `test_org_billing.py` |
| POST | `/api/org/checkout` | authed (owner) | `test_org_billing.py`, `test_billing_timeout.py` |
| POST | `/api/org/members` | authed (owner) | `test_org_billing.py` |
| DELETE | `/api/org/members/{member_user_id}` | authed (owner) | `test_org_billing.py` |
| POST | `/api/jobs` | authed | `journeys/test_core_journey.py`, `test_jobs_endpoint.py`, `test_job_idempotency.py` |
| GET | `/api/jobs` | authed | `journeys/test_core_journey.py`, `test_jobs_endpoint.py`, `test_read_rate_limit.py` |
| GET | `/api/jobs/{job_id}` | authed | `journeys/test_core_journey.py`, `test_jobs_endpoint.py` |
| GET | `/api/jobs/{job_id}/readiness` | authed (free) | `test_readiness.py`, `evals/test_readiness_evals.py` |
| PATCH | `/api/jobs/{job_id}` | authed | `journeys/test_core_journey.py`, `test_jobs_endpoint.py` |
| POST | `/api/jobs/import-preview` | authed | `test_ingestion_endpoint.py`, `test_greenhouse_client.py` |
| POST | `/api/prep-packs/generate` | Pro | `test_prep_pack_endpoint.py`, `journeys/test_core_journey.py` (503) |
| POST | `/api/prep/salary-negotiation` | Career+ | `test_career_plus.py`, `test_input_bounds.py` |
| POST | `/api/prep/cover-letter` | Pro | `test_prep_tools.py`, `test_llm_ceiling_refund.py` |
| POST | `/api/prep/study-plan` | Pro | `test_prep_tools.py` |
| POST | `/api/prep/tailored-resume` | Pro | `test_tailored_resume.py`, `test_resume_profile.py` |
| POST | `/api/prep/mock-interview` | Pro | `test_mock_interview.py` |
| POST | `/api/prep/mock-interview/{interview_id}/answer` | Pro | `test_mock_interview.py` |
| GET | `/api/prep/mock-interview/{interview_id}` | Pro | `test_mock_interview.py` |
| GET | `/api/prep/mock-interviews` | Pro | `test_mock_interview.py` |
| POST | `/api/coach/chat` | Pro | `journeys/test_core_journey.py`, `test_coach_endpoint.py`, `test_api_input_hardening.py` |
| GET | `/api/coach/suggestions` | authed | `journeys/test_core_journey.py`, `test_api_input_hardening.py`, `test_rate_limit_peruser.py` |
| POST | `/api/report` | authed | `test_content_report.py` |
| GET | `/api/insights/skill-gaps` | free | `test_skill_gaps.py` |
| POST | `/api/insights/learning-plan` | Pro | `test_skill_gaps.py` |
| GET | `/api/profile/resume` | authed | `test_resume_profile.py` |
| PATCH | `/api/profile/resume` | authed | `test_resume_profile.py` |
| POST | `/api/profile/enrich/github` | Pro | `test_github_enrichment.py` |
| GET | `/api/profile/enrichment` | authed (free) | `test_github_enrichment.py` |
| DELETE | `/api/profile/enrichment` | authed (free) | `test_github_enrichment.py` |
| GET | `/api/analytics/pipeline` | authed | `journeys/test_core_journey.py`, `test_perf_n1.py` |
| GET | `/api/analytics/summary` | token-gated | `test_analytics.py` |
| GET | `/` | public | `journeys/test_core_journey.py` (API root) |
| GET | `/health` | public | `journeys/test_core_journey.py` |
| GET | `/api/health` | public | `journeys/test_core_journey.py` |

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
