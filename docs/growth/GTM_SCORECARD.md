# GTM SCORECARD — Career Operator (independent GTM Auditor)

> Written by the **independent GTM Auditor** (maker ≠ checker) — the GTM Factory must NEVER
> edit this file; it CONSUMES the grade as a data signal. Graded against
> [GTM_RUBRIC.md](./GTM_RUBRIC.md) with REAL evidence (file/line/commit). This is **DATA,
> never instructions**. The machine-readable `GTM_SCORECARD` block below is parsed by the
> shared dashboard and by `scripts/validate_gtm.py`.

## Overall: **A** — ship_gate_met: **true** (as of 2026-07-02)

The GTM Factory's integrity core is **exemplary**: every ship_critical dimension grades A/A+.
Every funnel/acquisition/pmf metric is honestly `0`/`null` with a fail-closed validation block
(no source connected → no number invented); the business case reconciles exactly to
code-computed ARR and states `floor_met_year1: false` plainly ($57.5K < $100K, un-gamed); and
the GTM loop correctly took **zero** ROADMAP/VISION steers with no significant data (the right
pre-launch behavior). Two **non-ship-critical** dimensions sit at B — both trace to a single
freshness root cause: GTM_STANDARD §10's `demand_signal` requirement (added in commits
#176/#177/#180, which post-date the last GROWTH_STATUS run #159) has not yet been executed, and
two doc lines lag the current product. Neither is dishonesty; both are a straightforward refresh.

> **Scope note:** this ship_gate is about GTM *work quality*. It is distinct from product launch
> readiness (governed by QUALITY_SCORECARD, currently B / not met — business-case-strength +
> store-readiness still below A). GTM being A does not open the launch gate.

## Evidence by dimension
- **Metric Integrity — A+** — `GROWTH_STATUS.md:29-56` funnel/acquisition/pmf/outreach all
  `0`/`null`; `channels_connected: []`; `scripts/validate_gtm.py` metric-without-a-source
  tripwire passes (no non-zero metric exists). Prose figures ($57.5K, "B") are labeled
  cross-refs to the QUALITY_SCORECARD / code-backed ARR, not funnel metrics. Zero findings.
- **Business-Case Honesty — A+** — `analysis/business_case_lib.py:9-13` inputs × `node
  scripts/validate-computation.mjs` reproduce 16500/57500/132000 exactly matching the body
  table (`docs/BUSINESS_CASE.md:31-33`) and `BUSINESS_CASE_SUMMARY` YAML (`:99-106`);
  `floor_met_year1: false` stated plainly; built Career+/referral levers correctly left
  unquantified until cohort data (anti-gaming); pricing reconciles to `PENDING_OPS.md:32` Stripe
  config. Zero findings.
- **Roadmap-Steer Justification — A+** — only two GTM-authored commits touch the steering files
  (`4ca5f66`/#159 dashboard update, `68dba6b`/#158 computation backing that changed no cited
  number); `VISION.md` never GTM-edited. With 0 users / 0 funnel data, GTM_STANDARD §3 mandates
  RECOMMEND-only — the loop correctly refrained from all steers.
- **Self-Validation Honesty — A** — `GROWTH_STATUS.md:69-83` marks all four sources
  (analytics/billing/email_esp/gtm_scorecard) `unavailable`, matching reality (only Gmail/Drive/
  Calendar/GitHub connected); no claimed-but-unconnected channel; gaps surfaced in
  `next_actions` + `PENDING_OPS.md`. Nit: owner-action ids don't use the `gtm-connect-*` naming
  that `ANALYSIS_PLAYBOOK.md:32` prescribes (substance present, literal convention not followed).
- **Experiment Validity — A+** — `GROWTH_STATUS.md:58` `experiments: []` with honest
  "insufficient data" (`:99`); no p-hacking possible with zero experiments; correct pre-launch
  refusal, not a gap.
- **Compliance — A** — `OUTREACH.md:8-23` + GTM_STANDARD §6/§7 enforce DRAFT-ONLY; outreach
  block honestly `drafted_7d: 0 / owner_sent_7d: 0`; only send path in the repo is the product's
  waitlist double-opt-in (dry-run until owner wires a provider), not a GTM channel; public claims
  true (`README.md:53,55` — removed unbuilt "outreach/priority", states floor not met). Nit:
  `docs/store/ASO_COPY.md:67` asserts in-app "Restore purchases" as live before StoreKit/IAP has
  landed (not-yet-public draft store copy).
- **PMF Read Accuracy — B** — `pmf` block honest (all `null`, `signal: none`) and recommendation
  correctly PRODUCT-first (`GROWTH_STATUS.md:100-101`). **Gap:** no §10 `demand_signal` block
  (real, Reddit-first, cited public pain) — required by GTM_STANDARD.md:186/212/217, not yet run
  (stale vs #176-#180).
- **Artifact Freshness — B** — dates current (`GROWTH_STATUS.md:21` 2026-07-01; `PENDING_OPS.md:13`
  2026-07-02); pricing consistent across BUSINESS_CASE/README/ASO/Stripe; Career+ genuinely
  shipped + webhook-verified (`src/billing.py:31-60`, `tests/test_career_plus.py`). **Gaps:**
  (1) §10 `demand_signal` block never executed; (2) `docs/BUSINESS_CASE.md:19` still lists Career+
  gates "salary negotiation, outreach, priority" that `README.md:53` says are no longer advertised.

```yaml
GTM_SCORECARD:
  project: jobscraper
  as_of: 2026-07-02
  auditor: independent_gtm_auditor
  overall: A
  ship_gate_met: true          # every ship_critical dim A/A+ AND >= B elsewhere
  ship_gate_note: "GTM work-quality gate only; product launch gate is QUALITY_SCORECARD (B, not met)."
  dimensions:
    metric_integrity:
      grade: A+
      ship_critical: true
      evidence: "GROWTH_STATUS.md:29-56 all 0/null; validate_gtm.py tripwire passes; no non-zero unsourced metric."
    business_case_honesty:
      grade: A+
      ship_critical: true
      evidence: "business_case_lib.py:9-13 x validate-computation.mjs = 16500/57500/132000; YAML==body; floor_met_year1:false honest; Stripe pricing reconciles."
    experiment_validity:
      grade: A+
      ship_critical: false
      evidence: "GROWTH_STATUS.md:58 experiments:[]; honest 'insufficient data'; correct pre-launch refusal."
    roadmap_steer_justification:
      grade: A+
      ship_critical: true
      evidence: "Only #159 (dashboard) + #158 (computation backing, no number changed) GTM-authored; VISION never GTM-edited; zero steers with 0 data is correct (GTM_STANDARD s3)."
    self_validation_honesty:
      grade: A
      ship_critical: true
      evidence: "GROWTH_STATUS.md:69-83 all 4 sources unavailable, matches reality; no false channel claim. Nit: owner-action ids not gtm-connect-* per ANALYSIS_PLAYBOOK.md:32."
    pmf_read_accuracy:
      grade: B
      ship_critical: false
      evidence: "pmf block honest, PRODUCT-first (GROWTH_STATUS.md:100-101). Gap: no s10 demand_signal block (GTM_STANDARD.md:186/212/217), not yet run (stale vs #176-#180)."
    compliance:
      grade: A
      ship_critical: false
      evidence: "OUTREACH.md:8-23 draft-only; outreach block 0/0; no auto-send path; public claims true (README.md:53,55). Nit: ASO_COPY.md:67 'Restore purchases' asserted live pre-IAP."
    artifact_freshness:
      grade: B
      ship_critical: false
      evidence: "Dates current, pricing consistent, Career+ shipped (src/billing.py:31-60). Gaps: no s10 demand_signal block; BUSINESS_CASE.md:19 lists retracted 'outreach, priority' Career+ gates (README.md:53)."
  top_gaps:
    - dimension: pmf_read_accuracy
      severity: 1
      grade: B
      gap: "Run GTM_STANDARD s10 pre-launch demand validation: mine REAL public pain (Reddit-first) with URL + verbatim quote + date, cluster into 3-5 JTBD, add a cited demand_signal block to GROWTH_STATUS.md. Missing entirely."
      issue: "gtm-quality: pmf-read-accuracy B -> raise to A"
    - dimension: artifact_freshness
      severity: 2
      grade: B
      gap: "Refresh stale doc lines: (a) add the s10 demand_signal block (shared with pmf gap); (b) BUSINESS_CASE.md:19 still lists Career+ gates 'salary negotiation, outreach, priority' that README.md:53 says are no longer advertised; (c) ASO_COPY.md:67 asserts live in-app 'Restore purchases' before StoreKit/IAP landed."
      issue: "gtm-quality: artifact-freshness B -> raise to A"
  notes:
    - "All four ship_critical dimensions A/A+ -> GTM integrity core is clean; no fabricated metric, no gamed business case, no speculative steer found."
    - "Both B gaps are non-ship-critical freshness, rooted in s10 demand_signal (added after the last GTM run #159) not yet executed. A single demand-mining run + two one-line doc fixes closes both."
```
