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
  as_of: 2026-06-30
  last_run: 2026-06-30            # run 9 (fifth run on 2026-06-30)
  last_deep_audit: 2026-06-30    # the 8-scout sweep doubled as the ~daily deep audit
  this_run:
    changes_shipped: 5           # #126 input-bounds wallet-drain, #127 billing money-path tests, #128 mobile-billing event-set tests, #129 web coach a11y, #130 mobile a11y (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate (pytest/jest/tsc/flake8/eslint) before push
    review_rejections: 0         # UNUSUAL: all 10 reviewers (2/PR × 5) APPROVED first pass. NOT lax — verification was rigorous: 2 reviewers ran MUTATION tests in isolated worktrees to prove the new money-path tests (#127/#128) aren't tautological; 2 independently re-ran the mobile gate (#130); 1 re-verified the wallet-drain vuln against llm_workflows.py (#126). Clean sweep reflects tightly-scoped, single-concern, pre-verified PRs.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "BRANCH CONTAMINATION via a REVIEWER's local checkout (recovered): a PR-128 reviewer transiently applied the diff to the SHARED working tree to mutation-test, leaving tests/test_mobile_billing.py dirty on my local main. Caught via git status; git reset --hard origin/main. The remote PR branches were NEVER affected — all 5 merges used the GitHub API, not the local tree. RULE: reviewers needing a local checkout should use an isolated worktree (one did, correctly); when the local tree is dirty with work you didn't author, trust origin and reset."
      - "Skepticism rejected THREE functional-reality false positives before building: (a) job_public 'lazy-load crash' is None-guarded (job.application.status if job.application else SAVED); (b) the LLM-ceiling 'consume before call' is the DOCUMENTED wallet-drain design (an expensive attempt must count); (c) delete_user 'referral FK 500' — it already calls referrals.purge_user_referrals FIRST. Verified each against the code, built none (no churn)."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "ASGI.PY SLOT CHOICE this run: picked security input-bounds (#126) over analytics-instrumentation for the single contended asgi.py owner. Both real; the wallet-drain bounds defend live money the moment any traffic hits (provider spend caps still owner-unset), while PMF analytics yields NO signal pre-launch (0 users) — instrumenting now vs next run changes nothing measurable. Analytics deferred again, honestly."
      - "growth/PMF: privacy-safe analytics instrumentation — the PMF measurement foundation, deferred 6+ runs (still the priority asgi.py owner once it's free of a higher-urgency security/money item). DESIGN: AggregateEvent table keyed by event_type+cohort_date+window_date (NO PII/raw events); best-effort record_event() at signup/job-add/fit-score; a read endpoint GATED behind an env shared-secret bearer token (NOT any-authed-user — avoids leaking aggregate user counts), 503 when unset. Wants asgi.py + 1 migration."
      - "QUALITY_SCORECARD STALE (as_of 2026-06-29): its named ship-critical gaps are largely CLOSED since — CORS (#96), perf N+1 (#121), referral loop (#109), cross-instance limiter (#114). The independent Quality Auditor routine should re-grade; the factory consumes the scorecard as DATA and must NOT self-edit it (maker≠checker)."
      - "business-case-strength: Career+ ($24) tier — the 'genuine exclusive feature' problem is REAL (PREMIUM is already unlimited-everything incl. salary negotiation); a real entitlement needs metering PREMIUM down OR a new exclusive = multi-run design, NOT a clean one-PR change. TEAM/B2B2C tier remains the floor-flip lever (2-3 PRs + owner GTM)."
      - "security: CAPTCHA (needs owner Turnstile/hCaptcha keys; multi-surface web+mobile+asgi). Login lockout left in-memory by design (a shared store doesn't fix its targeted-DoS — CAPTCHA does)."
      - "store (NEW 2026 finding): Apple/Google now require a USER-REPORT/FLAGGING affordance for AI-generated content (GenAI/UGC guidelines) — added to ROADMAP Track D (loop-buildable: report endpoint + coach/prep UI; sprawls asgi.py+web+mobile → dedicated run). Texas SB2420 age-assurance → owner legal decision (PENDING_OPS)."
      - "Track E mobile VISUAL: jest-expo serializes component TREES, not pixels — committed screenshot IMAGES + the prep-pack vision verdict are human/CI (need a real render + an LLM key), NOT loop-buildable headlessly."
      - "store assets / brand icon: OWNER-BLOCKED per repo standard (loop must not auto-generate a brand mark — slop/DESIGNER QUESTION) + no image tooling. Did not fabricate."
  rolling_7d:
    merged_prs: 104              # 98 + 5 feature this run + 1 bookkeeping
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # last migration 993d75032689; no new migration this run (input-bounds = Pydantic-only schema bounds; the test + a11y PRs touch no models)
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 5
    unmet: [ai]                  # degraded_only — surfaced as OWNER_ACTION validation-capability-gemini (urgent)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 5 shipped, 0 abandoned, 0 circuit-breaker trips; a security wallet-drain hardening + two mutation-tested money-path coverage gaps + web & mobile a11y, all single-concern & file-disjoint. maker≠checker still earned its keep (mutation-tested the new tests in isolated worktrees to prove they're load-bearing, re-verified the wallet-drain vuln + the mobile gate) even though it drew no REQUEST_CHANGES — clean sweep reflects pre-verified scope, not lax review; skepticism rejected THREE functional-reality false positives (no churn). No recurring wall across runs → no harness proposal warranted.
```
