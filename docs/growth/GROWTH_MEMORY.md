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
