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
  last_run: 2026-06-30            # run 8 (fourth run on 2026-06-30)
  last_deep_audit: 2026-06-30    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 3           # #121 perf N+1 eager-load, #122 scorer batch-helper coverage, #123 mobile a11y (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate (pytest/jest/tsc/flake8/eslint) before push
    review_rejections: 3         # ALL 3 PRs drew ONE REQUEST_CHANGES, each a REAL fix resolved within ONE cycle: #121 (A: pipeline_stats missed selectinload(company) + the query-count guard had a blind spot — all jobs shared a company_name so job.company was never dereferenced); #122 (B: the bundled endpoint free-tier-cap test DUPLICATED the journey suite's test_free_tier_job_limit_enforced → removed, PR now scorer-only); #123 (BOTH: replace_all applied the feature-row a11y to only the PREMIUM branch's indent, missing the high-traffic free-tier branch + untested).
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "BRANCH CONTAMINATION (recovered): the scorer-test branch's amend captured asgi.py + test_perf_n1.py (the perf PR's files) into its single commit; Reviewer B's re-review (which reads the DIFF, not the maker's claim) caught the 'scorer-only' branch carrying the entire perf change. RECOVERY: git reset --hard origin/main; restore ONLY the intended file; git add explicit path; commit; force-with-lease; verify the remote diff is a single file before relying on it. The perf change was safe on its own PR throughout. RULE: when a branch diff contradicts what you believe you committed, trust the diff."
      - "replace_all is indentation-sensitive: two 'identical' JSX blocks at different nesting depths are different strings, so replace_all hit only one branch. When a value renders in two branches, edit + verify EACH explicitly. Both reviewers independently caught the half-applied fix."
      - "Scout false-positives caught by skepticism: (a) the test scout called the free-tier job cap 'only unit-tested' but the journey suite already covered it at the HTTP layer; (b) a bonus scout flagged greenhouse departments[0] as crashing on [] but it's guarded (`departments[0]['name'] if departments else None`). No churn fixes built."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "growth/PMF: privacy-safe analytics instrumentation — the PMF measurement foundation, deferred 5+ runs (NEXT is the priority asgi.py owner). DESIGN: AggregateEvent table keyed by event_type+cohort_date+window_date (NO PII/raw events); best-effort record_event() at signup/job-add/fit-score; a read endpoint GATED behind an env shared-secret bearer token (NOT any-authed-user — avoids leaking aggregate user counts), 503 when unset. Wants asgi.py + 1 migration."
      - "business-case-strength: Career+ ($24) tier — the 'genuine exclusive feature' problem is REAL (PREMIUM is already unlimited-everything incl. salary negotiation); a real entitlement needs metering PREMIUM down OR a new exclusive = multi-run design, NOT a clean one-PR change. TEAM/B2B2C tier remains the floor-flip lever (2-3 PRs + owner GTM)."
      - "security: CAPTCHA (needs owner Turnstile/hCaptcha keys; multi-surface web+mobile+asgi). Login lockout left in-memory by design (a shared store doesn't fix its targeted-DoS — CAPTCHA does)."
      - "store (NEW 2026 finding): Apple/Google now require a USER-REPORT/FLAGGING affordance for AI-generated content (GenAI/UGC guidelines) — added to ROADMAP Track D (loop-buildable: report endpoint + coach/prep UI; sprawls asgi.py+web+mobile → dedicated run). Texas SB2420 age-assurance → owner legal decision (PENDING_OPS)."
      - "Track E mobile VISUAL: jest-expo serializes component TREES, not pixels — committed screenshot IMAGES + the prep-pack vision verdict are human/CI (need a real render + an LLM key), NOT loop-buildable headlessly."
      - "store assets / brand icon: OWNER-BLOCKED per repo standard (loop must not auto-generate a brand mark — slop/DESIGNER QUESTION) + no image tooling. Did not fabricate."
  rolling_7d:
    merged_prs: 98               # 94 + 3 feature this run + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # last migration 993d75032689; no new migration this run (perf N+1 needed none — unique=True already indexes the FK)
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 5
    unmet: [ai]                  # degraded_only — surfaced as OWNER_ACTION validation-capability-gemini (urgent)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 3 shipped, 0 abandoned, 0 circuit-breaker trips; maker≠checker earned its keep HARD (all 3 PRs drew a real REQUEST_CHANGES, all fixed within ONE cycle — incl. a branch-contamination catch and a half-applied-fix catch a self-review would have missed); closed the named perf N+1 scorecard gap + real test coverage + mobile a11y for store review; skepticism rejected two scout false-positives (no churn). No recurring wall across runs → no harness proposal warranted.
```
