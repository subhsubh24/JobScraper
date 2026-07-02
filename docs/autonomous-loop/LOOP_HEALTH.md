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
  last_run: 2026-07-02            # run 15
  last_deep_audit: 2026-07-02    # run 14's FULL 8-scout sweep (run 15 ran a light 2-scout focused sweep — full audit was <6h prior)
  this_run:
    changes_shipped: 3           # #181 AI-consent gate (Track D centerpiece, backend+web+mobile), #182 auth-crypto unit tests (§26), #183 billing money-path auth-sync fix (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # every PR passed its local gate before push: backend 284 pass + flake8 clean; mobile tsc --noEmit + expo lint 0 + jest 60; web tsc + lint clean.
    review_rejections: 4         # #181: BOTH reviewers REQUEST_CHANGES for the SAME fail-open scorer default (independent) + Reviewer B also flagged the stale privacy date & a weak scoring test; #182: Reviewer B REQUEST_CHANGES (docstring overclaimed compare_digest→== timing coverage); #183: Reviewer B REQUEST_CHANGES (branch wrongly bundled test_auth_crypto.py via a checkout race). ALL fixed cycle 1. Anchor re-reviewed by 2 FRESH Opus-tier reviewers → both APPROVE (one caught a live-eval regression from the default flip, fixed + re-confirmed APPROVE).
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "maker≠checker's headline win: BOTH #181 reviewers INDEPENDENTLY caught a fail-OPEN scorer default — score_job defaulted use_embeddings=True and the dead/unrouted sibling score_all_jobs called it without the flag → a future 'rescore all' wiring would silently send resume/JD to Gemini for a non-consented user AND bypass the ceiling. Fixed: score_job defaults use_embeddings=False (FAIL CLOSED) + score_all_jobs computes client-and-consent. RULE: a function that can send data to a third party must be FAIL-CLOSED by default so a new caller can't leak by omission."
      - "A fail-closed default flip silently broke a LIVE-only eval (test_fit_score_real_embedding_path called score_job with no flag) — excluded by -m 'not live', so the PR's '284 pass' never caught it; it would fail on the next nightly run (§23). A re-reviewer caught it; fixed by opting the live eval into use_embeddings=True. RULE: when flipping a default, grep ALL callers INCLUDING live/nightly-only tests."
      - "CONCURRENT-agent tree contamination (run-9 redux): reviewers doing mutation tests + worktrees in the shared clone caused test_auth_crypto.py to get bundled into the billing branch via a checkout race (caught by 2 reviewers, fixed by recreating the branch clean from origin/main + force-with-lease), plus transient 'file modified since read' races and a fabricated prompt-injection 'system-reminder' a reviewer correctly ignored. RULE: authoritative state is origin/<branch> + git show <ref>:<file>; verify each branch's git diff --name-only origin/main...origin/<branch> before merge."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "DEAD-code Gemini call sites not consent-gated (defense-in-depth, non-blocking): LLMWorkflows.parse_job_description/generate_study_plan/generate_cover_letter + CareerCoach.get_session_summary call Gemini but have NO route/caller — if ever wired they MUST call require_ai_consent first. Not a live gap today."
      - "TEAM/B2B2C tier — still the PRIMARY named floor-lever (no loop-buildable lever honestly flips $100K pre-launch; crediting team ARR at 0 users = gaming). Multi-run epic + owner GTM."
      - "coach 100-msg/mo enforcement (doc↔code honesty — Pro gets unlimited today; wants the migration slot); Pro→Career+ in-place upgrade via Stripe portal; Career+ upgrade-rate wedges (voice mock / company dossier)."
      - "web SCREENSHOT REGEN (design-taste A→A+ artifact refresh — the stale 390px shot); /api/jobs/{id} N+1 + /api/analytics/pipeline pagination + free-tier TOCTOU (pre-launch 0-row polish, carried)."
      - "OWNER-BLOCKED (PENDING_OPS): mobile Career+ IAP client (RevenueCat keys/store accounts); store asset images/brand icon; CAPTCHA keys; CAREERPLUS_* Stripe price IDs."
  rolling_7d:
    merged_prs: 53             # git log origin/main --since="7 days ago" | grep -c '(#' (repo-wide across all routines); incl. this run's #181/#182/#183
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NEW migration this run: d4e7a1c9b8f2 (users.ai_consent_at; down_revision b2c8d4e6f1a5) — drift-gated, auto-applies on deploy. Latest migration is now d4e7a1c9b8f2.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 6
    unmet: []                    # ai closed 2026-07-02: GEMINI_API_KEY added to CI, test_llm_live.py real round-trip green
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 3         # fit-scoring, prep-pack, coach
    with_real_output_eval: 3     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — 3 shipped, 0 abandoned, 0 circuit-breaker trips. Headline: executed run-14's deferred DEDICATED centerpiece — the Apple 5.1.2(i) third-party-AI consent gate (PR #181, cross-stack backend+web+mobile, server-enforced + revocable + honest local-heuristic degrade + round-trip tested) — closing the last loop-buildable store-compliance FAIL (ACCEPTANCE_AUDIT A11 FAIL→PASS). maker≠checker earned its keep HARD again: BOTH #181 reviewers INDEPENDENTLY caught a fail-OPEN scorer default (score_job defaulted use_embeddings=True; the dead sibling score_all_jobs would have leaked to Gemini without consent) → fixed fail-closed; a fresh re-reviewer then caught that the flip silently broke a nightly LIVE eval (§23) → fixed by opting the live test into embeddings; 2 fresh re-reviewers APPROVE. Also shipped #182 (direct auth-crypto failure-branch unit tests, §26) and #183 (a real money-path functional bug: Stripe success synced only local state, leaving a stale 'Upgrade' post-purchase until reload). Recovered a run-9-style concurrent-agent checkout race (test file bundled into the wrong branch) without abandoning. HONEST on the number: no revenue lever this run; floor_met_year1 stays false; TEAM/B2B2C remains the primary named floor-lever. No recurring wall → no harness proposal warranted.
```
