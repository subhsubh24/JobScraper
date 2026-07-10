# LOOP HEALTH — is the LOOP getting better, not just busier?

Contract: the deep audit grades the PRODUCT (QUALITY_SCORECARD); this grades the LOOP.
Update the block below EVERY run in the ONE bookkeeping PR with REAL counts (from git/gh +
this run's record) — honest only (same anti-gaming rule as the business-case number; never
flatter the loop). Dashboard-readable. This is OBSERVABILITY, NOT a ship gate. CLASSIFY
every abandoned change so the loop never re-attempts the same dead-end. A `churning` or
`stuck` signal MUST trigger ONE "loop: harness improvement proposal" issue (the only channel
by which the loop's own rules improve — it cannot edit its routine or `.claude/`).

```yaml
LOOP_HEALTH:
  project: jobscraper
  as_of: 2026-07-10
  last_run: 2026-07-10            # run 38
  last_deep_audit: 2026-07-10    # run 38 ran a 6-scout Haiku sweep (seat-tier feasibility / mobile-IAP+store-assets / tests-evals+LLM-resilience / artifact-integrity+security / web-design-taste / roadmap+growth). run 35 ran the full 8-scout deep audit; runs 36/37/38 = targeted scout sweeps.
  this_run:                      # run 38
    changes_shipped: 1           # #339 model-death regression NET strengthened (tests/test_llm_nobypass_integration.py — no-bypass source-scan guard + workflow-level integration through the REAL LLMWorkflows._call_llm; product-code-FREE) — tests-evals ship-quality (+ this bookkeeping)
    changes_abandoned: 0         # seat-tier, mobile-IAP, store-assets, web-E2E captures, and a src/llm.py primary-swap were DEFERRED (named, principled), not abandoned — see deferred_decisions.
    abandoned_reasons: []        # reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner.
    verify_cycle_failures: 0     # 0 red REQUIRED CI checks on #339 (CI green first push). Ran the exact gates locally before push (flake8 clean + full non-live suite 583 passed, floor 88 held; guard PROVEN to redden on a planted bypass then green after removal).
    review_rejections: 0         # #339 both reviewers APPROVE first pass (Reviewer A empirically re-planted the bypass + verified the fake-client 404 classification; Reviewer B confirmed it is NOT redundant with the isolation test — different subject-under-test).
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "§23 RED NIGHTLY actioned + diagnosed OWNER-BLOCKED (not a code regression). Latest Nightly (live API validation, 2026-07-10 10:44 UTC) = 4 failed / 17 passed. Downloaded + read the CI logs (DEEP_DIAGNOSIS, observe-real-system): all 4 failures are tests/test_billing_live.py on careerplus_monthly/annual — STRIPE_PRICE_CAREERPLUS_* unset in the nightly env. Gemini AI-output live evals + Pro-plan billing PASS (NO model regression; owner has provisioned sk_test + Pro prices — a PARTIAL config: Pro done, Career+ not). The test is pytest.mark.live + correctly fail-loud (§28: a sellable tier with no price ID is a prod 503, #222) — weakening it = gaming (§23), so NOT touched. Already tracked (PENDING_OPS stripe-account, open/high); sharpened that item to name the current half-configured state. Owner-blocked ⇒ no new issue, no stuck code-signal."
      - "GROUND-TRUTH re-probe of the REAL Gemini endpoint (metrics win, §9): gemini-2.5-flash→HTTP 200 (ALIVE AGAIN), gemini-flash-latest→200, gemini-2.5-flash-lite→200, gemini-2.0-flash→404 (dead). The 5th audit's functional-reality D (model 'decommissioned' 2026-07-09) was TRANSIENT — Google restored 2.5-flash; with #330's fallback the surface is resilient regardless. Consuming the scorecard as DATA: its D is stale-favorable. Did NOT swap the primary default to the floating alias — that trades eval DETERMINISM for avoiding a rare 404+retry (debatable tradeoff, not a clear win; pinned-primary + alias-fallback is defensible) → no churn."
      - "LEDGER SELF-AUDIT: run 37's bookkeeping (#338) did NOT update this LOOP_HEALTH block (it stayed at run 36) — a bookkeeping lapse. Brought current to run 38, folding run 37's #336 (correctness slot-refund) + #337 (coverage 85→88) into the rolling counts honestly."
    deferred_decisions:          # named + deferred, NOT abandoned (value bar / feasibility / PMF-first — not dead-ends)
      - "TEAM/B2B2C seat tier — the named floor-lever, but the feasibility scout confirmed it CANNOT land cleanly in one run (10 entitlement gates in asgi.py = a customer-trust hole if rushed; needs 3 new tables + migration + org-Stripe webhook). AND its B2B demand is explicitly UN-validated (BUSINESS_CASE + GTM say so) so crediting it to cross the floor would be anti-gaming. AND §9 PMF-first deprioritizes monetization scaling pre-launch (0 pipeline). 23rd re-confirmed pre-launch DEFER — trigger = validated demand or an owner ask, then build across slices."
      - "mobile IAP client (react-native-purchases) — CI runs `cd mobile && npm ci` (exact-lockfile) on bleeding-edge Expo SDK 56 / RN 0.85 / React 19.2; the dep's compat is unverified, I can't reliably regenerate the lockfile or validate native integration on Linux → high 2×-CI-fail/abandon risk on a gate I can't validate, and it's owner-blocked for go-live anyway (needs RevenueCat keys + store accounts). The honest 'coming soon' stub is currently correct (no fake success, §6). blocked_owner + gate_build risk."
      - "web-E2E screenshot captures of the new flagship surfaces (/demo, /app/insights, interview) — a REAL design-taste artifact gap (scorecard names it), but they touch the REQUIRED web-E2E gate I can't validate locally (heavy npm ci + build + Playwright + running API) → adding blind steps risks a 2-cycle burn on a required check (BUILDS≠WORKS forbids shipping unverified). Revisit if the stack becomes locally runnable, or scope to the public /demo capture only (lowest risk) next run."
      - "src/llm.py primary-model swap to the floating gemini-flash-latest alias — considered + REJECTED as churn: it trades eval determinism for avoiding a rare 404+retry; the current pinned-primary + alias-fallback design is defensible and the pin is alive (probed 200)."
      - "rate_counters global TTL/sweep (Reviewer-A #331 follow-up) + _refund_counter window_key threading (Reviewer #337 follow-up) — low-severity named edges for a future run; both touch the shared counter used by rate-limit + lockout, disproportionate for the marginal impact."
      - "OWNER-BLOCKED (PENDING_OPS, unchanged): the two ship-critical C's — business-case floor + store-readiness (rendered assets, mobile IAP, native captures) — plus the Career+ Stripe price secrets (nightly). GEMINI live key IS set (probed real this run); Vercel DATABASE_URL→Neon / STRIPE_PRICE_CAREERPLUS_* / RevenueCat / CAPTCHA keys / connect an ESP. NO new migration this run (no schema change)."
  rolling_7d:
    merged_prs: 124            # repo-wide, approximate (120 at run 36 + run 37 #336/#337/#338 + run 38 #339); this bookkeeping merges after
    category_mix: {functional-reality: 1, security: 1, correctness: 1, tests-evals: 2}   # runs 36-38: #330 LLM-resilience / #331 lockout / #336 slot-refund / #337 coverage + #339 regression-net — spread across 4 categories
    diversity: varied
    reverts: 0
    readiness_attempts: 0        # not attempted — the two ship-critical C's stay owner/GTM-blocked (business-case floor + store assets/IAP), so submission-readiness is honestly not met
    readiness_rejected: 0
    recurring_failures: []       # the nightly Career+ red is a KNOWN owner-blocked external (missing secret), not a LOOP failure — tracked, not a stuck signal
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run. Head unchanged (a7d3e1f0c92b from run 31). Owner must still set Vercel DATABASE_URL→Neon before the next deploy (PENDING_OPS).
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 9        # unchanged — no new external capability introduced (#339 is a test-only regression guard).
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 5         # unchanged — #339 is call-path resilience test coverage, not a new LLM feature.
    with_real_output_eval: 5     # each LLM feature judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: steady                 # bootstrapping | improving | steady | churning | stuck — run 38: 1 shipped, 0 abandoned, 0 circuit-breaker trips, 0 red REQUIRED CI checks, 0 review rejections (APPROVE/APPROVE first pass). A genuinely QUIET run (§2 = SUCCESS): the 6-scout sweep CONFIRMED runs 35-37 already closed the fresh ship-critical gaps, so the honest buildable set was one real regression-net PR (#339 — closes the 'a NEW call site could bypass the model-death fallback and 502 silently' hole the isolation test can't catch) + actioning the red nightly (§23 — diagnosed OWNER-BLOCKED: Career+ Stripe prices unset, not a code regression; test correctly fail-loud, NOT weakened) + a ledger self-audit (run 37 skipped this block). GROUND TRUTH: re-probed Gemini — gemini-2.5-flash is ALIVE again, so the audit's functional-reality D was transient; did NOT churn src/llm.py on a debatable determinism tradeoff. Named deferrals (feasibility/PMF/gate-risk, NOT scarcity): seat tier (can't land cleanly + demand un-validated + PMF-first, 23rd run), mobile IAP (npm-ci lockfile + Expo-56/RN-0.85 compat on an unvalidatable gate), web-E2E captures (required gate I can't validate locally), primary-model swap (churn). Two owner-blocked ship-critical C's stand (floor $57.5K<$100K — 23rd run; store assets/IAP). No recurring LOOP wall → no harness proposal. floor_met_year1 stays false. FYI prior cadence: run 37 = 2 shipped, run 36 = 2, run 35 = 4.
```
