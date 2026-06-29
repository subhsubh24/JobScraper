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
  last_run: 2026-06-29            # run 4 of the day
  last_deep_audit: 2026-06-29    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 5           # #85 scorer NaN guard, #86 prep moderation, #87 mobile RevenueCat webhook, #88 paywall entitlement, #89 web visual hierarchy (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate (pytest/jest/tsc/flake8/eslint) on the first run before push
    review_rejections: 2         # #85 (B: drop out-of-scope normal-path test + redundant assert), #87 (A: add PAUSED to revoke set + a malformed-JSON 400 test) — BOTH resolved in 1 re-review cycle; #86/#88/#89 clean first pass both reviewers
    circuit_breaker_trips: 0
    incidents:                   # self-caught process foot-guns (recovered, NOT abandonments)
      - "git add -A swept the reviewer worktrees (.claude/worktrees/*) + cross-branch files into a post-review trim commit; caught via the push warning + git show --stat; reset --hard + explicit `git add <path>` to recover. RULE: never `git add -A` once reviewer worktrees exist — stage explicit paths."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar — not dead-ends)
      - "CAPTCHA: still a coherent web+mobile+api unit wanting asgi.py (owned by mobile billing this run) — defer to a clean-asgi.py run"
      - "privacy-safe server-side analytics (aggregate counters): marketing scout's top pick but wants asgi.py + a new table/migration — defer to a clean-asgi.py run (PMF measurement foundation, pre-launch)"
      - "on-device react-native-purchases SDK (Track C line 114): native + owner-blocked (needs RevenueCat keys) — server half shipped this run"
  rolling_7d:
    merged_prs: 74               # 68 + 5 feature this run + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # 2026-06-29: secret set + Neon PITR on + DB stamped at head & VERIFIED (schema==models); future migrations self-apply on merge
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 5 shipped, 0 abandoned, every reviewer find resolved in 1 cycle, no recurring wall (the git add -A incident was a one-time self-caught foot-gun, now a recorded rule)
```
