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
  as_of: 2026-07-07
  last_run: 2026-07-07            # run 30
  last_deep_audit: 2026-07-07    # run 30 ran a FULL 8-agent sweep (functional-reality / backend-correctness+security / doc-freshness+quality-reconcile / business-case-lever ADVERSARIAL stress-test / perf+disjoint-wins / store-readiness+test-coverage + a dead-code/N+1 pass) doubling as a focused audit; last full sweep was run 29. functional-reality found NO release-blocking dead-end (mature repo, all 29 endpoints sound); the business-case stress-test scout independently CONFIRMED (17th run) the team/B2B2C deferral stands on merit (org/seat CODE buildable but seat ARR uncreditable at 0 users = gaming; annual-first/founder pricing computed to LOWER ARPA — owner/GTM-blocked, not artificial scarcity).
  this_run:                      # run 30
    changes_shipped: 2           # #297 salary-negotiation PMF funnel event (asgi.py + src/analytics.py — the ONE generator invisible to the funnel; PMF-first §9) · #298 mobile Settings instanceof-ApiError error-hygiene/consistency fix (settings.tsx + its test) — file-DISJOINT (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # backend verified locally (full suite 490 passed / 9 skipped baseline; #297's new test + test_analytics green key-free; flake8 clean). Mobile jest/tsc not runnable on Linux (no node_modules) — leaned on the required preflight mobile gate + 2 Sonnet reviewers per iOS reality.
    review_rejections: 1         # #298 Reviewer A REQUEST_CHANGES on a REAL blocking test defect: the settings-screen jest.mock factory didn't export ApiError, so the prod change to `e instanceof ApiError` would evaluate `instanceof undefined` → TypeError, reddening 2 failure-path tests (the required mobile jest gate would have caught it). Fixed by mirroring the sibling-test pattern; a FRESH re-reviewer APPROVED (traced both tests green statically). Reviewer B had already APPROVED the prod change. #297's 2 reviewers APPROVED first pass (mutation-verified). Within the ≤2-cycle cap.
    circuit_breaker_trips: 0
    incidents:                   # self-caught + reviewer-caught process notes (recovered, NOT abandonments)
      - "maker≠checker caught a test that would have reddened the required mobile jest gate (#298): the production `instanceof ApiError` change was correct + Reviewer-B-approved, but the co-required test mock didn't export ApiError, so `instanceof undefined` would throw. HOLDING #298's auto-merge until reviewers approved (run-29 rule) meant it was fixed PRE-merge cleanly — not fixed-forward. Re-armed auto-merge only after the fresh re-review APPROVED."
      - "Two scout findings correctly NOT shipped (anti-padding, honest value bar): (a) the backend 'flush 500' finding (check_usage_limits' 30-day-reset flush during login/me response-building) is low-severity + idempotent-safe (the reset recomputes per-request; the write path commits it) — not a user-visible dead-end; (b) src/main.py's ingest N+1 + cli.py's broken orchestrator-method calls are a CLI-ONLY dead path (JobScraperOrchestrator is not imported by asgi.py; import-preview uses the ingestion clients directly) — no product value. Named as deferred/dead-code, not built."
      - "SHARED-TREE DISCIPLINE HELD: every reviewer subagent used `git worktree add /tmp/wt-*` (or read-only in place when the branch was already checked out) and NEVER checked out the main tree. Zero shared-tree incidents."
      - "STALE-LEDGER CATCH: the long-carried 'models.py:315 artifact_type comment is stale' deferral is ALREADY FIXED (the comment lists all 5 persisted types) — verified against code, dropped from the deferred list. Two #297 reviewers surfaced it from stale loop-memory notes; checking the code caught it as a non-issue (don't act on a ledger entry without re-verifying against current code)."
    deferred_decisions:          # named + deferred, NOT abandoned (disjoint rule / value bar / brakes — not dead-ends)
      - "asgi.py-conflicted with #297 this run (only ONE asgi.py PR ships disjoint/run): /api/analytics/pipeline SQL GROUP BY (perf A→A+; line-ref now asgi.py:1996, must still count no-application jobs as SAVED — currently a Python default); Coach-reply per-message id (schema change). Picked the higher-value PMF event this run."
      - "Migrate /profile/resume + /coach/suggestions + /insights/skill-gaps read limits to per-user keying (currently IP-keyed on non-hot paths). Remove now-duplicate salary deterministic eval in tests/test_llm_workflows.py (housekeeping)."
      - "DNS-rebinding SSRF residual — sole remaining url_guard residual; needs a connection-validating transport. Documented, low-priority."
      - "NEW: retire-or-fix the CLI-only dead path — cli.py calls several renamed/nonexistent JobScraperOrchestrator methods (crashes on invoke) + src/main.py's ingest loop has an N+1; both are CLI-only (no HTTP path). Candidate for deletion like the retired Flask app, or a real fix if the CLI is to be supported."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever. Adversarial stress-test scout CONFIRMED (17th consecutive run) it's genuinely owner/GTM-blocked: the org/seat CODE is loop-buildable but crediting seat ARR at 0 users/0 B2B pipeline = gaming; annual-first/founder pricing computed to LOWER Y1 ARPA (wrong direction). native-mobile snapshots + web screenshot regen (design-taste A→A+, needs a running app/emulator); login-lockout cross-instance (recorded decision: CAPTCHA is the fix)."
      - "STORE feature graphic + brand icon + screenshots — OWNER/DESIGNER per BRAND_KIT.md; mobile IAP client + native screenshots — native-build/CI-blocked on Linux."
      - "OWNER-BLOCKED (PENDING_OPS): set Vercel DATABASE_URL→Neon BEFORE next deploy (fail-loud); STRIPE_PRICE_CAREERPLUS_* secrets; mobile IAP client; store asset images (owner/designer); CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml."
  rolling_7d:
    merged_prs: 100            # repo-wide; incl. this run's #297/#298 (+ this bookkeeping) auto-merging through required CI
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # no NEW migration this run (both PRs are code/test — no schema change). Latest head unchanged: f1a2b3c4d5e6.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 9        # +1: github_enrichment (validation=mock — no secret; the unauthenticated GitHub API rate-limits from shared CI IPs so a live happy-path test would flake, the graceful-degrade path is real-observed + mock-pinned)
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 4         # fit-scoring, prep-tools, coach, skill-gap-heatmap. github_enrichment is NOT an LLM feature (structured GitHub API data, no model call) → not on this ratchet; it has its own deterministic golden + mocked round-trip tests.
    with_real_output_eval: 4     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: steady                 # bootstrapping | improving | steady | churning | stuck — run 30: 2 shipped (#297 salary PMF funnel event — PMF-first §9 completeness; #298 mobile Settings error-hygiene/consistency), 0 ABANDONED, 0 circuit-breaker trips, 0 verify-cycle failures, 1 review-rejection ACTIONED (#298 Reviewer A caught a real test-mock defect that would have reddened the required mobile jest gate → fixed pre-merge by mirroring the sibling pattern + fresh re-review APPROVE; #297 both reviewers APPROVE first pass, mutation-verified). Honest scope: a mature repo held below ship by two owner/GTM-blocked ship-critical C's (business-case-strength floor $57.5K<$100K — 17th-run adversarial-confirmed DEFER; store-readiness assets+IAP owner/designer/native), so the run drove the highest-value LOOP-buildable work: the last uninstrumented generator now feeds the PMF funnel, and the lone mobile error-handling outlier now matches the codebase convention. The disjoint rule (one asgi.py PR/run) shaped scope — the perf GROUP BY + read-limit-keying conflicts were deferred, NOT artificial scarcity; two scout findings were correctly NOT shipped as anti-padding (idempotent-safe flush; CLI-only dead-code N+1). No recurring wall → no harness proposal. floor_met_year1 stays false. FYI prior cadence: run 29 = 6 shipped, run 28 = 2 shipped/1 abandoned/2 review-rejections.
```
