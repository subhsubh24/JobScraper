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
  as_of: 2026-06-29
  last_run: 2026-06-29            # run 2 of the day
  last_deep_audit: 2026-06-29    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 4           # #68 waitlist capture+landing, #69 success-emoji design, #70 retire Flask app.py, #71 mobile component tests
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 2     # mobile jest mock-hoisting (router.push undefined) + a tsc 'global' undefined — both caught + fixed locally before CI ran
    review_rejections: 2         # #68 (B: "Work email" copy + Card reuse + sitemap/metadata), #71 (B: don't re-test markdown + assert offline msg) — both addressed + re-approved in 1 cycle
    circuit_breaker_trips: 0
  rolling_7d:
    merged_prs: 60
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON, --auto merge
  auto_migrate_on_deploy: job_committed_pending_secret # migrate job live in ci.yml; needs DATABASE_URL secret + PITR + stamp (OWNER_ACTION auto-migrate)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 4 shipped, 0 abandoned, every reviewer find resolved in <=1 cycle
```
