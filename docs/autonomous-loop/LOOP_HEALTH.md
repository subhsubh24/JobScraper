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
  last_run: 2026-07-08            # run 33
  last_deep_audit: 2026-07-07    # run 30 ran the last FULL 8-lens Haiku deep audit. runs 31/32/33 ran focused light sweeps. run 33 ran a 4-scout sweep (demo security-hardening / functional-reality+disjoint-wins / doc-business-quality reconcile / web-UX+design) — functional-reality found the import-preview UI gap (real; DEFERRED on merit, see this_run); the security scout produced the demo hardening checklist; doc-reconcile re-confirmed the two ship-critical C's owner/GTM-blocked + the perf top_gap loop-buildable. A full ~daily 8-lens DEEP AUDIT is now OVERDUE (3 runs since the last full one) — run it next run.
  this_run:                      # run 33
    changes_shipped: 3           # #315 §34 PUBLIC DEMO backend (POST /api/demo/skill-match — public/no-account/KEY-FREE skills match + demo_match.py pure fn + extract_skills→@staticmethod + tests + deterministic eval) · #316 §34 demo WEB page (/demo + waitlist link + browser E2E) · #317 perf A→A+ (/api/analytics/pipeline SQL GROUP BY, the QUALITY_SCORECARD top_gap deferred 5 runs) — all file-DISJOINT (asgi+insights+ranking / web / asgi+perf-test); #315+#316 = the §34 pre-launch demo funnel end-to-end (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner. NOTE: the import-preview-UI functional-reality finding was DEFERRED (not abandoned) — a real gap but low-value (description-less shell jobs) + hard to validate E2E (external ATS); named for a proper future build.
    verify_cycle_failures: 0     # 0 red REQUIRED CI checks. Ran the EXACT required gates locally before every push (backend pytest 564@ + flake8; web tsc/eslint/next-build; the demo browser E2E 5/5 via installed node_modules + the preinstalled Chromium executablePath) — nothing reddened CI.
    review_rejections: 3         # #315 both APPROVE first pass. #316: BOTH reviewers REQUEST_CHANGES (2) — Reviewer B: /demo had a canonical URL but was MISSING from sitemap.ts (undercuts §34 discoverability); Reviewer A: the E2E had ZERO honest-state coverage (no-résumé/no-skills/API-error — the demo's whole point). Fixed both (sitemap + 3 honest-state journeys + a11y persistent-live-region + copy tweak) → fresh re-reviewer APPROVE (5/5 journeys green), within ≤2 cycles. #317: both APPROVE (1 non-blocking dup nit — the dead `str(status)` fallback branch, removed in a cleanup commit).
    circuit_breaker_trips: 0
    incidents:                   # self-caught + reviewer-caught process notes (recovered, NOT abandonments)
      - "maker≠checker earned its keep on #316: Reviewer B caught /demo missing from sitemap.ts (a page whose whole §34 purpose is discoverability), and Reviewer A caught the E2E covering only the happy path — none of the honest-state branches (no-résumé/no-skills/API-error) that are the demo's differentiator. Both fixed + fresh re-review, ≤2 cycles."
      - "DECISION COROLLARY (§6) made explicitly up front on #315: built the demo as the KEY-FREE local skills half, NOT the Gemini-gated tailored-résumé — the latter would 503 on a missing owner key (a broken demo §34 forbids) or spend the owner's LLM budget on anon traffic. Recorded the call in the endpoint docstring + the module + the PR."
      - "Two asgi.py PRs shipped in ONE run safely by SEQUENCING: #315 (demo endpoint) merged FIRST, then #317 (perf) branched off the updated main → zero conflict. The 'one asgi.py PR/run' convention is about CONCURRENT-open-PR conflicts; sequential is fine and unblocked a 5-run-deferred perf gap."
      - "Concurrent web work + backend reviewers: gave reviewers the DIFF as source-of-truth and built the next PR in a git WORKTREE (+node_modules symlink) so the main tree stayed put for the reviewers reading it (run-28 shared-tree hazard avoided). Caveat learned: a symlinked node_modules breaks Turbopack `next build` ('points out of filesystem root') though tsc/eslint pass — run the real build/E2E in the actual tree once free."
      - "BUILDS≠WORKS on a public surface: drove the /demo page end-to-end in a real browser against the LIVE backend (Playwright config boots uvicorn+next; #315's endpoint was in main), asserted the real matching/missing skills + coverage % RENDER, route-intercepted a 500 to prove the configured-but-failing degrade (§6), and VISUALLY verified the screenshot (on-brand, correct 67%). Used the preinstalled Chromium (`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`) via a throwaway executablePath config since the npm playwright wanted a browser build the routine env lacks."
    deferred_decisions:          # named + deferred, NOT abandoned (disjoint rule / value bar / brakes — not dead-ends)
      - "ATS import-preview UI (functional-reality scout finding): POST /api/jobs/import-preview is built+tested+hardened + marketed (README:39, ROADMAP:47 [x]) but has ZERO UI in web/mobile — a marketed feature no user can reach. DEFERRED on merit, NOT padding: (a) the endpoint returns description-LESS listings → imported jobs would be unscoreable shells (low value); (b) the happy path needs a live external Greenhouse/Lever board I can't validate E2E deterministically. Build PROPERLY later (add a description fetch so imports are scoreable + a mock-based E2E). This is the value bar working."
      - "§34 GATED BETA invite mechanism (waitlist→codes→real app) — the remaining §34 half; gated on the owner SITE_GATE + §13-Gate-1, so unbuilt this run by design."
      - "readiness `_overall` NaN guard (1-line, unreachable defense-in-depth); readiness next-action UX polish (cosmetic); Coach-reply per-message id; migrate remaining IP-keyed read limits to per-user; DNS-rebinding SSRF residual (low); retire/fix the cli.py/src/main.py CLI-only dead path."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever; genuinely owner/GTM-blocked (seat ARR uncreditable at 0 users = gaming; building speculative B2B code pre-launch with 0 pipeline is the 'scale into a leaky bucket' §9 forbids — RE-CONFIRMED this run, 19th). native-mobile snapshots + web screenshot regen (design-taste A→A+); login-lockout cross-instance (recorded: CAPTCHA is the fix)."
      - "OWNER-BLOCKED (PENDING_OPS): SITE_GATE_PASSWORD (now ALSO gates §34's gated-beta half); GEMINI_API_KEY (live mock-interview 503; the demo is KEY-FREE so unaffected); Vercel DATABASE_URL→Neon; STRIPE_PRICE_CAREERPLUS_* secrets; mobile IAP client; store asset images (owner/designer); CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml. NO new migration this run (demo is key-free, no schema; perf is a query rewrite)."
  rolling_7d:
    merged_prs: 112            # repo-wide; +3 feature PRs this run (#315/#316/#317) over the ~109 at run 32; this bookkeeping merges after
    category_mix: {monetization-growth-funnel: 2, performance: 1}   # §37 diversity: #315+#316 = pre-launch funnel/PMF (a NEW category vs runs 31/32's Track-A feature focus), #317 = perf. varied — broke the recent Track-A monoculture toward the growth-funnel + a quality/perf lever.
    diversity: varied
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
    ai_features_total: 5         # unchanged — the demo skill-match is NOT an LLM feature (pure deterministic composite, no model call, like skill-gap-heatmap/readiness) → not on this ratchet; it has its own deterministic eval (tests/evals/test_demo_match_evals.py, 7 cases).
    with_real_output_eval: 5     # each LLM feature judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — run 33: 3 shipped, 0 ABANDONED, 0 circuit-breaker trips, 0 red REQUIRED CI checks. #315+#316 build the §34 PUBLIC DEMO of the core aha end-to-end (backend KEY-FREE skills-match endpoint + eval, /demo web page + browser E2E) — the pre-launch funnel driver / PMF leading indicator (§9), the correct PMF-first priority over the owner-blocked floor-lever; #317 closes the QUALITY_SCORECARD's named perf top_gap (analytics/pipeline SQL GROUP BY, deferred 5 runs, finally unblocked). maker≠checker earned its keep on #316 (a real sitemap discoverability gap + zero honest-state E2E coverage — both fixed + fresh re-review, ≤2 cycles) and made a clean DECISION COROLLARY on #315 (KEY-FREE demo, never 503s on a missing owner key). Diversity: broke the recent Track-A feature monoculture toward the growth-funnel + a perf/quality lever (§37: varied). The import-preview-UI functional-reality gap was DEFERRED on merit (low-value shell jobs + unvalidatable external ATS), not padded around. Honest scope: the SAME two owner/GTM-blocked ship-critical C's remain (business-case-strength floor $57.5K<$100K — RE-CONFIRMED; store-readiness assets+IAP), so the run drove the highest-value LOOP-buildable work. A full 8-lens DEEP AUDIT is now OVERDUE (run 30 was the last) — DUE next run. No recurring wall → no harness proposal. floor_met_year1 stays false. FYI prior cadence: run 32 = 4 shipped, run 31 = 4, run 30 = 2.
```
