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

### 2026-06-28 — Daily run
- **Observed:** No funnel data (unchanged from 2026-06-27). 0 visitors, 0 signups, 0 subscribers. No channels connected. `docs/quality/QUALITY_SCORECARD.md` does not exist — quality grading has not been established; launch gate is unassessable without it. No new commits since PR #44 (2026-06-27 bookkeeping). Track G (Marketing engine) and Track H (Growth-execution engine) remain 0% complete except for the Owner CONNECT runbook.
- **Concluded (insufficient data):** Phase = pre_launch (unchanged). Binding constraint = pre-acquisition infrastructure: the Pre-launch SITE GATE (Track G item 1) does not exist, keeping `site_gate_up: false`, which HARD-BLOCKS execute-mode. Without a waitlist landing page (Track G item 2) and privacy-safe analytics (Track G item 5, Track H item 4), the funnel is entirely unobservable.
- **Mode:** PREPARE (hard-blocked from execute-mode: `site_gate_up: false`). Driving zero external traffic.
- **Recommended to factory (single highest-ROI lever):** Build Track G item 1 — `web/middleware.ts` Pre-launch SITE GATE with `SITE_GATE_PASSWORD` env-gating (exempting `/`, `/waitlist`, `/privacy`, `/terms`). This is the sole prerequisite to flip `site_gate_up: true`, which unblocks Track G item 2 (Waitlist landing + capture) and Track H items. Second priority: establish `docs/quality/QUALITY_SCORECARD.md` via the independent Quality Auditor so launch-gate grades become verifiable.
- **Owner blocker:** No channels connected; SITE GATE not built; no waitlist landing; QUALITY_SCORECARD missing. Execute-mode stays FORBIDDEN.
