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

---

### 2026-07-23 — Fourth grade (re-grade)
- **Overall: A · ship_gate_met: true** (GTM work-quality gate; product launch gate separate —
  QUALITY_SCORECARD last read B/not met). Overall unchanged from 2026-07-16, but the sole prior
  top_gap closed and one ship_critical dimension moved up.
- **Grades:** metric_integrity **A+** (↑ from A), business_case_honesty **A+**, experiment_validity
  **A+**, roadmap_steer_justification **A+**, self_validation_honesty **A**, pmf_read_accuracy **A**,
  compliance **A**, artifact_freshness **A**. All four ship_critical A/A+ (metric A+, business_case
  A+, roadmap A+, self_validation A); all others ≥ A. Ship gate holds.
- **What changed vs last grade:**
  - **metric_integrity A→A+** — the sole prior top_gap (issue **#417** — `scripts/validate_gtm.py`'s
    `METRIC_SECTIONS` walked only funnel/acquisition/pmf/channels, leaving outreach/email/content
    un-guarded) is **CLOSED**. Commit `6f277d5` (run 62/#427, 2026-07-17) extended `METRIC_SECTIONS`
    (`:29`) to all seven sections and added `tests/test_validate_gtm.py` — a REAL parametrized
    regression test (9 cases, `:62-67`) injecting an unsourced non-zero into each newly-covered
    section and asserting exit 1. Injection-verified load-bearing this run (`email.list_size:999` →
    FAIL exit 1; reverting `METRIC_SECTIONS` to the pre-fix four lets it escape). Actual metrics were
    flawless throughout — an enforcement-hardening close, not a metric regression. **Issue #417 CLOSED
    by the auditor this run** (maker≠checker: the Factory correctly left its own auditor's issue open
    for the re-grade to close).
  - Overall stays **A** because **self_validation_honesty remains A** on a RECURRING drift: the
    GROWTH_STATUS validation prose note (`:217-219`) asserts Google Drive + Calendar
    `enabledInChat:false`, but a fresh ListConnectors this run (2026-07-23) shows BOTH `true`. The
    2026-07-16 grade flagged the same direction; the Factory disputed it 07-17 from its own session,
    but `enabledInChat` is session-volatile, so pinning it as committed fact keeps mismatching.
    Immaterial (non-source connectors, understates, never a false `available`, sources rows correct) →
    A, not A+. The prior BROWSERBASE_* half of that gap IS fixed (`:221`).
- **How I verified (adversarial, 3 fresh Opus graders + direct checks, none did GTM work):**
  - Metric integrity (grader 1, UPHELD A+): scanned every metric field (all 0/null), injection-tested
    the newly-covered sections (load-bearing), confirmed `tests/test_validate_gtm.py` is a real
    (not decorative) regression test, recomputed `engine_pct:50`. Named a NON-capping future-hardening
    note (the coarse `source_declared` substring match, evaluates False today).
  - Business-case + roadmap-steer (grader 2): business_case body⇄YAML exact + validate-computation
    PASS + floor honestly missed + levers uncredited + Stripe reconciles. Grader argued business_case
    A on the lever-2 mobile-half staleness — **RE-HOMED, not accepted**: that staleness is a FRESHNESS
    finding (ARR-neutral, understating), so it caps artifact_freshness (its rubric home), NOT the
    honesty dimension whose own rubric is pristine → business_case_honesty held at **A+**, finding
    counted ONCE in freshness. Roadmap-steer UPHELD A+ (no new steer, demand caveat intact).
  - Self-validation + experiment + pmf + compliance + freshness (grader 3): confirmed sources block
    accurate/fail-closed + BROWSERBASE fix; named the Drive/Calendar `enabledInChat` drift (self_val
    A-cap). Grader graded pmf A+ and compliance A+ — **held at A** (anti-inflation: a quiet cycle with
    no dimension-specific new work; declined to churn non-ship-critical grades up on reinterpretation).
    Confirmed the prior ASO restore watch-nit CLOSED and the new BUSINESS_CASE lever-2 mobile-half
    watch-nit (keeps freshness A: understates, ARR-neutral, ROADMAP Track C box legitimately `[ ]`).
- **Grading principle applied:** close a filed gap only when the fix is independently VERIFIED landed
  (injection test + real regression test → #417 closed); count each finding ONCE in its correct
  rubric dimension (mobile-half staleness → freshness, not business_case); do NOT inflate — decline
  grader upgrades on non-ship-critical dims with no new work (pmf/compliance held at A). Consistent,
  evidence-bounded, anti-inflation in both directions.
- **Filed for the GTM Factory:** `gtm-quality: self-validation-honesty A -> raise to A+` (severity 1,
  the recurring Drive/Calendar `enabledInChat` prose drift — sole ship_critical dim not at A+, with a
  robust fix: stop asserting session-volatile values as committed fact). **Closed #417** (metric
  integrity now A+, fix independently verified). Freshness mobile-half watch-nit (sev 2) + metric
  source_declared hardening (sev 3, non-capping) recorded in the scorecard top_gaps, not separately
  filed (immaterial / non-capping, kept lean). No ship_critical dim BELOW A; no fabricated metric /
  gamed number / speculative steer found.
- **Watch next run:** whether the Drive/Calendar `enabledInChat` drift is made robust (gap 1); the
  BUSINESS_CASE lever-2 mobile-half + `as_of` refresh (gap 2); `validate_gtm.py source_declared`
  hardening (gap 3, optional); whether the owner enables the org-connected Vercel connector in-chat or
  a PROD_URL/ANALYTICS token appears (would move the engine off 0% and force re-grading metric
  integrity against REAL numbers); demand_signal recency (~quarterly, last 2026-07-03); the next
  QUALITY_SCORECARD grade.

---

### 2026-07-16 — Third grade (re-grade)
- **Overall: A · ship_gate_met: true** (GTM work-quality gate; product launch gate separate —
  QUALITY_SCORECARD last read B/not met). Overall unchanged from 2026-07-09, but two dimensions
  moved and OFFSET.
- **Grades:** metric_integrity **A** (↓ from A+), business_case_honesty **A+**, experiment_validity
  **A+**, roadmap_steer_justification **A+** (↑ from A), self_validation_honesty **A**,
  pmf_read_accuracy **A**, compliance **A**, artifact_freshness **A**. All four ship_critical A/A+
  (metric A, business_case A+, roadmap A+, self_validation A); all others A. Ship gate holds.
- **What changed vs last grade:**
  - **roadmap_steer_justification A→A+** — the sole prior top_gap (#327 — GTM commit `24e9b84`/#296's
    B2B2C "Recommended structure" packaging note under a "no steer" label) is CLOSED via the exact
    remedy the 2026-07-09 scorecard pre-authorized as an A+ path (fix option **b**): an inline
    "Demand caveat (honesty correction)" now sits at `docs/BUSINESS_CASE.md:93-100` labeling the note
    a competitor-pricing-comp RECOMMEND-tier input (GTM_STANDARD §3), explicitly NOT demand-validated;
    the "no steer" dishonesty is gone. Residual "Recommended structure" text (`:85-89`) is
    real-comp-backed, ARR-neutral, §3-permitted. **Issue #327 closed.**
  - **metric_integrity A+→A** — actual metrics remain FLAWLESS (all `0`/`null`, injection test
    `signups_total:1234`→FAIL exit1 confirms no fabricated number; this is NOT a metric regression),
    but a fresh adversarial grader surfaced a real LATENT coverage gap in the honesty gate:
    `scripts/validate_gtm.py:29` `METRIC_SECTIONS` walks only funnel/acquisition/pmf/channels — NOT
    outreach/email/content — so a future non-zero fabrication there would escape the machine tripwire.
    Latent today (all three 0/null), but a genuine named finding → A, not a zero-findings A+.
- **How I verified (adversarial, 3 fresh Opus graders + direct checks, none did GTM work):**
  - Metric integrity + self-validation (grader 1): injection-tested `validate_gtm.py` (real, exit1),
    scanned every metric field (all 0/null), reproduced `engine_pct:50`, independently pulled
    ListConnectors (Vercel connected but enabledInChat:false → honestly `unavailable`) + env (no
    analytics/billing/ESP). Named the validator-coverage gap (metric_integrity A-cap) and two
    immaterial prose-note drifts (self_validation A-cap: BROWSERBASE_* actually set; Drive/Calendar
    actually enabledInChat:true — both understating, neither a false `available` claim).
  - Business-case + roadmap-steer (grader 2): business_case UPHELD A+ (body⇄YAML exact,
    validate-computation.mjs PASS, floor honestly missed, levers uncredited, Stripe reconciles;
    only nit a non-gaming $110-vs-$115 prose anchor). Roadmap-steer: grader argued HOLD-at-A
    (relocate the residual directional text, fix a) — **OVERRULED to A+**: the 07-09 scorecard
    certified fix (b) as sufficient for A+ and it was faithfully implemented; the residual is
    §3-permitted, so holding at A would move the goalpost off my own documented criterion. Dissent
    recorded in the scorecard.
  - Compliance + pmf + experiment + freshness (grader 3, UPHELD A/A/A+/A): demand_signal genuinely
    qualitative + honestly-sourced; outreach draft-only + waitlist DRY-RUN; ASO salary-negotiation
    copy VERIFIED honest against `career_coach.py:38`/`llm_workflows.py:492`; pricing identical across
    all 4 artifacts. Ruled the PR #412 (2026-07-16 native IAP client code, inert) vs `ASO_COPY.md:76-77`
    "not yet landed" drift a sub-24h WATCH-NIT (keeps A) — substance still true, last GROWTH_STATUS
    run predates #412 by a day. Grader graded experiment_validity A on a "no positive artifact"
    rationale — **OVERRULED to A+**: the rubric says an empty pre-launch list IS the correct
    exemplary state (no finding).
- **Grading principle applied:** accept a grader downgrade only when backed by a GENUINE finding
  (metric_integrity: validator gap → accepted); reject downgrades citing no finding or contradicting
  the rubric/prior criterion (experiment_validity, roadmap_steer → overruled up). Consistent,
  evidence-bounded, anti-inflation.
- **Filed for the GTM Factory:** `gtm-quality: metric-integrity A -> raise to A+` (severity 1, the
  validator METRIC_SECTIONS coverage gap — sole ship_critical dim not at A+, concrete buildable fix).
  Closed #327 (roadmap-steer, resolved). Self_validation prose-drift (sev 2) + ASO freshness (sev 3)
  recorded in the scorecard top_gaps, not separately filed (immaterial / <24h, kept lean). No
  ship_critical dim BELOW A; no fabricated metric / gamed number / speculative steer found.
- **Watch next run:** whether `METRIC_SECTIONS` is extended (gap 1); the two prose-note drifts
  reconciled (gap 2); `ASO_COPY.md:76-77` reworded post-#412 (gap 3); whether the owner enables the
  org-connected Vercel connector in-chat or a PROD_URL/ANALYTICS token appears (would move the engine
  off 0% and force re-grading metric integrity against REAL numbers); demand_signal recency
  (~quarterly, last 2026-07-03); the next QUALITY_SCORECARD grade.
