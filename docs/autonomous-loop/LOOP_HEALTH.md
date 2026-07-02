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
  last_run: 2026-07-02            # run 16
  last_deep_audit: 2026-07-02    # run 14's FULL 8-scout sweep; runs 15+16 ran focused sweeps (full audit was same-day)
  this_run:                      # run 16
    changes_shipped: 3           # #187 email abstraction + waitlist double-opt-in (Track H centerpiece), #185 remove dead upgrade_to_premium() booby-trap, #186 APP_PRIVACY_LABELS freshness (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate before push: backend 305→307 pass + flake8 clean + check_validation green; required CI (preflight + web E2E) green on every merge.
    review_rejections: 2         # #187 centerpiece: Reviewer A (cycle 1) REQUEST_CHANGES — Host-header phishing primitive in the confirm-email LINK; a fresh re-reviewer (cycle 2) REQUEST_CHANGES — the SIBLING open-redirect (CWE-601) on the confirm-endpoint redirect. Both fixed + regression-tested; a 3rd (final) 2-reviewer pass APPROVED. #185/#186: all 4 reviewers APPROVE first pass.
    review_cycles_centerpiece: 3 # JUSTIFIED (not thrash): each cycle a DISTINCT, real, reviewer-prescribed security bug; the diff CONVERGED; capped — a new real issue in the final pass would have meant ABANDON.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "maker≠checker HEADLINE (run 16): TWO distinct Host-header trust bugs caught in the centerpiece across review cycles, both hidden behind all-green tests. (a) the confirmation EMAIL link was built from request.base_url (raw Host, no TrustedHostMiddleware) → a spoofed Host on /join would email a victim a genuine-looking link to an ATTACKER domain (phishing). (b) the SIBLING: the confirm-endpoint 303 redirect dest fell back to request.base_url → an OPEN REDIRECT (CWE-601), triggerable even with an invalid token. RULE: any value derived from the request Host/base_url is attacker-controlled without TrustedHostMiddleware — it must NEVER reach outbound-email content OR a redirect Location; when you find one such sink, grep ALL request.base_url sinks (the sibling is usually one function away)."
      - "SKEPTICISM killed FOUR would-be-padding candidates before building (anti-padding): embedding cache = REDUNDANT (DB already caches via ensure_*_embedding); zero-vector cosine test = ALREADY-COVERED (test_scoring_evals.py); annual-first paywall = ALREADY BUILT (web pricing already defaults annual + savings badge); store feature-graphic + marketing/launch docs = padding/owner-blocked/GTM-territory. The scouts refuted the scorecard's own named gaps as stale — honest maximal set was 3, not artificial scarcity."
      - "Concurrent-agent shared-tree contamination (recurring, recovered): reviewers ran scratch mutation edits (revert-the-fix) in the shared clone to prove tests load-bearing; each restored + verified clean, and I re-verified my local tree == origin/<branch> (empty git diff) before every merge. RULE stands: origin/<branch> is authoritative."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "waitlist-form.tsx does not surface the API's conditional 'check your email' copy — LATENT under the dry-run default (both reviewers noted it as a fast follow-up for when a real ESP connects). Not a false claim today."
      - "TEAM/B2B2C tier — still the PRIMARY named floor-lever (genuine 15+ PR multi-run epic; crediting seat ARR at 0 users = gaming, so it does NOT honestly flip $100K pre-launch). Owner GTM."
      - "coach 100-msg/mo enforcement (doc↔code honesty — Pro is unlimited today; wants the asgi.py slot the centerpiece owned this run); /api/analytics/pipeline pagination + create_job dedup/idempotency (asgi.py, deferred by the disjoint rule); Pro→Career+ in-place upgrade via Stripe portal."
      - "web SCREENSHOT REGEN (design-taste A→A+ artifact refresh — the stale 390px shot); scorer ensure_user_embedding no-resume-text ValueError branch (tiny uncovered guard — deferred, sub-bar solo)."
      - "OWNER-BLOCKED (PENDING_OPS): connect a real ESP + set WEB_APP_URL to ACTIVATE waitlist-confirmation delivery (connect-marketing); mobile Career+ IAP client; store asset images/brand icon; CAPTCHA keys; CAREERPLUS_* Stripe price IDs."
  rolling_7d:
    merged_prs: 56             # repo-wide across all routines; incl. this run's #185/#186/#187
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run (double-opt-in reused the existing waitlist.confirmed_at column). Latest migration remains d4e7a1c9b8f2.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 7        # +email (run 16): send + confirm round-trip validated in CI via the capture backend
    unmet: []                    # ai closed 2026-07-02: GEMINI_API_KEY added to CI, test_llm_live.py real round-trip green
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 3         # fit-scoring, prep-pack, coach
    with_real_output_eval: 3     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 3 shipped, 0 abandoned, 0 circuit-breaker trips. Headline: built the two lowest-incomplete Track H items — an honest email-provider abstraction (dry-run default, never fakes a 'sent') + waitlist double-opt-in (stateless email-bound HMAC token, NO migration, F4.1 round-trip proven via a capture backend) in ONE cross-stack PR (#187). maker≠checker earned its keep HARD: across review cycles it caught TWO distinct Host-header trust bugs that all-green tests hid — a phishing primitive in the confirmation-email LINK, then the SIBLING open-redirect (CWE-601) on the confirm-endpoint redirect — both fixed + regression-tested (a 3rd cycle was justified convergence on distinct reviewer-prescribed security one-liners, not thrash; capped). Also shipped #185 (removed a dead unguarded upgrade_to_premium() client-trusted-unlock booby-trap + tripwire) and #186 (APP_PRIVACY_LABELS consent-section freshness). ANTI-PADDING: skepticism refuted FOUR would-be candidates as redundant/already-built/blocked (embedding cache, zero-vector test, annual-first paywall, store feature-graphic) — honest maximal set was 3. HONEST on the number: no revenue lever this run; floor_met_year1 stays false; TEAM/B2B2C remains the primary named floor-lever (doesn't flip the floor at 0 users). No recurring wall → no harness proposal warranted.
```
