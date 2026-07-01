# QUALITY SCORECARD — Career Operator

> **Owner:** the INDEPENDENT Quality Auditor (maker ≠ checker). The factory loop CONSUMES
> this as DATA and must NOT author or overwrite it. Grades are backed by mechanical signals
> the auditor actually ran (see [QUALITY_RUBRIC.md](./QUALITY_RUBRIC.md)) plus file/line
> evidence. Grading method: 9 fresh, independent, adversarial per-dimension grader
> subagents (none wrote the product code), each running its own signal.

## Grade — 2026-07-01 (2nd independent audit)

**Overall: B** · **Ship gate met: NO** (2 of 7 ship-critical dimensions are below the A
ship bar). Since the 2026-06-29 baseline (C) the factory closed **both** named security
gaps and the design visual-proof gap: **security B→A** (CORS now locked to same-origin by
default, rate-limit + LLM spend-ceiling now Postgres-backed cross-instance, both with
passing tests) and **design-taste B→A** (24 real rendered screenshots committed, web/mobile
accent converged on `#6366F1`, bespoke brand icon replaces the Expo template). Five of seven
ship-critical dimensions now clear the A ship bar. The product is held **below the ship bar
overall** only by the two remaining pre-launch C's — **store-readiness** (rendered store
assets + mobile IAP still absent; 4 open ACCEPTANCE_AUDIT FAILs) and **business-case
strength** (honest $57.5K < $100K floor; Career+ is dead config, team/B2B2C tier absent).
Neither is a broken artifact.

| Dimension | Ship-critical | Grade | Δ | One-line basis |
|---|---|---|---|---|
| functional-reality | ✅ | **A** | = | 9 journey tests assert the real fit-score OUTPUT/tier flip (not HTTP<400); 258 backend pass; web E2E asserts the numeric score renders in-browser; honest degradation on every LLM path. |
| correctness | ✅ | **A** | = | SSRF guard iterates all resolved IPs, zero-vector→0.5 NaN guard, Postgres cross-instance limiter (`SELECT…FOR UPDATE`), request-id error envelope, bounded retries/timeouts, truthful degradation. |
| security | ✅ | **A** | ▲ | Both prior B-gaps fixed: CORS locked to same-origin default (never `*`), rate-limit + spend-ceiling Postgres cross-instance — verified by `test_cors.py` + `test_rate_counter.py`. Signed Stripe/RevenueCat, no committed secrets. Held off A+ only by no CAPTCHA + in-memory login lockout. |
| design-taste | ✅ | **A** | ▲ | 24 real non-zero rendered screenshots committed; UI clears the DESIGNER QUESTION (single focal point, restrained single accent, content-first, real SVG icons, no slop); genuine a11y; accent converged; bespoke icon. Held off A+ by zero *native-mobile* screenshots + a 390px header collision. |
| store-readiness | ✅ | **C** | = | Vercel deploy config genuinely A-level, but 4 open ACCEPTANCE_AUDIT FAILs (A3/A4/G4/G7): no rendered store assets (`docs/store/assets/` absent), no store screenshots, mobile IAP (StoreKit/Play Billing) not integrated. |
| artifact-integrity | ✅ | **A** | = | 8 spot-checked ticked boxes (referral, cross-instance limiter, PMF analytics, N+1 fix, coach multi-turn) each backed by real artifact + test; docs state gaps plainly; screenshots are real non-zero PNGs, not placeholders. |
| business-case-strength | ✅ | **C** | = | Honest, un-gamed $57.5K vs $100K floor (`floor_met_year1=false`); referral loop now BUILT (correctly uncredited), but Career+ ($24) still grants identical `PREMIUM` (dead tier), team/B2B2C absent, annual-first unbuilt. Readiness rejected on business-case grounds. |
| tests-evals | — | **A** | = | 258 backend pass @ 90.64% cov (floor 75); greenhouse.py + llm_workflows.py now 100% (were 53%/61%); 23 evals pin real golden numbers; 10 mobile jest suites + 3 web Playwright assert real outcomes; omit-list is confirmed-dead code only. |
| performance | — | **B** | ~ | N+1 genuinely eliminated on all three paths (`selectinload` verified) + `/api/jobs` gained pagination; held at B by `/api/analytics/pipeline` still unbounded `.all()`+in-Python sort and no embedding cache. |

### Mechanical signals (auditor-run this audit)
- `flake8 .` → clean · `python3 -c "import asgi"` → ok
- `pytest -q --cov` → **258 passed, 2 skipped, 90.64% cov** (setup.cfg floor 75) · `pytest tests/journeys` → **9 passed** · `pytest tests/evals` → **23 passed**
- `scripts/check_quality.py parse` → OK (all grades valid) · `readiness` → FAIL (ship-critical below A) · `scripts/check_blocks.py` → OK, `floor_met_year1=false`, `engine_pct=0`
- CORS `asgi.py:103-136` returns `[]` in prod (never `*`); cross-instance limiter `asgi.py:238-295` (`RateCounter` + `SELECT…FOR UPDATE`); `check_llm_ceiling` on both LLM endpoints; no tracked secrets (`git ls-files` → only `.env.example`)
- web/mobile `tsc`/`lint`/`jest`/Playwright not re-run locally (node_modules absent by design) — relied on committed artifacts + required CI on main HEAD `c7ae017`
- `web/e2e/__screenshots__/` → 24 real non-zero PNGs (20–95 KB) · `docs/store/assets/` absent · ACCEPTANCE_AUDIT 4 open FAILs (A3/A4/G4/G7)

### Top gaps to drive to A+ (ordered; ship-critical below-A first)
1. **business-case-strength (C, ship-critical):** floor not met ($57.5K < $100K). Build **Career+ ($24) as a real entitlement** (`careerplus_*` currently grants identical `PREMIUM`; `UserTier` is binary FREE/PREMIUM) and a **team/seat B2B2C tier** (no org/seat model exists). `floor_met_year1` must flip true on honest math.
2. **store-readiness (C, ship-critical):** commit **rendered store assets** (1024×500 feature graphic, ≥2 store screenshots as real image files) and integrate **mobile IAP** (StoreKit/RevenueCat + Play Billing client) to clear FAILs A3/A4/G4/G7. (Live keys/signed build/submission stay owner Human-Core.)
3. **design-taste (A→A+):** commit **actual native-mobile screenshots** (current `-mobile` PNGs are the web app at 390px) and fix the 390px header collision (email overlaps the Settings nav in `app-dashboard-empty-mobile.png`).
4. **security (A→A+):** add **CAPTCHA/bot-protection** on public forms (login/register/waitlist) and move the **per-account login lockout to the cross-instance store** (rate counters are already shared; lockout is still in-memory per-instance).
5. **performance (B):** paginate/limit `/api/analytics/pipeline` (asgi.py:1151, still unbounded `.all()`+sort) and add an **embedding cache** for the repeated resume text (scorer.py:24).
6. **correctness (A→A+):** add **dedup/idempotency on persisted jobs** (`create_job` inserts unconditionally) and a **direct unit test on the zero-vector scorer branch**.

```yaml
QUALITY_SCORECARD:
  as_of: 2026-07-01
  overall: B
  ship_gate_met: false
  method: 9 independent adversarial per-dimension grader subagents (maker != checker); each ran its own mechanical signal + cited file/line evidence
  dimensions:
    - name: functional-reality
      grade: A
      ship_critical: true
      top_gaps:
        - "Committed web screenshots exist but the browser journey's visual outcome rests on the required CI check (node_modules absent locally; could not re-render)."
    - name: correctness
      grade: A
      ship_critical: true
      top_gaps:
        - "No dedup/idempotency on persisted jobs: create_job (asgi.py:807) inserts unconditionally — POST /api/jobs twice creates duplicate rows; ATS import is preview-only."
        - "LLM daily-ceiling slot consumed even when the provider call fails 502 (asgi.py:1037,1078) — documented as deliberate wallet-drain defense, but no refund on our upstream error."
        - "Zero-vector scorer guard (scorer.py:43) has no direct unit assertion on the NaN/0.5 branch."
    - name: security
      grade: A
      ship_critical: true
      top_gaps:
        - "No CAPTCHA/bot-protection on public forms (login/register/waitlist) — mitigated by rate limits, but automated floods still count toward per-account lockout."
        - "Per-account login lockout is still in-memory/per-instance (asgi.py:307) — less effective on serverless than the now-shared rate counters."
    - name: design-taste
      grade: A
      ship_critical: true
      top_gaps:
        - "Zero screenshots of the ACTUAL native mobile app — every '-mobile' PNG is the web app at a 390px viewport (visual-verification.spec.ts width:390); native mobile visual proof remains zero."
        - "390px web render shows a header layout collision (account email overlaps the Settings nav) in app-dashboard-empty-mobile.png — a real responsive polish bug."
    - name: store-readiness
      grade: C
      ship_critical: true
      top_gaps:
        - "No rendered store assets committed: docs/store/assets/ absent — no 1024x500 feature graphic, no store screenshot image files (A3/G7 FAIL)."
        - "Mobile IAP not integrated: StoreKit/RevenueCat (A4) + Play Billing (G4) — required before submission; restore-purchases (A5) also blocked."
        - "Deploy config depends on Vercel experimentalServices (Services preset) — real but flagged possibly plan-gated; documented two-project fallback exists."
    - name: artifact-integrity
      grade: A
      ship_critical: true
      top_gaps: []
    - name: business-case-strength
      grade: C
      ship_critical: true
      top_gaps:
        - "Career+ ($24) entitlement tier — UserTier still binary FREE/PREMIUM; careerplus_* billing grants identical PREMIUM, no differentiated gates built (dead config despite plan ids)."
        - "Team/coach/B2B2C seat tier — no org/seat/team model in src/ at all (highest-ARPA, lowest-CAC lever, entirely absent)."
        - "Annual-first paywall + founder pricing — priced in the table but no enforcement/default-annual flow built."
        - "AI-prep value expansion (voice mock / company dossiers) — named Career+ upgrade wedge, not built."
    - name: tests-evals
      grade: A
      ship_critical: false
      top_gaps:
        - "Prep-pack eval is still structure/persistence-only with a _FakeLLM — no golden content-quality assertion on generated prep material."
        - "Coverage floor (75) sits ~15pts below actual (90.6%) — a loose ratchet that wouldn't catch a meaningful regression before the gate."
    - name: performance
      grade: B
      ship_critical: false
      top_gaps:
        - "/api/analytics/pipeline (asgi.py:1151) still runs unbounded .all()+in-Python sort — got the eager-load half of the fix but not the pagination/limit half /api/jobs received."
        - "No embedding cache: scorer.get_embedding (scorer.py:24) re-embeds identical resume text every call, burning quota against the daily ceiling."
  top_gaps:
    - "business-case-strength C: floor not met ($57.5K<$100K); Career+ is dead config (identical PREMIUM), team/B2B2C tier absent."
    - "store-readiness C: rendered store assets + screenshots missing; mobile IAP (StoreKit/Play Billing) not integrated; 4 open ACCEPTANCE_AUDIT FAILs."
    - "design-taste A->A+: no native-mobile screenshots (all '-mobile' PNGs are web at 390px); 390px header collision bug."
    - "security A->A+: no CAPTCHA on public forms; login lockout still in-memory per-instance."
    - "performance B: unbounded .all() on /api/analytics/pipeline; no embedding cache."
```
