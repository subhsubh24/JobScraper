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
  as_of: 2026-07-03
  last_run: 2026-07-03            # run 22
  last_deep_audit: 2026-07-03    # run 18's full 8-scout sweep was the last FULL deep audit; runs 19–22 ran focused sweeps (< 24h since). Run 22 leaned on the FRESH 3rd independent QUALITY_SCORECARD (same-day, HEAD-matched) as its comprehensive-audit signal.
  this_run:                      # run 22
    changes_shipped: 3           # #234 moderated-decline §6 fix (asgi.py+llm_workflows+tests) · #235 drop unbuilt "Priority fit scoring" claim (web pricing + mobile paywall) · #236 deterministic JWT-forgery test (flaky required-CI security guard) — all file-disjoint (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # backend green (380 non-live) before the follow-ups; #234 rebased onto main post-#236 so its CI used the deterministic auth test. web/mobile not runnable locally (node_modules absent by design) — relied on the required CI checks.
    review_rejections: 1         # #235 cycle-1 Reviewer A REQUEST_CHANGES (real incompleteness: the identical false line was still live on mobile/src/app/paywall.tsx) → fixed cycle-2, both fresh reviewers APPROVE. #234 both cycle-1 reviewers APPROVED the core but Reviewer A flagged a coverage-composition gap (endpoint test stubbed the whole workflow) → strengthened to drive the REAL _call_llm end-to-end (mutation-verified), both cycle-2 reviewers APPROVE. #236 both APPROVE first pass.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "maker≠checker WIN #1 (#235): my first cut removed the false 'Priority fit scoring' Pro claim only from the WEB pricing page; BOTH cycle-1 reviewers independently caught the IDENTICAL line still live on mobile/src/app/paywall.tsx. RULE: when a false/duplicated claim (or any copy) appears in one client, grep ALL clients (web + mobile) — a shared feature list is usually mirrored, and fixing one surface leaves the lie live on the other."
      - "maker≠checker WIN #2 (#234): the endpoint moderated-decline regression test stubbed the whole LLMWorkflows (raised ModeratedContentError directly), so it proved only the endpoint HANDLER, not the moderation→raise wiring — a self-review would have shipped it. Strengthened to patch the get_llm_client seam and drive the REAL _call_llm→ContentModerator→raise end-to-end; mutation-verified it now reddens if the fix regresses (the stub stayed green)."
      - "SCOUT REFUTED (anti-padding): the web+mobile design scout's 'mobile coach send-button 20-24px touch target' rested on a wrong premise — RN's default alignItems:stretch makes the button match the input-row height (its own justifyContent:center confirms it's stretched taller than its text), so it's ~36px not 20px. Verified against the code, built nothing. (Its other finding — the delete-account bare-red-text button — is a defensible intentional low-emphasis for a destructive action, like the #171 report control; skipped.)"
      - "FLAKY SECURITY TEST (fixed #236): test_tampered_signature_is_rejected reddened once during this run's full-suite pass but passed 5/5 in isolation — a time-dependent base64 malleability flake (last-char flip is a no-op when its 2 low bits are padding). A false-red on a REQUIRED-CI security guard is a merge hazard; fixed deterministically as its own disjoint PR rather than ignored."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "create_job idempotency DB unique-constraint (belt-and-suspenders for the check-then-insert TOCTOU; needs a migration + asgi.py, which #234 owned this run) — run-17-acknowledged fast-follow, not a live bug pre-launch."
      - "salary-negotiation endpoint missing an analytics event (cover-letter/study-plan/prep-pack all record one) — minor instrumentation parity; needs the src/analytics.py allowlist too, out of #234's single-concern scope."
      - "issue #222 LOW get_session_summary None-guard — still UNROUTED dead code; guard before wiring any summary endpoint (marginal today, not padding to defer)."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever (Career+/annual-first/referral all built). A genuine MULTI-RUN epic; crediting seat ARR at 0 users = gaming, so it does NOT honestly flip $100K pre-launch. Business-case scout re-confirmed DEFER (9th consecutive run)."
      - "login-lockout cross-instance (RECORDED DECISION: kept in-memory — a shared store amplifies targeted-DoS; CAPTCHA is the real fix, owner-gated); native-mobile component snapshots + web SCREENSHOT REGEN (design-taste A→A+ — needs a running app / native emulator); /api/analytics/pipeline SQL GROUP BY + GET /api/jobs/{id} selectinload (pre-launch 0-row polish)."
      - "OWNER-BLOCKED (PENDING_OPS): set Vercel DATABASE_URL→Neon BEFORE next deploy (fail-loud); STRIPE_PRICE_CAREERPLUS_* secrets (nightly reddens without them); mobile IAP client; store asset images; CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml."
  rolling_7d:
    merged_prs: 73             # repo-wide across all routines; incl. this run's #234/#235/#236 (+ this bookkeeping)
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run (all 3 PRs are app-code/tests only). Latest migration remains d4e7a1c9b8f2.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 8        # unchanged (no new external dependency this run)
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 3         # fit-scoring, prep-tools (prep pack + cover letter + study plan — one module), coach
    with_real_output_eval: 3     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: steady                 # bootstrapping | improving | steady | churning | stuck — run 22: 3 shipped, 0 abandoned, 0 circuit-breaker trips, 0 verify-cycle failures, 1 review rejection (#235 mobile-paywall incompleteness) resolved cleanly cycle-2. Shipped a coherent honesty/integrity set: #234 fixed the run-21-DEFERRED §6 fake-success bug (a moderated LLM decline was persisted as the user's 'generated' prep pack + charged a usage + reported success:true) — the most dangerous failure class per §6, even though the moderation event is rare; #235 removed a false 'Priority fit scoring' Pro claim from BOTH customer-facing surfaces (web + mobile); #236 killed a false-red flake on a required-CI security guard test. maker≠checker earned its keep on TWO of the three (the mobile-paywall duplicate + the #234 coverage-composition gap), both caught by reviewers and converged within ≤2 cycles. Anti-padding held at SELECTION: REFUTED a scout's mobile touch-target 'defect' (wrong RN-stretch premise), and DEFERRED the perf /api/analytics/pipeline SQL-GROUP-BY A→A+ (non-ship-critical 0-row polish that also conflicts with #234 on asgi.py) + login-lockout-cross-instance (recorded decision) rather than pad. floor_met_year1 stays false (no honest pre-launch lever; TEAM/B2B2C re-confirmed DEFER). No recurring wall → no harness proposal warranted. Pattern across runs 17–22: a mature repo → small, high-value, well-reviewed sets (1–3 changes), NOT artificial scarcity — the big remaining levers are owner-core (store assets, mobile IAP, live keys) or multi-run epics (TEAM/B2B2C).
```
