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
  last_run: 2026-07-05            # run 28
  last_deep_audit: 2026-07-05    # run 28 ran a focused 6-scout sweep (business-case-lever / store-readiness-buildable / functional-reality / correctness+security / perf+disjoint-wins / doc-freshness+quality-reconcile) doubling as an audit; the last FULL deep audit was run 26 (~2 days). The functional-reality scout surfaced a real release-blocking dead-end (résumé had no post-signup edit path); the security scout surfaced a CRITICAL redirect-SSRF.
  this_run:                      # run 28
    changes_shipped: 2           # #276 CENTERPIECE résumé view/edit in Settings — closes a release-blocking DEAD-END gating the tailored-résumé + skill-gap features (asgi.py + web + mobile + api clients + tests) · #277 CRITICAL redirect-based SSRF closed in the ATS careers-page probe (src/ingestion) — file-DISJOINT → parallel merge (+ this bookkeeping)
    changes_abandoned: 1         # #278 store feature graphic — see abandoned_reasons
    abandoned_reasons:           # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
      - {change: "#278 auto-generated Google Play feature graphic", reason: "review_value/blocked_owner — BOTH Sonnet reviewers REQUEST_CHANGES: docs/brand/BRAND_KIT.md:78-80 explicitly designates the feature graphic OWNER/DESIGNER work the loop 'does not auto-generate' (generic-AI-slop risk), loop-memory run-24 already rejected it as padding/GTM-territory, it tripped VISION's AVOID-list (decorative gradient+glow), and preflight already expects an owner-provided feature_graphic.png. A re-attempted recorded DEAD-END the store-readiness scout re-surfaced; ledger+maker≠checker correctly killed it. RULE: check a store/marketing scout candidate against BRAND_KIT + the loop-memory dead-end ledger BEFORE building."}
    verify_cycle_failures: 1     # #276 mobile jest reddened in required CI: my failed-save ResumeCard test asserted the fallback copy while the card surfaces e.message (sibling pattern); fixed the mock's error message (1 cycle). Backend verified locally: 477 pytest (#276, +8 résumé tests incl. an end-to-end dead-end-unblock) / 484 (#277, +7 SSRF tests, mutation-verified) + flake8; web/mobile: no node_modules locally (iOS reality) → leaned on required-CI web E2E + mobile jest, which EARNED its keep.
    review_rejections: 2         # #276 Reviewer B REQUEST_CHANGES (mobile jest mock lacked getResume/saveResume → mount effect would throw) → added mocks + 2 ResumeCard tests, fresh re-reviewer APPROVE; Reviewer A APPROVE first pass (mutation-verified). #278 BOTH reviewers REQUEST_CHANGES → abandoned (correct). maker≠checker + the deterministic CI EACH caught a distinct real defect the other missed on #276.
    circuit_breaker_trips: 0
    incidents:                   # self-caught + reviewer-caught process notes (recovered, NOT abandonments)
      - "SHARED-TREE HAZARD (recovered): a Reviewer subagent ran `git checkout` in the shared /home/user/JobScraper working tree and moved HEAD, so my SSRF commit landed on the résumé branch instead of its own. Untangled via `git checkout -B ssrf-branch origin/main && git cherry-pick <sha>` (disjoint files → clean) + reset the résumé branch to its pushed state. RULE (now enforced): every reviewer/parallel subagent MUST `git worktree add /tmp/wt-*` and NEVER checkout/reset in the main tree — all reviewers after the incident complied cleanly. Echoes the run-25 worktree pattern."
      - "maker≠checker + CI double-catch (#276): the mobile Résumé card fires `api.getResume()` on mount; the existing settings-screen jest mock (hand-mocked object literal, no automock) lacked it → every render would throw, reddening the mobile gate — Reviewer B caught it pre-CI. Then CI caught my failed-save test asserting the wrong error copy. RULE: adding a component whose effect calls a NEW api method means updating that screen-test's hand-mock in the SAME change, AND matching the test's error assertion to how the component surfaces the error (e.message vs a fixed fallback)."
      - "maker≠checker (#271, both reviewers, independently + empirically): `requests.ConnectTimeout` subclasses BOTH `Timeout` AND `ConnectionError`, so the retry helper's bare `except ConnectionError` RETRIED a connect-timeout → up to ~3×20s ≈ 61.5s, overrunning the 60s Vercel budget the retry exists to respect (DEEP_DIAGNOSIS rule a) — the exact failure it was built to prevent. Fixed with `except requests.Timeout: raise` BEFORE the ConnectionError clause + a regression test using the concrete ConnectTimeout. RULE: the `requests` exception hierarchy is a trap — catch `Timeout` first when Timeout and ConnectionError must diverge."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "/api/analytics/pipeline SQL GROUP BY (perf A→A+, asgi.py) + rate-limit hardening on read endpoints (GET /api/auth/me, /api/referrals/me, /api/profile/enrichment, /api/jobs — HIGH-ish consistency) + salary-negotiation analytics event — ALL asgi.py, conflicted with #276's asgi.py ownership this run (disjoint rule); clean next-run PRs."
      - "DNS-rebinding SSRF residual — the sole remaining url_guard residual after #277 closed the redirect vector; needs a connection-validating transport (validate at connect time, not just pre-resolve). Documented, low-priority."
      - "Coach-reply ReportButton passes session id, not a message id (both web+mobile coach surfaces): needs a backend per-message id (schema change)."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever (owner-blocked GTM; crediting seat ARR at 0 users = gaming). Re-confirmed DEFER (15th consecutive run). Annual-first is already presented-first on the pricing page (a default toggle is marginal churn; a 'founder-pricing cutoff' would be dead config). native-mobile snapshots + web SCREENSHOT REGEN (design-taste A→A+ — needs a running app/emulator); login-lockout cross-instance (recorded decision: CAPTCHA is the fix)."
      - "STORE feature graphic + brand icon + screenshots — OWNER/DESIGNER work per BRAND_KIT.md (the loop must NOT auto-generate them; re-confirmed by abandoning #278). Screenshots additionally need a running build."
      - "OWNER-BLOCKED (PENDING_OPS): set Vercel DATABASE_URL→Neon BEFORE next deploy (fail-loud); STRIPE_PRICE_CAREERPLUS_* secrets; mobile IAP client; store asset images (owner/designer); CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml."
  rolling_7d:
    merged_prs: 92             # repo-wide; incl. this run's #276/#277 (+ this bookkeeping) pending auto-merge through required CI
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NEW migration this run: f1a2b3c4d5e6 (enriched_competencies), down_revision d4e7a1c9b8f2 — drift-gated, auto-applies on merge. Now the latest head.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 9        # +1: github_enrichment (validation=mock — no secret; the unauthenticated GitHub API rate-limits from shared CI IPs so a live happy-path test would flake, the graceful-degrade path is real-observed + mock-pinned)
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 4         # fit-scoring, prep-tools, coach, skill-gap-heatmap. github_enrichment is NOT an LLM feature (structured GitHub API data, no model call) → not on this ratchet; it has its own deterministic golden + mocked round-trip tests.
    with_real_output_eval: 4     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: steady                 # bootstrapping | improving | steady | churning | stuck — run 28: 2 shipped (#276 résumé-edit DEAD-END fix cross-stack, #277 CRITICAL redirect-SSRF), 1 ABANDONED (#278 feature graphic — review_value/blocked_owner: BOTH reviewers rejected a re-attempt of a BRAND_KIT-recorded owner/designer dead-end a scout re-surfaced; healthy kill, not churn), 0 circuit-breaker trips, 1 verify-cycle failure (my #276 mobile failed-save test copy — the required CI caught it, fixed in 1 cycle), 2 review-rejections ACTIONED. maker≠checker AND the deterministic CI EACH caught a distinct real #276 defect neither the other nor the local run would have: Reviewer B the mobile mock throw, CI the wrong error assertion. #278's abandonment is the deadend-ledger + maker≠checker doing exactly their job — a store-asset scout re-surfaced a candidate the docs had already ruled owner/designer. floor_met_year1 stays false (TEAM/B2B2C DEFER, 15th run — genuinely owner/GTM-blocked, not code-blocked). No recurring wall → no harness proposal. Pattern across runs 23–28 (mature repo): high-value, well-reviewed, coherent units sized to the honest work — a real dead-end fix + a CRITICAL security closure this run; abandoning a mis-selected candidate is the value bar working, not a regression. FYI: run 27 was 2 shipped / 0 abandoned / 2 review-rejections.
```
