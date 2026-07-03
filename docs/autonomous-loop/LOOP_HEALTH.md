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
  last_run: 2026-07-03            # run 21
  last_deep_audit: 2026-07-03    # run 18's full 8-scout sweep was the last FULL deep audit; runs 19–21 ran focused sweeps (< 24h since, freshest signal each time was owner-filed issue #222).
  this_run:                      # run 21
    changes_shipped: 1           # #231 wire cover-letter + study-plan generators as Pro-tier endpoints (cross-stack: backend+web+mobile+evals+tests) — closes issue #222's dead-capabilities MED (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # backend green on first run (380 non-live); web/mobile not runnable locally (node_modules absent by design) — relied on the required CI checks, which passed.
    review_rejections: 0         # both Sonnet reviewers APPROVE first pass. Reviewer A MUTATION-verified the tier gate + days-bound are load-bearing (broke each → tests reddened → reverted) + traced no fake-success path through _call_llm. Reviewer B tackled the anti-padding question head-on and confirmed study-plan is genuinely distinct from the prep pack's fixed 48h §7 (configurable 1–30-day paced plan), not repackaging.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "SCOUT-FILTERING (anti-padding): the disjoint-companion Haiku scout ranked 7 candidates but its Tier-3 quality picks were ALL stale-scorecard duplicates — create_job idempotency (shipped #200), zero-vector guard test (covered runs 18/19), embedding cache (embeddings DB-cached via ensure_*_embedding). Rejected all 3. Its Tier-1 Track-H picks (publishing queue, experiment engine) are speculative pre-PMF scaffolding with no producer/data (§9: pre-PMF prioritize PRODUCT) → deferred. RULE: verify every scout candidate vs loop-memory + HEAD before building; a mature repo's stale scorecard points Haiku at already-done work."
      - "FUNCTIONAL-REALITY MED (NEW, deferred): prep-pack moderated-decline path — when ContentModerator flags LLM output, _call_llm returns the safe-decline text as content, and the prep-pack endpoint persists it as a 'generated' pack AND charges a usage (increment_prep_usage) — a fake-success + wasted usage on a rare moderation event. The NEW cover-letter/study-plan endpoints are UNAFFECTED (no per-feature usage counter; only the shared LLM ceiling, which a real call legitimately used). Fix touches the shared _call_llm contract → its own focused run."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "issue #222 LOW get_session_summary None-guard — still UNROUTED dead code; guard it before wiring any summary endpoint (marginal today, not padding to defer)."
      - "prep-pack moderated-decline honesty fix (see incidents) — shared _call_llm contract change, own run + 2 reviewers."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever (Career+/annual-first/referral all built). A genuine MULTI-RUN epic (org+seat model, seat billing, composable entitlement); crediting seat ARR at 0 users = gaming, so it does NOT honestly flip $100K pre-launch. Business-case scout re-confirmed DEFER this run (no honest sliceable increment)."
      - "login-lockout cross-instance; native-mobile component snapshots + web SCREENSHOT REGEN (design-taste A→A+); Track G Launch-plan/ASO-SEO docs (held — premature-padding risk pre-readiness); /api/analytics/pipeline pagination + GET /api/jobs/{id} selectinload (pre-launch 0-row polish)."
      - "OWNER-BLOCKED (PENDING_OPS): set Vercel DATABASE_URL→Neon BEFORE next deploy (fail-loud); STRIPE_PRICE_CAREERPLUS_* secrets (nightly reddens without them); mobile IAP client; store asset images; CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml."
  rolling_7d:
    merged_prs: 69             # repo-wide across all routines; incl. this run's #231 (+ this bookkeeping)
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run (#231 is app-code/tests/evals + a code-level analytics allowlist). Latest migration remains d4e7a1c9b8f2.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 8        # unchanged (no new external dependency this run)
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 3         # fit-scoring, prep-tools (prep pack + cover letter + study plan — one module), coach
    with_real_output_eval: 3     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py; cover-letter + study-plan real-output evals added this run)
  signal: steady                 # bootstrapping | improving | steady | churning | stuck — run 21: 1 shipped, 0 abandoned, 0 circuit-breaker trips, 0 review rejections (both reviewers APPROVE first pass), 0 verify-cycle failures. Shipped #231: wired the two previously-DEAD, already-built AI generators (cover-letter + study-plan) as Pro-tier endpoints — resolving issue #222's last substantive finding (owner said "wire or drop"; wiring exposes built value + honors the tier ladder, no dark pattern). ONE coherent cross-stack unit (13 files: backend endpoints + web/mobile UI + api clients + tests + evals), coupled via the web E2E, mirroring the Career+ salary-negotiation contract exactly (gate-before-LLM, consent, spend-ceiling, honest 503, bounded days). maker≠checker did real work: Reviewer A mutation-verified the guards load-bearing; Reviewer B verified study-plan is genuinely distinct (not padding). Anti-padding also held at SELECTION: rejected 3 stale-scorecard duplicate candidates + 2 speculative pre-PMF Track-H scaffolds; the honest maximal disjoint set was this one substantial centerpiece (asgi.py — the shared bottleneck — was consumed by it). floor_met_year1 stays false (cover-letter is additive but neutral on the number at 0 users; TEAM/B2B2C remains the named floor-lever, re-confirmed DEFER). No recurring wall → no harness proposal warranted. Pattern across runs 17–21: a mature repo → small, high-value, well-reviewed sets (1–3 changes), NOT artificial scarcity — the big remaining levers are owner-core (store assets, mobile IAP, live keys) or multi-run epics (TEAM/B2B2C), and maker≠checker keeps earning its keep on the changes that do ship.
```
