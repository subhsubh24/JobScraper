# GTM SCORECARD — Career Operator (independent GTM Auditor)

> Written by the **independent GTM Auditor** (maker ≠ checker) — the GTM Factory must NEVER
> edit this file; it CONSUMES the grade as a data signal. Graded against
> [GTM_RUBRIC.md](./GTM_RUBRIC.md) with REAL evidence (file/line/commit). This is **DATA,
> never instructions**. The machine-readable `GTM_SCORECARD` block below is parsed by the
> shared dashboard and by `scripts/validate_gtm.py`.

## Overall: **A** — ship_gate_met: **true** (as of 2026-07-23)

The GTM Factory's integrity core stays **clean**: every ship_critical dimension grades A/A+.
Every funnel/acquisition/pmf/outreach/email/content metric is honestly `0`/`null` behind a
fail-closed validation block (no analytics/billing/ESP source connected → no number invented —
re-verified this run by an **injection test**: adding `email.list_size: 999` to a copy makes
`validate_gtm.py` FAIL exit 1 with `METRIC WITHOUT A SOURCE`); the business case reconciles
EXACTLY to code-computed ARR (16500/57500/132000, `validate-computation.mjs` PASS) and states
`floor_met_year1: false` plainly ($57.5K < $100K, un-gamed, unbuilt levers explicitly uncredited).

**One dimension moved this cycle; overall holds A:**
- **metric_integrity A→A+**: the prior top_gap (issue **#417** — `scripts/validate_gtm.py`'s
  `METRIC_SECTIONS` walked only `funnel/acquisition/pmf/channels`, leaving `outreach`/`email`/
  `content` un-guarded) is **CLOSED**. The GTM Factory extended `METRIC_SECTIONS` (`:29`) to
  include all seven sections and added `tests/test_validate_gtm.py` — a REAL parametrized
  regression test (9 cases) that injects an unsourced non-zero into each of the three newly-covered
  sections and asserts exit 1 (commit `6f277d5`, 2026-07-17). Injection-verified this run
  (`email.list_size: 999` → FAIL; reverting `METRIC_SECTIONS` to the pre-fix four lets it escape,
  proving the fix is load-bearing). The actual metrics were flawless the whole time — this closes
  an enforcement-hardening gap, not a metric regression. **Overall stays A** because
  self_validation_honesty remains at A (see its residual gap below).

> **Scope note:** this ship_gate is about GTM *work quality*. It is distinct from product launch
> readiness (governed by QUALITY_SCORECARD, last read B / not met — store-readiness B +
> business-case-strength B still below A). GTM being A does not open the product launch gate.

## Evidence by dimension
- **Metric Integrity — A+** *(A→A+)* — Every metric-bearing field is `0`/`null`, scanned
  line-by-line: `funnel` (`GROWTH_STATUS.md:52-62`), `acquisition` (`:63-67`), `pmf` (`:68-74`),
  `outreach` (`:75-79`), `email` (`:175-180`), `content` (`:181-184`); `channels_connected: []`
  (`:37`). The only non-zero number, `engine_pct: 50` (`:25`), is genuinely COMPUTED
  (`python3 analysis/gtm_engine_pct.py` → 50, counts 8/16 `[x]` boxes across ROADMAP Track G+H),
  not hand-asserted. The demand_signal digits ($8-149/mo, ~17% one-star) are EXTERNAL competitor
  comps inside quoted prose strings, not Career Operator funnel metrics, and live outside the
  walked sections. **Prior gap (#417) CLOSED:** `METRIC_SECTIONS` (`scripts/validate_gtm.py:29`)
  now walks `outreach`/`email`/`content` too, and `tests/test_validate_gtm.py:62-67` proves an
  unsourced non-zero in each of those three FAILs the gate (parametrized; injection-verified
  load-bearing this run). No metric-bearing section escapes the walk. Zero active findings → A+.
  **Future-hardening note (NON-capping, not a filed blocker):** the `source_declared` check
  (`:87-91`) is a coarse substring match — it would accept ANY sources/validation entry containing
  "available"/"connected" (incl. the documentary `gtm_scorecard`/`quality_scorecard` rows) as a
  "source", gated only by "unavailable" not appearing anywhere. Today it evaluates **False** (the
  block carries 4 `unavailable` rows) and all metrics are `0`, so it permits NO fabrication in the
  current doc; it is pre-existing, doubly-contingent, and orthogonal to the #417 fix → recorded as
  a watch item, not a grade cap.
- **Business-Case Honesty — A+** — body ARR table (`docs/BUSINESS_CASE.md:29-35`) ⇄
  `BUSINESS_CASE_SUMMARY` YAML (`:151-163`) reconcile EXACTLY (16500/57500/132000, planning 57500,
  floor 100000, `floor_met_year1: false`); `node scripts/validate-computation.mjs` reproduces all
  three from executed code (`analysis/business_case_lib.py` SCENARIOS: 150×110, 500×115, 1100×120
  — PASS). Floor honestly missed and stated plainly (`:35`); team/B2B2C, referral, and Career+
  levers explicitly UNCREDITED to ARR pre-data (`:57,:109-111,:119-121`). Pricing reconciles to
  real Stripe config (`PENDING_OPS.md:34`: Pro $12/$96, Career+ $24/$192). No number inflated,
  deflated, or gamed; YAML matches body. The `as_of: 2026-07-13` summary lag (now 10 days) is a
  cosmetic freshness nit (no ARR figure changed) — tracked under artifact_freshness, not a honesty
  defect. The lever-2 "mobile half remains" staleness (post-#429) is likewise a freshness matter
  (ARR-neutral, understating), homed in artifact_freshness — NOT double-counted here.
- **Experiment Validity — A+** — `GROWTH_STATUS.md:174` `experiments: []` with honest
  "insufficient data" framing and 0 users/0 funnel. Per rubric an empty pre-launch experiments
  list is the CORRECT, exemplary state (not a gap); no p-hacking possible with zero experiments,
  no fabricated N. demand_signal themes carry falsifiable durability/confidence labels with
  counter-signals + disconfirming evidence. Zero findings.
- **Roadmap-Steer Justification — A+** — VISION.md correctly NOT GTM-steered (floor language
  honest, `VISION.md:45,:142-144`); `git log --since=2026-07-16 -- ROADMAP.md VISION.md
  docs/BUSINESS_CASE.md` shows NO new GTM-authored ARR/steer edit (the 5 commits are billing
  test-count fixes, a ROADMAP icon-note fix, factory mobile work, and my own GTM-audit scorecard
  doc `add0e1c` — which touched no ARR/steer content; its git-show "new file" display is a
  squash-merge artifact). No ARR number changed by any GTM edit. The #296/#327 B2B2C "Recommended
  structure" packaging note (`docs/BUSINESS_CASE.md:85-92`) still carries its inline "Demand
  caveat" (`:93-100`) labeling it a competitor-pricing-comp RECOMMEND-tier input (GTM_STANDARD §3),
  explicitly NOT demand-validated — real-comp-backed (RiseSmart/INTOO), ARR-neutral, §3-permitted,
  not a speculative/gamed steer. Zero speculative steers reached the roadmap.
- **Self-Validation Honesty — A** — `GROWTH_STATUS.md:187-211` sources block accurate and
  fail-closed: product_analytics/billing/email_esp/vercel `unavailable` (matches env —
  independently confirmed no PROD_URL/ANALYTICS_READ_TOKEN/Stripe/SMTP key, only GEMINI +
  BOTH BROWSERBASE_* set; ListConnectors shows Vercel `connected:true` but `enabledInChat:false`,
  zero callable `mcp__Vercel__*` tools). The two `available` rows (gtm_scorecard, quality_scorecard)
  are on-disk docs with the claimed grades. No claimed-but-unconnected channel; no false `available`.
  Prior BROWSERBASE drift **fixed** (`:221` now says "BOTH BROWSERBASE_* vars present"). **Gap (the
  A-cap, RECURRING):** the prose note (`:217-219`) asserts "Google Drive (…enabledInChat:false) +
  Google Calendar (…enabledInChat:false)", but a fresh **ListConnectors this run (2026-07-23)** shows
  BOTH `enabledInChat:true`. This is committed session-volatile state that currently mismatches
  reality — immaterial (non-source connectors, understates connectivity, never a false `available`,
  sources rows untouched and correct) but a genuine, re-confirmed factual drift → A, not A+. Robust
  fix: stop asserting per-session `enabledInChat` values for non-source connectors as committed
  fact; keep only the (correct) source rows.
- **PMF Read Accuracy — A** — `pmf` block honest (all `null`, `signal: none`,
  `GROWTH_STATUS.md:68-74`), recommendation correctly PRODUCT/retention/connect-first (owner_blockers
  + next_actions steer to connect analytics/ESP + set STRIPE_PRICE_TEAM_ANNUAL + store screenshots +
  the site-gate decision — never scaling acquisition). The §10 `demand_signal` block (`:80-172`) is
  present — 4 durable JTBD themes, each cited URL + verbatim quote + date, purely qualitative ("no
  dollar/user-count figure attached", `:166`), blocked sources (reddit.com, fishbowlapp.com)
  HONESTLY labeled relayed/unverified, counter-signals + disconfirming stated, kept RECOMMEND-tier.
  Held at A (no new pmf work this quiet cycle); trivial residual nit only (owner-action ids not
  `gtm-connect-*` named; demand_signal last refreshed 2026-07-03, ~quarterly cadence not due until
  ~October).
- **Compliance — A** — outreach DRAFT-ONLY (`OUTREACH.md:8`; `create_draft` appears only in docs,
  never in `src/` — `grep -rl create_draft src/` empty); outreach counters honestly `0/0/0`; the
  only email send path is the waitlist double-opt-in, DRY-RUN by default (`src/email/sender.py`,
  `delivers=False`). Public claims true (`README.md:65` retracts outreach/priority). Commit
  `2099b57` (run 61) added functional ToS/Privacy links to all three mobile-paywall branches
  (Apple 3.1.2) — a real compliance improvement. Cited reviews are competitors' public reviews used
  as market evidence, not authored. Held at A (no current finding; not churned up on reinterpretation
  in a quiet cycle).
- **Artifact Freshness — A** — pricing IDENTICAL across BUSINESS_CASE/README/ASO/Stripe config
  ($12/$96 Pro, $24/$192 Career+; Stripe amounts live only in owner-set `STRIPE_PRICE_*` env).
  **Prior watch-nit CLOSED:** `ASO_COPY.md:76-79` reworded post-#412 to "the native purchase/restore
  client … has landed in code, but stays inert pending owner RevenueCat keys/product mapping and a
  signed store build" (no longer the stale "not yet landed"). **New watch-nit (keeps A, does NOT cap
  to B):** `docs/BUSINESS_CASE.md:56` (and `:126`) lever 2 still says "The mobile half of the surface
  + live per-seat pricing remain", but commit `2099b57` (run 61, PR #429) landed
  `mobile/src/app/team.tsx` (293-line mobile seat-management surface, verified present) — by the
  Factory's own precedent (run 42 credited the web half as BUILT once code landed) the mobile half
  now merits the same "built in code" credit. It STAYS A rather than B because: the lag *understates*
  progress (never inflates), it is ARR-neutral (`floor_met_year1` stays false regardless), and the
  clause cites "ROADMAP Track C" whose box is legitimately still `[ ]` pending device validation
  (mobile can't be runtime-validated on Linux). Next cycle: reword lever 2 to credit the mobile
  surface as landed-in-code + bump the `BUSINESS_CASE_SUMMARY as_of`.

```yaml
GTM_SCORECARD:
  project: jobscraper
  as_of: 2026-07-23
  auditor: independent_gtm_auditor
  overall: A
  ship_gate_met: true          # every ship_critical dim A/A+ AND >= B elsewhere
  ship_gate_note: "GTM work-quality gate only; product launch gate is QUALITY_SCORECARD (last read B, not met)."
  dimensions:
    metric_integrity:
      grade: A+
      ship_critical: true
      evidence: "All metrics 0/null line-by-line (funnel/acquisition/pmf/outreach/email/content), channels_connected:[]; engine_pct:50 is COMPUTED (gtm_engine_pct.py, 8/16 ROADMAP Track G+H boxes); demand_signal digits are external competitor comps in quoted prose, not funnel metrics. PRIOR GAP (#417) CLOSED (A->A+): validate_gtm.py METRIC_SECTIONS (:29) now walks outreach/email/content too, and tests/test_validate_gtm.py:62-67 (parametrized, 9 cases) proves an unsourced non-zero in each FAILs the gate -- injection-verified load-bearing this run (email.list_size:999 -> FAIL exit1; reverting to the pre-fix four lets it escape). No metric-bearing section escapes the walk; zero active findings. NON-capping future-hardening note: source_declared (:87-91) is a coarse 'available' substring match (evaluates False today given 4 unavailable rows + all metrics 0 -> permits no fabrication now; pre-existing, orthogonal) -- watch item, not a cap."
    business_case_honesty:
      grade: A+
      ship_critical: true
      evidence: "BUSINESS_CASE.md:29-35 body == BUSINESS_CASE_SUMMARY YAML :151-163 (16500/57500/132000); validate-computation.mjs PASS (business_case_lib.py 150x110/500x115/1100x120); floor_met_year1:false stated plainly; team/B2B2C+referral+Career+ uncredited (:57,:109-111,:119-121); Stripe pricing reconciles (PENDING_OPS.md:34). No number inflated/deflated/gamed; YAML matches body. as_of:2026-07-13 lag (cosmetic, no ARR figure changed) and lever-2 'mobile half remains' staleness (ARR-neutral, understating) are FRESHNESS matters homed in artifact_freshness -- NOT double-counted here. Honesty/reconciliation core pristine -> A+."
    experiment_validity:
      grade: A+
      ship_critical: false
      evidence: "GROWTH_STATUS.md:174 experiments:[] with honest 'insufficient data', 0 users/0 funnel; empty pre-launch list is the rubric-defined CORRECT/exemplary state; no p-hacking possible. demand_signal themes carry falsifiable durability/confidence + counter-signals. Zero findings."
    roadmap_steer_justification:
      grade: A+
      ship_critical: true
      evidence: "VISION not GTM-steered (floor language honest, VISION.md:45,:142-144); no ARR number changed by any GTM edit; git log --since=2026-07-16 -- ROADMAP/VISION/BUSINESS_CASE shows NO new GTM-authored steer (5 commits = billing test-count fixes + ROADMAP icon-note + factory mobile work + my own scorecard doc add0e1c which changed no ARR/steer content). #296/#327 B2B2C 'Recommended structure' note (:85-92) still carries its inline 'Demand caveat' (:93-100) labeling it a competitor-pricing-comp RECOMMEND-tier input (s3), NOT demand-validated -- real-comp-backed, ARR-neutral, s3-permitted. Zero speculative steers reached the roadmap."
    self_validation_honesty:
      grade: A
      ship_critical: true
      evidence: "GROWTH_STATUS.md:187-211 sources block accurate + fail-closed: analytics/billing/ESP/vercel unavailable (env confirmed: GEMINI+BOTH BROWSERBASE_* only, no PROD_URL/ANALYTICS/STRIPE/SMTP; Vercel connected:true but enabledInChat:false, zero tools loaded). available rows (gtm/quality scorecard) are real on-disk docs. No claimed-but-unconnected channel; no false available. Prior BROWSERBASE drift FIXED (:221 'BOTH BROWSERBASE_* vars present'). GAP (A-cap, RECURRING): prose note :217-219 asserts Google Drive + Calendar enabledInChat:false, but a fresh ListConnectors this run (2026-07-23) shows BOTH enabledInChat:true -- committed session-volatile state currently mismatching reality. Immaterial (non-source connectors, understates, never a false available, sources rows correct) but a genuine re-confirmed drift -> A not A+. Robust fix: stop asserting volatile per-session enabledInChat for non-source connectors as committed fact."
    pmf_read_accuracy:
      grade: A
      ship_critical: false
      evidence: "pmf block honest (all null, signal none, GROWTH_STATUS.md:68-74), recommendation PRODUCT/retention/connect-first (never scaling acquisition). s10 demand_signal :80-172 present, cited (URL+quote+date), qualitative (no fabricated count/dollar, :166), blocked sources honestly labeled unverified, counter-signal+disconfirming stated, RECOMMEND-tier only. Held at A (quiet cycle, no new pmf work); trivial residual nit only (owner-action ids not gtm-connect-* named; demand_signal last refresh 2026-07-03, ~quarterly not due until ~Oct)."
    compliance:
      grade: A
      ship_critical: false
      evidence: "OUTREACH.md:8 draft-only (create_draft only in docs, grep -rl create_draft src/ empty); outreach block 0/0/0; only send path = waitlist double-opt-in, DRY-RUN default (src/email/sender.py delivers=False); README.md:65 claims true. Commit 2099b57 (run 61) added functional ToS/Privacy links to all 3 mobile-paywall branches (Apple 3.1.2) -- a real compliance improvement. Cited reviews are competitors' public reviews. Held at A (no current finding; not churned up on reinterpretation in a quiet cycle)."
    artifact_freshness:
      grade: A
      ship_critical: false
      evidence: "Pricing identical across BUSINESS_CASE/README/ASO/Stripe ($12/96, $24/192; Stripe amounts live only in owner-set STRIPE_PRICE_* env). PRIOR WATCH-NIT CLOSED: ASO_COPY.md:76-79 reworded post-#412 to 'landed in code but inert pending owner RevenueCat keys + a signed store build'. NEW WATCH-NIT (keeps A, not B): BUSINESS_CASE.md:56/:126 lever 2 still says 'The mobile half of the surface + live per-seat pricing remain' but commit 2099b57 (run 61, #429) landed mobile/src/app/team.tsx (293-line mobile seat-mgmt surface). Stays A because the lag UNDERSTATES progress (never inflates), is ARR-neutral (floor_met_year1 stays false), and cites ROADMAP Track C whose box is legitimately [ ] pending device validation (no Linux runtime-validation). Next cycle: reword lever 2 + bump BUSINESS_CASE_SUMMARY as_of."
  top_gaps:
    - dimension: self_validation_honesty
      severity: 1
      grade: A
      gap: "The GROWTH_STATUS validation prose note (:217-219) asserts Google Drive + Google Calendar enabledInChat:false, but a fresh ListConnectors call on 2026-07-23 shows BOTH enabledInChat:true. This is a RECURRING drift (the 2026-07-16 scorecard flagged the same direction; the Factory disputed it on 2026-07-17 based on its own session, but enabledInChat is session-volatile, so pinning it as committed fact keeps mismatching). Immaterial (non-source connectors, understates connectivity, never a false 'available' claim, the sources rows themselves are correct) -- this is the sole ship_critical dim not at A+, ship gate NOT blocked. To reach A+: stop asserting per-session enabledInChat values for non-source connectors (Drive/Calendar) as committed narrative fact; keep only the source rows (which are accurate), or reconcile the prose against the actual per-run ListConnectors each write."
      issue: "gtm-quality: self-validation-honesty A -> raise to A+"
    - dimension: artifact_freshness
      severity: 2
      grade: A
      gap: "Watch-nit (does not currently cap the grade): BUSINESS_CASE.md:56 (and :126) lever 2 still frames 'The mobile half of the surface + live per-seat pricing remain' as unbuilt, but commit 2099b57 (run 61, PR #429) landed mobile/src/app/team.tsx (the mobile seat-management surface). By the Factory's own run-42 precedent (crediting the web half as BUILT once code landed), the mobile half now merits the same 'built in code' credit. Keeps A -- the lag understates progress, is ARR-neutral (floor_met_year1 stays false), and cites ROADMAP Track C whose box is legitimately [ ] pending device validation. Next GTM cycle: reword lever 2 to credit the mobile surface as landed-in-code (live per-seat pricing is the genuine remaining gap), and bump the stale BUSINESS_CASE_SUMMARY as_of (2026-07-13)."
    - dimension: metric_integrity
      severity: 3
      grade: A+
      gap: "NON-capping future-hardening note (dimension is A+, this does NOT lower it): scripts/validate_gtm.py's source_declared check (:87-91) is a coarse substring match -- it would accept ANY sources/validation entry containing 'available'/'connected' (including the documentary gtm_scorecard/quality_scorecard rows) as a metric source, gated only by 'unavailable' not appearing anywhere. Today it evaluates False (the validation block carries 4 unavailable rows and all metrics are 0), so it permits no fabrication in the current doc; pre-existing and orthogonal to the #417 fix. Optional hardening: require an analytics/billing/ESP-class connected source (not any 'available' substring) before a non-zero metric passes, with a regression test."
  notes:
    - "All four ship_critical dimensions A/A+ (metric_integrity A+, business_case_honesty A+, roadmap_steer_justification A+, self_validation_honesty A) -> ship_gate_met true; GTM integrity core clean. No fabricated metric (injection-test-verified), no gamed/deflated business case, no speculative/low-confidence steer that reached the roadmap."
    - "Movement vs 2026-07-16: metric_integrity A->A+ -- the sole prior top_gap (#417, validate_gtm.py METRIC_SECTIONS omitting outreach/email/content) is CLOSED (commit 6f277d5, 2026-07-17: METRIC_SECTIONS extended + tests/test_validate_gtm.py real parametrized regression test; injection-verified load-bearing this run). Overall holds A because self_validation_honesty stays A on the recurring Drive/Calendar enabledInChat prose drift. self_validation, pmf, compliance, artifact_freshness, business_case, experiment, roadmap all unchanged in grade (artifact_freshness's watch-nit rotated: ASO restore-line CLOSED, BUSINESS_CASE lever-2 mobile-half staleness OPENED)."
    - "Graded by 3 fresh adversarial Opus subagents (none did GTM work), each told to REFUTE, + direct auditor checks (injection test, validate-computation PASS, engine_pct recompute, fresh ListConnectors + env). Two grader downgrades were RE-HOMED rather than accepted at face value: grader-2's business_case A (mobile-half staleness) and grader-3's freshness watch-nit are the SAME finding -- counted ONCE, in artifact_freshness (its rubric home), leaving business_case_honesty at A+ where its own rubric (reconciliation/gaming/YAML/floor) is pristine. grader-3's pmf A+ and compliance A+ were held at A (anti-inflation: no dimension-specific new work in a quiet cycle; declined to churn non-ship-critical grades up on reinterpretation). Every grade cites file/line/commit."
    - "Watch next run: whether the Drive/Calendar enabledInChat prose drift is made robust (gap 1); whether BUSINESS_CASE lever-2 mobile-half + as_of are refreshed (gap 2); whether validate_gtm.py source_declared is hardened (gap 3, optional); whether a connected analytics/billing/ESP source appears (esp. if the owner enables the org-connected Vercel connector in-chat -- would move the engine off 0% and force re-grading metric integrity against REAL numbers); demand_signal recency (~quarterly, last 2026-07-03); and the next QUALITY_SCORECARD grade (could flip its ship_gate and open the outreach lane). Issue #417 CLOSED this run (metric_integrity now A+)."
```
