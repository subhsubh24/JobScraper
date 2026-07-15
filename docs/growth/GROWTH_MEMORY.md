# GROWTH MEMORY — Career Operator (dated cross-run learning log)

Append-only. Each entry: date, what we observed (aggregates), what we concluded, what
we recommended. Real data only; "insufficient data" is a valid, expected entry
pre-launch.

---

### 2026-07-15 — Daily GTM review (both scorecards unchanged; site-gate circuit-breaker now 4 reads; ASO-copy nit verified, not edited; new Vercel connector noted)
- **Observed:** Phase still `pre_launch`. Re-verified `ListConnectors` — Gmail (connected,
  enabled) + Google Drive (connected, not enabled-in-chat) + Google Calendar (unknown, not
  enabled) + Mobbin (connected, enabled) — plus **one new entry: a "Vercel" connector**
  (installState: connected at the org level) that was absent on every prior GTM read. Checked
  whether it changes anything: `enabledInChat: false`, and `ToolSearch` for `mcp__Vercel__*`
  returned **zero matching tools** — nothing is actually callable this session, so it is recorded
  as a new `vercel` row in `GROWTH_STATUS.validation.sources` with `status: unavailable`
  (fail-closed, not claimed) rather than silently ignored. `channels_connected: []` stays honest.
  Shell env: only `GEMINI_API_KEY` present, no `PROD_URL`/`ANALYTICS_READ_TOKEN`. Re-ran
  `analysis/gtm_engine_pct.py` (unchanged, 50) and `node scripts/validate-computation.mjs` (4/4
  figures PASS, none changed). Both independent scorecards read fresh and **UNCHANGED** since the
  last GTM read: **QUALITY_SCORECARD** still the 7th audit (`as_of: 2026-07-13`, overall B,
  `ship_gate_met: false`, same two ship-critical gaps — store-readiness C, business-case-strength
  B). **GTM_SCORECARD** still `as_of: 2026-07-09` (A, `ship_gate_met: true`) — now the **4th
  consecutive GTM read** (07-09, 07-11, 07-13, 07-15) without a fresh grade; noted, not treated as
  a stall since GTM's own ship-gate is unaffected.
- **Concluded:** No real funnel/PMF data justifies a ROADMAP/BUSINESS_CASE ARR/VISION steer this
  run (same reasoning as every prior pre-launch read — 0 users, 0 funnel data). Nothing scorecard-
  or channel-side changed enough to warrant a new asset or steer.
- **Did (real, in-repo, verification not edit):** Spot-checked the one still-open GTM_SCORECARD
  compliance nit — `ASO_COPY.md:42`'s Pro-tier "Ask the AI Career Coach about ... salary
  negotiation" line, flagged as worth watching against Career+'s dedicated "salary-negotiation
  coaching tool" (`:65`) — against the actual source instead of assuming either a fix or a pass:
  `src/ai_coach/career_coach.py:38`'s `SYSTEM_PROMPT` genuinely lists "Negotiate salaries" as an
  in-scope Pro-tier chat topic, while Career+'s `generate_salary_negotiation`
  (`src/enrichment/llm_workflows.py:492`) is a separate structured artifact (a generated
  scripts-and-strategies document), not chat. The copy accurately describes two different depths
  of the same topic, not a double-sell or overlapping claim — verified honest against the live
  code, so **no edit was made**. Refreshed `GROWTH_STATUS.md` (`as_of`, validation block with the
  new `vercel` source row, a new learnings entry, `next_actions`/`owner_blockers` re-worded to
  reflect "unchanged since the last read" rather than stale "this run's read" phrasing carried
  over from 07-13). **Circuit-breaker escalation:** the site-gate owner DECISION (`PENDING_OPS.md`
  `site-gate`, `ROADMAP.md:421-435`) has now gone **4 consecutive GTM reads** (2026-07-09 reframe,
  07-11, 07-13, 07-15) with zero owner movement — re-verified `PENDING_OPS.md` still shows
  `as_of: 2026-07-04`, `status: open`, unchanged. This is now the longest-running circuit-breaker
  instance in this loop's history (longer than the 5-read `SITE_GATE_PASSWORD` episode that
  preceded the 07-09 reframe), named explicitly as the single highest-leverage next owner action
  in `owner_blockers`.
- **Recommended (to factory):** Unchanged priority — store-readiness (store screenshots + bespoke
  icon + mobile IAP client) and business-case-strength (a live per-seat price + real B2B adoption
  data) are the two remaining ship-critical gaps, both product-factory/owner work. Zero outreach
  drafts this run (correct): `QUALITY_SCORECARD.ship_gate_met` is still false. Demand_signal
  cadence checked: last run 2026-07-03 (12 days), ~quarterly refresh not due until ~October.
- **Meta / operational note:** This was a routine dashboard-bookkeeping refresh (dates +
  validation reconciliation + one verification check that made no copy edit, consistent with the
  2026-07-07 precedent) — no maker≠checker review was run since no ROADMAP/BUSINESS_CASE/VISION/
  asset/copy change was made this run. Worth watching whether the owner enables the new Vercel
  connector in-chat next run — if so, it may expose real deployment/traffic data that could
  legitimately upgrade `product_analytics` from `unavailable`, the first potential channel-side
  movement in this loop's history.

---

### 2026-07-13 — Daily GTM review (QUALITY_SCORECARD 7th-audit reconcile; site-gate circuit-breaker escalation; business-case as_of freshness fix)
- **Observed:** Phase still `pre_launch`. Re-verified `ListConnectors` (only Gmail/Drive/
  Calendar, no analytics/billing/ESP MCP) and shell env (no `PROD_URL`/`ANALYTICS_READ_TOKEN`)
  — `channels_connected: []` stays honest. Re-ran `analysis/gtm_engine_pct.py` (unchanged, 50)
  and `node scripts/validate-computation.mjs` (4/4 figures PASS, none changed). The independent
  **QUALITY_SCORECARD re-graded the SAME DAY** (7th audit, commit `6d3b905`/#387): overall stays
  **B**, `ship_gate_met` stays **false**, but real dimensional movement — **functional-reality
  recovered A→A+** (the pinned `gemini-2.5-flash` default flagged at the 2026-07-11 GTM read is
  confirmed resolved: #379 moved it to the floating alias `gemini-flash-latest`, and the auditor
  independently re-probed the live Gemini endpoint), while **performance moved A+→A** on a
  genuine NEW finding (the Margin cost-telemetry shipped this window, #368/#369/#382, emits
  synchronously/blocking on the LLM hot path — bounded, fail-safe, non-ship-critical). Exactly
  two ship-critical dims remain open: **store-readiness (C, unchanged** — store screenshots +
  bespoke icon + mobile IAP client all still absent) and **business-case-strength (B, up from
  C** — the team/B2B2C seat tier is now genuinely user-reachable end-to-end via #356 (web admin
  surface) + #363 (`/pricing` Team band) + #383 (live Stripe-test seat coverage), but still no
  live per-seat price (`STRIPE_PRICE_TEAM_ANNUAL` owner-unset) and no validated B2B adoption, so
  `floor_met_year1` stays honestly false). None of this is self-certifiable by this loop — read
  fresh, consumed as-is. **GTM_SCORECARD unchanged**, still `as_of: 2026-07-09`, A,
  `ship_gate_met: true` — this is now the **3rd consecutive GTM read** (2026-07-09, 07-11, 07-13)
  without a fresh grade; noted, not treated as a stall since GTM's own ship-gate is unaffected.
- **Concluded:** No real funnel/PMF data justifies a ROADMAP/BUSINESS_CASE ARR/VISION steer this
  run (same reasoning as every prior pre-launch read — 0 users, 0 funnel data). The
  `BUSINESS_CASE.md` `as_of` fix is a reconciliation of this loop's own stale metadata, not a
  new steer or number change.
- **Did (real, in-repo, no channel/steer needed):** Fixed the `docs/BUSINESS_CASE.md` `as_of`
  staleness the independent GTM Auditor has flagged as a cosmetic nit across at least two prior
  audits (2026-07-09's `business_case_honesty` A+ note and `artifact_freshness` A note both cite
  "summary `as_of:2026-07-01` lags the doc"). Re-verified all 3 ARR figures are still
  code-computed and unchanged (`validate-computation.mjs` PASS) before bumping `as_of` to
  2026-07-13 — no ARR number or `floor_met_year1` changed. Refreshed `GROWTH_STATUS.md`
  (`as_of`, validation block reconciled against the fresh QUALITY_SCORECARD read, a new
  learnings entry, `next_actions`/`owner_blockers` updated). **Circuit-breaker escalation:** the
  site-gate owner DECISION (`PENDING_OPS.md` `site-gate`, `ROADMAP.md:421-435`) has now gone 3
  consecutive GTM reads (2026-07-09 reframe, 07-11, 07-13) with zero owner movement — re-verified
  `PENDING_OPS.md` still shows `as_of: 2026-07-04`, `status: open`, unchanged since the reframe.
  Flagged prominently in `owner_blockers` per the GTM_STANDARD brakes/circuit-breaker discipline
  rather than silently re-asking the same question a 4th time. Independent reviewer (maker!=
  checker, fresh subagent) reviewed the `BUSINESS_CASE.md` fix + `GROWTH_STATUS.md` update
  together: verified every factual claim in the diff against the live repo state (re-ran
  `gtm_engine_pct.py` and `validate-computation.mjs` itself, read both scorecards + PENDING_OPS +
  GROWTH_MEMORY dates) — APPROVED, with one process note (this `GROWTH_MEMORY.md` entry was
  missing at review time; added after review to close the gap).
- **Recommended (to factory):** Unchanged priority — store-readiness (store screenshots +
  bespoke icon + mobile IAP client) and business-case-strength (a live per-seat price +
  real B2B adoption data) are the two remaining ship-critical gaps, both product-factory/owner
  work. Zero outreach drafts this run (correct): `QUALITY_SCORECARD.ship_gate_met` is still
  false. Demand_signal cadence checked: last run 2026-07-03 (10 days), ~quarterly refresh not
  due until ~October.
- **Meta / operational note:** Site-gate circuit breaker is now ACTIVE (3 consecutive quiet
  reads since the 07-09 reframe). Unlike the pre-07-09 pattern (asking the owner to flip a
  no-op env var for 5 straight reads), this ask is confirmed current and correct — it is a
  genuine binary decision (A: reinstate the gate, B: drop the gated-beta track) sitting with the
  owner, not a stale premise. Watching for either the owner's decision or a 4th consecutive
  quiet read, whichever comes first.

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

### 2026-07-11 — Daily GTM review (quiet run; scorecards unmoved despite real product progress)
- **Observed:** Phase still `pre_launch`. Re-verified `ListConnectors` (only Gmail/Drive/
  Calendar, no analytics/billing/ESP MCP) and shell env (no `PROD_URL`/`ANALYTICS_READ_TOKEN`) —
  `channels_connected: []` stays honest. Re-ran `analysis/gtm_engine_pct.py` — unchanged at 50.
  Both independent scorecards read fresh this run: **neither has re-graded since 2026-07-09**
  (same `as_of` on both files) — despite real product-factory movement in between (runs 39-42,
  2026-07-10/11): the team/B2B2C seat-tier **backend** (PR #348) and its **web management
  surface** (PR #356) both shipped, gate-verified (`tests/test_org_billing.py` 21 cases +
  5 web-E2E journeys), and PR #336 closed the correctness A→A+ gap the 5th QUALITY_SCORECARD
  audit named (AI-slot refund on a provider 502). None of that is self-certifiable by this loop
  per GTM_STANDARD §4/FACTORY_STANDARD §28 — QUALITY_SCORECARD stays consumed **as-is** (C,
  `ship_gate_met: false`; functional-reality D, store-readiness C, business-case-strength C all
  still open on the auditor's own last grade) until its own next independent audit; outreach
  stays hard-blocked regardless. GTM_SCORECARD stays A/`ship_gate_met: true` (unchanged, GTM
  work-quality gate).
- **Concluded:** No real funnel/PMF data justifies a ROADMAP/BUSINESS_CASE ARR/VISION steer this
  run (same reasoning as every prior pre-launch read). The business-case floor-lever build work
  (team tier) is real and load-bearing, but crediting it in `floor_met_year1` before the next
  audit + before real adoption data would be self-certification — correctly left untouched.
- **Did (real, in-repo, no channel needed):** One small, genuine artifact-freshness fix in
  `docs/BUSINESS_CASE.md` lever 2: the prose said "the web/mobile admin surface... remain",
  which understated PR #356 (the web half is now shipped) — corrected to name the web half as
  built and only the mobile half + live per-seat pricing as remaining, matching
  `ROADMAP.md:291-300`'s own precise framing. No ARR number or `floor_met_year1` changed.
  Refreshed `GROWTH_STATUS.md` (`as_of`, validation block, a new learnings entry, an explicit
  new owner_blocker/next_action calling out `STRIPE_PRICE_TEAM_ANNUAL` as the seat tier's
  remaining sellability gap now that both build halves exist). Independent reviewer
  (maker≠checker, fresh subagent) reviewed the BUSINESS_CASE fix + GROWTH_STATUS update
  together: APPROVED.
- **Recommended (to factory):** Unchanged priority order on the 3 named ship-critical gaps
  (functional-reality fix confirmation, store-readiness assets/IAP, business-case floor) — all
  product-factory or owner work, not something this loop builds. Zero outreach drafts this run
  (correct): `QUALITY_SCORECARD.ship_gate_met` is still false. Site-gate owner decision still
  open — 2nd consecutive quiet GTM read since the 07-09 reframe; not yet a circuit-breaker
  pattern, but flagged to escalate on a 3rd.

---

### 2026-07-09 — Daily GTM review (site-gate reframe + engine_pct honesty fix + GTM_SCORECARD gap closed)
- **Observed:** Phase still `pre_launch`. `ListConnectors` confirms only Gmail (connected,
  enabled) + Google Drive (connected, not enabled-in-chat) + Google Calendar (unknown/not
  enabled) — no analytics/billing/email-provider MCP available; shell env has no `PROD_URL` or
  `ANALYTICS_READ_TOKEN` (`BROWSERBASE_API_KEY`/`BROWSERBASE_PROJECT_ID` ARE present, but that
  is FACTORY_STANDARD §29 deployed-app-validator infra, not a GTM source) —
  `channels_connected: []` stays honest. Both independent scorecards happened to re-grade the
  SAME DAY: **QUALITY_SCORECARD's 5th audit (2026-07-09) dropped B→C** — a NEW ship-critical
  regression, functional-reality A+→D: the shipped default LLM model (`gemini-2.5-flash`) was
  decommissioned upstream by Google, 502ing every paid AI feature (mock interview, coach, prep
  pack, cover letter, tailored résumé, salary-negotiation, learning plan). Per `git log`, the
  product factory shipped a same-day fix AFTER that audit landed (`fbb61ca` resilient
  model-fallback, `51020ad` cross-instance login-lockout) — but per GTM_STANDARD §4/
  FACTORY_STANDARD §28 this loop does NOT self-certify from adjacent commits: the scorecard
  stays read AS-IS (C, `ship_gate_met: false`) until its own independent auditor re-grades, so
  outreach stays hard-blocked regardless. **GTM_SCORECARD also re-graded** (2026-07-09, overall
  A, `ship_gate_met: true`, unchanged) — one named top_gap: `roadmap_steer_justification` A, not
  A+ (see "Did" below).
- **The two real corrections this run (both genuine artifact-freshness bugs owned by THIS
  loop, not the product factory):**
  1. **Site-gate framing was stale and would have kept being wrong.** `PENDING_OPS.md` and
     `ROADMAP.md:421-435` were updated by the product factory (run 34, same day) disclosing
     that the pre-launch SITE GATE was **deleted at owner request on 2026-07-02** —
     `web/middleware.ts` is now a literal pass-through (verified by reading the live file this
     run). This GTM loop had asked the owner to "apply `SITE_GATE_PASSWORD`" as the single
     highest-leverage 2-minute fix for **5 straight reads** (06-29 → 07-07) — that ask does
     literally nothing against the current code and would have kept recurring, incorrectly,
     every run without this catch. Rewrote `GROWTH_STATUS.md`'s `site_gate_up` commentary +
     `owner_blockers` + `next_actions` to the real open item: an owner **decision** (reinstate a
     rebuilt gate, or keep the app public and drop the §34 gated-beta track) — not an env-var
     task. `site_gate_up` stays `false` (still literally accurate), only the surrounding
     narrative was wrong.
  2. **`engine_pct: 0` / "not built" had been asserted for 6 GTM reads while ROADMAP Track G+H
     actually show 8/16 checked items** (waitlist+double-opt-in, email-provider seam, analytics
     read-API, CONNECT runbook, brand kit, analytics instrumentation, waitlist landing, public
     demo). Wrote `analysis/gtm_engine_pct.py` (parses ROADMAP.md Track G+H checkboxes,
     deterministic, FACTORY_STANDARD §22) → **50**, registered in `figures.json`, verified by
     `scripts/validate-computation.mjs`. `engine_built` stays `false` (50 < 100, satisfies
     `check_blocks.py`'s `engine_built` iff `engine_pct==100` invariant) — a build-completeness
     correction, NOT a claim that any channel is connected (`channels_connected` stays `[]`).
- **Closed GTM_SCORECARD's one named top_gap:** the auditor flagged that GTM commit `24e9b84`'s
  B2B2C packaging recommendation in `BUSINESS_CASE.md` lever 2 reads as a steer while its own
  commit message said "no steer," and that run's `demand_signal` explicitly could neither
  confirm nor refute B2B2C demand. Added an inline "Demand caveat" paragraph to
  `BUSINESS_CASE.md` lever 2 stating plainly the packaging note is a *competitor-pricing-comp*
  recommendation only, not demand-validated — per the auditor's own suggested fix (b). No ARR
  number or `floor_met_year1` changed.
- **Concluded:** No real funnel/PMF data justifies a ROADMAP/BUSINESS_CASE ARR/VISION steer this
  run (same reasoning as every prior pre-launch read — 0 users, 0 funnel data). The BUSINESS_CASE
  caveat edit is a reconciliation of THIS loop's own prior packaging note, not a new steer.
  Demand_signal cadence checked: last run 2026-07-03 (6 days), ~quarterly refresh not due until
  ~October. Zero outreach drafts (correct): `QUALITY_SCORECARD.ship_gate_met` is false.
- **Did:** All three changes (site-gate/engine_pct reconciliation in `GROWTH_STATUS.md`, the new
  `analysis/gtm_engine_pct.py` + `figures.json` registration, and the `BUSINESS_CASE.md` lever-2
  caveat) bundled into one PR and run through an independent reviewer (maker≠checker, fresh
  subagent) told to check: is the engine_pct computation methodology sound and non-gamed? does
  the site-gate reframe accurately reflect PENDING_OPS/ROADMAP without overclaiming or
  underclaiming? does the BUSINESS_CASE caveat honestly close the auditor's named gap without
  introducing a new speculative claim? — see PR for the verdict.
- **Meta / operational note (circuit breaker resolved, differently than expected):** The
  `SITE_GATE_PASSWORD` circuit-breaker item that had persisted across 5 consecutive GTM reads
  did NOT resolve by the owner acting on it — it resolved because the underlying premise turned
  out to be wrong (the owner had already made a DIFFERENT decision — removing the gate entirely
  — on 2026-07-02, and this loop kept re-asking the stale question for 5 more reads before the
  product factory's run-34 correction surfaced it). **Lesson for future circuit-breaker
  escalations:** an owner action that goes unaddressed for many consecutive reads is not only
  "the owner hasn't gotten to it yet" — it is also worth periodically re-verifying the action is
  STILL live against the current code/config, not just repeating the same ask by rote. Also
  worth noting: `engine_pct` had been silently wrong (hardcoded stale value, never recomputed)
  since bootstrap — a reminder to apply FACTORY_STANDARD §22's "compute it, don't eyeball it"
  discipline to EVERY GROWTH_STATUS numeric field, not just the ARR figures.

---

### 2026-07-07 — Daily GTM review (quiet run; VISION-pivot reconciliation, no steer)
- **Observed:** Phase still `pre_launch`. `ListConnectors` confirms only Gmail (connected,
  enabled) + Google Drive (connected, not enabled-in-chat) + Google Calendar (unknown/not
  enabled) — no analytics/billing/email-provider MCP available; shell env has no `PROD_URL` or
  `ANALYTICS_READ_TOKEN` — `engine_built: false` / `channels_connected: []` stay honest, same as
  every prior run. Pulled the full `main` branch (44 commits had landed since the last GTM read,
  2026-07-05 → 2026-07-07) and checked both independent scorecards with `git log --follow`:
  **neither `docs/quality/QUALITY_SCORECARD.md` nor `docs/growth/GTM_SCORECARD.md` has been
  re-touched since commit `b628f5b` (2026-07-03)** — no fresh independent grade exists despite
  ~20 intervening product-factory commits (coverage-floor ratchet 75→85, per-user rate limiting,
  a real per-PR prep-pack content-quality eval, ATS retry/backoff, profile enrichment, tailored
  résumé generation, a new §34 pre-launch public-demo-funnel ROADMAP item, a new §11 marketing
  media-gen adapter ROADMAP item). QUALITY_SCORECARD therefore stays read AS-IS: **B, ship gate
  NOT met**, same 2 ship-critical C's (business-case-strength, store-readiness). GTM_SCORECARD
  stays **A, ship_gate_met: true** (unchanged). `docs/BUSINESS_CASE.md` unchanged since the
  2026-07-05 GTM run (still $57.5K base < $100K floor; team/B2B2C tier still unbuilt).
- **The one genuinely notable event:** `VISION.md` was rewritten this cycle (commit `5846822`,
  outside the GTM loop, by the product factory) to name **"interview coaching (Siro for
  interviews)"** as the current frontier / surface 3 of the north star, and `ROADMAP.md` gained a
  full new track — "Interview coaching + the autonomous prep loop" (mock-interview engine,
  interview-readiness score, owner-gated voice/delivery analysis) — all still unchecked/unbuilt.
  This is exactly the JTBD theme this loop's 2026-07-03 §10 demand-signal pass flagged as only
  **PARTIALLY solved** ("interview-PRACTICE anxiety, distinct from content prep") and tied to
  `BUSINESS_CASE.md` lever 3's already-named "mock-interview voice sessions" wedge — the product
  factory converged on it independently, without a GTM-authored ROADMAP/VISION edit. Recording the
  convergence as a citable data point (commit `5846822` + the existing `demand_signal` block), not
  claiming credit for the pivot or crediting any ARR — 0 users still, and the mock-interview engine
  itself is `[ ]` unbuilt in `ROADMAP.md`.
- **Concluded:** No real data justifies a ROADMAP/BUSINESS_CASE/VISION steer this run (same
  reasoning as every prior pre-launch read — 0 users, 0 funnel data). Checked GTM_STANDARD §13
  (new this cycle, commit `53b7a57`) for a `marketing:` block / `MARKETING_APPROVED` /
  `MARKETING_HOLD` file: **none exists**, correctly — Gate 1's preconditions
  (`ship_gate_met` + a green computer-use E2E sweep + passed launch assets) are not met, so no
  waitlist-outreach plan should be proposed yet. Checked demand-signal refresh cadence: last run
  2026-07-03 (4 days), the ~quarterly refresh is not due. Checked ROADMAP §34 (pre-launch
  public-demo funnel): still unchecked — the pre-launch funnel shape is still the blank waitlist,
  unchanged from the last read.
- **Did:** Refreshed `GROWTH_STATUS.md` (dates, re-validated sources, the VISION-pivot
  reconciliation note, an explicit note that neither scorecard has been re-touched since the last
  audit despite substantial adjacent product work) and this entry. No new asset, no channel, no
  steer — a routine dashboard-bookkeeping refresh, not a substantive GTM change, so no
  maker≠checker review was run (consistent with how prior bookkeeping-only refreshes were
  handled; substantive research runs like 2026-07-03/07-05 DID go through review).
- **Recommended (to factory):** Unchanged priority — business-case-strength (team/B2B2C tier,
  annual-first pricing) and store-readiness (rendered assets + mobile IAP) remain the two
  ship-critical gaps per the last independent grade. Zero outreach drafts this run: the readiness
  gate (`QUALITY_SCORECARD.ship_gate_met`) is still false.
- **Meta / operational note (circuit breaker, escalating):** `SITE_GATE_PASSWORD` has now been
  named as the single highest-leverage owner action across **5 consecutive GTM reads**
  (2026-06-29, 07-01, 07-03, 07-05, 07-07) — the longest-standing single blocker in this loop's
  history. It remains a ~2-minute env-var set, unlike the Stripe/Apple/Google account-creation
  items. Also naming a second, related pattern for the first time: **both independent scorecards
  have now gone 2 straight GTM reads (07-05, 07-07) without a re-grade**, even though the product
  factory has been actively shipping in the interim — this loop correctly does NOT infer progress
  from adjacent commits (that would be self-certification, the exact failure mode GTM_STANDARD §4
  forbids), but it's worth watching whether the independent-auditor routines themselves have
  stalled, since a fresh QUALITY_SCORECARD grade is the most likely near-term way `ship_gate_met`
  flips true and opens the outreach gate.

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
