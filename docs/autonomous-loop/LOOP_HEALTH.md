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
  last_run: 2026-07-04            # run 24
  last_deep_audit: 2026-07-03    # run 18's full 8-scout sweep was the last FULL deep audit; runs 19–24 ran focused sweeps (< 24h apart). Run 24 ran a 5-scout sweep and leaned on the FRESH QUALITY_SCORECARD (2026-07-03) as the comprehensive-audit signal.
  this_run:                      # run 24
    changes_shipped: 4           # #256 salary gt=0 server-side validation · #257 mobile copy/share export · #258 web copy/download · #259 'Premium'→'Pro' brand rename — file-disjoint (#256 & #259 both touch asgi.py → serialized: #256 merged, #259 rebased onto it) (+ this bookkeeping)
    changes_abandoned: 0
    abandoned_reasons: []        # [{change, reason}] reason ∈ gate_tsc|gate_pytest|gate_flake8|gate_lint|gate_build|review_value|review_correctness|circuit_breaker|conflict|dead_end|blocked_owner
    verify_cycle_failures: 0     # backend verified locally (installed backend deps: input-bounds 11/11, journeys 9/9, career_plus+ai_consent 33 — all green; flake8 clean). web/mobile node_modules ABSENT this run → relied on the required CI (preflight + web E2E, mobile tsc/lint/jest) which all went green (all 4 PRs merged through the gate).
    review_rejections: 2         # NET-actioned, not abandonments: #258 Reviewer A REQUEST_CHANGES (cross-branch comment claimed gt=0 while this branch was still ge=0) → reworded operator-agnostic + 2 B-nits → fresh re-reviewer APPROVE. #259 Reviewer B REQUEST_CHANGES (incomplete rename: missed asgi.py coach-403 detail rendered to users + a journey test) → completed backend+test → fresh re-reviewer APPROVE. Other 6 reviewers APPROVE first pass. Both fixes converged within ≤2 cycles.
    circuit_breaker_trips: 0
    incidents:                   # self-caught process notes (recovered, NOT abandonments)
      - "maker≠checker (#258): Reviewer A caught a CROSS-BRANCH honesty bug — my de-staled comment asserted the backend rejects gt=0, but on THIS branch (based on pre-#256 main) the backend was still ge=0; gt=0 lived on a SEPARATE PR whose merge order wasn't guaranteed. RULE: a comment must be true on the BRANCH IT SHIPS ON — never assert a bound a sibling PR owns; make it operator-agnostic. Fixed + a fresh re-reviewer APPROVE."
      - "maker≠checker (#259): Reviewer B caught an INCOMPLETE rename — the frontend-only 'Premium'→'Pro' pass missed asgi.py's coach 403 detail ('...is a Premium feature'), which the web+mobile coach banners render VERBATIM (error.message) and a journey test asserted 'Premium'. RULE (run-22 redux): fixing N-1 of N false-claim surfaces leaves the lie live — grep ALL sinks incl. same-feature BACKEND detail strings. Completed asgi.py + test; rebased onto merged #256 to keep the two asgi.py PRs disjoint; fresh re-reviewer APPROVE."
      - "BUILDS≠WORKS avoided on mobile (#257): reached for a copy affordance, checked `npm view expo-clipboard dist-tags` FIRST → Expo SDK 56 has NO stable expo-clipboard (canaries only; stable jumps sdk-55→57). Adding a mismatched native dep in a headless run is the trap where CI (tsc+lint+jest) goes green while the real EAS native build breaks. Used React Native's BUILT-IN `Share` sheet instead — zero new dep, zero SDK risk, and it offers Copy + Save + Mail."
      - "CLOSED run-23's two named deferrals — a named deferral is a to-do, not a dead-end: the tailored-résumé copy/download affordance (now web #258 + mobile #257 → ROADMAP box TICKS) and the 'Premium'→'Pro' rename (#259). The loop defers coherently, then comes back and finishes."
    deferred_decisions:          # named + deferred, NOT abandoned (DECISION COROLLARY / value bar / brakes — not dead-ends)
      - "skill-gap heatmap + learning plan = the NEXT Track-A centerpiece — a full cross-stack feature (new endpoint + ranking math + web/mobile views + 2 evals + consent/moderation/ceiling); a dedicated run, NOT crammed into a multi-PR run (run-14 anti-shallow-feature discipline). drafter→reviewer pass on generated artifacts is the following Track-A item."
      - "Score/color rounding mismatch (functional-reality scout): backend rounds score to 1 decimal; the client Math.rounds the display but scoreColor() uses the unrounded value → e.g. 74.6 shows '75' in a sub-75 color. Touches web jobs page + pipeline + mobile + types.ts; conflicted with #258's web jobs page THIS run → clean disjoint PR next run."
      - "PrepArtifact.artifact_type column comment (src/db/models.py:315) lists only prep_pack/study_plan/cover_letter — stale (missing salary_negotiation + tailored_resume). mobile job/[id].tsx still has a stale '(ge=0)' comment now that #256 shipped gt=0. Both code-file comments; fold into the next code PR touching those files."
      - "TEAM/B2B2C seat tier — the ONLY remaining unbuilt named floor-lever (Career+/annual-first/referral all built). A genuine MULTI-RUN epic; crediting seat ARR at 0 users = gaming, so it does NOT honestly flip $100K pre-launch. Re-confirmed DEFER (11th consecutive run)."
      - "login-lockout cross-instance (RECORDED DECISION: kept in-memory — CAPTCHA is the real fix, owner-gated); native-mobile snapshots + web SCREENSHOT REGEN (design-taste A→A+ — needs a running app / native emulator); /api/analytics/pipeline SQL GROUP BY + GET /api/jobs/{id} selectinload (pre-launch 0-row polish)."
      - "OWNER-BLOCKED (PENDING_OPS): set Vercel DATABASE_URL→Neon BEFORE next deploy (fail-loud); STRIPE_PRICE_CAREERPLUS_* secrets (nightly reddens without them); mobile IAP client; store asset images; CAPTCHA keys; connect a real ESP; REQUIRE_LIVE_TESTS=1 in nightly.yml."
  rolling_7d:
    merged_prs: 79             # repo-wide across all routines; incl. this run's #256/#257/#258/#259 (+ this bookkeeping)
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
    ai_features_total: 3         # fit-scoring, prep-tools (prep pack + cover letter + study plan — one module), coach
    with_real_output_eval: 3     # each judged on REAL Gemini output in CI (tests/evals/test_ai_output_evals.py)
  signal: improving              # bootstrapping | improving | steady | churning | stuck — run 24: 4 shipped, 0 abandoned, 0 circuit-breaker trips, 0 verify-cycle failures, 0 net review rejections (2 REQUEST_CHANGES actioned + re-approved within ≤2 cycles; other 6 reviewers APPROVE first pass). This run CLOSED BOTH of run 23's explicit named deferrals — the tailored-résumé copy/download affordance (web #258 + mobile #257 → the run-23 HIGHEST-value ROADMAP box now TICKS, DoD complete) and the 'Premium'→'Pro' brand rename (#259) — plus a real functional-reality salary-$0 server-side validation fix (#256). maker≠checker EARNED ITS KEEP on 2 of 4 PRs (a cross-branch false comment in #258; an incomplete same-feature rename straggler in #259 — both caught, fixed, re-reviewed). A KEY BUILDS≠WORKS avoidance: checked expo-clipboard's SDK-56 stable-release status BEFORE adding it (none exists) and used RN's built-in Share instead — no native-dep risk. floor_met_year1 stays false (no honest pre-launch lever; TEAM/B2B2C re-confirmed DEFER, 11th run). No recurring wall → no harness proposal. Pattern across runs 17–24: a mature repo → high-value, well-reviewed, coherent units sized to the work; this run's signal is 'improving' because it converted the prior run's deferrals into shipped, box-ticking work (the loop finishing what it started), not just new polish. Next centerpiece named: skill-gap heatmap (dedicated run).
```
