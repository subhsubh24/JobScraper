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
  as_of: 2026-07-09
  last_run: 2026-07-09            # run 36
  last_deep_audit: 2026-07-09    # run 36 ran an 8-scout Haiku sweep (LLM-resilience / store-assets / business seat-tier / functional-reality / security / artifact-integrity / mobile-IAP / roadmap+regression-guards). run 35 ran the full 8-scout deep audit the day prior.
  this_run:                      # run 36
    changes_shipped: 2           # #330 resilient LLM model fallback (src/llm.py + 2 call sites + tests/test_llm_fallback.py + .env.example — ship-critical functional-reality; asgi.py-FREE) · #331 login-lockout moved to the cross-instance rate_counters table (security A→A+; asgi.py + tests) — file-DISJOINT (src/llm+ai_coach+enrichment / asgi.py+account-test) (+ this bookkeeping)
    changes_abandoned: 0         # store-assets, mobile-IAP, seat-tier, and the slot-refund were DEFERRED (named, principled), not abandoned — see deferred_decisions.
    abandoned_reasons: []        # reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner.
    verify_cycle_failures: 0     # 0 red REQUIRED CI checks on authored changes. Ran the exact gates locally before push (flake8 + targeted pytest; #330 proven END-TO-END against the REAL Gemini endpoint — dead primary gemini-2.0-flash recovered via gemini-flash-latest).
    review_rejections: 0         # #330 both reviewers APPROVE (Reviewer B independently reproduced the live round-trip; Reviewer A verified the real openai.NotFoundError classification). #331 reviewers: APPROVE/APPROVE.
    circuit_breaker_trips: 0
    incidents:                   # self-caught + reviewer-caught process notes (recovered, NOT abandonments)
      - "SCORECARD-vs-REALITY reconciliation (metrics win, §9 + DEEP_DIAGNOSIS): the 5th audit dropped overall C / ship-gate NO on a ship-critical functional-reality D — default model gemini-2.5-flash 'decommissioned'. Probed the REAL endpoint this run: gemini-2.5-flash → HTTP 200, it WORKS (both flagship reviewers reproduced). The model recovered / the audit's probe hit a transient 404. So I did NOT 'bump the dead pin' (the pin is alive); I built the DURABLE fix the incident CLASS needs — a resilient fallback — since gemini-2.0-flash IS genuinely dead and Google decommissions without notice. Observe the real system before acting on a DATA feed."
      - "\"merging\" ≠ \"merged\": run 34's bookkeeping (#321) titled 'import UI + perf shipped' and its loop-memory said #320 was 'merging' — but #320 NEVER merged (its required web-E2E was RED for a full day from a getByLabel(/Company/i) strict-mode collision). The marketed ATS import had NO UI on main while the ledger claimed it shipped. RULE reinforced: a claim ticks ONLY on PR merged:true + green required checks; I verified `git show origin/main:<file>` for every claim this run."
      - "maker≠checker EARNED ITS KEEP on ALL 3 non-trivial PRs: #322 (test covered 2/11 endpoints vs a docstring claiming 11 → parametrized all 11; + an undisclosed invalid-token-flood trade-off → documented); #323 (setup.sh `python cli.py init` under set -e would hard-fail onboarding after the deletion → fixed to scripts/init_db.py + real next-steps; AND a reviewer caught MY OWN bogus '~86%' coverage comment — I'd measured --cov=. over the whole repo, real CI cov is 91.82% → reverted); #324 (false 'one tap' report claim on a 2-step flow + overstated policy mandate → both fixed). Every PR had a real defect a reviewer caught; the value bar/gates alone would not have."
      - "Shared-tree hazard managed: reviewer subagents share the working dir, so I told them to review via refs (`git show <branch>:<file>`) or an isolated `git worktree`; several spawned their own worktrees for mutation-testing the PR2 reverts, keeping my main tree stable while I built the next PR. (Still hit one transient E2E boot failure when a reviewer briefly touched the tree — re-ran clean.)"
      - "BUILDS≠WORKS on the web E2E: the preinstalled Chromium is build 1194 but @playwright/test wants 1228, so a plain `playwright test` errors 'Executable doesn't exist … chrome-headless-shell-1228'. Ran the FULL suite 20/20 green via a throwaway config pointing executablePath at /opt/pw-browsers/chromium-1194/chrome-linux/chrome + --no-sandbox (root). This is the recovery recipe for the routine env."
      - "Coverage-measurement foot-gun (self-inflicted, reviewer-caught): `pytest --cov=.` measures the WHOLE repo (tests/scripts included) and reported 86%; the CI-configured coverage is `source=src,asgi` via `pytest -m \"not live\" --cov` = 91.82%. Always measure with the configured source / the exact preflight command, not --cov=."
    deferred_decisions:          # named + deferred, NOT abandoned (disjoint rule / value bar / brakes — not dead-ends)
      - "correctness A→A+ — refund the daily AI slot on a provider 502 (check_llm_ceiling pre-consumes the slot BEFORE the call; a flaky provider burns a legit user's quota). Needs asgi.py → collides with #331's asgi.py change this run (disjoint rule = ≤1 asgi.py PR/run). Clean next-run item; a _refund_counter + calls in the ~9 502 except-blocks."
      - "store-readiness C — rendered feature graphic/screenshots are DESIGN-TASTE-gated (a PIL/SVG auto-gen would read as generic slop → fails THE DESIGNER QUESTION, net-negative); the brand icon is designer-only; the mobile IAP round-trip is native/owner-gated (a JS-only react-native-purchases wiring that still shows 'coming soon' is grep-theater, NOT the real purchase flow — can't round-trip without a native build/store account). Keep the honest stub; owner-blocked."
      - "TEAM/B2B2C seat tier — the named floor-lever, but a ~530-LOC data-model→migration→endpoints vertical that deserves a FOCUSED run; a foundation-only slice risks Reviewer-B 'speculative' rejection (no entitlement/billing effect) AND credits $0 ARR pre-launch (doesn't move the C). Pre-launch DEFER RE-CONFIRMED (21st run)."
      - "rate_counters has no global TTL/sweep (Reviewer A #331 follow-up): distinct attacker-chosen ghost-email subjects each leave a permanent login_fail row (inherited property of the shared counter — IP/user-id subjects too — not a regression from #331). Low severity; a periodic sweep / TTL job is the fix. Named ticket for a future run."
      - "Coverage floor 85→88: VIABLE (CI actual 91.8%, ~7pt buffer). Standalone setup.cfg one-liner next run. §29 Browserbase validator (needs a reachable PROD_URL). Visual-verification native captures (owner-blocked). CAPTCHA TURNSTILE_SECRET (belt-and-suspenders on the lockout, owner key)."
      - "OWNER-BLOCKED (PENDING_OPS, unchanged): the two ship-critical C's — business-case-strength floor + store-readiness (rendered assets, mobile IAP, native captures). GEMINI live key IS set (probed real this run); Vercel DATABASE_URL→Neon/STRIPE_PRICE_*/RevenueCat/CAPTCHA keys/connect an ESP/REQUIRE_LIVE_TESTS=1. NO new migration this run (no schema change)."
  rolling_7d:
    merged_prs: 120            # repo-wide, approximate (118 at run 35 + this run's #330/#331); this bookkeeping merges after
    category_mix: {functional-reality: 1, security: 1}   # #330 LLM-resilience (functional-reality) / #331 cross-instance login-lockout (security) — two distinct categories
    diversity: varied
    reverts: 0
    readiness_attempts: 0        # not attempted — the two ship-critical C's stay owner/GTM-blocked (business-case floor + store assets/IAP), so submission-readiness is honestly not met
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
    ai_features_total: 5         # unchanged — no new LLM feature this run (#330 is call-path resilience, not a new model feature; #331 is auth security).
    with_real_output_eval: 5     # each LLM feature judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — run 36: 2 shipped, 0 abandoned, 0 circuit-breaker trips, 0 red REQUIRED CI checks, 0 review rejections (both PRs APPROVE/APPROVE first pass). CENTERPIECE: reconciled the 5th audit's ship-critical functional-reality D (default model 'decommissioned') against the REAL Gemini endpoint — gemini-2.5-flash returns HTTP 200, it WORKS (both reviewers reproduced) — so instead of 'bumping a dead pin' (the pin is alive), built the DURABLE fix the incident CLASS needs: #330 resilient model fallback (gemini-2.0-flash IS genuinely dead → wrapper recovers via gemini-flash-latest, PROVEN end-to-end live) + a per-PR regression guard that closes the 'model death passes every merge because live evals are nightly-only' hole. #331 moved the login-lockout to the cross-instance rate_counters table (the in-memory dict was ~zero real defense on serverless). KEY LESSON banked: a DATA feed (the scorecard) can be stale/transient — observe the REAL system before acting (DEEP_DIAGNOSIS); the metrics win (§9). Named deferrals (not scarcity): correctness slot-refund-on-502 (needs the contended asgi.py, next run), store assets (design/owner-gated), seat tier (focused-run + $0 pre-launch ARR), rate_counters TTL sweep (Reviewer-A follow-up). Two owner-blocked ship-critical C's stand (floor $57.5K<$100K — 21st run; store assets/IAP). No recurring wall → no harness proposal. floor_met_year1 stays false. FYI prior cadence: run 35 = 4 shipped, run 34 = 2, run 33 = 3.
```
