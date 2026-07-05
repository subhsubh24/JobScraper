# QUALITY SCORECARD — Career Operator

> **Owner:** the INDEPENDENT Quality Auditor (maker ≠ checker). The factory loop CONSUMES
> this as DATA and must NOT author or overwrite it. Grades are backed by mechanical signals
> the auditor actually ran (see [QUALITY_RUBRIC.md](./QUALITY_RUBRIC.md)) plus file/line
> evidence. Grading method: 9 fresh, independent, adversarial per-dimension grader
> subagents (none wrote the product code), each running its own signal.

## Grade — 2026-07-05 (4th independent audit)

**Overall: B** · **Ship gate met: NO** (2 of 7 ship-critical dimensions are below the A
ship bar). No overall grade change since the 2026-07-03 audit, and no dimension moved a
letter — but real, evidence-backed internal progress: the correctness dimension's standing
retry/backoff gap is now **closed with a direct test** (PR #271), the security dimension's
**redirect-based SSRF** in the ATS probe is closed (PR #277), the eval suite grew **31→46**
and the backend suite **387→484 @ 92.21% cov**, and the job-detail GET now eager-loads its
relationships (PR #266). Seven of nine dimensions clear the A ship bar (three at **A+**:
functional-reality, correctness, artifact-integrity). The product is still held **below the
ship bar overall** by the *same two* pre-launch C's — **store-readiness** (no rendered store
assets, no mobile IAP client; 4 open ACCEPTANCE_AUDIT FAILs) and **business-case strength**
(honest $57.5K < $100K floor; the highest-ARPA lever — a team/B2B2C seat tier — remains
unbuilt). Neither is a broken artifact; both are honestly disclosed. Notable this run: the
grader environment had a live `GEMINI_API_KEY`, so the `live`-marked content evals (tailored
résumé grounding, prep-pack real output) **actually ran and passed** — the "the AI output is
real" claim was exercised, not just nightly-theoretical.

| Dimension | Ship-critical | Grade | Δ | One-line basis |
|---|---|---|---|---|
| functional-reality | ✅ | **A+** | = | 15 journeys assert the real fit-score VALUE (`test_core_journey.py:115`), tier non-flip on unverified purchase (:205-217), pipeline status flip, waitlist confirm side-effect flip; web E2E pulls the numeric score from the DOM and asserts `>0` (`core-journey.spec.ts:58`). All 5 features shipped since last audit (skill-gap #261, tailored résumé #247, drafter→reviewer #265, GitHub enrichment #270, résumé edit #276) are nav-reachable + eval-covered; no dead-ends. |
| correctness | ✅ | **A+** | ▲(gap closed) | Prior retry/backoff gap CLOSED by #271: `get_with_retry` bounded exponential backoff on 429/5xx, never on Timeout, correct ConnectTimeout edge case (`src/ingestion/base.py:22-55`) + `test_ats_retry.py` asserts exact call counts; redirect-SSRF re-validates every hop (`url_guard.py:61-84`, tested); zero-vector→0.5 guard (`scorer.py:63-66`) + dedup/idempotency (`asgi.py:1058-1074`) tested. Residual: LLM ceiling slot not refunded on provider 502 — now a documented tradeoff, not a latent bug. |
| security | ✅ | **A** | = | #277 closed the ATS redirect-SSRF (`url_guard.py:74-84`, per-hop re-validation). Server-side entitlement from signature-verified Stripe/RevenueCat webhooks; CORS `[]` in prod (never `*`); DB-backed cross-instance spend ceiling + `analytics/summary` gated by server-side token; zero committed secrets. Held off A+ by the no-op-until-connected CAPTCHA seam (`captcha.py:53-71`) + still-in-memory per-instance login lockout (`asgi.py:327`). |
| design-taste | ✅ | **A** | = | Live web surfaces are designer-grade (single `#6366F1` accent converged web↔mobile `theme.ts:10-12`, real SVG icons, zero emoji-as-icons, focus-visible a11y, real loading/empty/error states); header collision fixed in source (`layout.tsx:23,37-39`). Held off A+ by the SAME two gaps: committed `-mobile` screenshots are the web app at 390px (`visual-verification.spec.ts:18-21`), NOT regenerated since 2026-07-03, and there are zero true native-mobile captures. |
| store-readiness | ✅ | **C** | = | Vercel deploy config is genuinely A-level (`vercel.json:3-15`, env/routing contract), but 4 open ACCEPTANCE_AUDIT FAILs (A3/A4/G4/G7): no rendered store assets (`docs/store/assets/` absent), no store screenshots, mobile IAP (StoreKit/RevenueCat + Play Billing) not integrated — `paywall.tsx:40,118` are deferral comments, `react-native-purchases` absent from `mobile/package.json`. `check_quality.py readiness` → FAIL. No store asset or IAP moved since last audit. |
| artifact-integrity | ✅ | **A+** | = | Every spot-checked ticked box maps to a real, tested artifact on main (skill-gap `asgi.py:1752`+`skill_gaps.py:68`, tailored résumé `asgi.py:1587`, `_refine` wired into 6 generators but not `parse_job_description` exactly as ROADMAP claims, GitHub enrichment `github_enricher.py:82`, ATS retry `base.py:22`); 72 targeted tests pass. Gaps honestly disclosed: CAPTCHA no-op (ROADMAP:329), SQLite default (issue #222, flagged not hidden), `floor_met_year1=false`, store FAILs. No ticked box without code+test; no fabricated metric. |
| business-case-strength | ✅ | **C** | = | Honest, un-gamed $57.5K vs $100K floor (`analysis/arr_base.py`→57500, `BUSINESS_CASE.md:35,103-106`, `floor_met_year1=false`). Shipped levers (Career+ salary-negotiation gate, referral, tailored résumé Pro+, skill-gap AI plan) diversify the wedge but are explicitly NOT credited to the projection (anti-gaming) and don't floor-flip on any defensible mix. The team/B2B2C seat (org) tier — highest ARPA — remains **entirely unbuilt** (no Organization/Seat model in `src/db/models.py`; `UserTier` binary FREE/PREMIUM at `billing.py:63`). Readiness rejected on business-case grounds. |
| tests-evals | — | **A** | = (better within A) | 484 backend pass (was 387) @ 92.21% cov (floor 75); **46 evals** (was 31) pin real golden scores (70.0/30.0/50.0/56.67, `test_scoring_evals.py:46-58`); new drafter→reviewer evals prove the REVIEWED text is persisted + COGS toggle (`test_prep_tools_evals.py:171-258`); 9 skips are all `live_guard.py:51` env-gates that `pytest.fail()` under `REQUIRE_LIVE_TESTS=1` (fail-loud in nightly, not hidden); omit list grep-confirmed dead. Held off A+ by the coverage floor (75) sitting ~17pts under actual (92%) + the per-PR prep-pack eval being `_FakeLLM` structure-only. |
| performance | — | **A** | = | #266 verified: job-detail GET eager-loads application+score+company via `joinedload` (`asgi.py:1189-1195`); `/api/jobs` paginated (`limit`≤500 + `offset`) with selectinload triad; skill-gap cross-pipeline query capped at 500 (`_SKILL_GAP_JOB_CAP`); embeddings DB-cached; dual DB-backed spend ceilings (`.with_for_update()`). Held off A+ by the SAME single low-severity gap: `/api/analytics/pipeline` (`asgi.py:1980-2002`) still runs an unbounded `.all()`+in-Python top-5 sort (fully batched, no N+1) — should be SQL `GROUP BY`+`ORDER BY…LIMIT 5`. |

### Mechanical signals (auditor-run this audit, HEAD `7572338`)
- `flake8 .` → clean · `python3 -c "import asgi"` → ok
- `pytest -q --cov` → **484 passed, 9 skipped, 92.21% cov** (setup.cfg floor 75) · `pytest tests/journeys` → **15 passed** · `pytest tests/evals` → **46 passed**
- `scripts/check_quality.py parse` → OK (all grades valid) · `readiness` → **FAIL** (`store-readiness` is C) · `scripts/check_blocks.py` → OK, `floor_met_year1=false`, `engine_pct=0`
- `analysis/arr_base.py` → **57500** (< $100K floor) · no tracked secrets (`git ls-files | grep -iE '\.env$|secret|pem|credential|key$'` → empty) · CORS `[]` in prod (`asgi.py:143-144`)
- Retry/backoff `src/ingestion/base.py:22-55` (+ `test_ats_retry.py`); redirect-SSRF per-hop guard `url_guard.py:74-84` (+ `test_url_guard_redirect.py`); `docs/store/assets/` absent; ACCEPTANCE_AUDIT 4 open FAILs (A3/A4/G4/G7); no `react-native-purchases` in `mobile/package.json`
- 9 subagent graders each ran their own signal + cited file/line (maker ≠ checker); grader env had a live `GEMINI_API_KEY` so `live`-marked content evals ran + passed
- web/mobile `tsc`/`lint`/`jest`/Playwright not re-run locally (node_modules absent by design) — relied on committed artifacts + required CI on main HEAD `7572338`

### Top gaps to drive to A+ (ordered; ship-critical below-A first)
1. **business-case-strength (C, ship-critical):** floor not met ($57.5K < $100K). Shipped Pro value-adds diversify but don't floor-flip on honest math. Build the **team/B2B2C seat (org) tier** — an `Organization`/`Seat` model (absent from `src/db/models.py`), per-seat billing distinct from the binary `UserTier`, bulk-seat provisioning + admin roster, seat-priced Stripe products (highest ARPA, lowest CAC/seat). This is the one named lever with the math to honestly cross the floor. Do NOT credit seat ARR until real funnel data exists. `floor_met_year1` must flip true on honest math.
2. **store-readiness (C, ship-critical):** commit **rendered store assets** (1024×500 no-alpha feature graphic, ≥2 store screenshots as real image files, brand icon) and integrate the **mobile IAP client** (`react-native-purchases` + Play Billing, with restore-purchases) to clear FAILs A3/A4/G4/G7. The CLIENT wiring is loop-buildable now (server-side RevenueCat webhook already exists); only live keys/signed build/submission stay owner Human-Core.
3. **design-taste (A→A+):** **regenerate the committed visual-verification screenshots** (the `-mobile` PNGs are still the web app at 390px, not regenerated since 2026-07-03) and add **true native-mobile captures** (Expo/Detox/Maestro) — native-mobile taste is currently unverified by artifact.
4. **security (A→A+):** activate real bot-protection (the CAPTCHA seam is a no-op until `TURNSTILE_SECRET` + web sitekey + a native widget ship — owner-gated) and move the **per-account login lockout to the cross-instance store** (`asgi.py:327` is still in-memory per-instance while the rate counters are already shared).
5. **performance (A→A+):** replace `/api/analytics/pipeline`'s unbounded `.all()`+in-Python top-5 (`asgi.py:1980-2002`) with a SQL `GROUP BY` for status counts + a separate `ORDER BY overall_score DESC LIMIT 5`.
6. **tests-evals (A→A+):** ratchet the coverage floor from 75 toward ~88 (a large regression could land silently green at 75 vs actual 92%) and add a per-PR deterministic-fixture content-quality assertion for the prep-pack (today's per-PR eval is `_FakeLLM` structure-only).
7. **correctness (watch-item, non-blocking):** a flaky-provider 502 still burns a user's daily AI quota for a result they never received (`asgi.py:1366` consumes the slot before the 502) — defensible as a wallet-drain defense, but worth a product decision on refund-on-provider-error.

```yaml
QUALITY_SCORECARD:
  as_of: 2026-07-05
  overall: B
  ship_gate_met: false
  method: 9 independent adversarial per-dimension grader subagents (maker != checker); each ran its own mechanical signal + cited file/line evidence
  dimensions:
    - name: functional-reality
      grade: A+
      ship_critical: true
      top_gaps:
        - "Browser E2E visual outcome (numeric score renders in-DOM, core-journey.spec.ts:58) is CI-gated, not locally reproducible (web node_modules absent) — corroborated statically + backend 15/15 journeys independently run."
    - name: correctness
      grade: A+
      ship_critical: true
      top_gaps:
        - "LLM daily-ceiling slot is intentionally not refunded on a provider 502 (asgi.py:1366, documented wallet-drain defense) — can burn a legitimate user's daily AI quota under a flaky provider; worth a refund-on-provider-error product decision."
    - name: security
      grade: A
      ship_critical: true
      top_gaps:
        - "CAPTCHA is a built but NO-OP seam (src/security/captcha.py:53-71) — does not protect public forms until the owner sets TURNSTILE_SECRET + web sitekey + a native mobile widget; today's live bot defense is rate-limiting only."
        - "Per-account login lockout is still in-memory/per-instance (asgi.py:327) — less effective on serverless than the now-shared rate counters."
    - name: design-taste
      grade: A
      ship_critical: true
      top_gaps:
        - "Committed -mobile screenshots are the web app at a 390px viewport (visual-verification.spec.ts:18-21), NOT regenerated since 2026-07-03 — native-mobile taste is unverified by artifact."
        - "Zero screenshots of the ACTUAL native mobile app — native mobile visual proof remains zero (needs Expo/Detox/Maestro captures)."
    - name: store-readiness
      grade: C
      ship_critical: true
      top_gaps:
        - "No rendered store assets committed: docs/store/assets/ absent — no 1024x500 feature graphic, no store screenshot image files (A3/G7 FAIL)."
        - "Mobile IAP client not integrated: react-native-purchases absent from mobile/package.json; paywall.tsx:40,118 are deferral comments only (A4 StoreKit / G4 Play Billing FAIL); restore-purchases (A5) also blocked."
        - "Deploy config (vercel.json) is real + A-level, but the store half carries the 4 open FAILs; readiness gate self-reports C."
    - name: artifact-integrity
      grade: A+
      ship_critical: true
      top_gaps: []
    - name: business-case-strength
      grade: C
      ship_critical: true
      top_gaps:
        - "Team/coach/B2B2C seat tier — no Organization/Seat/Team model in src/db/models.py at all (highest-ARPA, lowest-CAC lever, entirely absent); the one lever with the math to flip the floor."
        - "Annual-first pricing is already presented-first (~2-5% ARPA, sub-floor); shipped Career+/referral/tailored-résumé/skill-gap levers diversify the wedge but don't floor-flip and are honestly uncredited in the projection."
        - "Honest planning median $57.5K < $100K floor (analysis/arr_base.py, floor_met_year1=false) — the correct pre-launch state, but readiness stays rejected on business-case grounds."
    - name: tests-evals
      grade: A
      ship_critical: false
      top_gaps:
        - "Coverage floor (setup.cfg fail_under=75) sits ~17pts below actual (92.21%) — a large regression could land silently green; ratchet toward ~88."
        - "Per-PR prep-pack eval is _FakeLLM structure-only (test_prep_pack_evals.py) — the real content-quality check is pytest live-marked, deselected per-PR (nightly-only, though it ran+passed this audit's env)."
    - name: performance
      grade: A
      ship_critical: false
      top_gaps:
        - "/api/analytics/pipeline (asgi.py:1980-2002) still runs an unbounded .all()+in-Python top-5 sort (fully batched, no N+1) — should be a SQL GROUP BY + ORDER BY ... LIMIT 5; low-severity."
  top_gaps:
    - "business-case-strength C: floor not met ($57.5K<$100K); shipped Pro levers diversify but don't floor-flip; team/B2B2C seat tier (highest ARPA) still unbuilt in src/db/models.py."
    - "store-readiness C: rendered store assets + screenshots missing; mobile IAP client (react-native-purchases/Play Billing) not integrated; 4 open ACCEPTANCE_AUDIT FAILs."
    - "design-taste A->A+: committed -mobile screenshots are web@390px, not regenerated since 2026-07-03; still no true native-mobile captures."
    - "security A->A+: CAPTCHA seam is no-op until owner connects; login lockout still in-memory per-instance."
    - "performance A->A+: unbounded-but-batched .all()+in-Python sort on /api/analytics/pipeline."
```
