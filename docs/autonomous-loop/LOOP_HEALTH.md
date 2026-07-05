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
  as_of: 2026-07-05
  last_run: 2026-07-05            # run 29
  last_deep_audit: 2026-07-05    # run 29 ran a FULL 6-scout sweep (functional-reality / backend-correctness+security / disjoint-wins-ranking / test-eval-coverage / doc-freshness+quality-reconcile / business-case+store deferral STRESS-TEST) doubling as a focused audit; the last FULL deep audit was run 26. functional-reality found NO release-blocking defect (mature repo); the business-case stress-test scout independently CONFIRMED the team/B2B2C deferral stands on merit (genuinely owner/GTM-blocked, not artificial scarcity).
  this_run:                      # run 29
    changes_shipped: 6           # #289 per-user rate-limiting on 6 authed reads (§12; asgi.py) · #290 prep-pack deterministic content-quality eval (tests-evals A→A+) · #291 salary-negotiation eval parity (deterministic+live) · #293 coverage floor 75→85 · #292 ROUTE_INVENTORY §14 refresh + #294 its reviewer-caught path-inaccuracy fix-forward — all file-DISJOINT → parallel auto-merge (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # backend verified locally each PR (full suite 486 green on #289; prep-pack/salary evals green key-free; coverage floor 91.50%>85 via the exact CI cmd). Self-caught the #289 test's shadow-row seeding bug (the first loop's real requests created a counter row shadowing the seed) BEFORE push — restructured to seed-before-call; not a CI failure.
    review_rejections: 1         # #292 BOTH reviewers REQUEST_CHANGES on a REAL doc inaccuracy I introduced (GitHub-enrichment bullet conflated POST /profile/enrich/github [Pro] with GET/DELETE /profile/enrichment [free, DIFFERENT path]). #292 had already auto-merged on green CI → fixed forward in #294 (both reviewers APPROVE, source-verified). The other 8 reviewer passes (#289/#290/#291/#293, 2 each) APPROVED first pass, several mutation-verified.
    circuit_breaker_trips: 0
    incidents:                   # self-caught + reviewer-caught process notes (recovered, NOT abandonments)
      - "AUTO-MERGE OUTRAN maker≠checker (#292): auto-merge gates on the required CI checks, NOT on my reviewer subagents, so #292 merged on green CI while its 2 reviewers were still running — both then caught a real doc path-inaccuracy, forcing a fix-forward (#294) instead of a pre-merge fix. RULE (applied to #294): when reviewer scrutiny is likely to matter (anything beyond the most trivial), HOLD auto-merge until BOTH reviewers APPROVE, then enable it. CI catches broken code; it does NOT catch a plausible-but-wrong doc/claim — that is exactly maker≠checker's job, so don't let CI outrun it."
      - "maker≠checker earned its keep on a DOC PR (#292→#294): two INDEPENDENT reviewers, from different angles, caught the SAME route-path conflation by cross-checking asgi.py — a doc whose whole purpose is a precise route checklist must state the real paths/gates. Reviewer B on #291 separately found docs/ci/EVAL_COVERAGE.md was FALSELY GREEN at the per-function level (the gate only checks file-existence, so a per-function coverage gap was invisible) — #291 closed the salary real-output gap."
      - "SHARED-TREE DISCIPLINE HELD (run-28 lesson applied): every reviewer/parallel subagent used `git worktree add --detach /tmp/wt-*` and NEVER checked out the main tree — several reviewers explicitly noted the main tree's branch changed under them mid-review and correctly avoided it. Zero shared-tree incidents this run (vs 1 recovered in run 28)."
    deferred_decisions:          # named + deferred, NOT abandoned (disjoint rule / value bar / brakes — not dead-ends)
      - "asgi.py-conflicted with #289 this run (only ONE asgi.py PR ships disjoint/run): /api/analytics/pipeline SQL GROUP BY (perf A→A+); salary-negotiation analytics event (analytics.record_event + EVENT_TYPES — the ONE generator invisible to the PMF funnel; asgi.py:1448 + src/analytics.py); Coach-reply per-message id (schema change). Clean next-run PRs."
      - "Migrate /profile/resume + /coach/suggestions + /insights/skill-gaps read limits to per-user keying (Reviewer-B #289 follow-up — currently IP-keyed on non-hot paths). Remove now-duplicate salary deterministic eval in tests/test_llm_workflows.py (housekeeping, #291)."
      - "DNS-rebinding SSRF residual — sole remaining url_guard residual; needs a connection-validating transport. Documented, low-priority."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever. Adversarial stress-test scout CONFIRMED (16th consecutive run) it's genuinely owner/GTM-blocked: the CODE is loop-buildable but crediting seat ARR at 0 users/0 B2B pipeline = gaming (block is the honest projection + sales motion, NOT code); annual-first ENFORCEMENT is buildable but ~$3-5K, insufficient. native-mobile snapshots + web screenshot regen (design-taste A→A+, needs a running app/emulator); login-lockout cross-instance (recorded decision: CAPTCHA is the fix)."
      - "STORE feature graphic + brand icon + screenshots — OWNER/DESIGNER per BRAND_KIT.md; mobile IAP client + native screenshots — native-build/CI-blocked on Linux."
      - "OWNER-BLOCKED (PENDING_OPS): set Vercel DATABASE_URL→Neon BEFORE next deploy (fail-loud); STRIPE_PRICE_CAREERPLUS_* secrets; mobile IAP client; store asset images (owner/designer); CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml."
  rolling_7d:
    merged_prs: 98             # repo-wide; incl. this run's #289/#290/#291/#292/#293/#294 (+ this bookkeeping) auto-merging through required CI
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # no NEW migration this run (all 6 PRs are code/test/doc/config — no schema change). Latest head unchanged: f1a2b3c4d5e6.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 9        # +1: github_enrichment (validation=mock — no secret; the unauthenticated GitHub API rate-limits from shared CI IPs so a live happy-path test would flake, the graceful-degrade path is real-observed + mock-pinned)
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 4         # fit-scoring, prep-tools, coach, skill-gap-heatmap. github_enrichment is NOT an LLM feature (structured GitHub API data, no model call) → not on this ratchet; it has its own deterministic golden + mocked round-trip tests.
    with_real_output_eval: 4     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: steady                 # bootstrapping | improving | steady | churning | stuck — run 29: 6 shipped (#289 §12 per-user read rate-limiting, #290 prep-pack content eval, #291 salary eval parity, #293 coverage floor 75→85, #292 ROUTE_INVENTORY §14 refresh, #294 its fix-forward), 0 ABANDONED, 0 circuit-breaker trips, 0 verify-cycle failures, 1 review-rejection ACTIONED (#292 → #294). Three of the five distinct changes directly closed named QUALITY_SCORECARD tests-evals A→A+ top_gaps (prep-pack content eval, salary eval parity, coverage floor); one closed a real §12 security gap; one fixed real §14 doc drift. maker≠checker earned its keep on a DOC PR: both #292 reviewers independently caught a route-path inaccuracy CI could never catch → fix-forward #294. KEY PROCESS LESSON: auto-merge gates on CI, not on my reviewer subagents, so #292 merged before its reviewers finished — now HOLD auto-merge until both reviewers APPROVE when scrutiny matters (applied to #294). floor_met_year1 stays false (TEAM/B2B2C DEFER, 16th run — an adversarial stress-test scout independently confirmed it's genuinely owner/GTM-blocked, NOT artificial scarcity: the code is buildable but seat ARR can't be honestly credited at 0 users/0 pipeline). No recurring wall → no harness proposal. Pattern across runs 23–29 (mature repo): high-value, well-reviewed, coherent file-disjoint units sized to the honest work; the disjoint rule (one asgi.py PR/run) shaped scope, NOT artificial scarcity. FYI: run 28 was 2 shipped / 1 abandoned / 2 review-rejections.
```
