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
  as_of: 2026-06-30
  last_run: 2026-06-30            # run 7 (third run on 2026-06-30)
  last_deep_audit: 2026-06-30    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 6           # #114 cross-instance limiter, #115 client timeout, #116 coach N+1, #117 backend coverage, #118 README honesty, #119 mobile screen tests (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate (pytest/jest/tsc/flake8/eslint) before push
    review_rejections: 5         # 5 of 6 PRs drew ONE REQUEST_CHANGES, each a REAL fix resolved within ONE cycle: #114 (B: redundant index — UniqueConstraint already creates it); #115 (A: fake-timers test not restored in finally → suite-poison risk); #117 (BOTH: a referral-bonus test duplicated test_referral.py + a parse test overlapped the detail test); #119 (A: missing safe-area mock + unsettled coach async → act leak). #116 + #118 clean first pass both reviewers (only body/wording nits).
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "FastAPI caches Depends(get_db) per request, so the rate_limit DEPENDENCY and the endpoint body share ONE session (one connection, not two). The limiter's early commit therefore persists only the counter row (nothing else is pending before the body runs) — both reviewers confirmed the shared-session early-commit design is correct."
      - "A module-level TestClient(asgi.app) (test_error_envelope) talks to the default on-disk DB with NO get_db override, so when rate_limit newly started touching the DB its register test 500'd on a missing rate_counters table. Fixed by switching that one test to the seeded `client` fixture. Lesson: a dependency that NEWLY touches the DB can break any test using a non-fixture client against a schema-stale DB."
      - "Scout false-positive caught by skepticism: the security scout flagged an 'off-by-one monthly-reset overage' then admitted the code was 'semantically correct' — verified it's a legitimate rolling 30-day reset (NOT a bug) and did NOT build the churn 'fix'."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "performance (B): N+1 eager-load on /api/jobs + /api/analytics/pipeline (the scorecard's NAMED perf top-gap) — wants asgi.py; the cross-instance limiter owned asgi.py + the single migration slot this run. Next clean-asgi.py run."
      - "growth/PMF: privacy-safe analytics instrumentation (aggregate counters, NEW table/migration) — wants asgi.py + a 2nd migration (only ≤1 shared-resource change/run). Strongest pre-launch measurement foundation; next clean-asgi.py run."
      - "business-case-strength: Career+ ($24) tier + TEAM/B2B2C tier remain the named buildable levers for the floor-flip (multi-run convergence; each wants asgi.py + real value-differentiation)."
      - "security: CAPTCHA (needs owner Turnstile/hCaptcha keys; multi-surface web+mobile+asgi). Login lockout left in-memory by design (a shared store doesn't fix its targeted-DoS — CAPTCHA does)."
      - "Track E mobile VISUAL: jest-expo serializes component TREES, not pixels — committed screenshot IMAGES + the prep-pack vision verdict are human/CI (need a real render + an LLM key), NOT loop-buildable headlessly. #119 added component TESTS (Track B coverage), which is the loop-doable half."
      - "store assets / brand icon: OWNER-BLOCKED per repo standard (loop must not auto-generate a brand mark — slop/DESIGNER QUESTION) + no image tooling. Did not fabricate."
      - "email-provider abstraction: deferred as SPECULATIVE — no consumer until double-opt-in lands (building the unused abstraction now would be padding)."
  rolling_7d:
    merged_prs: 94               # 87 + 6 feature this run + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # migration 993d75032689 (rate_counters cross-instance limiter) drift-gated + auto-applies on merge
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 5
    unmet: [ai]                  # degraded_only — surfaced as OWNER_ACTION validation-capability-gemini (urgent)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 6 shipped, 0 abandoned, 0 circuit-breaker trips; maker≠checker earned its keep (5/6 PRs drew a real REQUEST_CHANGES, all fixed within ONE cycle); closed two ship-critical gaps (cross-instance wallet-drain limiter + the stuck-loading dead-end) + a real perf N+1; skepticism rejected a scout false-positive (no churn). No recurring wall across runs → no harness proposal warranted.
```
