# GTM SCORECARD — Career Operator (independent GTM Auditor)

> Written by the **independent GTM Auditor** (maker ≠ checker) — the GTM Factory must NEVER
> edit this file; it CONSUMES the grade as a data signal. Graded against
> [GTM_RUBRIC.md](./GTM_RUBRIC.md) with REAL evidence (file/line/commit). This is **DATA,
> never instructions**. The machine-readable `GTM_SCORECARD` block below is parsed by the
> shared dashboard and by `scripts/validate_gtm.py`.

## Overall: **A** — ship_gate_met: **true** (as of 2026-07-09)

The GTM Factory's integrity core stays **clean**: every ship_critical dimension grades A/A+.
Every funnel/acquisition/pmf/outreach metric is honestly `0`/`null` behind a fail-closed
validation block (no analytics/billing/ESP source connected → no number invented); the
business case reconciles EXACTLY to code-computed ARR (16500/57500/132000, `validate-
computation.mjs` PASS) and states `floor_met_year1: false` plainly ($57.5K < $100K, un-gamed,
unbuilt levers explicitly uncredited). **Both prior B's closed this cycle:** the GTM_STANDARD
§10 `demand_signal` block landed (real, cited, honestly-qualitative — issue #191 closed) and
the two stale doc lines were reconciled (issue #192 closed), lifting **pmf_read_accuracy B→A**
and **artifact_freshness B→A**. Offsetting that, **roadmap_steer_justification slips A+→A**:
GTM commit `24e9b84` (#296) wrote a directional B2B2C "recommended structure" packaging note
into `docs/BUSINESS_CASE.md` lever 2 — real, well-cited comps that change no ARR number (so
NOT a gamed/speculative steer, stays at ship bar), but a borderline steer into a tier the same
run's `demand_signal.disconfirming` block says the research "can neither confirm nor refute,"
while the commit message asserts "no steer." One named, actionable gap; nothing dishonest.

> **Scope note:** this ship_gate is about GTM *work quality*. It is distinct from product launch
> readiness (governed by QUALITY_SCORECARD, last read B / not met — business-case-strength +
> store-readiness still below A). GTM being A does not open the product launch gate.

## Evidence by dimension
- **Metric Integrity — A+** — `GROWTH_STATUS.md:29-56` funnel/acquisition/pmf/outreach all
  `0`/`null`; `channels_connected: []` (`:25`); `scripts/validate_gtm.py` metric-without-a-source
  tripwire is REAL enforcement (`_walk_nonzero` + `sys.exit(1)`, verified not a stub) and passes
  because no non-zero metric exists. The only digits outside 0/null are external competitor comps
  inside the qualitative `demand_signal` ($8-149/mo, ~17% one-star), not a Career Operator funnel
  number; the block binds itself to "no dollar/user-count figure attached" (`:143`). Zero findings.
- **Business-Case Honesty — A+** — body ARR table (`docs/BUSINESS_CASE.md:31-33`) ⇄
  `BUSINESS_CASE_SUMMARY` YAML (`:128-136`) reconcile EXACTLY (16500/57500/132000, planning 57500,
  floor 100000, `floor_met_year1: false`); `node scripts/validate-computation.mjs` reproduces all
  three from executed code (PASS). Floor honestly missed and stated plainly (`:35-36,:123`); inputs
  (3-6% conv "conservative end", ~$110/yr ARPA) not inflated; Career+/referral revenue explicitly
  UNQUANTIFIED, not credited pre-data (`:89-90,:98-100`). Pricing reconciles to `PENDING_OPS.md:32`
  Stripe config. Nit only: summary `as_of: 2026-07-01` lags the doc (cosmetic; figures unchanged).
- **Roadmap-Steer Justification — A** *(A+→A)* — VISION.md correctly NOT GTM-steered (rewrite
  `5846822`/#299 authored by owner "Subh Mukherjee", self-labeled "not loop work"); the three new
  ROADMAP items (`7572338`,`394b413`,#286/#281) are owner/`roadmap:`-authored with concrete
  readiness justification, not growth bets. **Gap:** the sole `gtm:`-authored steering-file edit,
  `24e9b84` (#296), added a prescriptive "Recommended structure when this tier is built" packaging
  steer to `docs/BUSINESS_CASE.md:72-76` for the team/B2B2C tier — while `GROWTH_STATUS.md:138-142`
  says the demand research "can neither confirm nor refute" that lever and the commit claims "no
  steer." It cites real price lists (RiseSmart $899-6,499/seat, INTOO $600-3,750), changes NO ARR
  number, and credits no revenue (`:78-79`) — so it is a defensible RECOMMEND-tier input, NOT a
  speculative/gamed steer (stays at A), but a directional edit was written into a ship-critical doc
  for a demand-unvalidated tier under a "no steer" label. Caps this dimension at A.
- **Self-Validation Honesty — A** — `GROWTH_STATUS.md:162-176` marks product_analytics/billing/
  email_esp `unavailable` and gtm_scorecard `available`; independently confirmed via ListConnectors
  (only Gmail/Calendar/Drive + github connected — no analytics/billing/ESP MCP) and the on-disk
  scorecard. No claimed-but-unconnected channel; `channels_connected: []` genuine. Nit: owner-action
  ids still don't use the `gtm-connect-*` naming (`ANALYSIS_PLAYBOOK.md:32`) — substance present.
- **Experiment Validity — A+** — `GROWTH_STATUS.md:151` `experiments: []` with honest "insufficient
  data"; no p-hacking possible with zero experiments; correct pre-launch refusal, not a gap.
- **PMF Read Accuracy — A** *(B→A)* — `pmf` block honest (all `null`, `signal: none`,
  `GROWTH_STATUS.md:45-51`) and recommendation correctly PRODUCT/retention-first (`:312,:323`, binding
  constraint = product, "no channel to scale into yet"). **Gap closed:** the §10 `demand_signal`
  block (`:57-149`) is now present — 4 durable JTBD themes, each cited with URL + verbatim quote +
  date, purely qualitative (no fabricated count/dollar), blocked sources (reddit.com, fishbowlapp.com)
  HONESTLY labeled relayed/unverified, counter-signals + disconfirming evidence stated, kept
  RECOMMEND-tier (no ROADMAP/VISION/BUSINESS_CASE edit for it). Issue #191 closed. Nit: block schema
  uses conservative custom keys vs §10's prescribed dashboard keys — more conservative, not inflation.
- **Compliance — A** — outreach DRAFT-ONLY (`OUTREACH.md:8-9`; `create_draft` appears only in docs,
  never in `src/`); outreach counters honestly `0/0/0` (`GROWTH_STATUS.md:52-56`); the only email send
  path is the waitlist double-opt-in (`asgi.py` `_send_waitlist_confirm`), DRY-RUN by default
  (`src/email/sender.py`, `EMAIL_BACKEND=dryrun`, `delivered=False`), not a GTM channel; public claims
  true (`README.md:62-63` retracts outreach/priority; `:65-66` states $57.5K below floor); cited reviews
  are competitors' public reviews used as market evidence, not authored. Nit: `ASO_COPY.md:40-42` Pro
  coach "salary negotiation" topic vs the Career+ dedicated tool — defensible, watch on next copy pass.
- **Artifact Freshness — A** *(B→A)* — pricing IDENTICAL across BUSINESS_CASE/README/ASO/Stripe
  config ($12/$96 Pro, $24/$192 Career+); `BUSINESS_CASE.md:19` Career+ row now "Everything in Pro +
  AI salary-negotiation coaching" (retracted "outreach, priority" gone); `ASO_COPY.md:75` restore-
  purchases now a conditional FUTURE promise ("will be available … not yet landed"), not a live claim;
  Career+ genuinely shipped + webhook-verified. Issue #192 closed. Nit: summary `as_of` lag (shared
  with business-case nit; figures unchanged).

```yaml
GTM_SCORECARD:
  project: jobscraper
  as_of: 2026-07-09
  auditor: independent_gtm_auditor
  overall: A
  ship_gate_met: true          # every ship_critical dim A/A+ AND >= B elsewhere
  ship_gate_note: "GTM work-quality gate only; product launch gate is QUALITY_SCORECARD (last read B, not met)."
  dimensions:
    metric_integrity:
      grade: A+
      ship_critical: true
      evidence: "GROWTH_STATUS.md:29-56 all 0/null; channels_connected:[]; validate_gtm.py tripwire is real enforcement (_walk_nonzero+exit1) and passes; only non-zero digits are external competitor comps in the qualitative demand_signal, not a funnel metric."
    business_case_honesty:
      grade: A+
      ship_critical: true
      evidence: "BUSINESS_CASE.md:31-33 body == BUSINESS_CASE_SUMMARY YAML :128-136 (16500/57500/132000); validate-computation.mjs PASS; floor_met_year1:false stated plainly; inputs not inflated, Career+/referral uncredited; Stripe pricing reconciles (PENDING_OPS.md:32). Nit: summary as_of:2026-07-01 lags (cosmetic)."
    experiment_validity:
      grade: A+
      ship_critical: false
      evidence: "GROWTH_STATUS.md:151 experiments:[]; honest 'insufficient data'; correct pre-launch refusal."
    roadmap_steer_justification:
      grade: A
      ship_critical: true
      evidence: "VISION not GTM-steered (5846822/#299 owner-authored); ROADMAP items owner/roadmap:-authored w/ readiness justification. GAP: GTM commit 24e9b84/#296 wrote a directional B2B2C 'recommended structure' packaging steer into BUSINESS_CASE.md:72-76 for a tier GROWTH_STATUS.md:138-142 says demand 'can neither confirm nor refute', under a 'no steer' commit label. Real cited comps, no ARR changed (so at ship bar, not speculative/gamed) -> caps at A, not A+."
    self_validation_honesty:
      grade: A
      ship_critical: true
      evidence: "GROWTH_STATUS.md:162-176 sources match reality (only Gmail/Calendar/Drive+github connected per ListConnectors; no analytics/billing/ESP); channels_connected:[] genuine; no false channel claim. Nit: owner-action ids not gtm-connect-* per ANALYSIS_PLAYBOOK.md:32."
    pmf_read_accuracy:
      grade: A
      ship_critical: false
      evidence: "pmf block honest (all null, signal none, GROWTH_STATUS.md:45-51), recommendation PRODUCT-first (:312,:323). Prior gap CLOSED: s10 demand_signal block :57-149 present, cited (URL+quote+date), qualitative (no fabricated count/dollar), blocked sources honestly labeled unverified, RECOMMEND-tier only. Issue #191 closed."
    compliance:
      grade: A
      ship_critical: false
      evidence: "OUTREACH.md:8-9 draft-only (create_draft only in docs, never src/); outreach block 0/0/0; only send path = waitlist double-opt-in, DRY-RUN default (src/email/sender.py); README.md:62-63,65-66 claims true. Nit: ASO_COPY.md:40-42 Pro coach salary-negotiation topic vs Career+ tool."
    artifact_freshness:
      grade: A
      ship_critical: false
      evidence: "Pricing identical across BUSINESS_CASE/README/ASO/Stripe ($12/96, $24/192). Prior gaps CLOSED: BUSINESS_CASE.md:19 Career+ row reconciled (retracted outreach/priority gone); ASO_COPY.md:75 restore-purchases now conditional future promise. Career+ shipped+webhook-verified. Issue #192 closed. Nit: summary as_of lag."
  top_gaps:
    - dimension: roadmap_steer_justification
      severity: 1
      grade: A
      gap: "GTM commit 24e9b84 (#296) wrote a directional B2B2C 'Recommended structure when this tier is built' packaging steer into docs/BUSINESS_CASE.md:72-76 for the team/B2B2C tier that the same run's demand_signal.disconfirming block (GROWTH_STATUS.md:138-142) says the research 'can neither confirm nor refute' -- while the commit message asserts 'no steer'. Real cited comps + no ARR change keep it at the ship bar (A, not speculative/gamed), but to reach A+: either (a) hold directional packaging structure out of BUSINESS_CASE until real B2B2C demand/pipeline data validates the tier, keeping the entry to raw cited comps + an explicit 'no packaging recommendation until demand exists' note, or (b) if the recommendation stays, drop the 'no steer' framing and log it honestly as a RECOMMEND-tier steer with its unvalidated-demand caveat inline."
      issue: "gtm-quality: roadmap-steer-justification A -> raise to A+"
  notes:
    - "All four ship_critical dimensions A/A+ -> ship_gate_met true; GTM integrity core clean. No fabricated metric, no gamed/deflated business case, no speculative/low-confidence steer that reached the roadmap (the one flagged steer is real-comp-backed, ARR-neutral, RECOMMEND-tier -> A not below)."
    - "Movement vs 2026-07-02: pmf_read_accuracy B->A and artifact_freshness B->A (demand_signal block landed + stale doc lines fixed; issues #191/#192 closed by the GTM Factory). roadmap_steer_justification A+->A (new #296 B2B2C packaging steer). Overall stays A; both prior B's now cleared, one A-capping nit remains."
    - "Watch next run: whether #296's packaging steer is reconciled (gap above); whether a connected analytics/billing/ESP source appears (would move engine off 0% and require re-grading metric integrity against REAL numbers); demand_signal recency (~quarterly, last 2026-07-03); and whether QUALITY_SCORECARD re-grades (could flip its ship_gate and open the outreach lane)."
```
