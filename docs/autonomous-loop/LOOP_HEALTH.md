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
  last_run: 2026-07-08            # run 31
  last_deep_audit: 2026-07-08    # run 31 ran a focused 2-scout Haiku sweep (functional-reality+security; disjoint-wins+doc-freshness) doubling as a light audit — functional-reality/security found NO CRITICAL/HIGH (mature repo); disjoint-wins found one genuinely file-disjoint reliability bug. The run was a north-star CENTERPIECE (mock interview engine end-to-end), so scope was the feature + one disjoint fix, not a full 8-lens sweep; next ~daily deep audit due.
  this_run:                      # run 31
    changes_shipped: 4           # #305 mock-interview BACKEND engine (model+migration+generators+4 endpoints+tests+evals) · #306 disjoint LIVE-path greenhouse fetch_jobs non-dict-location fix · #307 mock-interview WEB runner · #308 mock-interview MOBILE runner — all file-DISJOINT (backend/ingestion/web/mobile), forming ONE north-star feature (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # 0 red REQUIRED CI checks. Installed web+mobile node_modules and ran the EXACT required gates locally before every push (backend pytest 507@91.28% + flake8; web tsc/lint/next-build; mobile tsc/expo-lint/jest 78) — a handful of local gate catches (web tsc Job.company→company_name; mobile jest nested-Text split; mobile eslint set-state-in-effect) were fixed pre-push, none reddened CI.
    review_rejections: 3         # ALL actioned within the ≤2-cycle cap. (1) #306 Reviewer B: the original departments guard was on a DEAD path (fetch_job_details, only cli.py/src/main.py-reachable, orphaned per setup.cfg) + the PR overclaimed reachability → RETARGETED to the genuinely-LIVE fetch_jobs location bug; fresh reviewer APPROVE. (2) #307 Reviewer B: a11y (3 bare buttons missing the standard focus ring; textarea missing aria-label; a dead ternary) → fixed; fresh re-review APPROVE. (3) #308 Reviewer A: a REAL BLOCKING mid-session-403 DEAD-END (submit()/openSession() didn't route a lapsed-Pro/revoked-consent 403 to the paywall) → fixed on mobile AND cross-applied to the identical latent bug in web; fresh re-review APPROVE. #305 both reviewers APPROVE first pass (2 nits folded in).
    circuit_breaker_trips: 0
    incidents:                   # self-caught + reviewer-caught process notes (recovered, NOT abandonments)
      - "maker≠checker caught a DEAD-PATH scout candidate (#306): the departments 'bug' was real at the unit level but on cli.py's orphaned path; the LIVE version of the same non-dict crash was one function over (fetch_jobs, which import-preview actually calls). A scout is a candidate generator, not an architect — trace reachability before building. Retargeting turned a dead-path-churn PR into an honest live-path fix rather than abandoning."
      - "maker≠checker caught a mid-session-403 DEAD-END (#308) that ALSO existed in web (#307): a blocking finding on one platform MUST be checked on the sibling — fixing only mobile would have shipped the same trap on web. Cross-applied the fix."
      - "Installing web/mobile node_modules removed the 'can't validate frontend locally' risk: ran the exact required gates (tsc/lint/next-build; tsc/expo-lint/jest) before every frontend push, so no red REQUIRED check across 4 frontend commits. This is the counter to the recurring iOS-reality mobile-blind-spot (prior runs leaned only on CI + reviewers)."
      - "SHARED-TREE DISCIPLINE HELD: every reviewer subagent used `git worktree add /tmp/wt-*` (or read-only diff when the branch was already checked out); the maker's own branch-switching in the main tree occasionally shifted HEAD under a reviewer mid-read, but each reviewer re-did its review in an isolated worktree — zero corrupted verdicts."
      - "Structured the north-star feature as 4 file-DISJOINT PRs (backend/ingestion/web/mobile) merged best-first (backend first, so the frontends branch off a main WITH the endpoints) — banks backend value regardless of frontend outcomes, matches the disjoint rule, isolates the untested-frontend risk."
    deferred_decisions:          # named + deferred, NOT abandoned (disjoint rule / value bar / brakes — not dead-ends)
      - "NEXT lowest-incomplete Track-A item: Interview-readiness score + autonomous next-best-action (computes readiness from mock-interview scores + skill-gap coverage + artifacts; recommends the single next action; deterministic readiness-math eval; web+mobile). The mock-interview engine this run is its key input."
      - "Mobile entry-point Pro-gating symmetry: the job-detail 'Practice interview' CTA shows unconditionally while other Pro tools gate at entry — non-blocking (the runner page handles the gate honestly, no dead-end); a fast-follow for consistency."
      - "answerMockInterview return type declares `answer` though the POST /answer result omits it (client compensates with the submitted text; GET echoes the persisted value). A backend echo of `answer` in the /answer result would make the type exact — tiny consistency follow-up."
      - "lever.py non-dict `.get()` hardening (same class as #306's fetch_jobs fix) + retire-or-fix the cli.py/src/main.py CLI-only DEAD path (broken orchestrator-method calls + an N+1) — both surfaced by #306 review."
      - "/api/analytics/pipeline SQL GROUP BY (perf A→A+); Coach-reply per-message id; migrate remaining IP-keyed read limits to per-user keying; DNS-rebinding SSRF residual (low-priority)."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever; genuinely owner/GTM-blocked (seat ARR uncreditable at 0 users = gaming). native-mobile snapshots + web screenshot regen (design-taste A→A+); login-lockout cross-instance (recorded decision: CAPTCHA is the fix)."
      - "OWNER-BLOCKED (PENDING_OPS): GEMINI_API_KEY for live mock-interview generation (feature degrades honestly to 503 without it); Vercel DATABASE_URL→Neon BEFORE next deploy (a NEW migration a7d3e1f0c92b ships this run); STRIPE_PRICE_CAREERPLUS_* secrets; mobile IAP client; store asset images (owner/designer); CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml."
  rolling_7d:
    merged_prs: 104            # repo-wide; incl. this run's #305/#306/#307/#308 (+ this bookkeeping) auto-merging through required CI
    reverts: 0
    readiness_attempts: 0
    readiness_rejected: 0
    recurring_failures: []
    harness_proposals_open: 0     # #57 RESOLVED 2026-06-28 — gates now enforced as required checks
  enforced_in_ci: true           # required checks on main (preflight + web E2E), enforce_admins=ON
  auto_migrate_on_deploy: enabled # NEW migration this run: a7d3e1f0c92b (add mock_interviews). New head a7d3e1f0c92b (drift-gated, forward-only, auto-applies on deploy). Owner must set Vercel DATABASE_URL→Neon before the deploy (PENDING_OPS).
  validation:                    # self-validation manifest readiness (compute every run: scripts/check_validation.py --report)
    enforced_in_ci: true         # validate-capabilities runs inside the required `preflight` check
    capabilities_total: 9        # +1: github_enrichment (validation=mock — no secret; the unauthenticated GitHub API rate-limits from shared CI IPs so a live happy-path test would flake, the graceful-degrade path is real-observed + mock-pinned)
    unmet: []                    # all external capabilities validated (real or mock)
  eval_coverage:                 # OUTPUT-quality coverage (compute: scripts/check_eval_coverage.py --report)
    enforced_in_ci: true         # check_eval_coverage runs inside the required `preflight` check
    ai_features_total: 5         # fit-scoring, prep-tools, coach, skill-gap-heatmap, mock-interview (NEW run 31). github_enrichment is NOT an LLM feature (structured GitHub API data, no model call) → not on this ratchet; it has its own deterministic golden + mocked round-trip tests.
    with_real_output_eval: 5     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py) — mock-interview added 2 live evals (role-specific questions; HONEST strong>weak scoring ordering)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — run 31: 4 shipped forming ONE north-star feature (the mock interview engine — surface 3 of the north star — built end-to-end backend+web+mobile+evals + a disjoint live-path reliability fix), 0 ABANDONED, 0 circuit-breaker trips, 0 red REQUIRED CI checks, 3 review-rejections ALL ACTIONED within the ≤2-cycle cap (a dead-path scout candidate retargeted to the live bug; an a11y set; a real mid-session-403 dead-end fixed on BOTH platforms). maker≠checker earned its keep three times — catching a dead-path candidate, a cross-platform dead-end, and a11y gaps the value bar alone wouldn't. Honest scope: a mature repo still held below ship by the same two owner/GTM-blocked ship-critical C's (business-case-strength floor $57.5K<$100K — 18th-run DEFER; store-readiness assets+IAP owner/designer/native), so the run drove the highest-value LOOP-buildable work: the north-star interview-coaching pillar now exists, honest-scored, nav-reachable, dead-end-free. Installing web/mobile node_modules to run the exact required gates locally is the counter to the recurring iOS-reality mobile-blind-spot. No recurring wall → no harness proposal. floor_met_year1 stays false. FYI prior cadence: run 30 = 2 shipped, run 29 = 6 shipped, run 28 = 2 shipped/1 abandoned.
```
