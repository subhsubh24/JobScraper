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
  last_run: 2026-07-03            # run 19
  last_deep_audit: 2026-07-03    # run 18's 6-scout sweep was the last FULL deep audit (today); run 19 did a targeted per-gap reconcile vs HEAD instead of a fresh full sweep (< 24h since run 18)
  this_run:                      # run 19
    changes_shipped: 2           # #226 CAPTCHA/Turnstile seam (Track F), #225 scorer configured-but-failing embedding guard-test (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 1     # #226 CI web-lint failed once: an UNUSED `no-var` eslint-disable in turnstile.tsx (max-warnings 0) — no-var doesn't fire inside `declare global`. Removed → green. Backend/mobile/web-tsc were green throughout; 1 verify cycle, well within the ≤2 cap.
    review_rejections: 2         # cycle-1 REQUEST_CHANGES on BOTH PRs — REAL defects, not thrash: #226 owner_action pointed at a non-existent PENDING_OPS `connect-captcha` while native mobile sends no token + fail-closed → setting TURNSTILE_SECRET would 403 all native auth (mobile-outage risk); #225 my first draft's 2 zero-vector cosine tests DUPLICATED tests/evals/test_scoring_evals.py (scorecard correctness top_gap STALE). Both fixed within ≤2 cycles → APPROVE.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "STALE-SCORECARD reconcile (the run's biggest efficiency win): verifying each scorecard top_gap against HEAD before building showed MOST already closed by later runs — 390px header collision (already fixed, hidden sm:block + flex-wrap), create_job dedup (idempotency guard present), embedding re-embed (DB-column-cached), analytics/pipeline (already N+1-guarded via test_perf_n1.py), and ALL business-case levers except team-tier (Career+/annual-first/referral built). Avoided shipping ~4 redundant PRs. LESSON: on a mature repo a stale scorecard points at done work — verify vs HEAD first."
      - "maker≠checker caught 2 real defects invisible from green tests: (#226) a documentation/ordering hazard where enabling the captcha secret would silently 403 native mobile auth (no mobile token) — fixed with owner_action:null + a loud CONNECT-ORDER warning in code+manifest + the connect-captcha PENDING_OPS entry (both-keys-together caveat); (#225) a redundant test with a false 'no direct assertion' docstring claim — reduced to the genuine net-new configured-but-failing embedding coverage (mutation-verified load-bearing by both reviewers)."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever (Career+/annual-first/referral are all already built). A genuine MULTI-RUN epic (org+seat model, seat billing, composable entitlement); crediting seat ARR at 0 users = gaming, so it does NOT honestly flip $100K pre-launch. The right next big build."
      - "login-lockout cross-instance (the OTHER security A→A+ item) — loop deliberately keeps lockout in-memory citing CAPTCHA as the real targeted-abuse fix (now shipped); revisit only if the auditor still flags it."
      - "native-mobile component snapshots + web SCREENSHOT REGEN (design-taste A→A+ artifact refresh); Pro→Career+ in-place upgrade via Stripe portal; a native mobile Turnstile widget (unblocks live captcha enforcement)."
      - "OWNER-BLOCKED (PENDING_OPS): CAPTCHA keys (connect-captcha — mobile widget FIRST); mobile Career+ IAP client; store asset images/brand icon; CAREERPLUS_* Stripe price IDs; connect a real ESP (EMAIL_BACKEND=smtp)."
  rolling_7d:
    merged_prs: 64             # repo-wide across all routines; incl. this run's #225/#226 (+ this bookkeeping)
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run (all 3 changes are app-code/tests/web-only). Latest migration remains d4e7a1c9b8f2.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 8        # +captcha (run 19): Turnstile TURNSTILE_SECRET declared, validation:mock (siteverify round-trip mocked), blocking:false
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 3         # fit-scoring, prep-pack, coach
    with_real_output_eval: 3     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: steady                 # bootstrapping | improving | steady | churning | stuck — run 19: 2 shipped, 0 abandoned, 0 circuit-breaker trips, 1 verify cycle (trivial web-lint). Headline: on a MATURE repo the honest maximal set was 2 value-bar-clearing changes — a stale-scorecard reconcile against HEAD showed ~4 named gaps ALREADY closed (390px, create_job dedup, embedding cache, analytics N+1, Career+/annual-first/referral), so building them would have been padding; the one remaining ship-critical business-case lever (team/B2B2C seat tier) is a genuine multi-run epic + store-readiness is owner-core, so 2 changes is NOT artificial scarcity. Shipped: #226 CAPTCHA/Turnstile bot-protection seam (closes the open Track F box; DISABLED-by-default, degrades honestly; one of two security A→A+ items — lockout-cross-instance remains, deliberately), #225 a net-new scorer configured-but-failing-embedding guard-test. maker≠checker earned its keep AGAIN: caught a native-mobile-auth-outage ordering hazard (#226) and a duplicate-test-with-false-claim (#225), both invisible from green tests. floor_met_year1 stays false (no revenue lever this run; team/B2B2C is the named path). No recurring wall → no harness proposal warranted. Prior run 18 headline: maker≠checker caught a REAL defect in BOTH backend PRs (a Postgres transaction-poisoning completeness gap in the §32 signup guard #216, and a duplicate-test-with-a-false-claim in #217 — the scorecard's zero-vector correctness top_gap is stale/already-covered), both invisible from green tests and both fixed within the ≤2-cycle cap on a reviewer-prescribed fix (convergence, not thrash). Shipped: #212 §32 signup resilience (no non-essential side-effect can hard-block account creation, rollback-safe on Postgres), scorer structured logging (print→career_operator.scorer), web job-detail role=alert a11y. Anti-padding held (rejected embedding-cache dead-end, stale 390px screenshot, intentional border-focus inputs, cross-instance login-lockout, duplicate prep eval; refuted the AI-consent-modal-hang false positive). No revenue lever (floor_met_year1 stays false; TEAM/B2B2C remains the named floor-lever); no recurring wall → no harness proposal warranted. Prior run 17 headline retained below for history: closed the audit-filed §28 synthetic-green issue #197 on two fronts — (1) the nightly `live` real-service lane now FAILS-not-skips when its key is unexpectedly absent (tests/live_guard.py; owner sets REQUIRE_LIVE_TESTS in nightly.yml to arm it), and (2) added a REAL SMTP delivering backend to the email seam (previously dryrun/capture only) that is honest (delivered=True only on server-accept; fail-loud on incomplete config; inert by default) and CI-validated via monkeypatched smtplib — so a connected owner just sets SMTP_* env. Also fixed a scorecard-named correctness gap: create_job is now idempotent (identical re-submit returns the existing job, no dup row / no double paid-rescore / no double usage-count / no double analytics). ANTI-PADDING held (rejected speculative pagination + a restrictive coach counter in favor of the honest CORRECT-DOCS fix). Bookkeeping aligned 3 stale doc claims (issue #192). No recurring wall → no harness proposal warranted. HONEST on the number: no revenue lever this run; floor_met_year1 stays false; TEAM/B2B2C remains the primary named floor-lever (doesn't flip the floor at 0 users). No recurring wall → no harness proposal warranted.
```
