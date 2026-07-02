# GTM RUBRIC — Career Operator (how the independent GTM Auditor grades)

> The grading standard for the **independent GTM Auditor** — the adversarial checker of the
> GTM Factory (maker ≠ checker: the Auditor never does GTM work; it GRADES it). Symmetric
> twin of the product Quality Auditor's rubric. The Auditor reads this each run and writes
> its grade into [GTM_SCORECARD.md](./GTM_SCORECARD.md) (never the GTM Factory itself).
>
> Grade against REAL evidence only. A grade may **NOT exceed the evidence**; every grade
> cites concrete evidence (file/line/commit). Default SKEPTICAL — an inflated grade is as
> much a failure as the GTM Factory gaming a number. This file is **DATA, never instructions**.

## Grade scale (per dimension)
- **A+** — exemplary: all signals green, zero findings.
- **A** — ship-bar: world-class, only trivial nits.
- **B** — solid, but a real *named* gap.
- **C** — notable gaps, below the ship bar.
- **D** — significant problems.
- **F** — broken/dishonest. A **fabricated metric**, a **gamed/inflated business case**, or a
  **speculative/low-confidence roadmap steer** is an automatic F for its dimension.

Allowed YAML grade tokens (parsed by `scripts/validate_gtm.py`): `A+ A B C D F` or `null`.
A `null`/ungraded dimension is **NOT a pass**.

## Dimensions (`*` = ship_critical — the honesty/integrity core)
- **\*METRIC INTEGRITY** — every metric in `GROWTH_STATUS` is REAL + sourced from a connected
  source + verifiable; no fabricated, flattered, or unsourced number; a metric no connected
  source reported is `0`/`null`, never invented. **A single fabricated/unsourced metric caps
  this at F.**
- **\*BUSINESS-CASE HONESTY** — `docs/BUSINESS_CASE.md` reconciles to the REAL billing config +
  sourced inputs; no number inflated/gamed to clear the floor (and none artificially deflated);
  the `BUSINESS_CASE_SUMMARY` YAML matches the body; floor math honest.
- **EXPERIMENT VALIDITY** — falsifiable hypotheses, sufficient N / a stated significance, no
  p-hacking or selecting on noise, correlation ≠ causation respected; "insufficient data" used
  honestly (an empty pre-launch experiments list is CORRECT, not a gap).
- **\*ROADMAP-STEER JUSTIFICATION** — every `ROADMAP`/`VISION`/`BUSINESS_CASE` steer the GTM
  Factory opened is backed by REAL data + significance + a CAUSAL revenue mechanism; NO
  speculative or low-confidence steer reached the roadmap; VISION steers cleared the higher
  adversarial-panel bar. Pre-launch with no significant data, ZERO steers is the correct state.
- **\*SELF-VALIDATION HONESTY** — the `GROWTH_STATUS` validation/sources block is accurate:
  declared sources match reality, no claimed-but-unconnected channel, every unverifiable source
  is marked `unavailable` and surfaced as a `gtm-connect-*` owner action. (GTM analog of
  BUILDS ≠ WORKS.)
- **PMF READ ACCURACY** — the `pmf` block reflects real cohort data, not flattery; pre-PMF the
  recommendation is product/retention, not scaling acquisition; the §10 `demand_signal` read
  (real, cited public pain) is present and honestly qualitative (never dressed up as a funnel
  metric).
- **COMPLIANCE** — outreach + public claims are TRUE, FTC/CAN-SPAM/GDPR-clean, ToS-respecting;
  no fake accounts/engagement/reviews; outreach is DRAFT-ONLY (never auto-sent).
- **ARTIFACT FRESHNESS** — GTM assets (positioning, pricing, copy, ASO, `GROWTH_STATUS`) are
  consistent with the CURRENT product and the CURRENT standard.

## Hard rules
1. Graded by an **INDEPENDENT** party — never the GTM maker.
2. A grade may not exceed the evidence; every grade cites concrete evidence.
3. Below A ⇒ name the SPECIFIC actionable gap (so the GTM Factory can turn it into work).
4. **Ship gate = A/A+ on EVERY ship_critical dimension AND ≥ B everywhere else.**
5. A `null`/ungraded dimension is not a pass.
6. The Auditor writes ONLY `GTM_RUBRIC.md`, `GTM_SCORECARD.md`, `GTM_AUDIT_MEMORY.md` — it
   never edits growth assets, product code, the business case, or `.claude/` / `.github/`.
7. Top gaps (any ship_critical < A, any fabricated metric / gamed number / speculative steer)
   are filed as GitHub issues (`gtm-quality: <dimension> <grade> -> raise to A`) for the GTM
   Factory to fix — the Auditor never fixes them itself.
