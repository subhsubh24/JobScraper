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
  last_run: 2026-06-29            # run 5 of the day
  last_deep_audit: 2026-06-29    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 4           # #96 CORS-lock, #97 Track E visual verification (24 screenshots), #98 authed-nav mobile fix, #99 test coverage (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate (pytest/jest/tsc/flake8/eslint + the Playwright capture) before push
    review_rejections: 2         # #97 (A: scope the screenshot un-ignore to *.png + assert job-detail rendered before the shot), #99 (B: cut a tautological golden-content eval + 2 duplicate moderation tests) — BOTH resolved in 1 re-review cycle; #96/#98 clean first pass both reviewers
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "Playwright version skew: local PW 1.61 wants chromium build 1228 but only 1194 is pre-installed → launch with executablePath:'/opt/pw-browsers/chromium' (temporary, reverted before commit so CI uses its own download). Also use ./node_modules/.bin/playwright, not npx (grabbed a broken global)."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "business-case-strength #1 gap — Career+ tier: dedicated NEXT run (no-enum-migration design: identify Career+ via verified Subscription.plan prefix + ONE exclusive gate + pricing card). Floor-flip needs the TEAM/B2B2C tier (biggest build) — multi-run convergence."
      - "store assets / brand icon (#93/#95): OWNER-BLOCKED per repo standard (loop must not auto-generate a brand mark — slop/DESIGNER QUESTION) + no image tooling installed. Did not fabricate."
      - "accent convergence (#95): dropped (13-file web find-replace + stale-screenshot coherence friction vs the Track E capture; low value) — clean standalone follow-up"
      - "CAPTCHA + N+1 pagination: both want asgi.py (CORS owned it this run) + CAPTCHA needs owner keys; cross-instance rate-limit needs owner Upstash — defer to a clean-asgi.py run"
  rolling_7d:
    merged_prs: 79               # 74 + 4 feature this run + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # 2026-06-29: secret set + Neon PITR on + DB stamped at head & VERIFIED (schema==models); future migrations self-apply on merge
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 4 shipped, 0 abandoned, every reviewer find resolved in 1 cycle, no recurring wall; dual-axis visual review caught a real DOM-passing bug (nav overlap) and shipped the fix same run
```
