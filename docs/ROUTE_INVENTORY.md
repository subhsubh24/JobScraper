# ROUTE / FLOW INVENTORY — provable coverage

Every API route and the runtime journey that proves it **works as a user** (not just
HTTP<400). Auto-checked by `tests/journeys/` (run: `./scripts/run_journeys.sh`).

## Backend API (`api.py`)

| Method | Route | What it does | Journey coverage | Outcome asserted |
|---|---|---|---|---|
| GET | `/health` | Liveness + LLM availability | `test_health_reports_llm_disabled` | 200, `llm_enabled` truthful |
| POST | `/api/auth/register` | Create free user, return JWT | `test_full_core_journey` | real JWT, tier=free |
| POST | `/api/auth/login` | Authenticate, return JWT | `test_full_core_journey`, `test_auth_failures_are_safe` | case-insensitive; generic error on bad creds |
| GET | `/api/auth/me` | Current user + usage | `test_full_core_journey` | real email + remaining counts |
| POST | `/api/auth/verify-purchase` | Upgrade to premium | (manual — needs receipt) | ⚠️ receipt verify is Track C |
| POST | `/api/jobs` | Add job, score it, track it | `test_full_core_journey`, `test_free_tier_job_limit_enforced` | real heuristic score; 403 over free limit |
| GET | `/api/jobs` | List user's jobs | `test_full_core_journey` | job renders in list |
| GET | `/api/jobs/{id}` | Job detail | `test_full_core_journey` | correct job |
| PATCH | `/api/jobs/{id}` | Update pipeline status | `test_full_core_journey` | status moves; invalid -> 422 |
| POST | `/api/prep-packs/generate` | AI interview prep | `test_paywall_and_ai_degrade_gracefully` | 503 truthful when no key; 403 over limit |
| POST | `/api/coach/chat` | AI coach (Pro) | `test_paywall_and_ai_degrade_gracefully` | 403 paywall for free; 503 when no key |
| GET | `/api/coach/suggestions` | Context-aware prompts | `test_full_core_journey` | works WITHOUT a key |
| GET | `/api/analytics/pipeline` | Pipeline stats | `test_full_core_journey` | real counts + avg score |

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
