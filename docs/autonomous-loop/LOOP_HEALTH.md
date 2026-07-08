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
  as_of: 2026-07-08
  last_run: 2026-07-08            # run 32
  last_deep_audit: 2026-07-07    # run 30 ran the last FULL 8-lens Haiku deep audit. run 32 ran a focused 3-scout sweep (functional-reality+security / disjoint-wins+reachability / doc-freshness+business-case-reconcile) doubling as a light audit — functional-reality/security found NO CRITICAL/HIGH (mature repo); disjoint-wins confirmed the lever.py + greenhouse non-dict crash class on the LIVE import path; doc-reconcile found NO drift + re-confirmed the two ship-critical C's owner/GTM-blocked. A full ~daily 8-lens deep audit is now due next run.
  this_run:                      # run 32
    changes_shipped: 4           # #310 interview-readiness BACKEND (src/insights/readiness.py pure/key-free composite + GET /api/jobs/{id}/readiness + deterministic eval + endpoint tests) · #311 disjoint ATS-ingestion hardening (lever.py + greenhouse.py fetch_jobs graceful-degrade on malformed payloads + regression tests) · #312 readiness WEB card · #313 readiness MOBILE card — all file-DISJOINT (backend / ingestion / web / mobile); #310/#312/#313 complete the north-star READINESS LOOP end-to-end (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # 0 red REQUIRED CI checks. Ran the EXACT required gates locally before every push (backend pytest 525@91.6% + flake8; web tsc/lint/next-build; mobile tsc/expo-lint/jest 16) using installed web+mobile node_modules — nothing reddened CI.
    review_rejections: 2         # BOTH on #311, SAME issue, actioned in ONE fix within the ≤2-cycle cap: both ingestion reviewers (A+B) caught that a PRESENT-but-non-list greenhouse `jobs` field degraded to [] WITHOUT setting last_error → import-preview would misreport a malformed payload as "no open roles" (honesty-contract violation), and Reviewer A additionally caught the regression test was MUTATION-BLIND (`{"jobs":"nope"}` is an iterable string so the test passed even with the guard reverted). Fixed: set last_error + return []; reparametrized the test over non-iterable fixtures (None/42) + assert last_error. Fresh re-reviewer APPROVE (mutation-verified). #310/#312/#313 all APPROVE (web/mobile B nits folded proactively into a polish commit, fresh re-review APPROVE).
    circuit_breaker_trips: 0
    incidents:                   # self-caught + reviewer-caught process notes (recovered, NOT abandonments)
      - "maker≠checker earned its keep on #311: both reviewers independently caught the greenhouse `jobs`-field guard skipping last_error (a genuine honesty-contract gap — a malformed payload would read as an empty board), AND a mutation-blind guard-test (an iterable-string fixture that couldn't redden on a reverted guard). The value bar + gates alone would have shipped both. Fixed + fresh re-review, within ≤2 cycles."
      - "Merged the north-star feature backend-FIRST (#310) so the web (#312) + mobile (#313) surfaces branch off a main that already has GET /api/jobs/{id}/readiness — the E2E/journey suites boot the real endpoint, no 404 on the card fetch. Same proven structure as run 31's mock-interview 4-PR split."
      - "Added `getReadiness` to the mobile job-detail jest mock (the run-30 missing-mock class — an api method the screen now calls but the mock lacked would make `api.getReadiness` undefined → the screen errors → the required jest gate reddens). Paired with a degrade-gracefully test; both mutation-verified by Reviewer A (remove the mock → all 16 fail; remove .catch → only the degrade test fails)."
      - "Ran the exact required gates locally (backend pytest+flake8; web tsc/lint/next-build; mobile tsc/expo-lint/jest) via installed node_modules before every push — the standing counter to the iOS-reality mobile-blind-spot; 0 red required checks across 4 PRs."
      - "A recovery note (process, not a defect): an early `git checkout main` landed on a STALE local main (divergent-branches pull config), briefly hiding the just-merged work; recovered cleanly with `git fetch && git reset --hard origin/main`. Lesson: after auto-merges, hard-sync local main to origin/main rather than trusting a local pull."
    deferred_decisions:          # named + deferred, NOT abandoned (disjoint rule / value bar / brakes — not dead-ends)
      - "readiness `_overall` NaN guard: `_overall` catches TypeError/ValueError but not float('nan') (which would slip through un-clamped and later crash int(round(nan))). Reviewer-confirmed UNREACHABLE today (overall is server-COMPUTED from clamped 0–5 sub-scores, never client-supplied), so a guard is defense-in-depth on an unreachable path — deferred as a 1-line `math.isnan` hardening, not shipped as padding."
      - "readiness next-action UX polish (reviewer nits, non-blocking): `redo_answer` encodes a bare question number, not which session (only matters with >1 session/job); mobile CTA is shrink-wrapped vs the full-width primary buttons below (parity-consistent with web); when action==start_mock_interview both the card CTA and the 'Practice interview' section read the same (inherited from web). All cosmetic; batch a fast-follow."
      - "/api/analytics/pipeline SQL GROUP BY (perf A→A+, named since run 31); Coach-reply per-message id; migrate remaining IP-keyed read limits to per-user keying; DNS-rebinding SSRF residual (low-priority)."
      - "Retire-or-fix the cli.py/src/main.py CLI-only DEAD path (broken orchestrator-method calls + an N+1) — still orphaned per setup.cfg; polishing it is not product value until it's wired or retired."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever; genuinely owner/GTM-blocked (seat ARR uncreditable at 0 users = gaming — RE-CONFIRMED this run by the doc-reconcile scout). native-mobile snapshots + web screenshot regen (design-taste A→A+); login-lockout cross-instance (recorded decision: CAPTCHA is the fix)."
      - "OWNER-BLOCKED (PENDING_OPS, unchanged): GEMINI_API_KEY for live mock-interview generation (degrades honestly to 503); Vercel DATABASE_URL→Neon; STRIPE_PRICE_CAREERPLUS_* secrets; mobile IAP client; store asset images (owner/designer); CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml. NO new migration this run (readiness reuses existing tables; ingestion is code-only)."
  rolling_7d:
    merged_prs: 108            # repo-wide; +4 this run (#310/#311/#312/#313) over the 104 at run 31; this bookkeeping merges after
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run. Head unchanged (a7d3e1f0c92b from run 31). Owner must still set Vercel DATABASE_URL→Neon before the next deploy (PENDING_OPS).
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 9        # unchanged — readiness is KEY-FREE (no external secret, no LLM); ingestion is code-only. No new external capability introduced.
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 5         # unchanged — readiness is NOT an LLM feature (pure deterministic composite, no model call, like skill-gap-heatmap) → not on this ratchet; it has its own deterministic readiness-math eval (tests/evals/test_readiness_evals.py, 9 cases).
    with_real_output_eval: 5     # each LLM feature judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — run 32: 4 shipped, 0 ABANDONED, 0 circuit-breaker trips, 0 red REQUIRED CI checks. #310/#312/#313 COMPLETE the north-star interview-readiness LOOP end-to-end (backend pure/key-free composite + eval, web card, mobile card — the "differentiator that drives a candidate to interview-ready", ROADMAP Track A box now [x]); #311 is a disjoint LIVE-path crash-guard (lever+greenhouse malformed-payload degrade). maker≠checker earned its keep on #311 — both reviewers caught a real honesty-contract gap (malformed greenhouse `jobs` field misreported as an empty board) AND a mutation-blind guard test; fixed + fresh re-review within ≤2 cycles. Web/mobile B nits (a11y aria-label, 4% 0-sliver, indigo shade) folded proactively for coherence with the sibling ProgressBar. Honest scope: the SAME two owner/GTM-blocked ship-critical C's remain (business-case-strength floor $57.5K<$100K — RE-CONFIRMED owner-blocked; store-readiness assets+IAP owner/designer/native), so the run drove the highest-value LOOP-buildable work. No recurring wall → no harness proposal. floor_met_year1 stays false. FYI prior cadence: run 31 = 4 shipped, run 30 = 2 shipped, run 29 = 6 shipped.
```
