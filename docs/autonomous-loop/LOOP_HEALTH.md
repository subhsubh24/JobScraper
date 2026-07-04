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
  as_of: 2026-07-04
  last_run: 2026-07-04            # run 25
  last_deep_audit: 2026-07-03    # run 18's full 8-scout sweep was the last FULL deep audit; runs 19–25 ran focused sweeps (< 24h apart). Run 25 ran a full 6-scout sweep and leaned on the FRESH QUALITY_SCORECARD (2026-07-03) as the comprehensive-audit signal. A full 8-scout deep audit is due soon (~7 runs since the last).
  this_run:                      # run 25
    changes_shipped: 3           # #261 CENTERPIECE cross-pipeline skill-gap heatmap + AI learning plan (backend+web+mobile+evals) · #262 fit-score color-rounding consistency (web+mobile) · #263 living-artifact freshness (README/ASO/models comment) — all file-DISJOINT → parallel auto-merge (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # centerpiece verified locally in full: backend 417 pytest (+16 new) + flake8 + 5 deterministic gates (eval-coverage/validation/blocks/GTM/quality) all green; web tsc+eslint clean; mobile tsc+expo-lint clean + 71 jest (+5). PR2/PR3 verified in isolated worktrees (symlinked node_modules for web/mobile tsc+lint). All 3 PRs then merged through the required CI (preflight + web E2E) green.
    review_rejections: 0         # all 6 per-change Sonnet reviewers APPROVE first pass (centerpiece A mutation-verified the ranking split + tier gate; B judged both UI surfaces designer-grade + genuinely distinct from the prep tools). Non-blocking notes only (a color-regression test for the 4-line #262 fix — marginal/anti-padding; an ASO narrative paragraph for tailored résumé — nice-to-have).
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "WORKTREE isolation (new pattern): the centerpiece's 2 reviewers MUTATE the main working tree in place to prove tests are load-bearing (Reviewer A flipped the gap/strength split → 10/16 tests reddened, then reverted). Building PR2/PR3 in the same tree would have collided, so they were built in git worktrees (/tmp/wt-rounding, /tmp/wt-docs) with node_modules symlinked from the main checkout for tsc/lint. Reusable pattern for parallel PR-building during in-tree review."
      - "PIPE MASKS EXIT CODE (gate-integrity): the models.py de-stale first produced a 130-char comment line (E501). `python3 -m flake8 ... | tail -3 && echo CLEAN` printed the E501 error AND 'CLEAN' — the pipe made the shell see tail's exit (0), not flake8's (1), so the `&&` fired a false-positive. Caught it by re-running flake8 WITHOUT a pipe (exit 0 check) and moved the comment above the column line. RULE: verify a gate by its exit code, never by piped stdout + &&."
      - "DECISION COROLLARY on a ROADMAP SPEC: the item said 'a learning plan with web-searched resources'. A per-skill live WebSearch in the serverless request path is fragile (latency > budget risk, fabricated/dead links = the 'obviously-AI/inaccurate' output the growth counter-signal names). Chose LLM-suggested REPUTABLE named resources + time estimates (prompt hard-told not to invent URLs) — equivalent value, honest, robust. Recorded as a dated decision + reflected in the ticked ROADMAP text (living artifact) rather than shipping a worse literal reading."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "drafter→reviewer pass on generated artifacts (product-side maker≠checker on AI output) = the NEXT Track-A item — before returning a cover letter / tailored résumé / study plan / learning plan, run ONE independent LLM critique + revise once, guarded under the per-user/day LLM ceiling."
      - "Web+mobile ReportButton passes job-id, not artifact.id (functional-reality MED): a moderator can't tell WHICH artifact within a job was flagged. Touches web + mobile job/[id] pages, which overlapped #262's files this run → clean disjoint PR next run."
      - "/api/analytics/pipeline SQL GROUP BY (perf A→A+) + GET /api/jobs/{id} + PATCH /api/jobs/{id} selectinload N+1 — all asgi.py, pre-launch 0-row polish; asgi.py was owned by the centerpiece this run."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever (Career+/annual-first/referral all built). A genuine MULTI-RUN epic; crediting seat ARR at 0 users = gaming, so it does NOT honestly flip $100K pre-launch. Re-confirmed DEFER (12th consecutive run)."
      - "login-lockout cross-instance (RECORDED DECISION: kept in-memory — CAPTCHA is the real fix, owner-gated); native-mobile snapshots + web SCREENSHOT REGEN (design-taste A→A+ — needs a running app / native emulator)."
      - "OWNER-BLOCKED (PENDING_OPS): set Vercel DATABASE_URL→Neon BEFORE next deploy (fail-loud); STRIPE_PRICE_CAREERPLUS_* secrets (nightly reddens without them — confirmed the current nightly red is EXACTLY this, not a code regression); mobile IAP client; store asset images; CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml."
  rolling_7d:
    merged_prs: 82             # repo-wide across all routines; incl. this run's #261/#262/#263 (+ this bookkeeping)
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NO new migration this run (all 4 PRs are app-code/tests/copy only). Latest migration remains d4e7a1c9b8f2.
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 8        # unchanged (no new external dependency this run)
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 4         # fit-scoring, prep-tools (prep pack + cover letter + study plan + tailored résumé + salary negotiation — one module), coach, skill-gap-heatmap (learning plan — LLM half; the ranking is deterministic/key-free)
    with_real_output_eval: 4     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py); check_eval_coverage.py --report → 4 features, all with deterministic + real-output evals
  signal: improving              # bootstrapping | improving | steady | churning | stuck — run 25: 3 shipped, 0 abandoned, 0 circuit-breaker trips, 0 verify-cycle failures, 0 review rejections (ALL 6 per-change reviewers APPROVE first pass). Built the named next centerpiece — the cross-pipeline skill-gap heatmap + AI learning plan (#261, Track A's `/upskill`) → the ROADMAP box TICKS — plus a real fit-score color-consistency fix (#262) and living-artifact freshness (#263). maker≠checker earned its keep proactively (Reviewer A mutation-verified the ranking split + tier gate load-bearing; Reviewer B confirmed the feature is genuinely distinct, not a reskin). Two reusable process wins: WORKTREE isolation for parallel PR-building during in-tree review, and catching a pipe-masked flake8 exit before it hit CI. floor_met_year1 stays false (no honest pre-launch lever; TEAM/B2B2C DEFER, 12th run). No recurring wall → no harness proposal. Signal 'improving': converted the prior run's named deferral (skill-gap heatmap) into a shipped, box-ticking centerpiece — the loop finishing what it planned. Next centerpiece named: drafter→reviewer pass on AI output. FYI: run 24 was 4 shipped / 0 abandoned / 2 actioned-review-rejections. 4 shipped, 0 abandoned, 0 circuit-breaker trips, 0 verify-cycle failures, 0 net review rejections (2 REQUEST_CHANGES actioned + re-approved within ≤2 cycles; other 6 reviewers APPROVE first pass). This run CLOSED BOTH of run 23's explicit named deferrals — the tailored-résumé copy/download affordance (web #258 + mobile #257 → the run-23 HIGHEST-value ROADMAP box now TICKS, DoD complete) and the 'Premium'→'Pro' brand rename (#259) — plus a real functional-reality salary-$0 server-side validation fix (#256). maker≠checker EARNED ITS KEEP on 2 of 4 PRs (a cross-branch false comment in #258; an incomplete same-feature rename straggler in #259 — both caught, fixed, re-reviewed). A KEY BUILDS≠WORKS avoidance: checked expo-clipboard's SDK-56 stable-release status BEFORE adding it (none exists) and used RN's built-in Share instead — no native-dep risk. floor_met_year1 stays false (no honest pre-launch lever; TEAM/B2B2C re-confirmed DEFER, 11th run). No recurring wall → no harness proposal. Pattern across runs 17–24: a mature repo → high-value, well-reviewed, coherent units sized to the work; this run's signal is 'improving' because it converted the prior run's deferrals into shipped, box-ticking work (the loop finishing what it started), not just new polish. Next centerpiece named: skill-gap heatmap (dedicated run).
```
