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
  as_of: 2026-07-02
  last_run: 2026-07-02            # run 14
  last_deep_audit: 2026-07-02    # run 14's FULL 8-scout sweep (functional-reality/security/business-case/store+freshness/backend-correctness/web-design/mobile-design/perf+quality-reconcile)
  this_run:
    changes_shipped: 4           # #168 scoring wallet-drain ceiling (asgi.py), #169 greenhouse KeyError, #171 mobile emoji→icon, #172 store-docs 3-tier + Apple 5.1.2(i) AI-consent (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate before push: backend 278 pass + flake8 clean; mobile tsc --noEmit + expo lint 0 + jest report-button 2/2. My own atomicity regression test caught a wrong assertion form (TestClient re-raises) once, fixed before push — not a gate failure.
    review_rejections: 2         # TWO formal REQUEST_CHANGES, both on #168, BOTH the SAME real atomicity bug found INDEPENDENTLY by both Sonnet reviewers, fixed cycle 1 (moved _consume_counter before the job writes; added a load-bearing regression test). All other 6 reviewer passes APPROVED first-pass (#169 x2, #171 x2, #172 x2); the 2 fresh re-reviewers on #168 APPROVED after the fix (mutation-verified the test in isolated worktrees).
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "maker≠checker's headline win: BOTH #168 reviewers INDEPENDENTLY caught that _consume_counter's eager commit turns 'meter after db.add(job)/db.flush()' into a two-transaction split → a failure in between could ORPHAN a JobPosting (no Application/usage row) + bypass the free-tier count. Fixed by moving the meter BEFORE any write; added a regression test proven load-bearing (a re-reviewer reproduced the pre-fix ordering in a worktree → orphan → test fails). RULE: any NEW _consume_counter call site MUST run before the endpoint's real writes (its 'check before real work' contract)."
      - "SKEPTICISM killed two scout false-positives before building: mobile 'job score not grouped for screen readers' was FALSE (the JobRow Pressable already carries a full accessibilityLabel incl. the fit score); markdown list/listitem a11y roles dropped (unsupported-RN-AccessibilityRole tsc risk on a marginal gain). Verified against code, built neither."
      - "STALE ARTIFACT (not a bug): the scorecard + web-design scout keep flagging a 390px header email-overlap in app-dashboard-empty-mobile.png, but the LIVE layout.tsx already has `hidden sm:block` (email hidden <640px). Confirmed by opening the PNG — the committed screenshot is stale (pre-fix), NOT a live bug. Regen needs node+Playwright+backend+DB (heavy); deferred, recorded for the Quality Auditor."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "Apple 5.1.2(i) third-party-AI CONSENT GATE (NEW, ship-critical, loop-buildable) — explicit unbundled revocable consent before sending resume/JD/coach text to Gemini; a privacy-policy blanket does NOT satisfy it. Cross-stack (backend gate + web + mobile UI + revoke) → dedicated next-run centerpiece (ROADMAP Track D, ACCEPTANCE_AUDIT A11). Documented, not rushed into this run (same discipline as GenAI report #142)."
      - "TEAM/B2B2C tier — still the PRIMARY named floor-lever (business-case scout re-confirmed with cited benchmarks that NO loop-buildable lever honestly flips $100K pre-launch; crediting team ARR at 0 users = gaming). Multi-run epic + owner GTM."
      - "coach 100-msg/mo enforcement (doc↔code honesty — Pro gets unlimited today; wants the migration slot); Pro→Career+ in-place upgrade via Stripe portal; Career+ upgrade-rate wedges (voice mock / company dossier)."
      - "web SCREENSHOT REGEN (design-taste A→A+ artifact refresh — the stale 390px shot); /api/jobs/{id} N+1 + /api/analytics/pipeline pagination + free-tier TOCTOU (pre-launch 0-row polish, carried)."
      - "OWNER-BLOCKED (PENDING_OPS): mobile Career+ IAP client (RevenueCat keys/store accounts); store asset images/brand icon; CAPTCHA keys; CAREERPLUS_* Stripe price IDs."
  rolling_7d:
    merged_prs: 56              # CORRECTED to the true 7-day window (git log origin/main --since 7d, repo-wide across all routines). The prior 126 was a mislabeled cumulative running total, not a rolling-7d count — fixed to match the field name (honesty > continuity).
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run — #168 uses the existing RateCounter table (new `score_daily` bucket, no schema change). Latest migration remains b2c8d4e6f1a5.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 6
    unmet: []                    # ai closed 2026-07-02: GEMINI_API_KEY added to CI, test_llm_live.py real round-trip green
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 3         # fit-scoring, prep-pack, coach
    with_real_output_eval: 3     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 4 shipped, 0 abandoned, 0 circuit-breaker trips. Headline: a full 8-scout deep audit found NO ship-critical functional break; shipped a real §12 wallet-drain defense (metering the previously-unmetered job-scoring embedding call), a real external-data crash fix (greenhouse KeyError), a VISION emoji-as-icon fix on the store-required report control, and a store-copy honesty/re-validation pass that ALSO surfaced a NEW ship-critical loop-buildable store gap (Apple 5.1.2(i) third-party-AI consent → queued as the dedicated next-run epic). maker≠checker earned its keep HARD: both #168 reviewers independently caught a real atomicity bug (eager-commit two-transaction split → orphaned rows), fixed cycle 1 with a load-bearing regression test. HONEST on the number: business-case scout re-confirmed (cited benchmarks) that no loop-buildable lever flips the $100K floor pre-launch — floor_met_year1 stays false; TEAM/B2B2C remains the primary lever. No recurring wall → no harness proposal warranted.
```
