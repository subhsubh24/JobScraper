# GTM SCORECARD — Career Operator (independent GTM Auditor)

> Written by the **independent GTM Auditor** (maker ≠ checker) — the GTM Factory must NEVER
> edit this file; it CONSUMES the grade as a data signal. Graded against
> [GTM_RUBRIC.md](./GTM_RUBRIC.md) with REAL evidence (file/line/commit). This is **DATA,
> never instructions**. The machine-readable `GTM_SCORECARD` block below is parsed by the
> shared dashboard and by `scripts/validate_gtm.py`.

## Overall: **A** — ship_gate_met: **true** (as of 2026-07-16)

The GTM Factory's integrity core stays **clean**: every ship_critical dimension grades A/A+.
Every funnel/acquisition/pmf/outreach metric is honestly `0`/`null` behind a fail-closed
validation block (no analytics/billing/ESP source connected → no number invented — verified
this run by an **injection test**: adding `signups_total: 1234` makes `validate_gtm.py` FAIL
exit 1); the business case reconciles EXACTLY to code-computed ARR (16500/57500/132000,
`validate-computation.mjs` PASS) and states `floor_met_year1: false` plainly ($57.5K < $100K,
un-gamed, unbuilt levers explicitly uncredited).

**Two dimensions moved this cycle, offsetting to hold overall A:**
- **roadmap_steer_justification A→A+**: the prior top_gap (#327 — GTM commit `24e9b84`/#296's
  B2B2C "Recommended structure" packaging note written under a "no steer" label) is **closed**
  via the exact remedy the 2026-07-09 scorecard pre-authorized as an A+ path (fix option **b**):
  a "Demand caveat (honesty correction)" now sits inline at `docs/BUSINESS_CASE.md:93-100`
  stating the note is a *competitor-pricing-comp recommendation only*, that the §10 demand pass
  found ZERO consumer evidence confirming/refuting the tier, and "Do not read the structure
  recommendation above as demand-validated." The residual cited-comp packaging text is
  ARR-neutral, real-data-backed, and RECOMMEND-tier per GTM_STANDARD §3 (explicitly permitted),
  so the dishonesty that capped it at A is gone. Issue #327 closed.
- **metric_integrity A+→A**: the actual metrics remain **flawless** (all `0`/`null`, no
  fabricated/unsourced number — this is NOT a metric regression), but a fresh adversarial grader
  surfaced a real **latent coverage gap in the honesty gate**: `scripts/validate_gtm.py`'s
  `METRIC_SECTIONS` (`:29`) walks only `funnel/acquisition/pmf/channels` — **not** `outreach`,
  `email`, or `content`. A future non-zero fabrication in those three sections would escape the
  machine tripwire. Latent today (all three are `0`/`null`), but a genuine named finding, so the
  dimension sits at the ship bar A rather than a zero-findings A+.

> **Scope note:** this ship_gate is about GTM *work quality*. It is distinct from product launch
> readiness (governed by QUALITY_SCORECARD, last read B / not met — store-readiness C +
> business-case-strength B still below A). GTM being A does not open the product launch gate.

## Evidence by dimension
- **Metric Integrity — A** *(A+→A)* — Every metric-bearing field is `0`/`null`, scanned
  line-by-line: `funnel` (`GROWTH_STATUS.md:52-62`), `acquisition` (`:63-67`), `pmf` (`:68-74`),
  `outreach` (`:75-79`), `email` (`:175-180`), `content` (`:181-184`); `channels_connected: []`
  (`:37`). The only non-zero number, `engine_pct: 50` (`:25`), is genuinely COMPUTED
  (`python3 analysis/gtm_engine_pct.py` → 50, counts 8/16 `[x]` boxes across ROADMAP Track G+H),
  not hand-asserted. The demand_signal digits ($8-149/mo, ~17% one-star) are EXTERNAL competitor
  comps in prose, not Career Operator funnel metrics, and live outside the walked sections.
  `validate_gtm.py` is REAL enforcement (injection test: `signups_total:1234` → `FAIL … METRIC
  WITHOUT A SOURCE`, exit 1); the `and "unavailable" not in txt` guard (`:91`) makes it
  conservative. **Gap (the A-cap):** `METRIC_SECTIONS` (`scripts/validate_gtm.py:29`) omits
  `outreach`/`email`/`content` — the honesty gate does not machine-guard those three metric
  sections. Latent (all `0`/`null`), no metric currently escapes, but a real coverage hole →
  A, not A+.
- **Business-Case Honesty — A+** — body ARR table (`docs/BUSINESS_CASE.md:29-35`) ⇄
  `BUSINESS_CASE_SUMMARY` YAML (`:151-163`) reconcile EXACTLY (16500/57500/132000, planning 57500,
  floor 100000, `floor_met_year1: false`); `node scripts/validate-computation.mjs` reproduces all
  three from executed code (`analysis/business_case_lib.py` SCENARIOS: 150×110, 500×115, 1100×120
  — PASS). Floor honestly missed and stated plainly (`:35`); team/B2B2C, referral, and Career+
  levers explicitly UNCREDITED to ARR pre-data (`:57,:109-111,:119-121`). Pricing reconciles to
  real Stripe config (`PENDING_OPS.md:34`: Pro $12/$96, Career+ $24/$192). The prior `as_of` lag
  is fixed (now 2026-07-13, commit `94275cd`, as_of-line-only, no figure changed). Nit only: prose
  calls "~$110/yr" the "anchor" while base uses $115 / optimistic $120 (disclosed in the same
  table) — a non-gaming rounding nit ($57.5K is ~42% below floor either way).
- **Experiment Validity — A+** — `GROWTH_STATUS.md:174` `experiments: []` with honest
  "insufficient data" framing and 0 users/0 funnel. Per rubric an empty pre-launch experiments
  list is the CORRECT, exemplary state (not a gap); no p-hacking possible with zero experiments,
  no fabricated N. Zero findings.
- **Roadmap-Steer Justification — A+** *(A→A+)* — VISION.md correctly NOT GTM-steered (only
  commit is owner "Subh Mukherjee" bookkeeping); no ARR number changed by any GTM edit across
  in-tree history; no NEW GTM steer since 2026-07-09 (the sole `gtm:`-authored steering-file
  commit, `94275cd`, is the as_of-only fix). **Prior gap closed:** the #296 B2B2C packaging steer
  is cured via the pre-authorized fix (b) — `docs/BUSINESS_CASE.md:93-100` now carries an inline
  "Demand caveat" labeling it a competitor-pricing-comp RECOMMEND-tier input (§3) that is NOT
  demand-validated; the "no steer" dishonesty is gone. The residual "Recommended structure"
  text (`:85-89`) is real-comp-backed (RiseSmart/INTOO price lists), ARR-neutral, and §3-permitted
  — not a speculative/gamed steer. **Dissent recorded:** a fresh adversarial grader argued to
  hold at A on the grounds that the residual directional text should be relocated out of the
  ship-critical doc (fix option a) for a strict zero-findings A+. Overruled: the 2026-07-09
  scorecard explicitly certified fix (b) — "if the recommendation stays … log it honestly as a
  RECOMMEND-tier steer with its unvalidated-demand caveat inline" — as sufficient for A+, and it
  was faithfully implemented; penalizing a §3-compliant, honestly-caveated input would move the
  goalpost off my own documented criterion.
- **Self-Validation Honesty — A** — `GROWTH_STATUS.md:187-216` sources block accurate and
  fail-closed: product_analytics/billing/email_esp `unavailable` (matches env — independently
  confirmed no PROD_URL/ANALYTICS_READ_TOKEN/Stripe key, only GEMINI/BROWSERBASE/VALIDATOR set),
  and the NEW `vercel` row handled exemplarily — ListConnectors shows Vercel `connected:true`
  but `enabledInChat:false` (ToolSearch returns zero Vercel tools), correctly marked `unavailable`
  (could have inflated by claiming deployment/traffic analytics; did not). The two `available`
  rows (gtm_scorecard, quality_scorecard) are on-disk docs with the exact claimed grades. No
  claimed-but-unconnected channel. **Gap (the A-cap):** two verifiable prose-note drifts, both
  immaterial and in the conservative/understating direction — `:225` says "no BROWSERBASE_* this
  run" but env HAS both BROWSERBASE vars (BROWSERBASE is §29 validator infra, never a GTM source);
  `:221-222` calls Drive "not enabled" / Calendar "not enabled" but ListConnectors shows both
  `enabledInChat:true`. Neither is a false `available` claim; both are per-run env/session
  observation misses. Real factual misses → A, not A+.
- **PMF Read Accuracy — A** — `pmf` block honest (all `null`, `signal: none`,
  `GROWTH_STATUS.md:68-74`), recommendation correctly PRODUCT/retention-first (binding constraint
  = product, "not acquisition", `:513`). The §10 `demand_signal` block (`:80-172`) is present —
  4 durable JTBD themes, each cited URL + verbatim quote + date, purely qualitative ("no
  dollar/user-count figure attached", `:166`), blocked sources (reddit.com, fishbowlapp.com)
  HONESTLY labeled relayed/unverified, counter-signals + disconfirming stated, kept RECOMMEND-tier.
  Nit: owner-action ids still not `gtm-connect-*` named (`ANALYSIS_PLAYBOOK.md`).
- **Compliance — A** — outreach DRAFT-ONLY (`OUTREACH.md:8`; `create_draft` appears only in docs,
  never in `src/`); outreach counters honestly `0/0/0`; the only email send path is the waitlist
  double-opt-in, DRY-RUN by default (`src/email/sender.py`, `delivered=False`). Public claims true
  (`README.md:56-65` retracts outreach/priority, states $57.5K below floor); cited reviews are
  competitors' public reviews used as market evidence, not authored. The one flagged copy nit
  VERIFIED honest against source: `ASO_COPY.md:42`'s Pro-coach "salary negotiation" chat topic
  (`src/ai_coach/career_coach.py:38` SYSTEM_PROMPT lists "Negotiate salaries") vs Career+'s
  dedicated `generate_salary_negotiation` structured artifact (`src/enrichment/llm_workflows.py:492`)
  — two depths of one topic, not a misleading double-sell.
- **Artifact Freshness — A** — pricing IDENTICAL across BUSINESS_CASE/README/ASO/Stripe config
  ($12/$96 Pro, $24/$192 Career+); README claims current; Career+ shipped + webhook-verified.
  **Watch-nit (keeps A, does NOT cap to B):** PR #412 (`70f6ba7`, 2026-07-16) shipped native mobile
  IAP CLIENT code (RevenueCat) with a restore flow wired into `mobile/src/app/paywall.tsx`, but it
  is INERT pending owner RevenueCat keys/products (`ROADMAP.md:259-274`, PENDING_OPS `revenuecat`).
  `ASO_COPY.md:76-77` still says restore is available "once mobile in-app subscriptions are
  integrated (StoreKit/Play Billing — not yet landed)". The user-facing substance is STILL TRUE
  (functional IAP is not usable), and the last GROWTH_STATUS run (2026-07-15) predates #412 by a
  day, so the Factory has had zero cycles to reconcile it — a sub-24h drift, not a stale-and-ignored
  gap. Next cycle: reword `:76-77` to "integration code landed but inert pending store products/keys".

```yaml
GTM_SCORECARD:
  project: jobscraper
  as_of: 2026-07-16
  auditor: independent_gtm_auditor
  overall: A
  ship_gate_met: true          # every ship_critical dim A/A+ AND >= B elsewhere
  ship_gate_note: "GTM work-quality gate only; product launch gate is QUALITY_SCORECARD (last read B, not met)."
  dimensions:
    metric_integrity:
      grade: A
      ship_critical: true
      evidence: "All metrics 0/null line-by-line (funnel/acquisition/pmf/outreach/email/content), channels_connected:[]; engine_pct:50 is COMPUTED (gtm_engine_pct.py, 8/16 ROADMAP Track G+H boxes); demand_signal digits are external competitor comps, not funnel metrics. validate_gtm.py is REAL (injection test signups_total:1234 -> FAIL exit1). GAP (A-cap, A+->A this cycle): validate_gtm.py METRIC_SECTIONS (:29) walks only funnel/acquisition/pmf/channels -- NOT outreach/email/content, so a future non-zero fabrication there escapes the machine gate. Latent (all 0/null now), no metric currently dishonest -> A not A+."
    business_case_honesty:
      grade: A+
      ship_critical: true
      evidence: "BUSINESS_CASE.md:29-35 body == BUSINESS_CASE_SUMMARY YAML :151-163 (16500/57500/132000); validate-computation.mjs PASS (business_case_lib.py 150x110/500x115/1100x120); floor_met_year1:false stated plainly; team/B2B2C+referral+Career+ uncredited (:57,:109-111,:119-121); Stripe pricing reconciles (PENDING_OPS.md:34). as_of lag fixed (2026-07-13, commit 94275cd, no figure changed). Nit: ~$110 prose anchor vs $115/$120 higher scenarios -- non-gaming rounding."
    experiment_validity:
      grade: A+
      ship_critical: false
      evidence: "GROWTH_STATUS.md:174 experiments:[] with honest 'insufficient data', 0 users/0 funnel; empty pre-launch list is the rubric-defined CORRECT/exemplary state; no p-hacking possible. Zero findings."
    roadmap_steer_justification:
      grade: A+
      ship_critical: true
      evidence: "VISION not GTM-steered (owner-authored); no ARR number changed by any GTM edit; no NEW GTM steer since 2026-07-09 (sole gtm: commit 94275cd is as_of-only). PRIOR GAP (#327) CLOSED via pre-authorized fix (b): BUSINESS_CASE.md:93-100 'Demand caveat' now labels the #296 B2B2C packaging note a competitor-pricing-comp RECOMMEND-tier input (GTM_STANDARD s3), NOT demand-validated -- the 'no steer' dishonesty is gone. Residual 'Recommended structure' text (:85-89) is real-comp-backed + ARR-neutral + s3-permitted, not speculative/gamed. Dissent: a grader argued hold-at-A (relocate the directional text, fix a); overruled -- the 07-09 scorecard certified fix (b) as sufficient for A+ and it was faithfully implemented (goalpost-honoring)."
    self_validation_honesty:
      grade: A
      ship_critical: true
      evidence: "GROWTH_STATUS.md:187-216 sources block accurate + fail-closed: analytics/billing/ESP unavailable (env confirmed: no PROD_URL/ANALYTICS_READ_TOKEN/Stripe), NEW vercel row correctly unavailable (connected:true but enabledInChat:false, zero tools loaded -- not inflated). available rows (gtm/quality scorecard) are real on-disk docs. No claimed-but-unconnected channel. GAP (A-cap): two immaterial prose-note drifts, both understating -- :225 'no BROWSERBASE_*' but env HAS them (validator infra, not a GTM source); :221-222 Drive/Calendar 'not enabled' but ListConnectors shows enabledInChat:true. Real factual misses -> A not A+."
    pmf_read_accuracy:
      grade: A
      ship_critical: false
      evidence: "pmf block honest (all null, signal none, GROWTH_STATUS.md:68-74), recommendation PRODUCT-first (:513). s10 demand_signal block :80-172 present, cited (URL+quote+date), qualitative (no fabricated count/dollar, :166), blocked sources honestly labeled unverified, counter-signal+disconfirming stated, RECOMMEND-tier only. Nit: owner-action ids not gtm-connect-* named."
    compliance:
      grade: A
      ship_critical: false
      evidence: "OUTREACH.md:8 draft-only (create_draft only in docs, never src/); outreach block 0/0/0; only send path = waitlist double-opt-in, DRY-RUN default (src/email/sender.py delivered=False); README.md:56-65 claims true. ASO_COPY.md:42 Pro-coach 'salary negotiation' VERIFIED honest vs Career+ tool (career_coach.py:38 SYSTEM_PROMPT + llm_workflows.py:492 -- two depths, not a double-sell)."
    artifact_freshness:
      grade: A
      ship_critical: false
      evidence: "Pricing identical across BUSINESS_CASE/README/ASO/Stripe ($12/96, $24/192); README current; Career+ shipped+webhook-verified. WATCH-NIT (keeps A, not B): PR #412 (70f6ba7, 2026-07-16) shipped native IAP CLIENT code (RevenueCat, restore wired into paywall.tsx) but INERT pending owner keys/products (ROADMAP.md:259-274); ASO_COPY.md:76-77 still says restore 'not yet landed' -- user-facing substance still TRUE (IAP not usable) + last GROWTH_STATUS run (07-15) predates #412 by a day, so sub-24h drift not a stale gap. Next cycle: reword :76-77."
  top_gaps:
    - dimension: metric_integrity
      severity: 1
      grade: A
      gap: "The honesty gate scripts/validate_gtm.py has a latent coverage hole: METRIC_SECTIONS (:29) walks only funnel/acquisition/pmf/channels, so the outreach/email/content metric sections are NOT machine-guarded -- a future non-zero fabrication there would escape the metric-without-a-source tripwire. Latent today (all three are 0/null, nothing currently escapes, no metric is dishonest -- this is an enforcement-hardening gap, not a metric regression). To reach A+: extend METRIC_SECTIONS to include outreach, email, and content (and add a regression test asserting an unsourced non-zero in each of those three sections FAILs the gate, mirroring the existing funnel injection behavior)."
      issue: "gtm-quality: metric-integrity A -> raise to A+"
    - dimension: self_validation_honesty
      severity: 2
      grade: A
      gap: "Two immaterial-but-real factual drifts in the GROWTH_STATUS validation prose note (both understate connectivity, neither a false 'available' claim): :225 asserts 'no BROWSERBASE_* this run' while the env has BROWSERBASE_PROJECT_ID+BROWSERBASE_API_KEY (validator infra, not a GTM source); :221-222 calls Google Drive/Calendar 'not enabled' while ListConnectors shows both enabledInChat:true. To reach A+: reconcile the prose note against the actual per-run env + ListConnectors state (or drop the specific env-var/enabled claims from the narrative, keeping only the source rows which are correct)."
    - dimension: artifact_freshness
      severity: 3
      grade: A
      gap: "Watch-nit (does not currently cap the grade): PR #412 (2026-07-16) landed the RevenueCat mobile IAP CLIENT code (purchase+restore wired into paywall.tsx) but it is inert pending owner keys/products; ASO_COPY.md:76-77 still frames restore-purchases as 'not yet landed'. The user-facing substance is still accurate (functional IAP unusable) and the drift is <24h old, so it keeps A -- but next GTM cycle should reword :76-77 to 'integration code landed but inert pending store products/keys' to stay precise."
  notes:
    - "All four ship_critical dimensions A/A+ (metric_integrity A, business_case_honesty A+, roadmap_steer_justification A+, self_validation_honesty A) -> ship_gate_met true; GTM integrity core clean. No fabricated metric (injection-test-verified), no gamed/deflated business case, no speculative/low-confidence steer that reached the roadmap."
    - "Movement vs 2026-07-09: roadmap_steer_justification A->A+ (prior gap #327 closed via the pre-authorized fix b -- inline demand caveat added, 'no steer' dishonesty removed; issue closed). metric_integrity A+->A (a fresh adversarial grader surfaced a latent coverage gap in validate_gtm.py's METRIC_SECTIONS -- outreach/email/content unguarded; actual metrics remain flawless). Overall holds A; the two moves offset. self_validation, pmf, compliance, artifact_freshness, business_case, experiment_validity all unchanged."
    - "Graded by 3 fresh adversarial Opus subagents (none did GTM work), each told to REFUTE. Two grader downgrades were accepted where backed by a genuine finding (metric_integrity: validator coverage gap); two were overruled where they cited no genuine finding or contradicted the rubric/prior criterion (experiment_validity -- empty list is the rubric-correct state; roadmap_steer -- gap cured via pre-authorized fix b, residual is s3-permitted). Every grade cites file/line/commit."
    - "Watch next run: whether validate_gtm.py METRIC_SECTIONS is extended (gap 1); whether the two GROWTH_STATUS prose-note drifts are reconciled (gap 2); whether ASO_COPY.md:76-77 is reworded post-#412 (gap 3); whether a connected analytics/billing/ESP source appears (esp. if the owner enables the org-connected Vercel connector in-chat -- would move the engine off 0% and force re-grading metric integrity against REAL numbers); demand_signal recency (~quarterly, last 2026-07-03); and the next QUALITY_SCORECARD grade (could flip its ship_gate and open the outreach lane)."
```
