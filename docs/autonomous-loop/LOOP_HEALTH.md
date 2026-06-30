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
  last_run: 2026-06-30            # run 6 (first run on 2026-06-30)
  last_deep_audit: 2026-06-30    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 3           # #109 referral invite loop, #110 llm fail-loud (empty/malformed completions), #111 mobile design polish (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate (pytest/jest/tsc/flake8/eslint) before push
    review_rejections: 3         # #109 cycle1: BOTH reviewers REQUEST_CHANGES (A: signup-break race on a code-collision IntegrityError; B: register copy blind to ?ref + missing mobile referral surface); cycle2 re-review: 1 more (mobile share link used the API origin, would 404 the web /register). ALL resolved within the 2-cycle cap. #110/#111 clean first pass both reviewers.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "Bash cwd persists between calls: a leftover `cd web`/`cd mobile` silently ran later git/npm from the wrong dir (a `git add` from web/ failed pathspec; an install's `cd web` no-op'd). Use absolute paths or re-cd to the repo root."
      - "MCP enable_pr_auto_merge refuses on mergeable_state=unstable (the non-required Vercel preview deploy pending), even with required checks green. Merged via merge_pull_request (squash) instead — branch protection still gated it (405 'required checks in progress' until preflight+journeys went green), so it was the gate, NOT an --admin bypass."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "business-case-strength: referral loop now BUILT (#109); Career+ tier + TEAM/B2B2C tier remain the named buildable levers for the floor-flip (multi-run convergence; each wants asgi.py + real value-differentiation)."
      - "security (B): CAPTCHA (needs owner Turnstile/hCaptcha keys; multi-surface web+mobile+asgi) + cross-instance rate-limit/spend-ceiling (Postgres-backable, no owner key, but wants asgi.py — referral owned it this run). Next clean-asgi.py run."
      - "performance (B): N+1 eager-load on /api/jobs + /api/analytics/pipeline — wants asgi.py (referral owned it). Defer to a clean-asgi.py run."
      - "growth/PMF: privacy-safe analytics instrumentation (aggregate counters, new table) — wants asgi.py; strongest pre-launch measurement foundation. Defer to a clean-asgi.py run."
      - "store assets / brand icon: OWNER-BLOCKED per repo standard (loop must not auto-generate a brand mark — slop/DESIGNER QUESTION) + no image tooling. Did not fabricate."
  rolling_7d:
    merged_prs: 87               # ~79 + GTM sync PRs (#105-108) + 3 feature this run + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # referral migration c3f2a9b41d77 (users.referral_code/bonus_prep_packs + referrals table) drift-gated + auto-applies on merge
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 5
    unmet: [ai]                  # degraded_only — surfaced as OWNER_ACTION validation-capability-gemini (urgent)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 3 shipped, 0 abandoned; maker≠checker earned its keep hard (reviewers caught a real signup-breaking race + a 404-ing share link, both fixed within the cycle cap); built the #1 named business-case lever (referral) that had been deferred for several runs
```
