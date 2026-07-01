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
  last_run: 2026-07-01            # run 11
  last_deep_audit: 2026-07-01    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 3           # #142 GenAI user-report affordance (Track D, store-compliance), #143 coach-suggestions bounded query (perf), #144 mobile a11y (auth link roles + job-row status) (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate (pytest/jest/tsc/flake8/eslint) + web next build before push
    review_rejections: 1         # #143 Reviewer A REQUEST_CHANGES: the bounded-query regression test counted SQL *statements*, but old `.all()` and new `.first()` both emit ONE statement → NOT load-bearing. Rewrote to assert every applications SELECT carries a LIMIT (the .first() bound); mutation-verified it fails against reverted `.all()`. Fixed cycle 1, then BOTH reviewers APPROVE. The other 5 reviewers APPROVED first pass (Reviewer A mutation-tested the #142 cascade/rate-limit/bounds guards + the #144 a11y assertions — all genuinely load-bearing).
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "maker≠checker's headline catch: a 'query count constant' perf-regression test is NOT load-bearing for a `.all()`→`.first()` bound, because both emit ONE statement — the discriminating signal is the LIMIT in the SQL, not the statement count. RULE: when guarding a bounded-query fix, assert the BOUND (LIMIT / rows fetched), never the statement count. Fixed + mutation-verified."
      - "Skepticism deferred low-value/false candidates before building: functional-reality's mobile `?ref` parity gap (web-flow-covered, needs native deep-linking); the two TOCTOU self-limit-bypass findings (low-sev, asgi.py-reserved); greenhouse `job_data['id']` KeyError robustness (real Greenhouse boards always carry id+title — marginal); landing-subtext contrast (slate-500 on near-black is ~AA-borderline, not a clear fail) + pricing-hierarchy taste (subjective) — dropped as padding-risk."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "ASGI.PY SLOT CHOICE this run: the single asgi.py owner went to the Track-D GenAI report affordance (#142) — the long-deferred (3+ runs) store-compliance gap, finally its DEDICATED run now that no higher-urgency functional/security break contends. Analytics instrumentation (also wants asgi.py + a migration) deferred AGAIN as the ≤1-migration-slot / single-asgi.py-owner loser — but it is now the CLEAR next-run asgi.py priority (no higher-urgency item remains)."
      - "growth/PMF: privacy-safe analytics instrumentation — the PMF measurement foundation, deferred 8+ runs (NOW the priority asgi.py owner — the report affordance that kept jumping it is shipped). DESIGN: AggregateEvent table keyed by event_type+cohort_date+window_date (NO PII/raw events); best-effort record_event() at signup/job-add/fit-score; a read endpoint GATED behind an env shared-secret bearer token (NOT any-authed-user — avoids leaking aggregate user counts), 503 when unset. Wants asgi.py + 1 migration."
      - "NEW deferred (security scout): rate limits on GET /api/auth/me + /api/referrals/me (they lack a rate_limit dep; low-sev, token-gated) — wants asgi.py, which #142 owned this run. Fold into the next asgi.py PR."
      - "free-tier job-limit TOCTOU — create_job reads check_usage_limits then increment_job_usage without locking; concurrent add-job requests can exceed the 5-job free cap by ~1. Low severity (self-limit bypass, needs parallel requests). Fix = atomic conditional increment in auth_service (avoids asgi.py). Deferred, recorded."
      - "business-case-strength: Career+ ($24) tier — the 'genuine exclusive feature' problem is REAL (PREMIUM is already unlimited-everything incl. salary negotiation); a real entitlement needs metering PREMIUM down OR a new exclusive = multi-run design, NOT a clean one-PR change. TEAM/B2B2C tier remains the floor-flip lever (2-3 PRs + owner GTM). Founder/annual-first + 'surge pricing' scout idea REJECTED (surge = a dark pattern / gaming risk; founder discount is an owner Stripe-coupon config, not loop code)."
      - "security: CAPTCHA (needs owner Turnstile/hCaptcha keys; multi-surface web+mobile+asgi). Login lockout left in-memory by design (a shared store doesn't fix its targeted-DoS — CAPTCHA does). Texas SB2420 age-assurance → owner legal decision (PENDING_OPS)."
      - "Track E mobile VISUAL: jest-expo serializes component TREES, not pixels — committed screenshot IMAGES + the prep-pack vision verdict are human/CI (need a real render + an LLM key), NOT loop-buildable headlessly."
      - "store assets / brand icon: OWNER-BLOCKED per repo standard (loop must not auto-generate a brand mark — slop/DESIGNER QUESTION) + no image tooling. Did not fabricate. mobile IAP client (StoreKit/RevenueCat/Play Billing) needs owner keys — native, owner-blocked."
      - "mobile ReportButton trigger uses a '⚑' glyph vs web's inline SVG — Reviewer B non-blocking nit (acceptable: 12px muted monochrome dingbat, not emoji-as-icon, wrapped in a labelled Pressable). A shared vector icon is a clean future consistency polish."
  rolling_7d:
    merged_prs: 115              # 111 + 3 feature this run + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NEW migration a1b7c2f9e0d3 (content_reports, down_revision 993d75032689) — drift-gated, auto-applies on merge to main; the ≤1-migration-slot for the run
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 5
    unmet: [ai]                  # degraded_only — surfaced as OWNER_ACTION validation-capability-gemini (urgent). /api/report reads NO new secret → no new capability declaration needed.
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 3 shipped, 0 abandoned, 0 circuit-breaker trips. Headline: finally executed the long-deferred Track-D GenAI user-report affordance as its DEDICATED run (store-readiness ship-critical), closing a real 2026 Apple/Google compliance gap end-to-end (backend row + web+mobile UI, side-effect-honest). maker≠checker earned its keep by catching a non-load-bearing perf test (statement-count vs the LIMIT bound) — fixed + mutation-verified within cycle 1. Anchor was ONE coherent 15-file cross-stack feature; the other 2 PRs stayed strictly file-disjoint for parallel merge. Skepticism dropped several padding/false candidates. No recurring wall → no harness proposal warranted.
```
