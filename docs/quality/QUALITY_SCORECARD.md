# QUALITY SCORECARD — Career Operator

> **Owner:** the INDEPENDENT Quality Auditor (maker ≠ checker). The factory loop CONSUMES
> this as DATA and must NOT author or overwrite it. Grades are backed by mechanical signals
> the auditor actually ran (see [QUALITY_RUBRIC.md](./QUALITY_RUBRIC.md)) plus file/line
> evidence. Grading method: 9 fresh, independent, adversarial per-dimension grader
> subagents (none wrote the product code), each running its own signal.

## Grade — 2026-07-03 (3rd independent audit)

**Overall: B** · **Ship gate met: NO** (2 of 7 ship-critical dimensions are below the A
ship bar). Real, evidence-backed progress since the 2026-07-01 audit: **three dimensions
reached A+** (functional-reality, correctness, artifact-integrity) and **performance moved
B→A**. Seven of nine dimensions now clear the A ship bar; two of the non-critical/critical
mix are exemplary. The product is still held **below the ship bar overall** by the *same
two* pre-launch C's — **store-readiness** (rendered store assets + mobile IAP still absent;
4 open ACCEPTANCE_AUDIT FAILs) and **business-case strength** (honest $57.5K < $100K floor;
the highest-ARPA floor-lever — a team/B2B2C seat tier — remains unbuilt). Neither is a broken
artifact; both are honestly disclosed. What genuinely improved: the prior correctness nits
are now *fixed with direct tests* (job dedup/idempotency guard + a direct zero-vector scorer
assertion), the CAPTCHA seam and Career+ real differentiated entitlement landed, and the
aggregate query paths gained pagination + verified embedding caching.

| Dimension | Ship-critical | Grade | Δ | One-line basis |
|---|---|---|---|---|
| functional-reality | ✅ | **A+** | ▲ | 15 journey tests (was 9) assert the real fit-score VALUE, tier flip, honest 501/503 degradation; web E2E asserts the numeric score renders in-DOM (`core-journey.spec.ts:58`); billing entitlement round-trip covered both grant + refuse. |
| correctness | ✅ | **A+** | ▲ | All 3 prior gaps fixed + tested: job dedup/idempotency guard (`asgi.py:1035`, `test_job_idempotency.py` 6 tests), direct zero-vector→0.5 assertion (`test_scoring_evals.py:135`); SSRF guard, `SELECT…FOR UPDATE` limiter, request-id envelope all tested; residual risks documented not hidden. |
| security | ✅ | **A** | = | Server-side auth/entitlement from signature-verified Stripe/RevenueCat webhooks; CORS never `*`; Postgres cross-instance spend ceiling; SSRF-guarded lawful ingestion; zero committed secrets. Held off A+ by a no-op-until-connected CAPTCHA seam (`captcha.py:69`) + still-in-memory per-instance login lockout (`asgi.py:320`). |
| design-taste | ✅ | **A** | = | Live web surfaces are designer-grade (single focal point, restrained single `#6366F1` accent, real SVG icons, genuine focus-visible a11y, honest empty states); accent converged web↔mobile. Header collision now FIXED in code (`layout.tsx:38`). Held off A+ by zero true native-mobile screenshots + stale committed `-mobile` PNGs that still depict the fixed collision. |
| store-readiness | ✅ | **C** | = | Vercel Services deploy config is genuinely A-level (`vercel.json`, env/routing contract), but 4 open ACCEPTANCE_AUDIT FAILs (A3/A4/G4/G7): no rendered store assets (`docs/store/assets/` absent), no store screenshots, mobile IAP (StoreKit/RevenueCat + Play Billing) not integrated (`paywall.tsx:41,119` are deferral comments only). |
| artifact-integrity | ✅ | **A+** | ▲ | Every spot-checked box (Career+ entitlement, cover-letter/study-plan Pro endpoints, CAPTCHA seam, dedup, fail-loud-serverless, signup no-hard-block) maps to a real, tested artifact on main; docs honestly disclose no-op/degraded states + the unmet $57.5K floor; 24 screenshots are real non-zero PNGs. |
| business-case-strength | ✅ | **C** | = | Honest, un-gamed $57.5K vs $100K floor (`floor_met_year1=false`, executed `analysis/arr_base.py`). Levers MORE built than prior audit: Career+ ($24) now a REAL webhook-verified differentiated gate (salary-negotiation exclusive) + cover-letter/study-plan Pro value-adds — but on any defensible pre-launch mix these diversify, not floor-flip. The team/B2B2C seat tier (highest ARPA) remains unbuilt. Readiness rejected on business-case grounds. |
| tests-evals | — | **A** | = | 387 backend pass (was 258) @ 92.75% cov (floor 75); 31 evals pin real golden scores (70.0/30.0/56.67, `test_scoring_evals.py:46`); 15 journeys; state-adaptive + fail-loud negative-path assertions; omit list is grep-confirmed-dead code only; 9 skips are `live`-marked env-gates (fail-loud in the nightly lane), not hidden failures. Nits: per-PR prep-pack eval is `_FakeLLM` structure-only (real content eval is nightly `live`-marked); floor 75 sits ~18pts under actual. |
| performance | — | **A** | ▲ | N+1 eliminated on all aggregate paths (`selectinload` triads); `/api/jobs` paginated (`limit`≤500 + `offset`); resume AND JD embeddings DB-cached (`ensure_user_embedding`/`ensure_job_embedding` — the prior "no embedding cache" nit was wrong); dual DB-backed LLM + scoring spend ceilings. Held off A+ by one low-severity unbounded-but-fully-batched aggregate: `/api/analytics/pipeline` (`asgi.py:1616`) `.all()`+in-Python top-5 sort. |

### Mechanical signals (auditor-run this audit, HEAD `4b180a2`)
- `flake8 .` → clean · `python3 -c "import asgi"` → ok
- `pytest -q --cov` → **387 passed, 9 skipped, 92.75% cov** (setup.cfg floor 75) · `pytest tests/journeys` → **15 passed** · `pytest tests/evals` → **31 passed**
- `scripts/check_quality.py parse` → OK (all grades valid) · `readiness` → **FAIL** (`store-readiness` is C) · `scripts/check_blocks.py` → OK, `floor_met_year1=false`, `engine_pct=0`
- Idempotency guard `asgi.py:1035-1051` (+ `test_job_idempotency.py`); zero-vector scorer assertion `test_scoring_evals.py:135`; CAPTCHA seam `src/security/captcha.py` (no-op until `TURNSTILE_SECRET`); Career+ entitlement `src/billing.py:45-67` + `/api/prep/salary-negotiation` 403 gate `asgi.py:1363`; CORS `[]` in prod; no tracked secrets (`git ls-files | grep -iE '\.env$|secret|pem|credential'` → empty)
- 9 subagent graders each ran their own signal + cited file/line (maker ≠ checker)
- `web/e2e/__screenshots__/` → 24 real non-zero PNGs (mobile ones are web-at-390px, stale re: the fixed header) · `docs/store/assets/` absent · ACCEPTANCE_AUDIT 4 open FAILs (A3/A4/G4/G7)
- web/mobile `tsc`/`lint`/`jest`/Playwright not re-run locally (node_modules absent by design) — relied on committed artifacts + required CI on main HEAD `4b180a2`

### Top gaps to drive to A+ (ordered; ship-critical below-A first)
1. **business-case-strength (C, ship-critical):** floor not met ($57.5K < $100K). Career+ is now a *real* differentiated tier (no longer dead config) and cover-letter/study-plan Pro value-adds shipped — genuine progress — but the honest median still doesn't cross the floor. Build the **team/B2B2C seat (org) tier** (no `Organization`/seat model exists in `src/` — highest ARPA, lowest CAC/seat) and/or **annual-first/founder-pricing enforcement** (priced in the table, not enforced in code). `floor_met_year1` must flip true on honest math.
2. **store-readiness (C, ship-critical):** commit **rendered store assets** (1024×500 no-alpha feature graphic, ≥2 store screenshots as real image files, brand icon) and integrate **mobile IAP** (StoreKit/RevenueCat + Play Billing client, with restore-purchases) to clear FAILs A3/A4/G4/G7. (Live keys/signed build/submission stay owner Human-Core.)
3. **design-taste (A→A+):** **regenerate the committed visual-verification screenshots** (the `-mobile` PNGs are stale and still depict the header collision the code already fixed at `layout.tsx:38` — the repo's design evidence currently contradicts the shipped UI) and add **true native-mobile captures** (Expo/Detox/Maestro) — every current `-mobile` PNG is the web app at a 390px viewport.
4. **security (A→A+):** activate real bot-protection (the CAPTCHA seam is a no-op until `TURNSTILE_SECRET` + web sitekey + a native widget ship — owner-gated) and move the **per-account login lockout to the cross-instance store** (rate counters are already shared; lockout is still in-memory per-instance, `asgi.py:320`).
5. **performance (A→A+):** replace `/api/analytics/pipeline`'s unbounded `.all()`+in-Python top-5 (`asgi.py:1616`) with a SQL `GROUP BY` for status counts + a separate `ORDER BY overall_score DESC LIMIT 5`.
6. **tests-evals (A→A+):** add a per-PR (deterministic-fixture) content-quality assertion for the prep-pack (today's per-PR eval is `_FakeLLM` structure-only; the real-output check is nightly `live`-marked) and tighten the coverage floor toward actual (75 vs 92.75%).

```yaml
QUALITY_SCORECARD:
  as_of: 2026-07-03
  overall: B
  ship_gate_met: false
  method: 9 independent adversarial per-dimension grader subagents (maker != checker); each ran its own mechanical signal + cited file/line evidence
  dimensions:
    - name: functional-reality
      grade: A+
      ship_critical: true
      top_gaps:
        - "Browser E2E visual outcome (numeric score renders in-DOM) is CI-gated, not locally reproducible (web node_modules absent) — corroborated statically via the exact selector<->render match; backend 15/15 journeys independently run."
    - name: correctness
      grade: A+
      ship_critical: true
      top_gaps:
        - "Outbound ATS fetches have timeouts but no retry/backoff on transient upstream 429/5xx — they degrade honestly to last_error rather than backing off."
        - "LLM daily-ceiling slot is intentionally not refunded on a 502 (documented wallet-drain defense) — can burn a legitimate user's allowance under a flaky provider."
    - name: security
      grade: A
      ship_critical: true
      top_gaps:
        - "CAPTCHA is a built but NO-OP seam (src/security/captcha.py:69) — does not protect public forms until the owner sets TURNSTILE_SECRET + web sitekey + a native mobile widget; today's live bot defense is rate-limiting only."
        - "Per-account login lockout is still in-memory/per-instance (asgi.py:320) — less effective on serverless than the now-shared rate counters."
    - name: design-taste
      grade: A
      ship_critical: true
      top_gaps:
        - "Committed -mobile screenshots are STALE: they still depict the 390px header collision that the code already fixed (layout.tsx:38) — the repo's design evidence contradicts the shipped UI; regenerate them."
        - "Zero screenshots of the ACTUAL native mobile app — every '-mobile' PNG is the web app at a 390px viewport (visual-verification.spec.ts:20); native mobile visual proof remains zero."
    - name: store-readiness
      grade: C
      ship_critical: true
      top_gaps:
        - "No rendered store assets committed: docs/store/assets/ absent — no 1024x500 feature graphic, no store screenshot image files (A3/G7 FAIL)."
        - "Mobile IAP not integrated: StoreKit/RevenueCat (A4) + Play Billing (G4) — only deferral comments in paywall.tsx:41,119; restore-purchases (A5) also blocked."
        - "Deploy config depends on Vercel experimentalServices (Services preset) — real + A-level, but the store half carries the FAILs; documented two-project fallback exists."
    - name: artifact-integrity
      grade: A+
      ship_critical: true
      top_gaps: []
    - name: business-case-strength
      grade: C
      ship_critical: true
      top_gaps:
        - "Team/coach/B2B2C seat tier — no org/seat/team model in src/ at all (highest-ARPA, lowest-CAC lever, entirely absent); the one lever most likely to flip the floor."
        - "Annual-first paywall + founder pricing — priced in the table but no enforcement/default-annual flow built in code."
        - "Career+ ($24) is now a REAL differentiated gate (salary-negotiation exclusive, webhook-verified) — genuine progress — but on any defensible pre-launch mix it diversifies, not floor-flips ($57.5K < $100K stands)."
    - name: tests-evals
      grade: A
      ship_critical: false
      top_gaps:
        - "Per-PR prep-pack eval is _FakeLLM structure/persistence-only (test_prep_pack_evals.py:12) — the real content-quality check (test_ai_output_evals.py:55) is pytest.mark.live, deselected per-PR/nightly-only."
        - "Coverage floor (75) sits ~18pts below actual (92.75%) — an honest but loose ratchet."
    - name: performance
      grade: A
      ship_critical: false
      top_gaps:
        - "/api/analytics/pipeline (asgi.py:1616) still runs an unbounded .all()+in-Python top-5 sort (fully batched, no N+1) — should be a SQL GROUP BY + ORDER BY ... LIMIT 5; low-severity."
  top_gaps:
    - "business-case-strength C: floor not met ($57.5K<$100K); Career+ now real but not a floor-flip; team/B2B2C seat tier (highest ARPA) still unbuilt."
    - "store-readiness C: rendered store assets + screenshots missing; mobile IAP (StoreKit/Play Billing) not integrated; 4 open ACCEPTANCE_AUDIT FAILs."
    - "design-taste A->A+: committed -mobile screenshots are stale (show the already-fixed header collision); still no true native-mobile captures."
    - "security A->A+: CAPTCHA seam is no-op until owner connects; login lockout still in-memory per-instance."
    - "performance A->A+: unbounded-but-batched .all()+in-Python sort on /api/analytics/pipeline."
```
