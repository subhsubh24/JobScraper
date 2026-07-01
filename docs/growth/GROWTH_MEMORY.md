# GROWTH MEMORY — Career Operator (dated cross-run learning log)

Append-only. Each entry: date, what we observed (aggregates), what we concluded, what
we recommended. Real data only; "insufficient data" is a valid, expected entry
pre-launch.

---

### 2026-06-27 — Bootstrap
- **Observed:** No funnel exists. 0 visitors, 0 signups, 0 subscribers. No channels
  connected. (Insufficient data for any inference.)
- **Concluded:** Phase = pre_launch. The binding constraint cannot be measured until a
  waitlist + analytics exist and at least one acquisition channel is connected.
- **Recommended (to factory):** Build the waitlist capture + privacy-safe analytics
  read-API (Tracks G/H) so the funnel becomes observable. Owner action: connect an
  email provider + analytics per CONNECT.md to leave prepare-mode.

---

### 2026-06-29 — Daily growth review (run 6)
- **Observed:** Phase = pre_launch. 0 visitors, 0 signups, 0 subscribers. No channels
  connected. `site_gate_up: false`. QUALITY_SCORECARD (independent audit, 2026-06-29):
  overall C, ship gate NOT met — 4 ship-critical dims below A:
  business-case-strength C ($57.5K < $100K floor; referral loop, Career+ tier, B2B2C
  tier all unbuilt), store-readiness C (no rendered store assets, mobile IAP not
  integrated, 4 open ACCEPTANCE_AUDIT FAILs), security B (no CAPTCHA on public forms,
  per-instance rate limits; CORS fixed in PR #96), design-taste B (no committed visual
  screenshots, template icon, web/mobile accent divergence). Insufficient data for any
  PMF inference (expected pre-launch).
- **Concluded:** Binding constraint = PRODUCT QUALITY. The ship gate cannot open until
  all 4 ship-critical dims reach A. No PMF signal exists (pre-launch, expected).
  Execute-mode outreach is hard-blocked (`site_gate_up: false`; `phase: pre_launch`).
  Pre-PMF recommendation is PRODUCT, not acquisition -- no point building an acquisition
  engine before the product clears the ship bar.
- **Recommended (to factory):** In priority order per QUALITY_SCORECARD top_gaps:
  (1) business-case-strength C->A: build referral/share-a-prep-pack invite loop, Career+
  ($24) tier as a REAL entitlement (not dead config), team/seat B2B2C tier to clear the
  $100K/yr floor honestly; (2) store-readiness C->A: commit rendered store assets (icon,
  feature graphic, screenshots) + integrate mobile IAP (StoreKit/RevenueCat client +
  Play Billing); (3) security B->A: CAPTCHA/bot-protection on public forms, cross-instance
  rate-limit + spend-ceiling via Upstash Redis/Postgres; (4) design-taste B->A: land
  dual-axis visual verification (screenshots + verdict), converge accent, replace template
  icon. Zero outreach drafts this run: no traction to honestly report, site gate down,
  product not ship-ready. A quiet run with zero outreach is correct here.

---

### 2026-07-01 — Daily GTM review (business-case computation integrity; still pre-launch)
- **Observed:** Phase still `pre_launch`. Checked for any connected analytics/billing/
  email-provider MCP tool this run — **none available** (only Gmail, for the outreach
  draft exception, and GitHub). Confirms `engine_built: false`, `channels_connected: []`
  honestly; every funnel/pmf/acquisition metric stays 0/null (no fabrication). The
  independent QUALITY_SCORECARD (2nd audit, dated 2026-07-01) moved **C → B overall**:
  ship-critical dims below A dropped from 4 to **2** — security and design-taste both
  closed to A since the last GTM read (CORS + cross-instance rate/spend limiter; 24
  committed screenshots + bespoke icon). The two still open: **business-case-strength
  (C)** — Career+ ($24) is now a REAL webhook-verified tier (PRs #152/#153/#155,
  correctly left unquantified in the projection until cohort data exists — anti-gaming),
  but the team/B2B2C seat tier and annual-first paywall remain unbuilt, so
  `floor_met_year1` is still `false` ($57.5K < $100K) — and **store-readiness (C)** —
  rendered store assets + mobile IAP integration still absent (4 open ACCEPTANCE_AUDIT
  FAILs). No `docs/growth/GTM_SCORECARD.md` exists yet — a GTM Auditor routine was stood
  up 2026-06-30 (per loop-memory) but hasn't landed its first grade; consumed as absent,
  never fabricated. Zero PMF signal (no users exist to measure).
- **Concluded:** No real data justifies a ROADMAP/BUSINESS_CASE/VISION steer this run —
  0 users, 0 funnel data, nothing statistically significant to act on. Per GTM_STANDARD
  §3 this stays a quiet run on the steering front (correct, not a gap). The named,
  buildable levers to clear the $100K floor are unchanged from the last read (team/
  B2B2C tier, annual-first pricing) — the factory is already tracking them in
  BUSINESS_CASE.md's lever list, so no new RECOMMEND was needed beyond reflecting the
  scorecard's current read into GROWTH_STATUS.
- **Did (real, in-repo, no channel needed):** Closed a genuine FACTORY_STANDARD §22 gap
  — the three BUSINESS_CASE.md ARR scenarios ($16.5K / $57.5K / $132K) were cited in
  prose/table but had **zero executed-code backing** (`analysis/figures.json` was empty
  since the gate landed in PR #156). Added `analysis/business_case_lib.py` (shared
  scenario inputs) + `arr_conservative.py` / `arr_base.py` / `arr_optimistic.py`, and
  registered all three in `figures.json` so `scripts/validate-computation.mjs` re-verifies
  them every gate run going forward. Verified locally (`node scripts/validate-computation.mjs`
  → 3/3 PASS; `flake8 analysis/` clean); no cited number changed. Independent reviewer
  (maker≠checker, fresh Sonnet subagent) re-ran the same checks and APPROVED — see PR
  (business-case computation-integrity branch).
- **Recommended (to factory):** Unchanged priority order — business-case-strength
  (team/B2B2C tier, annual-first pricing) and store-readiness (rendered assets + mobile
  IAP) are the two remaining ship-critical gaps; both are already product-factory work,
  not something the GTM loop can build. Zero outreach drafts this run: no new genuinely
  strategic target surfaced, site gate still down, 2 ship-critical dims still open — a
  quiet run with zero outreach remains correct (per OUTREACH.md). No content
  calendar/email-sequence assets exist yet in the repo; deferred rather than built
  speculatively — there's no connected channel or launch date to schedule them against,
  and drafting one now would be unmoored padding, not a real asset.
