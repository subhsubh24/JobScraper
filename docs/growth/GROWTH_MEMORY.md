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

---

### 2026-07-05 — Daily GTM review (quiet run on funnel/steer front; real packaging research on the team/B2B2C lever)
- **Observed:** Phase still `pre_launch`. `ListConnectors` confirms only Gmail (connected,
  enabled) + Google Drive (connected, not enabled-in-chat) + Google Calendar (unknown/not
  enabled) — no analytics/billing/email-provider MCP available; shell env has no `PROD_URL` or
  `ANALYTICS_READ_TOKEN`, so the `GET /api/analytics/summary` read path (built PR #146, wired for
  the agent PR #245) could not be called either — `engine_built: false` / `channels_connected: []`
  stay honest. **QUALITY_SCORECARD unchanged** since the last GTM read: still the 3rd audit,
  `as_of 2026-07-03`, overall B, ship gate NOT met — the SAME 2 ship-critical dims
  (business-case-strength, store-readiness) are C for a 3rd consecutive GTM read now, despite the
  product factory shipping 29 runs of adjacent work in the interim (rate limiting, coverage-floor
  ratchet, ATS retry/backoff, résumé-view fix, redirect-SSRF fix, etc.) — none of it touches the
  team/B2B2C tier or store assets/mobile IAP specifically. **GTM_SCORECARD unchanged** too: still
  `as_of 2026-07-02`, overall A, `ship_gate_met: true` — no new auditor grade has landed, so no
  fresh top_gap to work this run. Two new ROADMAP build items appeared since the last GTM read —
  `§11 marketing media-gen adapter` (epic #281) and `§34 pre-launch funnel: public demo of the
  core aha + gated beta` (epic #286, replaces the blank waitlist) — both product-factory-authored
  (not a GTM steer); worth watching, especially §34, since it will change the shape of the
  pre-launch funnel once built.
- **Concluded:** No real data justifies a ROADMAP/BUSINESS_CASE/VISION steer this run (same
  reasoning as every prior pre-launch read — 0 users, 0 funnel data). Zero outreach drafts is the
  ONLY compliant outcome this run, and for a sharper reason than "no traction to report": re-read
  of `GTM_STANDARD.md` §6 confirms its readiness gate is a HARD BLOCK on **both** outbound
  lanes — including the bespoke 1:1 Gmail-draft lane — until the independent
  `QUALITY_SCORECARD.ship_gate_met` is true. It is still false, so no outreach draft would be
  compliant this run regardless of how strategic a target might be. (Correcting my own framing
  going forward: prior entries said "no traction to honestly report" as the reason for zero
  drafts — that's true but incomplete; the actual gate is binary and ship-gate-keyed, not a
  traction judgment call.)
- **Did (real, in-repo, no channel/steer needed):** Ran real GTM business-analytics research (the
  applied-business-scientist remit — pricing & packaging, competitive analysis) on the single
  highest-ARPA, lowest-CAC lever the business case names but hasn't built: the team/B2B2C seat
  tier. Found that every consumer job-tool competitor with an org/institutional offering (Huntr,
  Careerflow, Big Interview) publishes **zero public seat pricing** — all sales-gated
  ("Request a Demo"/"Contact Sales"); the one adjacent category that DOES publish real numbers is
  outplacement/career-transition software sold to HR/L&D — Randstad RiseSmart publishes a clean
  per-employee, duration-tiered price list ($899–$6,499) and INTOO tiers by seniority band
  ($600–$3,750); LinkedIn Learning for Business seats reportedly run ~$350–500/seat/yr at
  enterprise volume (hedged as a secondary-sourced anchor, not LinkedIn's own page). Added a
  cited packaging recommendation to `docs/BUSINESS_CASE.md` lever 2: mirror RiseSmart's hybrid —
  publish a self-serve starter/low-seat price so a single bootcamp cohort or small outplacement
  engagement can check out without a sales call, then route anything above a seat threshold to a
  sales-assisted annual contract. Every number is attributed to the third-party competitor it
  belongs to, never claimed as Career Operator's own; no ARR scenario or `floor_met_year1` was
  touched (the tier still doesn't exist, so crediting it would be gaming the business case);
  explicitly labeled RECOMMEND-tier input for the product factory, not a steer. Ran the change
  through an independent reviewer (maker≠checker, fresh subagent) — it caught one real nit (3 of
  6 named competitors lacked an individually-cited URL for the "zero public pricing" claim) —
  fixed by re-scoping the absolute claim to the 3 individually-cited names and hedging the other 2
  as "directional, not independently cited" — then the reviewer APPROVED.
- **Recommended (to factory):** Unchanged priority — business-case-strength (team/B2B2C tier,
  now with a real cited packaging structure to start from; annual-first pricing) and
  store-readiness (rendered assets + mobile IAP) remain the two ship-critical gaps. Watch §34
  (pre-launch demo funnel) landing — once built, re-evaluate whether it changes
  `ANALYSIS_PLAYBOOK.md`'s phase/gate logic (a public demo is a new, measurable pre-launch surface
  distinct from a blank waitlist).
- **Meta / operational note:** Named the circuit-breaker explicitly this run (GTM_STANDARD's
  brakes) — the same 2 ship-critical dims and the same `SITE_GATE_PASSWORD` owner-action have now
  persisted across >=3-4 consecutive GTM reads. Not treating it as a stall (each has a clearly
  named, in-progress buildable lever, and adjacent product work continues), but naming
  `SITE_GATE_PASSWORD` prominently in `GROWTH_STATUS.owner_blockers` as the SINGLE
  highest-leverage next connect (a ~2-minute env-var set, unlike the Stripe/Apple/Google
  account-creation items) rather than re-listing every blocker with equal weight.

---

### 2026-07-03 — Daily GTM review (first §10 demand-validation pass; closes GTM Auditor issues #191/#192)
- **Observed:** Phase still `pre_launch`. `ListConnectors` confirms only Gmail (connected,
  enabled) + Google Drive (connected, not enabled-in-chat) + Google Calendar (unknown/not
  enabled) — no analytics/billing/email-provider MCP tool available this run, same as every
  prior run; `engine_built: false` / `channels_connected: []` stay honest. The independent
  **GTM_SCORECARD** landed its FIRST grade since the last GTM run (as_of 2026-07-02, bootstrap):
  overall **A**, `ship_gate_met: true` (GTM work-quality gate — distinct from product launch
  readiness). All four ship-critical GTM dims A/A+; two non-ship-critical dims sat at **B**:
  `pmf_read_accuracy` (no §10 `demand_signal` block existed) and `artifact_freshness` (same root
  cause + two stale doc lines). Filed as GitHub issues #191/#192. Checked those two stale lines
  directly (`git diff`/`git log`): **both were already fixed by the product factory** before this
  run — `docs/BUSINESS_CASE.md:19`'s Career+ row now matches `README.md:53` (fixed in bookkeeping
  run 21, commit `53a1f24`), and `docs/store/ASO_COPY.md:67`'s restore-purchases line already
  reads as a conditional future promise, not a live claim. Only the `demand_signal` block itself
  remained undone. The independent **QUALITY_SCORECARD** also re-graded (3rd audit, 2026-07-03):
  overall **B** still, ship gate still NOT met, but real progress — 3 dims reached **A+**
  (functional-reality, correctness, artifact-integrity) and performance moved **B→A**. The same 2
  ship-critical C's persist unchanged for a 2nd consecutive read: business-case-strength (team/
  B2B2C tier + annual pricing unbuilt) and store-readiness (rendered assets + mobile IAP unbuilt).
- **Did (the §10 pass):** Ran the first GTM_STANDARD §10 pre-launch demand-validation pass.
  `reddit.com` direct fetch is BLOCKED in this environment (`WebFetch` → "unable to fetch"), so
  Reddit evidence had to come either indirectly (one thread relayed via a secondary source,
  honestly labeled unverified/not-primary) or from adjacent public sources the environment CAN
  reach: Chrome Web Store reviews (Huntr — a direct job-tracker competitor), Product Hunt reviews
  (Final Round AI — an interview-prep competitor), and Fishbowl forum posts (career-coaching
  demand). All citations are real URL + verbatim quote; dates are included where the source page
  showed one (mostly Jun 2026 / Jan 2026 / May 2026 for the Chrome Web Store reviews) and honestly
  marked "unverified"/"not shown on page" where it wasn't (Fishbowl posts, Product Hunt reviews,
  the one relayed Reddit citation) — no invented date, no invented count (GTM_STANDARD §4/§10 hard
  bounds). Clustered into **4 durable JTBD themes**: (1) application-tracking chaos — SOLVED by
  the built job pipeline/CRM; (2) ATS-driven resume-tailoring pain — SOLVED by built fit-scoring +
  prep packs (plus a genuine counter-signal: a Huntr reviewer caught the AI addressing a cover
  letter to "random people" — real users penalize bad AI output, reinforcing why the tests-evals
  top_gap on real prep-pack content quality matters); (3) interview-PRACTICE anxiety (distinct
  from content prep — Final Round AI/Yoodli/Big Interview reviewers specifically credit
  practice/delivery-feedback with reducing anxiety) — only PARTIALLY solved, since Career
  Operator's prep is text/content only, no live voice mock-interview; (4) salary-negotiation
  anxiety (two real Fishbowl posts asking for a negotiation coach) — SOLVED by the already-built
  Career+ tier. Explicitly recorded a **disconfirming** note: zero consumer-pain evidence exists
  either way for the team/B2B2C tier (out of scope for job-seeker pain mining, not evidence
  against it). Wrote the full cited block to `GROWTH_STATUS.demand_signal`.
- **Concluded:** This is a **RECOMMEND-tier** signal only (GTM_STANDARD §3) — real, cited, mostly
  recent, but qualitative and not statistically significant/causal by construction (competitor
  reviews + forum posts, not our own funnel). It raises qualitative CONFIDENCE in two levers
  **already named** in `docs/BUSINESS_CASE.md` before this run (lever 3's mock-interview voice
  sessions, lever 6's Career+ salary-negotiation coaching, already built) — it does NOT justify a
  ROADMAP/BUSINESS_CASE/VISION steer (no new lever invented, no number attached, no reprioritization
  above the 2 ship-critical C's). No PMF signal exists (0 users; expected pre-launch).
- **Recommended (to factory):** Unchanged priority — business-case-strength (team/B2B2C tier,
  annual-first pricing) and store-readiness (rendered assets + mobile IAP) remain the two
  ship-critical gaps, both product-factory work. When the factory next revisits
  `docs/BUSINESS_CASE.md` lever 3 (mock-interview voice sessions), the `demand_signal` block above
  is real supporting evidence for why that lever is worth building, not just a nice-to-have. Zero
  outreach drafts this run: no new genuinely strategic target surfaced, site gate still down — a
  quiet run with zero outreach remains correct (per OUTREACH.md).
- **Meta / operational note:** `reddit.com` is unreachable via `WebFetch` in this environment
  (403/blocked) even though `WebSearch` can return Reddit-adjacent results indirectly. Future §10
  runs should expect the same and lean on competitor-review platforms (Chrome Web Store, Product
  Hunt, Trustpilot — largely fetchable) + forum sites that allow fetch, rather than retrying direct
  Reddit fetches every run.
