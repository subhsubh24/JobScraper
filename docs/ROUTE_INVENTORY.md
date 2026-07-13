# ROUTE / FLOW INVENTORY — provable coverage

Every API route and the test that proves it **works as a user** (not just HTTP<400). The core
end-to-end loop is proven by the outcome-asserting **journey suite** (`tests/journeys/`, run:
`./scripts/run_journeys.sh`); every other route is proven by a dedicated **integration** test
(`tests/*.py`, real FastAPI `TestClient` against a seeded DB) or a browser **e2e** spec
(`web/e2e/*.spec.ts`). Live third-party round-trips (real Stripe test-mode / Gemini) run in the
nightly **live** lane (`tests/*_live.py`, `tests/evals/`). Routes are defined in `asgi.py`.

Coverage kinds: **journey** = `tests/journeys/` end-to-end · **e2e** = Playwright web flow ·
**integration** = `TestClient` route test · **live** = real-provider nightly round-trip.

## Auth & account

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| POST | `/api/auth/register` | Create free user, return JWT | journey `test_full_core_journey` | real JWT, tier=free |
| POST | `/api/auth/login` | Authenticate, return JWT | journey `test_full_core_journey`, `test_auth_failures_are_safe` | case-insensitive; generic error on bad creds; lockout `test_account_and_security.py` |
| GET | `/api/auth/me` | Current user + usage | journey `test_full_core_journey` | real email + remaining counts |
| DELETE | `/api/auth/me` | Delete account, purge data | integration `test_account_and_security.py`, `test_org_billing.py` | rows purged; no orphan org/seat rows |
| POST | `/api/auth/verify-purchase` | Upgrade via receipt (Track C) | journey `test_no_fake_success_on_unverified_purchase` | ⚠️ no fake success; real receipt verify is Track C |
| POST | `/api/ai-consent` | Grant AI-processing consent (Apple 5.1.2) | integration `test_ai_consent.py` | consent persisted; AI routes gated on it |
| DELETE | `/api/ai-consent` | Withdraw AI consent | integration `test_ai_consent.py` | consent cleared; AI routes 403 after |
| GET | `/api/referrals/me` | Referral code + bonus stats | integration `test_referral.py` | stable code; real bonus counts |

## Waitlist (pre-launch funnel)

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| POST | `/api/waitlist/join` | Join waitlist, send double-opt-in | journey `test_double_optin_full_round_trip` | row created; confirm email dispatched (capture round-trip) |
| GET | `/api/waitlist/confirm` | Confirm via signed token | journey `test_double_optin_full_round_trip`, `test_forged_token_confirms_nothing` | only a valid token confirms; forged token confirms nothing |

## Billing (individual)

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| POST | `/api/billing/checkout` | Start Stripe Checkout (Pro/Career+) | integration `test_billing.py`, `test_billing_timeout.py`; live `test_billing_live.py` | real session for every plan; honest 503 when unconfigured; sub-budget timeout |
| POST | `/api/billing/webhook` | Stripe webhook → grant/revoke tier | integration `test_billing.py` | only a signature-verified event flips tier |
| POST | `/api/billing/revenuecat-webhook` | Mobile IAP webhook → grant/revoke | integration `test_mobile_billing.py` | constant-time HMAC; forged header grants nothing |

## Org / team seat tier (B2B2C)

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| POST | `/api/org` | Create org (owner only) | integration `test_org_billing.py`; e2e `team-journey.spec.ts` | one org per owner; DB constraint on race |
| GET | `/api/org` | Get org owned or seated in | integration `test_org_billing.py`; e2e `team-journey.spec.ts` | owner sees roster; member sees read-only |
| POST | `/api/org/checkout` | Stripe seat checkout (quantity) | integration `test_org_billing.py`, `test_billing_timeout.py`; live `test_billing_live.py` | real seat session; honest 503 when unconfigured |
| POST | `/api/org/members` | Assign a seat by email (owner) | integration `test_org_billing.py`; e2e `team-journey.spec.ts` | seat-cap enforced; idempotent; reactivates soft-deleted |
| DELETE | `/api/org/members/{member_user_id}` | Free a seat (owner) | integration `test_org_billing.py`; e2e `team-journey.spec.ts` | soft-delete; tier recomputed; tenant-isolated |

## Jobs (core loop)

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| POST | `/api/jobs` | Add job, score it, track it | journey `test_full_core_journey`, `test_free_tier_job_limit_enforced` | real heuristic score; 403 over free limit |
| GET | `/api/jobs` | List user's jobs | journey `test_full_core_journey` | job renders in list |
| GET | `/api/jobs/{job_id}` | Job detail | journey `test_full_core_journey` | correct job; tenant-isolated |
| PATCH | `/api/jobs/{job_id}` | Update pipeline status | journey `test_full_core_journey` | status moves; invalid → 422 |
| GET | `/api/jobs/{job_id}/readiness` | Readiness score for a job | integration `test_readiness.py` | real bounded score; degrades without a key |
| POST | `/api/jobs/import-preview` | Preview bulk job import (ATS) | integration `test_ingestion_endpoint.py`; e2e `import-journey.spec.ts` | parsed preview; bounded; rate-limited |

## Demo (public, no-account aha)

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| POST | `/api/demo/skill-match` | Bounded public fit/skill match | integration `test_demo_skill_match.py`; e2e `demo-journey.spec.ts` | real result; rate-limited + spend-capped; no account |

## Prep tools (monetized AI)

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| POST | `/api/prep-packs/generate` | AI interview prep pack | journey `test_paywall_and_ai_degrade_gracefully` | 503 truthful when no key; 403 over limit |
| POST | `/api/prep/salary-negotiation` | Salary coaching (Career+ only) | integration `test_career_plus.py`, `test_input_bounds.py` | 403 for non-Career+; server-side gate |
| POST | `/api/prep/cover-letter` | AI cover letter (Pro) | integration `test_prep_tools.py`, `test_llm_ceiling_refund.py` | gated; spend-ceiling refund on provider error |
| POST | `/api/prep/study-plan` | AI study plan (Pro) | integration `test_prep_tools.py` | gated; degrades honestly without a key |
| POST | `/api/prep/tailored-resume` | Tailored résumé rewrite (Pro) | integration `test_tailored_resume.py`, `test_resume_profile.py` | grounded in real résumé; no hallucinated facts |
| POST | `/api/prep/mock-interview` | Start a mock interview (Pro) | integration `test_mock_interview.py` | interview created; questions reference the JD |
| POST | `/api/prep/mock-interview/{interview_id}/answer` | Submit an answer, get scoring | integration `test_mock_interview.py` | bounded answer; real scored feedback |
| GET | `/api/prep/mock-interview/{interview_id}` | Fetch a mock interview | integration `test_mock_interview.py` | correct interview; tenant-isolated |
| GET | `/api/prep/mock-interviews` | List a user's mock interviews | integration `test_mock_interview.py` | only the caller's interviews |

## Coach (AI)

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| POST | `/api/coach/chat` | AI career coach (Pro) | journey `test_paywall_and_ai_degrade_gracefully` | 403 paywall for free; 503 when no key |
| GET | `/api/coach/suggestions` | Context-aware prompts | journey `test_full_core_journey` | works WITHOUT a key |

## Insights

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| GET | `/api/insights/skill-gaps` | Skill-gap analysis | integration `test_skill_gaps.py` | real gaps from job+profile data |
| POST | `/api/insights/learning-plan` | AI learning plan (Pro) | integration `test_skill_gaps.py` | gated; degrades honestly without a key |

## Profile & enrichment

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| GET | `/api/profile/resume` | Get stored résumé | integration `test_resume_profile.py` | caller's résumé only |
| PATCH | `/api/profile/resume` | Update résumé | integration `test_resume_profile.py` | bounded; persisted |
| POST | `/api/profile/enrich/github` | Enrich profile from GitHub | integration `test_github_enrichment.py` | SSRF-guarded fetch; real enrichment |
| GET | `/api/profile/enrichment` | Get enrichment result | integration `test_github_enrichment.py` | caller's enrichment only |
| DELETE | `/api/profile/enrichment` | Clear enrichment | integration `test_github_enrichment.py` | row removed |

## Analytics & content

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| GET | `/api/analytics/pipeline` | Pipeline stats | journey `test_full_core_journey` | real counts + avg score |
| GET | `/api/analytics/summary` | Aggregate metrics read | integration `test_analytics.py` | real aggregates; rate-limited |
| POST | `/api/report` | Report content (moderation) | integration `test_content_report.py` | report persisted; rate-limited |

## Ops / liveness

| Method | Route | What it does | Proving test | Outcome asserted |
|---|---|---|---|---|
| GET | `/` | Friendly root | journey `test_root_is_friendly` | 200, friendly payload |
| GET | `/health`, `/api/health` | Liveness + LLM availability | journey `test_health_reports_llm_disabled` | 200, `llm_enabled` truthful |

## Mobile (Expo) — see `mobile/`
Mobile screen/flow coverage is asserted at the level runnable on CI (typecheck-clean +
component/integration tests). **Native device runs are a human/CI check** — see the
human-only checklist below.

## HUMAN-ONLY checklist (cannot be asserted by the loop — must be MANUALLY verified)
- [ ] Real Apple/Google **payment CAPTURE** end-to-end (sandbox + production)
- [ ] **Receipt/signature verification** server-side (Track C) actually rejects forged receipts
- [ ] **Email deliverability** (signup/waitlist) lands in inbox, not spam
- [ ] **Native device** store-purchase + restore flow on a real iOS and Android device
- [ ] Live LLM responses (prep pack + coach) are high-quality with a real key
- [ ] Account deletion truly purges data (Apple A8 / Google G3)

> Reminder: "it compiles / passes" ≠ "it works". A build-but-broken flow is a
> release-blocking FAIL equal to a red test.
