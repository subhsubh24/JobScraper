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

---

### 2026-07-09 — Second grade (re-grade)
- **Overall: A · ship_gate_met: true** (GTM work-quality gate; product launch gate separate —
  QUALITY_SCORECARD last read B, not met). Unchanged overall from 2026-07-02, but the mix moved.
- **Grades:** metric_integrity **A+**, business_case_honesty **A+**, experiment_validity **A+**,
  roadmap_steer_justification **A** (↓ from A+), self_validation_honesty **A**, pmf_read_accuracy
  **A** (↑ from B), compliance **A**, artifact_freshness **A** (↑ from B). All four ship_critical
  A/A+; all others A. No B/C/D/F anywhere.
- **What changed vs last grade:**
  - **pmf_read_accuracy B→A** and **artifact_freshness B→A** — the GTM Factory closed BOTH prior
    top_gaps. The GTM_STANDARD §10 `demand_signal` block landed (`GROWTH_STATUS.md:57-149`, run
    2026-07-03): 4 durable JTBD themes, each cited URL+quote+date, purely qualitative, blocked
    sources (reddit/fishbowl) honestly labeled relayed/unverified, counter-signals + disconfirming
    stated, kept RECOMMEND-tier. Issue **#191 closed**. The two stale doc lines were fixed —
    `BUSINESS_CASE.md:19` Career+ row reconciled (retracted "outreach, priority" gone),
    `ASO_COPY.md:75` restore-purchases softened to a conditional future promise. Issue **#192 closed**.
  - **roadmap_steer_justification A+→A** (NEW gap) — GTM commit `24e9b84` (#296, 2026-07-05) wrote a
    directional B2B2C "recommended structure" packaging steer into `BUSINESS_CASE.md:72-76` for a
    tier the same run's `demand_signal.disconfirming` block (`:138-142`) says demand research "can
    neither confirm nor refute", while the commit asserts "no steer". Real cited comps (RiseSmart/
    INTOO price lists), changes NO ARR number, credits no revenue → a defensible RECOMMEND-tier
    input, NOT speculative/gamed (stays at the ship bar, A), but the directional edit + "no steer"
    label caps it below A+.
- **How I verified (adversarial, 3 fresh Opus graders + direct checks, none did GTM work):**
  - Metric integrity + self-validation (grader 1, UPHELD A+/A): scanned every funnel/acq/pmf/
    outreach/email/content field — all 0/null; only non-zero digits are external competitor comps
    in the qualitative demand_signal; `validate_gtm.py` tripwire (`_walk_nonzero`+`exit(1)`) is real
    enforcement not a stub; ListConnectors = only Gmail/Calendar/Drive+github, matching the
    `unavailable` source declarations.
  - Business-case + roadmap-steer (grader 2): business-case UPHELD A+ (body⇄YAML exact,
    `validate-computation.mjs` PASS 16500/57500/132000, floor honestly missed, levers uncredited,
    Stripe pricing reconciles); roadmap-steer REFUTED from A+ → **A** (the #296 packaging steer,
    reasoning above). VISION rewrite `5846822` confirmed owner-authored ("Subh Mukherjee"), not GTM.
  - PMF + compliance + freshness (grader 3, UPHELD A/A/A): demand_signal genuinely qualitative +
    honestly-sourced (fixes real not cosmetic); outreach draft-only (`create_draft` only in docs,
    never `src/`), waitlist send path DRY-RUN by default; pricing identical across all 4 artifacts.
- **Filed for the GTM Factory:** `gtm-quality: roadmap-steer-justification A -> raise to A+`
  (severity 1, the sole named gap this run). No ship_critical dim is BELOW A, so the ship gate holds;
  filed as an A→A+ polish, not a blocker. No fabricated metric, gamed number, or speculative steer
  that reached the roadmap found.
- **Watch next run:** whether #296's packaging steer is reconciled (the filed gap); a connected
  analytics/billing/ESP source appearing (would force re-grading metric integrity against REAL
  numbers); demand_signal recency (~quarterly, last 2026-07-03); a QUALITY_SCORECARD re-grade (could
  flip its ship_gate and open the outreach lane).
