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
  last_run: 2026-07-01            # run 12
  last_deep_audit: 2026-07-01    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 3           # #146 privacy-safe analytics instrumentation (Track G+H, PMF foundation), #147 web coach-chip focus-visible a11y, #148 scorer embedding-reload coverage (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate before push; anchor: 254 backend pass + migration drift green + check_validation OK; web tsc+eslint clean
    review_rejections: 0         # all 6 reviewers APPROVED first pass. #146 drew TWO non-blocking nits (Rev B: docstring "retention" overclaim on an aggregate-only table; Rev A: no rate-limit on the read endpoint) — both FIXED proactively in a refine commit (cycle 1) before merge, not formal REQUEST_CHANGES.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "maker≠checker's value this run = two non-blocking honesty/hardening nits on the anchor: (a) a docstring claiming the aggregate table yields per-user RETENTION — it CANNOT (no per-user dimension, by design); reworded to activation/engagement only. (b) the read endpoint lacked the rate_limit every sibling has — added rate_limit('analytics',30) vs shared-secret brute-forcing. Both fixed pre-merge, cycle 1."
      - "Rejected scout FALSE POSITIVES before building: mobile job-status 'fake success' (verified FALSE — setJob(await updateJobStatus(...)) sets state from the awaited server response, not optimistically); web landing headings 'non-semantic' (already <h3>); get_session_summary coverage (DEAD CODE — defined, wired to no endpoint); the by-design LLM-ceiling-consume-before-call (an expensive attempt must count)."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "ASGI.PY SLOT CHOICE this run: the single asgi.py + ≤1-migration owner FINALLY went to analytics instrumentation (#146) — deferred 8+ runs, now unblocked because NOTHING outranked it (security clean, no ship-critical functional bug; the perf N+1 + TOCTOUs are pre-launch 0-row polish). Track G line 287 + Track H line 294 both TICKED."
      - "PMF-first over a revenue lever: business-case scout ranked TEAM/B2B2C as the floor-flip lever, but it's a multi-run epic that CONTENDS the exact asgi.py/models.py/migration slot analytics needed, and pre-PMF (0 users) a B2B2C sales tier moves no REAL ARR — analytics is the prerequisite to VALIDATE any model with real cohort data (§9). Analytics this run; TEAM = the dedicated next epic (2-3 PRs + owner GTM). Career+-solo stays REJECTED (dishonest dark pattern — PREMIUM is already unlimited-everything)."
      - "coach '100 msg/mo' doc↔code mismatch (store scout): README + BUSINESS_CASE promise Pro 100 coach msgs/mo; code enforces only the daily LLM SPEND ceiling + rate limit, not a monthly message count. User-GENEROUS (not deceptive vs the user), but a living-artifact gap — resolve by enforcing a monthly counter (models+migration+asgi, like prep-pack counting) OR correcting the docs. Wants the shared resources analytics took → dedicated next run."
      - "perf: /api/jobs/{id} GET lacks selectinload (3 lazy-loads via job_public) — real but pre-launch 0-row polish; asgi.py-contended this run. free-tier job/prep TOCTOU (concurrent requests exceed the cap by ~1; low-sev self-bypass) — fix = atomic conditional increment in auth_service (avoids asgi.py). rate limits on /api/auth/me + /api/referrals/me (low-sev, asgi.py). All deferred, named."
      - "security: CAPTCHA (needs owner Turnstile/hCaptcha keys; multi-surface). Login lockout left in-memory by design. Texas SB2420 age-assurance → owner legal decision (PENDING_OPS)."
      - "Track E mobile VISUAL: jest-expo serializes component TREES, not pixels — committed screenshot IMAGES + the prep-pack vision verdict are human/CI. store assets / brand icon + mobile IAP client = OWNER-BLOCKED (keys/signing/design). Did not fabricate."
      - "mobile silent-failure UX polish (settings referral card vanishes on error; coach suggestions silently empty) + a hardcoded rgba in ErrorBanner — dropped as churn-ish (optional/secondary surfaces; primary flows already have honest error states)."
  rolling_7d:
    merged_prs: 119              # 115 + 3 feature this run + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NEW migration b2c8d4e6f1a5 (aggregate_events, down_revision a1b7c2f9e0d3) — drift-gated, auto-applies on merge to main; the ≤1-migration-slot for the run
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 6        # +analytics (validation=real; read path exercised in CI via an in-test token; blocking=false — record path needs no key)
    unmet: [ai]                  # degraded_only — surfaced as OWNER_ACTION validation-capability-gemini (urgent). analytics is validated (real) → not unmet.
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 3 shipped, 0 abandoned, 0 circuit-breaker trips, all 6 reviewers APPROVE first pass. Headline: FINALLY shipped the long-deferred (8+ runs) PMF-measurement foundation — privacy-safe aggregate analytics (Track G line 287 + Track H line 294 both TICKED), which had lost the asgi.py/migration slot to higher-urgency work every prior run. It's the prerequisite to reconcile the business case against real cohort data (§9). maker≠checker earned its keep on two anchor honesty/hardening nits (a retention-overclaim docstring + a missing read-endpoint rate-limit), both fixed pre-merge. Deliberately chose measurement over the TEAM/B2B2C revenue epic (contends the same slot; pre-PMF a sales tier moves no real ARR). No recurring wall → no harness proposal warranted.
```
