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
  as_of: 2026-07-02
  last_run: 2026-07-02            # run 17
  last_deep_audit: 2026-07-02    # run 14's FULL 8-scout sweep; runs 15/16/17 ran focused sweeps (full audit was same-day)
  this_run:                      # run 17
    changes_shipped: 3           # #198 §28 live-lane fail-not-skip, #199 real SMTP email backend (§28), #200 create_job idempotency (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate before push: full non-live suite green (308→313→320→323 across PRs) + flake8 clean + check_validation EXIT 0.
    review_rejections: 0         # all 6 Sonnet reviewers (2 per PR) APPROVE first pass — tightly-scoped, pre-verified, single-concern PRs; reviewers independently re-ran gates + mutation-tested the new guards load-bearing.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "§28 fail-loud is owner-gated at the last inch: the loop builds the mechanism (tests/live_guard.py — skip locally, FAIL when REQUIRE_LIVE_TESTS set + key absent) but the REQUIRED-lane wiring (set REQUIRE_LIVE_TESTS=1 in nightly.yml) lives in .github, which the loop never edits. Recorded HONESTLY: #198 does NOT yet redden the nightly by itself — it builds + PROVES the mechanism and files PENDING_OPS require-live-tests. Ties §28's 'enforcement wiring stays human-gated'."
      - "This routine's env carries a real GEMINI_API_KEY, so during local verify the Gemini `live` tests ACTUALLY RAN green (not skipped) — the guard's fail-loud path was proven with the (absent) Stripe test key under REQUIRE_LIVE_TESTS=1 (billing lane errored/reddened; unset → skipped). Confirms the guard distinguishes present/absent correctly."
      - "ANTI-PADDING: rejected /api/analytics/pipeline pagination (pre-launch 0-row speculative perf) and the coach-100/mo as a CODE change — the code is MORE generous (25 AI-actions/day shared, LLM_DAILY_CEILING=25), so the honest fix is CORRECT-DOCS (done in bookkeeping), not a restrictive new monthly counter. Scout ranked create_job idempotency > both."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "GET /api/jobs/{id} selectinload N+1 (functional-reality scout's only finding — pre-launch single-row polish, asgi.py); a DB unique constraint backing create_job idempotency (belt-and-suspenders for the check-then-insert TOCTOU — acceptable pre-launch at 0 rows)."
      - "TEAM/B2B2C tier — still the PRIMARY named floor-lever (genuine multi-run epic; crediting seat ARR at 0 users = gaming, so it does NOT honestly flip $100K pre-launch). Owner GTM."
      - "web SCREENSHOT REGEN (design-taste A→A+ artifact refresh — the stale 390px shot); Pro→Career+ in-place upgrade via Stripe portal; waitlist-form.tsx conditional 'check your email' copy (LATENT under dry-run until a real ESP connects)."
      - "OWNER-BLOCKED (PENDING_OPS): set REQUIRE_LIVE_TESTS=1 in nightly.yml; connect a real ESP via EMAIL_BACKEND=smtp + SMTP_* + WEB_APP_URL; mobile Career+ IAP client; store asset images/brand icon; CAPTCHA keys; CAREERPLUS_* Stripe price IDs."
  rolling_7d:
    merged_prs: 59             # repo-wide across all routines; incl. this run's #198/#199/#200 (pending merge at write time)
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run (create_job idempotency is an app-layer guard). Latest migration remains d4e7a1c9b8f2.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 7        # email now declares SMTP_* (real SMTPBackend added run 17) — stays validation:real, blocking:false
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 3         # fit-scoring, prep-pack, coach
    with_real_output_eval: 3     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 3 shipped, 0 abandoned, 0 circuit-breaker trips, all 6 reviewers APPROVE first pass. Headline: closed the audit-filed §28 synthetic-green issue #197 on two fronts — (1) the nightly `live` real-service lane now FAILS-not-skips when its key is unexpectedly absent (tests/live_guard.py; owner sets REQUIRE_LIVE_TESTS in nightly.yml to arm it), and (2) added a REAL SMTP delivering backend to the email seam (previously dryrun/capture only) that is honest (delivered=True only on server-accept; fail-loud on incomplete config; inert by default) and CI-validated via monkeypatched smtplib — so a connected owner just sets SMTP_* env. Also fixed a scorecard-named correctness gap: create_job is now idempotent (identical re-submit returns the existing job, no dup row / no double paid-rescore / no double usage-count / no double analytics). ANTI-PADDING held (rejected speculative pagination + a restrictive coach counter in favor of the honest CORRECT-DOCS fix). Bookkeeping aligned 3 stale doc claims (issue #192). No recurring wall → no harness proposal warranted. HONEST on the number: no revenue lever this run; floor_met_year1 stays false; TEAM/B2B2C remains the primary named floor-lever (doesn't flip the floor at 0 users). No recurring wall → no harness proposal warranted.
```
