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
  last_run: 2026-07-05            # run 27
  last_deep_audit: 2026-07-05    # run 27 ran a focused 6-scout sweep (functional-reality / backend-correctness+security / enrichment-feasibility+SSRF / disjoint-small-wins / doc-freshness+quality-reconcile / business-case+monetization); the last FULL deep audit was run 26 (~1 day prior). Functional-reality + backend-security scouts found NO new ship-critical break beyond known-deferred; the disjoint scout surfaced ONE genuine disjoint win (ATS retry).
  this_run:                      # run 27
    changes_shipped: 2           # #270 CENTERPIECE profile enrichment from public GitHub (backend model+migration+enricher+endpoint+scorer/generator integration + web + mobile + evals — Track A lowest-incomplete → box TICKS) · #271 ATS retry/backoff (src/ingestion, closes the correctness top_gap) — file-DISJOINT → parallel auto-merge (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # centerpiece verified locally: backend 452 non-live pytest (28 new enrichment tests + golden eval) @ 91.99% cov + flake8 + 5 deterministic gates (eval-coverage/validation/blocks/GTM) all green; the enrichment endpoint flow exercised at RUNTIME via the FastAPI TestClient (403 gate / 400 invalid / 200 real aggregation / honest found=0 / GET+DELETE / scoring feed). ATS PR: 29 ingestion tests green. web/mobile: no node_modules locally (iOS reality) → leaned on required-CI web E2E + mobile tsc/lint/jest.
    review_rejections: 2         # BOTH actioned within the ≤2-cycle cap + fresh re-review APPROVE. #270: Reviewer B REQUEST_CHANGES — the MOBILE enrichment card hid itself from free users (`if (!isPro) return null`), a discoverability regression vs BOTH the web card and the repo's insights.tsx convention; fixed (show-with-upgrade-CTA + a missing web-parity clear affordance). #271: BOTH reviewers independently REQUEST_CHANGES on the same real serverless-budget bug (see incidents); fixed. Reviewer A on #270 APPROVED first pass (mutation-verified 3 guards + fuzzed the SSRF/username parse).
    circuit_breaker_trips: 0
    incidents:                   # self-caught + reviewer-caught process notes (recovered, NOT abandonments)
      - "maker≠checker (#271, both reviewers, independently + empirically): `requests.ConnectTimeout` subclasses BOTH `Timeout` AND `ConnectionError`, so the retry helper's bare `except ConnectionError` RETRIED a connect-timeout → up to ~3×20s ≈ 61.5s, overrunning the 60s Vercel budget the retry exists to respect (DEEP_DIAGNOSIS rule a) — the exact failure it was built to prevent. Fixed with `except requests.Timeout: raise` BEFORE the ConnectionError clause + a regression test using the concrete ConnectTimeout. RULE: the `requests` exception hierarchy is a trap — catch `Timeout` first when Timeout and ConnectionError must diverge."
      - "maker≠checker (#270): Reviewer B caught the mobile card hiding from free users (discoverability/conversion regression); the FRESH re-reviewer of the fix then surfaced a downstream CI-blocker — the settings-screen jest mock lacked getEnrichment/enrichGithub/clearEnrichment, so a premium render (whose card useEffect calls getEnrichment) would throw, AND a free render now has TWO 'Upgrade to Pro' CTAs (getByText→getAllByText). Fixed the test mock + assertions in the same PR. RULE: adding a component that fires an effect for a tier the existing screen-test covers means updating that test's api mock in the SAME change."
      - "SELF-CAUGHT before push (#270): my JobScorer.__init__ edit inserted the new _enriched_skills method BETWEEN `self.db=db` and the existing `self.client=get_llm_client()`, orphaning the client assignment after a `return` — the full pytest run reddened test_scorer_workflow ('JobScorer has no attribute client'); fixed before commit. RULE: when Edit-inserting a method after the first line of __init__, confirm no later __init__ statements got stranded below it."
      - "SELF-CAUGHT before push (#271): adding get_with_retry (which reads response.status_code) reddened existing ATS client tests whose mock Response had no status_code; added a default status_code=200 to those mocks (a real Response has one). Not masking behavior — a 200 is non-retryable, so the pre-existing tests are unchanged."
      - "STALE LOCAL main: local `main` ref was behind origin/main (8141b91 vs 157f3da), showing pre-#259 'Premium' strings on disk. My PR branches were correctly cut from origin/main (the real HEAD). RULE (echoes run-20): never trust the local `main` ref or an on-disk read after a branch switch — verify against origin/main / `git show origin/main:<path>`."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "Profile enrichment portfolio/Scholar source connectors (additional source types; GitHub — the tech-ICP's dominant source — shipped first) + an optional authenticated GITHUB_TOKEN for the 5000/hr rate limit (today unauthenticated 60/hr per-IP → degrades gracefully to found=0). Named by both #270 reviewers as sound follow-ups, not blockers."
      - "Coach-reply ReportButton passes session id, not a message id (both web+mobile coach surfaces): needs a backend per-message id (schema change)."
      - "/api/analytics/pipeline SQL GROUP BY + PATCH /api/jobs/{id} post-refresh serialization (perf A→A+, asgi.py) — conflicted with the centerpiece's asgi.py ownership this run (disjoint rule); a clean next-run PR."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever (owner-blocked GTM; crediting seat ARR at 0 users = gaming). Re-confirmed DEFER (14th consecutive run). Annual-first is already presented-first on the pricing page (a default-annual toggle is marginal churn). native-mobile snapshots + web SCREENSHOT REGEN (design-taste A→A+ — needs a running app/emulator); login-lockout cross-instance (recorded decision: CAPTCHA is the fix)."
      - "OWNER-BLOCKED (PENDING_OPS): set Vercel DATABASE_URL→Neon BEFORE next deploy (fail-loud); STRIPE_PRICE_CAREERPLUS_* secrets; mobile IAP client; store asset images; CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml."
  rolling_7d:
    merged_prs: 90             # repo-wide across all routines; incl. this run's #270/#271 (+ this bookkeeping) pending auto-merge through required CI
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
  signal: steady                 # bootstrapping | improving | steady | churning | stuck — run 27: 2 shipped, 0 abandoned, 0 circuit-breaker trips, 0 verify-cycle failures, 2 review-rejections ACTIONED (both fixed within ≤2 cycles + fresh re-review APPROVE — maker≠checker EARNED ITS KEEP TWICE: a mobile discoverability regression on #270 and a subtle Python-exception-MRO serverless-budget bug on #271 that BOTH reviewers independently caught, neither catchable by the green gate alone). Advanced the LOWEST incomplete loop-buildable ROADMAP item — Track A's profile enrichment (#270, box TICKS) — as a substantial honest cross-stack centerpiece, REJECTING the feasibility scout's regex-HTML-scrape design (slop/hallucination risk) for the structured, SSRF-free fixed-host GitHub-API design; plus a disjoint ATS retry/backoff (#271) closing the QUALITY_SCORECARD correctness top_gap. floor_met_year1 stays false (no honest pre-launch lever; TEAM/B2B2C DEFER, 14th run — genuinely owner/GTM-blocked, not code-blocked). No recurring wall → no harness proposal. Pattern across runs 23–27 (mature repo): high-value, well-reviewed, coherent units sized to the honest work — a big centerpiece + the genuine disjoint win, never artificial scarcity, never padding. FYI: run 26 was 4 shipped / 0 abandoned / 1 review-rejection.
```
