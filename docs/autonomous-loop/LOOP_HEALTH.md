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
  last_run: 2026-07-11            # run 40
  last_deep_audit: 2026-07-11    # run 40 ran a full ~8-scout Haiku sweep (Track G/H buildability · business-case pricing lever · functional-reality+correctness · security/abuse · tests-evals+artifact-freshness) doubling as the ~daily DEEP AUDIT. run 35 = prior full 8-scout deep audit.
  this_run:                      # run 40
    changes_shipped: 1           # #351 org-endpoint HARDENING — closes a real concurrent-double-org integrity race on the run-39 seat tier (UNIQUE(owner_id) + IntegrityError→409) + a whitespace-only org-name gap (post-strip validator). 4 new tests, all fail-loud. (+ this bookkeeping)
    changes_abandoned: 0         # A genuinely QUIET convergence run (§2 = SUCCESS): the 8-scout deep audit found a CLEAN codebase — prior-scorecard artifact gaps already resolved, coverage met, no theater, functional-reality solid. See deferred/verified-already below.
    abandoned_reasons: []        # reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner.
    verify_cycle_failures: 0     # 0 red REQUIRED CI checks. Ran the full non-live suite locally before push (609→608 passed after dropping a padding test; floor 88 held; migration drift green; flake8 clean).
    review_findings_fixed: 1     # maker≠checker EARNED ITS KEEP: Reviewer B (value) REQUEST_CHANGES on a bundled email-shape validator that only turned a SAFE 404 into a 422 (no integrity/security gain; lookup already parameterized) → dropped as padding. Reviewer A (correctness) APPROVE after empirically revert-testing every guard (real, no theater) + confirming migration chain + db.rollback() safety + _EMAIL_RE forward-ref.
    review_rejections: 1         # 1 REQUEST_CHANGES (Reviewer B, padding) resolved pre-merge; final state 2/2 substantive approvals on the reduced diff.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "FALSE-POSITIVE caught before spawning work (verify-before-act): the functional-reality scout flagged ~12 unguarded analytics.record_event() call sites as a defense-in-depth 500 risk. VERIFIED src/analytics.py:50 — record_event has a top-level `except Exception` that rolls back + logs + returns None (never raises by design), so the unguarded sites CANNOT turn a success into a 500. No bug; did NOT ship a fix for a non-bug (would have been churn)."
      - "GROUND-TRUTH on the 5th-audit ship-critical dims (2 days stale): functional-reality D (model-death) is RESOLVED on main by runs 36-39 (#330 fallback chain + #336 slot-refund + #339 no-bypass guard); business-case seat tier BACKEND shipped run 39 (#348). Consumed the scorecard as DATA; its D + 'seat tier unbuilt' reads are stale-favorable."
      - "SCOUT DISCIPLINE (value bar, not padding): the Track G/H scout surfaced publishing-queue + experiment-engine as 'CRITICAL' buildables. REJECTED as speculative infra pre-launch (§5 no speculative abstractions; §9 PMF-first deprioritizes acquisition-scaling with 0 users/0 traffic — nothing to publish, nothing to A/B). The business-case scout confirmed no honest BACKEND pricing lever crosses $100K (founder pricing LOWERS ARPA + is unvalidatable pre-launch; the seat surface + annual-first are web/mobile). Both correctly left unbuilt — convergence, not scarcity."
    deferred_decisions:          # named + deferred, NOT abandoned (value bar / feasibility / PMF-first — not dead-ends)
      - "ENUMERATION-via-status-code on POST /api/org/members (security scout, MEDIUM) — DEFERRED as a UX tradeoff, not a clear win: add_member requires is_org_active(org) BEFORE the email lookup, so enumeration needs a real PAID, active org (Stripe subscription) + costs rate-limited calls; on that authenticated/paid surface the 'no account exists' message is legitimate admin UX. Flattening it would harm the product for marginal security. Not value-bar-clearing."
      - "seat-tier WEB/MOBILE admin SURFACE — the lowest incomplete ROADMAP item, but purely web/mobile UI (the org BACKEND is complete: create/view/checkout/add-member/remove all exist). Touches the REQUIRED web-E2E gate I can't fully validate locally (node_modules absent) — the class runs 34-39 repeatedly deferred as would-ship-blind. Build when the stack is locally runnable or scope tightly."
      - "publishing-queue + experiment-engine (Track H) — SPECULATIVE pre-launch infra (0 users/0 traffic): nothing to publish, nothing to bucket. §9 PMF-first says fix the PRODUCT, not build acquisition-scaling plumbing that nothing consumes. Correctly deferred 40× — build when there's real traffic to serve."
      - "annual-first / founder pricing — annual-first enforcement is web/mobile UI (+$2–5K est, honest); founder pricing LOWERS Y1 ARPA and can't be validated pre-launch (gaming to credit). Named; not this run."
      - "VALIDATION.md STRIPE_PRICE_* / GEMINI override catalog (artifact scout) — NOT drift: VALIDATION.md declares the billing/ai CAPABILITY + how it's validated (test files), not an env-var catalog; price IDs are non-secret (check_validation green). Adding a catalog would be padding, inconsistent with the doc's design. Skipped."
      - "mobile IAP client (react-native-purchases) — owner/native-blocked (RevenueCat keys + store accounts) + npm-ci lockfile risk on Expo-56/RN-0.85; the honest 'coming soon' stub is currently correct (§6). store assets (rendered icon/screenshots) = owner/design-core. blocked_owner."
      - "OWNER-BLOCKED (PENDING_OPS, unchanged): the two ship-critical C's — business-case floor ($57.5K<$100K, now needs live adoption data not more building) + store-readiness (rendered assets, mobile IAP, native captures) — plus the Career+ Stripe price secrets (nightly). NO new external capability this run."
  rolling_7d:
    merged_prs: 127            # repo-wide, approximate (126 through run 39 #348/#349 + run 40 #351); this bookkeeping merges after
    category_mix: {functional-reality: 1, security: 2, correctness: 1, tests-evals: 2, business-case-strength: 1}   # runs 36-40: #330 LLM-resilience / #331 lockout / #336 slot-refund / #337 coverage / #339 regression-net / #348 seat-tier / #351 org-hardening — spread across 5 categories
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
    capabilities_total: 9        # unchanged — no new external capability introduced (#339 is a test-only regression guard).
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 5         # unchanged — #339 is call-path resilience test coverage, not a new LLM feature.
    with_real_output_eval: 5     # each LLM feature judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: steady                 # bootstrapping | improving | steady | churning | stuck — run 40: 1 shipped (#351 org-endpoint hardening), 0 abandoned, 0 circuit-breaker trips, 0 red REQUIRED CI checks, 1 review rejection (padding, resolved). A QUIET late-CONVERGENCE run (§2 = SUCCESS): the full 8-scout deep audit found a genuinely CLEAN codebase — the 5th scorecard's ship-critical gaps are RESOLVED on main (functional-reality by runs 36-39; seat-tier backend by #348), artifact gaps already fixed, coverage met (91.8%>88), zero theater, functional-reality solid (a scout false-positive on analytics guards was caught by verify-before-act). The one genuine value-bar-clearing find was a real integrity race on the NEWEST feature (run-39 seat tier) → shipped as #351. maker≠checker earned its keep (dropped a padding validator). The remaining ship-blockers are ALL owner-core (business-case floor now needs LIVE adoption data not more building — build-levers near-exhausted; store assets/IAP native; Career+ Stripe secrets) — correctly NOT gamed. Speculative growth infra (publishing queue / experiment engine) correctly left unbuilt pre-launch (§9 PMF-first). No recurring wall → no harness proposal. floor_met_year1 stays false (honest). Prior signal (run 39) retained below.
  # --- run 39 signal (retained) ---
  signal_run39: improving        # run 39: 1 shipped (the BIGGEST ship-critical lever, stuck 23×: #348 team/org seat-tier BACKEND), 0 abandoned, 0 circuit-breaker trips, 0 red REQUIRED CI checks. maker≠checker caught + fixed 3 DISTINCT real billing bugs across 4 review rounds (Career+ bypass, seat-cap race, mobile reconciliation) — the review process demonstrably WORKING, which let a "can't land cleanly" lever land cleanly. The scorecard's independent #3 top_gap overrode the loop's own 23× self-defer — a healthy maker≠checker correction, not scarcity. No recurring wall → no harness proposal. floor_met_year1 stays false (near-exhausted build-levers; crossing $100K now needs live adoption data). FYI prior cadence: run 38 = 1 shipped (steady), run 37 = 2, run 36 = 2, run 35 = 4.
```
