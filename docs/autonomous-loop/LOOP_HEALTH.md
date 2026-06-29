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
  last_run: 2026-06-29            # run 3 of the day
  last_deep_audit: 2026-06-29    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 7           # #77 README freshness, #78 mobile-auth tests, #79 billing tests, #80 coach/scorer tests, #81 store-docs, #82 web a11y, #83 brand kit (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate (pytest/jest/tsc/flake8/eslint) on the first run before push
    review_rejections: 4         # #77 (A: npm run dev ghost script), #78 (A: assert signUp called + pin OR guard), #82 (A: 2 missed a11y links), #83 (A: cite real accent source) — ALL resolved in 1 re-review cycle; #79/#80/#81 clean first pass
    circuit_breaker_trips: 0
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar — not dead-ends)
      - "CAPTCHA: a coherent web+mobile+api unit (env-gated Turnstile) — a server-only gate would dead-end signup; do on a clean-asgi.py run (no PR owned asgi.py this run)"
      - "Rejected the deep-audit CORS 'default-src none' suggestion — it would break the Swagger /docs CDN assets (padding/risky)"
      - "ASO/SEO + Launch plan docs deferred (pre-PMF planning; avoid doc-padding) — brand kit was the one genuine Track G asset this run"
  rolling_7d:
    merged_prs: 68               # 60 + 7 feature this run + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON; VERIFIED live this run — a squash merge was BLOCKED "2 of 2 required checks in progress"
  auto_migrate_on_deploy: enabled # 2026-06-29: secret set + Neon PITR on + DB stamped at head & VERIFIED (schema==models); future migrations self-apply on merge
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 7 shipped, 0 abandoned, every reviewer find resolved in 1 cycle, no recurring wall
```
