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
  as_of: 2026-07-03
  last_run: 2026-07-03            # run 18
  last_deep_audit: 2026-07-03    # run 18's 6-scout sweep doubled as the deep audit (last full was run 14, ~4 runs prior)
  this_run:                      # run 18
    changes_shipped: 3           # #218 web job-detail role=alert a11y, #217 scorer print→structured logger, #216 §32 signup-resilience (closes #212) (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate before push (backend: pytest non-live + flake8 green; web role=alert leaned on CI).
    review_rejections: 2         # cycle-1 REQUEST_CHANGES on BOTH backend PRs — REAL defects, not thrash: #216 missing db.rollback()/refresh (Postgres tx-poison → 500); #217 zero-vector test was a DUPLICATE of tests/evals/test_scoring_evals.py (scorecard correctness top_gap STALE). Both fixed cycle 2 → 2/2 APPROVE each. #218 approved first pass.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "maker≠checker's biggest win this run: a REAL bug in BOTH backend PRs, both invisible from green tests. #216 — a bare try/except around the analytics side-effect is INCOMPLETE on Postgres: a failed statement poisons the tx, so the next query (user_public→check_usage_limits, outside the try) 500s anyway; fixed by mirroring the referral block's db.rollback()+refresh. #217 — my zero-vector regression test duplicated existing coverage in tests/evals/test_scoring_evals.py; reduced the PR to the genuine logging-only change and recorded the scorecard's 'zero-vector untested' correctness top_gap as STALE."
      - "HONESTY over a green test: I attempted a poisoned-transaction regression test for #216 but the sqlite harness does not reproduce PendingRollbackError on the follow-up query (it passed with AND without the rollback), so I REMOVED it rather than ship theater; the Postgres half is covered by mirroring the already-proven referral pattern + review, stated openly in the PR/commit."
      - "ANTI-PADDING held: rejected embedding-cache (recorded dead-end — DB already caches via ensure_*_embedding; the scorecard perf top_gap is bogus), 390px header collision (run-14-confirmed STALE screenshot), Field focus-ring (intentional border-focus input pattern per #147), login-lockout-cross-instance (recorded decision: CAPTCHA is the fix), and a deterministic prep-pack golden eval (already covered). Refuted the functional-reality scout's 'AI-consent modal hangs' (false: Not now always settles)."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "/api/analytics/pipeline pagination + GET /api/jobs/{id} selectinload N+1 (pre-launch 0-row asgi.py polish — perf is a non-ship-critical B)."
      - "TEAM/B2B2C tier — still the PRIMARY named floor-lever (genuine multi-run epic; crediting seat ARR at 0 users = gaming, so it does NOT honestly flip $100K pre-launch). Owner GTM."
      - "native-mobile component snapshots + web SCREENSHOT REGEN (design-taste A→A+ artifact refresh); Pro→Career+ in-place upgrade via Stripe portal."
      - "OWNER-BLOCKED (PENDING_OPS): set REQUIRE_LIVE_TESTS=1 in nightly.yml; connect a real ESP via EMAIL_BACKEND=smtp + SMTP_* + WEB_APP_URL; mobile Career+ IAP client; store asset images/brand icon; CAPTCHA keys; CAREERPLUS_* Stripe price IDs."
  rolling_7d:
    merged_prs: 62             # repo-wide across all routines; incl. this run's #218/#217/#216
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run (all 3 changes are app-code/tests/web-only). Latest migration remains d4e7a1c9b8f2.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 7        # email now declares SMTP_* (real SMTPBackend added run 17) — stays validation:real, blocking:false
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 3         # fit-scoring, prep-pack, coach
    with_real_output_eval: 3     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — run 18: 3 shipped, 0 abandoned, 0 circuit-breaker trips. Headline: maker≠checker caught a REAL defect in BOTH backend PRs (a Postgres transaction-poisoning completeness gap in the §32 signup guard #216, and a duplicate-test-with-a-false-claim in #217 — the scorecard's zero-vector correctness top_gap is stale/already-covered), both invisible from green tests and both fixed within the ≤2-cycle cap on a reviewer-prescribed fix (convergence, not thrash). Shipped: #212 §32 signup resilience (no non-essential side-effect can hard-block account creation, rollback-safe on Postgres), scorer structured logging (print→career_operator.scorer), web job-detail role=alert a11y. Anti-padding held (rejected embedding-cache dead-end, stale 390px screenshot, intentional border-focus inputs, cross-instance login-lockout, duplicate prep eval; refuted the AI-consent-modal-hang false positive). No revenue lever (floor_met_year1 stays false; TEAM/B2B2C remains the named floor-lever); no recurring wall → no harness proposal warranted. Prior run 17 headline retained below for history: closed the audit-filed §28 synthetic-green issue #197 on two fronts — (1) the nightly `live` real-service lane now FAILS-not-skips when its key is unexpectedly absent (tests/live_guard.py; owner sets REQUIRE_LIVE_TESTS in nightly.yml to arm it), and (2) added a REAL SMTP delivering backend to the email seam (previously dryrun/capture only) that is honest (delivered=True only on server-accept; fail-loud on incomplete config; inert by default) and CI-validated via monkeypatched smtplib — so a connected owner just sets SMTP_* env. Also fixed a scorecard-named correctness gap: create_job is now idempotent (identical re-submit returns the existing job, no dup row / no double paid-rescore / no double usage-count / no double analytics). ANTI-PADDING held (rejected speculative pagination + a restrictive coach counter in favor of the honest CORRECT-DOCS fix). Bookkeeping aligned 3 stale doc claims (issue #192). No recurring wall → no harness proposal warranted. HONEST on the number: no revenue lever this run; floor_met_year1 stays false; TEAM/B2B2C remains the primary named floor-lever (doesn't flip the floor at 0 users). No recurring wall → no harness proposal warranted.
```
