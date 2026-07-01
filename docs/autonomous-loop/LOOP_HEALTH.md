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
  last_run: 2026-07-01            # run 10
  last_deep_audit: 2026-07-01    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 6           # #135 web coach session-continuity FIX, #136 mobile coach session-continuity FIX, #137 API input-bounds+rate-limit hardening, #138 web shared-component a11y, #139 web pipeline dashboard a11y+responsive, #140 mobile a11y (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate (pytest/jest/tsc/flake8/eslint) before push
    review_rejections: 1         # #138 Reviewer B REQUEST_CHANGES: I applied the focus-visible ring to 3 of 4 legal-page links but MISSED the footer "Back to home" link in the same file (replace-all-style incompleteness) → fixed cycle 1. Also #137 Reviewer A APPROVED but named a real follow-up (session_id bound 64 vs the String(36) DB column → latent 502) → tightened to 36 within cycle. 11 of 12 reviewers APPROVED first pass; the 2 misses were BOTH genuine reviewer catches on the subtlest points.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "FUNCTIONAL-REALITY bug hidden behind green tests + a 'wired' flow (the run's headline): the AI coach threaded no session_id from EITHER client → the backend started a fresh session per message → zero multi-turn memory on the flagship PAID feature, yet every unit/journey test passed (the coach RETURNED replies). Only tracing the client→backend session CONTRACT end-to-end caught it. Fixed web (#135) + mobile (#136). Classic BUILDS≠WORKS."
      - "Skepticism killed TWO scout false positives before building: perf scout's '/api/jobs → score_all_jobs → N embedding calls' is FALSE (score_all_jobs is wired to NO endpoint — only defs in scorer.py); functional-reality scout's free-tier job-limit TOCTOU is REAL but low-severity (self-limit bypass, needs concurrency, ~1 extra job) → deferred not built."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "ASGI.PY SLOT CHOICE this run: the single asgi.py owner went to the API security hardening (#137), NOT the Track-D GenAI report affordance NOR analytics instrumentation. Rationale: the run's queue was reordered by a ship-critical FUNCTIONAL BREAK (coach continuity) which owned the coach surfaces; the report affordance sprawls those very surfaces → it's correctly a dedicated next run. The hardening completes #126's input-bounds pass + closes two rate-limit gaps — real, low-risk, single-file-contended."
      - "DROPPED A SELECTED CANDIDATE as padding (anti-artificial-volume): composite indexes on Application(user_id,status) + ChatMessage(user_id,session_id) were scouted + selected but dropped BEFORE implementation — pre-launch (0 rows), no query-plan evidence, NOT a named scorecard gap (the real N+1 was fixed #121), and they carry migration + index-redundancy friction. Revisit with real query-plan evidence post-launch."
      - "store: GenAI user-report/flag affordance (Track D, OPEN) — the one loop-buildable store-compliance gap, but sprawls asgi.py + web coach/prep + mobile coach/prep → a DEDICATED run (do not bundle). Confirmed still open + correctly scoped by the store scout this run."
      - "growth/PMF: privacy-safe analytics instrumentation — the PMF measurement foundation, deferred 7+ runs (still the priority asgi.py owner once it's free of a higher-urgency item). DESIGN: AggregateEvent table keyed by event_type+cohort_date+window_date (NO PII/raw events); best-effort record_event() at signup/job-add/fit-score; a read endpoint GATED behind an env shared-secret bearer token (NOT any-authed-user — avoids leaking aggregate user counts), 503 when unset. Wants asgi.py + 1 migration."
      - "NEW deferred (functional-reality scout): free-tier job-limit TOCTOU — create_job reads check_usage_limits then increment_job_usage without locking, so concurrent add-job requests can exceed the 5-job free cap by ~1. Low severity (self-limit bypass only, needs parallel requests). Fix = atomic conditional increment in auth_service (avoids asgi.py). Deferred, recorded."
      - "QUALITY_SCORECARD STALE (as_of 2026-06-29): its named ship-critical gaps are largely CLOSED since — CORS (#96), perf N+1 (#121), referral loop (#109), cross-instance limiter (#114). The independent Quality Auditor routine should re-grade; the factory consumes the scorecard as DATA and must NOT self-edit it (maker≠checker)."
      - "business-case-strength: Career+ ($24) tier — the 'genuine exclusive feature' problem is REAL (PREMIUM is already unlimited-everything incl. salary negotiation); a real entitlement needs metering PREMIUM down OR a new exclusive = multi-run design, NOT a clean one-PR change. TEAM/B2B2C tier remains the floor-flip lever (2-3 PRs + owner GTM)."
      - "security: CAPTCHA (needs owner Turnstile/hCaptcha keys; multi-surface web+mobile+asgi). Login lockout left in-memory by design (a shared store doesn't fix its targeted-DoS — CAPTCHA does). Texas SB2420 age-assurance → owner legal decision (PENDING_OPS)."
      - "Track E mobile VISUAL: jest-expo serializes component TREES, not pixels — committed screenshot IMAGES + the prep-pack vision verdict are human/CI (need a real render + an LLM key), NOT loop-buildable headlessly."
      - "store assets / brand icon: OWNER-BLOCKED per repo standard (loop must not auto-generate a brand mark — slop/DESIGNER QUESTION) + no image tooling. Did not fabricate."
  rolling_7d:
    merged_prs: 111              # 104 + 6 feature this run + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # last migration 993d75032689; NO new migration this run (coach fix = client-only; hardening = Pydantic bounds; a11y = markup/props; composite indexes were DROPPED as pre-launch padding, not implemented)
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 5
    unmet: [ai]                  # degraded_only — surfaced as OWNER_ACTION validation-capability-gemini (urgent)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 6 shipped, 0 abandoned, 0 circuit-breaker trips. Headline: functional-reality caught a REAL ship-critical break (paid coach lost all multi-turn context) that green tests hid — fixed both clients. maker≠checker earned its keep on the two subtlest points (a #138 half-applied focus-ring sweep + a #137 session_id bound-vs-DB-column-width latent 502), each fixed within cycle 1. Skepticism killed 2 scout false positives; DROPPED a selected candidate (composite indexes) as pre-launch padding rather than pad the count. Single-concern, file-disjoint, no recurring wall → no harness proposal warranted.
```
