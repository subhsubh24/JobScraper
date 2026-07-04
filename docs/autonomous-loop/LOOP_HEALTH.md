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
  as_of: 2026-07-04
  last_run: 2026-07-04            # run 26
  last_deep_audit: 2026-07-04    # run 26 ran a full 6-scout sweep (functional-reality / backend-correctness+security / disjoint-wins+deferral-verify / doc-freshness+quality-reconcile / design-taste / business-case+PMF) doubling as the DEEP AUDIT — the last FULL sweep was run 18 (~8 runs prior). Backend-correctness scout found NO new ship-critical break (core paths sound); design scout found only marginal scale-purism nits (skipped as anti-padding).
  this_run:                      # run 26
    changes_shipped: 4           # #265 CENTERPIECE drafter→reviewer pass on AI artifacts (src/enrichment/llm_workflows.py + evals) · #267 web ReportButton artifact-id · #268 mobile ReportButton artifact-id · #266 GET job-detail joinedload perf — all file-DISJOINT → parallel auto-merge (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # centerpiece verified locally in full: backend 422 pytest (+10 new refine evals) + flake8 + 5 deterministic gates (eval-coverage/validation/blocks/GTM/quality) all green. perf PR: 14 job/perf tests green + flake8. web/mobile: no node_modules locally (per iOS reality) → leaned on the required-CI mobile+web tsc/lint/jest, all merged through required CI (preflight + web E2E) green.
    review_rejections: 1         # #266 perf: Reviewer B REQUEST_CHANGES on the PATCH half (an untested marginal 7→6 half-measure — post-db.refresh re-serialization defeats the joinedload). ACTIONED within the ≤2-cycle cap by dropping PATCH (the reviewer's own prescribed resolution), keeping the both-approved GET 4→1 win. Other 7 reviewers APPROVE (centerpiece A mutation-verified 3 guards load-bearing; B's 2 non-blocking wording/log nits folded in).
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "maker≠checker on a perf PR (the review-rejection this run): the PATCH /api/jobs/{id} joinedload LOOKED like a symmetric win but Reviewer B's instrumented run showed 7→6 (not 4→1) — after db.commit()+db.refresh(job) the response re-serialization lazy-loads all 3 relationships again, so the joinedload saved only the pre-commit read. Dropped PATCH (reviewer-prescribed), kept the solid GET win. RULE: an eager-load before a commit+refresh does NOT help the post-refresh serialization; verify the query count across the commit boundary, not just before it."
      - "STRAY WORKING-TREE LEAK (self-caught, no impact): after committing the web PR on its branch, the web files showed as staged on a later branch checkout. The pushed branches were all CLEAN (verified `git show --stat HEAD` per branch — centerpiece was llm_workflows-only). Discarded the stray copies with `git restore --staged --worktree`. RULE: `git status --short` before every commit; never trust a -B checkout to have discarded prior working changes."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "PATCH /api/jobs/{id} post-refresh serialization (#266's dropped half): re-fetch with joinedload after commit / drop the refresh+lazy pattern, plus a reliable cross-commit query-count regression test. A real but untested-as-shipped win — earns its own focused PR."
      - "Coach-reply ReportButton passes session id, not a message id (both web+mobile coach surfaces): a moderator can't tell WHICH coach reply in a session was flagged. Needs a backend per-message id (a schema change) — honestly scoped out of the artifact-id fix this run."
      - "/api/analytics/pipeline SQL GROUP BY (perf A→A+): DELIBERATELY not done this run — low-severity, already-batched (3 queries, no N+1), and the status-count rewrite has a subtle null-application→SAVED coalesce edge; the GET joinedload was the distinct, safe hot-path win instead."
      - "Profile enrichment from linked public sources = the NEXT Track-A item (the market's /expand; owner-authorized fetch, source-tagged, real-output eval)."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever (owner-blocked GTM). Re-confirmed DEFER (13th consecutive run). native-mobile snapshots + web SCREENSHOT REGEN (design-taste A→A+ — needs a running app/emulator); login-lockout cross-instance (recorded decision: CAPTCHA is the fix)."
      - "OWNER-BLOCKED (PENDING_OPS): set Vercel DATABASE_URL→Neon BEFORE next deploy (fail-loud); STRIPE_PRICE_CAREERPLUS_* secrets; mobile IAP client; store asset images; CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml."
  rolling_7d:
    merged_prs: 87             # repo-wide across all routines; incl. this run's #265/#266/#267/#268 (+ this bookkeeping)
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run (all 4 PRs are app-code/tests/copy only). Latest migration remains d4e7a1c9b8f2.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 8        # unchanged (no new external dependency this run)
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 4         # fit-scoring, prep-tools (prep pack + cover letter + study plan + tailored résumé + salary negotiation — one module), coach, skill-gap-heatmap (learning plan — LLM half; the ranking is deterministic/key-free)
    with_real_output_eval: 4     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py); check_eval_coverage.py --report → 4 features, all with deterministic + real-output evals
  signal: improving              # bootstrapping | improving | steady | churning | stuck — run 26: 4 shipped, 0 abandoned, 0 circuit-breaker trips, 0 verify-cycle failures, 1 review-rejection ACTIONED (not a net loss: #266 perf PATCH half dropped per the reviewer's own prescription, keeping the both-approved GET win; the other 7 per-change reviewers APPROVE). Built the named next centerpiece — the drafter→reviewer pass on AI artifacts (#265, product-side maker≠checker → the Track A box TICKS) — plus the web+mobile ReportButton artifact-id compliance fix (#267/#268, closing run-25's named deferral) and a GET job-detail joinedload perf win (#266). maker≠checker EARNED ITS KEEP on the perf PR: Reviewer B's instrumented run caught that the PATCH joinedload saved only 1 of 7 queries (post-db.refresh re-serialization defeats it) — a marginal untested half-measure — and I dropped it, converging within ≤2 cycles rather than shipping padding. Reviewer A mutation-verified the centerpiece's 3 guards load-bearing; Reviewer B's 2 non-blocking wording/log nits folded in. Signal 'improving': converted the prior runs' named deferral (drafter→reviewer) into a shipped, box-ticking centerpiece AND closed run 25's ReportButton artifact-id deferral — the loop finishing what it planned, three runs running. floor_met_year1 stays false (no honest pre-launch lever; TEAM/B2B2C DEFER, 13th run). No recurring wall → no harness proposal. Next centerpiece named: profile enrichment from linked public sources (Track A). FYI: run 25 was 3 shipped / 0 abandoned / 0 review-rejections.
```
