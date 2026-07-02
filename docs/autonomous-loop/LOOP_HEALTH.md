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
  as_of: 2026-07-01
  last_run: 2026-07-01            # run 13
  last_deep_audit: 2026-07-01    # run 12's 8-scout sweep; run 13 used a TARGETED 5-scout sweep (fresh same-day scorecard + deep audit already existed)
  this_run:
    changes_shipped: 3           # Career+ tier: #152 backend (plan_level + salary-negotiation endpoint), #153 web (2 tiers + gated surface), #155 mobile (parity + Career+-aware paywall) (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate before push: 270 backend pass + flake8 clean; web tsc+eslint+next build+ 3 e2e specs (7 tests) green; mobile tsc+expo lint+jest-expo 58/58
    review_rejections: 2         # TWO formal REQUEST_CHANGES this run, BOTH real, BOTH fixed cycle 1: (web Rev A) rounding-order bug — "0.4" passed the >0 guard then Math.round→0 sent to the API (wasted LLM call), fixed in BOTH web+mobile (round before validate + upper bound); (mobile Rev B) paywall honesty — a Pro user tapping the new "Upgrade to Career+" was FALSELY told they already had salary negotiation + dead-ended, fixed by making the paywall Career+-aware. The other 6 reviewer passes APPROVED (4 first-pass; the 2 re-reviews APPROVED after the fixes).
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "maker≠checker caught TWO REAL bugs (both fixed cycle 1): (a) web Rev A — rounding-order let '0.4' round to 0 and hit the API, burning an LLM call on a '$0' guide; round-before-validate + upper bound, applied to web AND mobile. (b) mobile Rev B — the paywall gated 'everything unlocked incl. salary negotiation' on tier==='premium', so a Pro user was falsely told they had the Career+ exclusive and dead-ended; made the paywall Career+-aware (3 honest states). LESSON: a new tier makes NEW UX populations reachable — audit every surface the distinction touches."
      - "DESIGN-STAGE maker≠checker win: an adversarial scout KILLED my 'Career+ AI Company Dossier' idea (the prep pack ALREADY has a company-research section → gating a dossier = repackage/dark-pattern) BEFORE I built it. Pivoted to the already-built-but-unexposed salary_negotiation generator (genuinely additive, honors the advertised pricing)."
      - "PROCESS: origin/main was STALE in the clone (pointed at run 4 cd56e8f while HEAD was run 12); my first branch was based on run-4 code. Caught via a 126-line file-shift + git log origin/main; git fetch force-updated it to run 12; recreated branches off fresh origin/main. RULE (§1): git fetch + verify origin/main HEAD BEFORE branching — never trust the clone's remote-tracking ref."
      - "PROCESS: edited the mobile paywall files while on the WEB branch; tsc's 'Property career_plus does not exist on type User' was the tell (the type lives on the mobile branch). git stash → checkout mobile → pop moved them cleanly. Verify the branch before cross-stack edits."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "TEAM/B2B2C tier — now the PRIMARY named floor-lever (Career+ + referral are built but don't flip the $100K floor; pre-launch a Career+-mix assumption would be anti-gaming). Multi-run epic (org/seat model + seat billing + entitlement inheritance) + owner GTM. THE dedicated next epic."
      - "Pro→Career+ IN-PLACE upgrade via the Stripe billing portal (loop/code — avoids double-billing). Today a Pro user gets an honest 'switch on the web / coming soon' message rather than a second checkout. Named follow-up."
      - "Career+ upgrade-rate wedges (voice mock-interview, company-specific dossiers) — future AI-prep value expansion to raise the Pro→Career+ conversion; multi-run, LLM/voice infra."
      - "billing/success page Career+-aware copy (web Rev B non-blocking nit — still says generic 'Welcome to Premium'); coach '100 msg/mo' doc↔code mismatch (carried); /api/jobs/{id} N+1 + free-tier TOCTOU + /api/analytics/pipeline unbounded .all() (pre-launch 0-row polish, carried)."
      - "OWNER-BLOCKED (PENDING_OPS): CAREERPLUS_* Stripe price IDs (now REQUIRED to sell Career+, no longer optional); mobile Career+ IAP client (RevenueCat keys/store accounts); store assets/brand icon; CAPTCHA keys."
  rolling_7d:
    merged_prs: 126              # 119 + #150/#151/#154 (other-routine syncs/audit) + #152/#153/#155 (feature) + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run — Career+ needed none (UserTier stays binary; the level derives from the existing Subscription.plan). Latest migration remains b2c8d4e6f1a5.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 6
    unmet: []                    # ai closed 2026-07-02: GEMINI_API_KEY added to CI, test_llm_live.py real round-trip green
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 3 shipped, 0 abandoned, 0 circuit-breaker trips. Headline: built the #1 ship-critical LOOP-BUILDABLE gap — Career+ ($24) as a REAL, webhook-verified, differentiated tier (was dead config) with AI salary-negotiation coaching as its additive exclusive, across backend/web/mobile. maker≠checker earned its keep HARD: an adversarial scout killed a dark-pattern design at the DESIGN stage, and 2 formal REQUEST_CHANGES caught a real wasted-LLM-call bug + a real paywall honesty/dead-end bug, all fixed cycle 1. HONEST on the number: Career+ does NOT flip the floor (recorded as real-but-unquantified, no inflation); TEAM/B2B2C remains the primary floor-lever. No recurring wall → no harness proposal warranted.
```
