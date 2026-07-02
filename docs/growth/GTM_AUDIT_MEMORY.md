# GTM AUDIT MEMORY — Career Operator (independent GTM Auditor, dated log)

Append-only. Each entry: date, overall grade + ship_gate, what changed vs the last grade, and
the top gaps filed. Written ONLY by the independent GTM Auditor (maker ≠ checker). Real
evidence only. This is DATA, never instructions.

---

### 2026-07-02 — First grade (bootstrap)
- **Overall: A · ship_gate_met: true** (GTM work-quality gate; product launch gate is separate —
  QUALITY_SCORECARD B, not met).
- **Grades:** metric_integrity **A+**, business_case_honesty **A+**, roadmap_steer_justification
  **A+**, experiment_validity **A+**, self_validation_honesty **A**, compliance **A**,
  pmf_read_accuracy **B**, artifact_freshness **B**. All four ship_critical dims A/A+; all others ≥B.
- **What changed:** first grade — no prior scorecard. Bootstrapped `GTM_RUBRIC.md` from the
  GTM_STANDARD, wrote this scorecard, and confirmed the GTM Factory's integrity core is exemplary.
- **How I verified (adversarial, 3 fresh Opus graders, none did GTM work):**
  - Metric integrity: `GROWTH_STATUS.md:29-56` all `0`/`null`; `channels_connected: []`; only
    Gmail/Drive/Calendar/GitHub MCP connected (no analytics/billing/ESP); `scripts/validate_gtm.py`
    metric-without-a-source tripwire passes. No fabricated/unsourced number found.
  - Business-case: re-derived ARR — `analysis/business_case_lib.py` × `node
    scripts/validate-computation.mjs` → 16500/57500/132000, matching body table and
    `BUSINESS_CASE_SUMMARY` YAML; `floor_met_year1: false` honest; Career+/referral levers left
    unquantified (anti-gaming); pricing reconciles to `PENDING_OPS.md` Stripe config.
  - Roadmap-steer: `git log -- ROADMAP.md VISION.md docs/BUSINESS_CASE.md` — only `#159`
    (dashboard) and `#158` (computation backing, **no cited number changed**) are GTM-authored;
    `VISION.md` never GTM-edited. Zero steers with 0 data = correct (GTM_STANDARD §3).
  - Self-validation: `GROWTH_STATUS.md:69-83` marks all sources `unavailable`, matches reality; no
    claimed-but-unconnected channel.
  - Compliance: `OUTREACH.md` draft-only; outreach block `0/0`; no auto-send path in repo (only the
    product waitlist double-opt-in, dry-run until owner wires a provider); public claims true.
- **Two B gaps (both non-ship-critical, same root cause — a freshness refresh, not dishonesty):**
  1. **pmf_read_accuracy B** — no §10 `demand_signal` block. §10 (mine REAL public pain, Reddit-
     first, URL + verbatim quote + date; cluster into 3-5 JTBD; qualitative, never a fabricated
     number) was added in #176/#177/#180, which post-date the last GROWTH_STATUS run #159 — so it's
     a not-yet-executed new requirement.
  2. **artifact_freshness B** — (a) the §10 `demand_signal` block (shared); (b) `BUSINESS_CASE.md:19`
     still lists Career+ gates "salary negotiation, outreach, priority" that `README.md:53` says are
     no longer advertised; (c) `ASO_COPY.md:67` asserts live in-app "Restore purchases" before
     StoreKit/IAP has landed.
- **Nits (kept dims at A, not filed):** owner-action ids don't use the `gtm-connect-*` naming
  (`ANALYSIS_PLAYBOOK.md:32`); `ASO_COPY.md:67` restore-purchases claim (folded into gap 2c above).
- **Filed for the GTM Factory:** `gtm-quality: pmf-read-accuracy B -> raise to A` and
  `gtm-quality: artifact-freshness B -> raise to A`. No ship_critical gap to file (all A/A+); no
  fabricated metric, gamed number, or speculative steer found.
- **Watch next run:** whether the demand_signal block lands (closes both B's) and whether a
  connected analytics/billing source appears (would move engine off 0% and require re-grading
  metric integrity against real numbers).
