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
  as_of: 2026-07-11
  last_run: 2026-07-11            # run 41
  last_deep_audit: 2026-07-11    # run 40 ran the full ~8-scout Haiku sweep (the ~daily DEEP AUDIT). run 41 (this run, ~6h later, 0 main changes since) ran a FOCUSED 4-scout sweep of the newest surface, NOT a full re-audit (spend discipline §16 — a full re-sweep would only re-derive run 40's identical clean conclusion). run 35 = prior full 8-scout deep audit.
  this_run:                      # run 41
    changes_shipped: 1           # #353 tests-evals — a §26 regression-net test closing a real uncovered {individual Stripe sub + mobile RevenueCat, no org} entitlement-reconciliation path (Stripe subscription.deleted webhook → recompute_user_tier with mobile as survivor). Test-only, file-disjoint. Revert-verified genuine guard. (+ this bookkeeping)
    changes_abandoned: 0         # A genuinely QUIET convergence run (§2 = SUCCESS): the focused 4-scout sweep of the newest org-billing surface found it CLEAN (correctness + security scouts: NO FINDINGS); the one honest value-bar-clearing find was the test-coverage gap. No padding, no scarcity.
    abandoned_reasons: []        # reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner.
    verify_cycle_failures: 0     # 0 red REQUIRED CI checks. Ran the new test + full tests/test_org_billing.py locally before push (22 passed, was 21; flake8 clean). Revert-verified the guard reddens on a planted regression.
    review_findings_fixed: 0     # No REQUEST_CHANGES this run: both Sonnet reviewers APPROVE first pass, each having INDEPENDENTLY mutation-tested the guard (planted the tier→FREE regression, confirmed only the new test breaks) — empirical proof it's non-redundant, not assertion. maker≠checker validated value + correctness on a small, focused diff.
    review_rejections: 0
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "VERIFY-BEFORE-ACT (no fix for non-bugs): issue #222's still-open 'dead capabilities' claim (generate_study_plan/generate_cover_letter unrouted) is STALE/RESOLVED — both ARE routed (asgi.py:1865/1930). get_session_summary (career_coach.py:261) remains unrouted/latent, so a None-client guard would be an impossible-case fix (sub-bar). Shipped nothing for either."
      - "CADENCE DISCIPLINE (spend, §16): run 40 ran the full ~daily deep audit earlier the SAME day with 0 main changes + 0 owner env changes since. Re-running a full 8-scout sweep would re-derive an identical clean conclusion for real $ — chose a FOCUSED 4-scout sweep of the newest (least-audited) surface instead. 3 of 4 scouts clean; consistent with run 40's late-convergence read."
      - "GROUND-TRUTH re-probe (§28, owner env is git-invisible): no new connector, no PROD_URL/ANALYTICS_READ_TOKEN in env, Stripe Career+ price secrets still unset (nightly RED by design) — nothing changed externally, so no source flips connected; channels_connected=[] stays honest."
    deferred_decisions:          # named + deferred, NOT abandoned (value bar / feasibility / PMF-first — not dead-ends)
      - "ENUMERATION-via-status-code on POST /api/org/members (security scout, MEDIUM) — DEFERRED as a UX tradeoff, not a clear win: add_member requires is_org_active(org) BEFORE the email lookup, so enumeration needs a real PAID, active org (Stripe subscription) + costs rate-limited calls; on that authenticated/paid surface the 'no account exists' message is legitimate admin UX. Flattening it would harm the product for marginal security. Not value-bar-clearing."
      - "seat-tier WEB/MOBILE admin SURFACE — the lowest incomplete ROADMAP item, but purely web/mobile UI (the org BACKEND is complete: create/view/checkout/add-member/remove all exist). Touches the REQUIRED web-E2E gate I can't fully validate locally (node_modules absent) — the class runs 34-40 repeatedly deferred as would-ship-blind. Build when the stack is locally runnable or scope tightly."
      - "publishing-queue + experiment-engine + ASO/SEO plan + launch-plan doc + §11 media-gen adapter (Track G/H) — SPECULATIVE pre-launch infra (0 users/0 traffic/0 channels): nothing to publish, nothing to bucket, no audience for a launch plan. §9 PMF-first says fix the PRODUCT, not build acquisition-scaling plumbing/collateral that nothing consumes. run 41's Track-G/H scout independently re-classified all of these as padding, not levers. Correctly deferred 41× — build when there's real traffic to serve."
      - "annual-first / founder pricing — annual-first enforcement is web/mobile UI (+$2–5K est, honest); founder pricing LOWERS Y1 ARPA and can't be validated pre-launch (gaming to credit). Named; not this run."
      - "VALIDATION.md STRIPE_PRICE_* / GEMINI override catalog (artifact scout) — NOT drift: VALIDATION.md declares the billing/ai CAPABILITY + how it's validated (test files), not an env-var catalog; price IDs are non-secret (check_validation green). Adding a catalog would be padding, inconsistent with the doc's design. Skipped."
      - "mobile IAP client (react-native-purchases) — owner/native-blocked (RevenueCat keys + store accounts) + npm-ci lockfile risk on Expo-56/RN-0.85; the honest 'coming soon' stub is currently correct (§6). store assets (rendered icon/screenshots) = owner/design-core. blocked_owner."
      - "OWNER-BLOCKED (PENDING_OPS, unchanged): the two ship-critical C's — business-case floor ($57.5K<$100K, now needs live adoption data not more building) + store-readiness (rendered assets, mobile IAP, native captures) — plus the Career+ Stripe price secrets (nightly). NO new external capability this run."
  rolling_7d:
    merged_prs: 129            # repo-wide, approximate (128 through run 40 #351/#352 + run 41 #353); this bookkeeping merges after
    category_mix: {functional-reality: 1, security: 2, correctness: 1, tests-evals: 3, business-case-strength: 1}   # runs 36-41: #330 LLM-resilience / #331 lockout / #336 slot-refund / #337 coverage / #339 regression-net / #348 seat-tier / #351 org-hardening / #353 reconciliation-test — spread across 5 categories
    diversity: varied
    reverts: 0
    readiness_attempts: 0        # not attempted — the two ship-critical C's stay owner/GTM-blocked (business-case floor + store assets/IAP), so submission-readiness is honestly not met
    readiness_rejected: 0
    recurring_failures: []       # the nightly Career+ red is a KNOWN owner-blocked external (missing secret), not a LOOP failure — tracked, not a stuck signal
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run. Head unchanged (a7d3e1f0c92b from run 31). Owner must still set Vercel DATABASE_URL→Neon before the next deploy (PENDING_OPS).
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 9        # unchanged — no new external capability introduced (#353 is a test-only regression guard).
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 5         # unchanged — #353 is entitlement-reconciliation test coverage, not a new LLM feature.
    with_real_output_eval: 5     # each LLM feature judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: steady                 # bootstrapping | improving | steady | churning | stuck — run 41: 1 shipped (#353 entitlement-reconciliation regression test), 0 abandoned, 0 circuit-breaker trips, 0 red REQUIRED CI checks, 0 review rejections (2/2 clean APPROVE with independent mutation-test proof). A QUIET late-CONVERGENCE run (§2 = SUCCESS), the 2nd in a row: run 40's full 8-scout deep audit (same day) found a clean codebase; run 41 ran a FOCUSED 4-scout sweep of the newest surface (spend discipline — no full re-audit 6h later with 0 main changes) and found it clean too (correctness + security scouts: NO FINDINGS). The one genuine value-bar-clearing find was a §26 regression-net gap on a paid-entitlement path (the uncovered {individual+mobile} reconciliation via the Stripe subscription.deleted webhook) → #353. maker≠checker earned its keep by empirically PROVING non-redundancy (both reviewers independently mutation-tested). The remaining ship-blockers are ALL owner-core (business-case floor now needs LIVE adoption data not more building — build-levers exhausted; store assets/IAP native; Career+ Stripe secrets) — correctly NOT gamed. Speculative growth infra (publishing queue / experiment engine / media-gen / launch docs) correctly left unbuilt pre-launch (§9 PMF-first). No recurring wall → no harness proposal. floor_met_year1 stays false (honest). Two consecutive quiet convergence runs is the honest signal of a mature product whose remaining gaps are owner/live-data-gated, NOT a churning/stuck loop. Prior signal (run 40) retained below.
  # --- run 40 signal (retained) ---
  signal_run40: steady           # run 40: 1 shipped (#351 org-endpoint hardening — concurrent-double-org integrity race + whitespace-name gap), 0 abandoned, 0 circuit-breaker trips, 1 review rejection (Reviewer B dropped a padding email-shape validator, resolved). The full 8-scout deep audit found a CLEAN codebase; the 5th scorecard's ship-critical gaps are RESOLVED on main (functional-reality by runs 36-39; seat-tier backend by #348); a scout false-positive on analytics guards was caught by verify-before-act. No recurring wall → no harness proposal. floor_met_year1 false. FYI prior cadence: run 39 = 1 shipped (improving, the 23×-stuck seat-tier backend), run 38 = 1 (steady), run 37 = 2, run 36 = 2, run 35 = 4.
```
