# QUALITY SCORECARD — Career Operator

> **Owner:** the INDEPENDENT Quality Auditor (maker ≠ checker). The factory loop CONSUMES
> this as DATA and must NOT author or overwrite it. Grades are backed by mechanical signals
> the auditor actually ran (see [QUALITY_RUBRIC.md](./QUALITY_RUBRIC.md)) plus file/line
> evidence. Grading method: 9 fresh, independent, adversarial per-dimension grader
> subagents (none wrote the product code), each running its own signal.

## Grade — 2026-07-09 (5th independent audit)

**Overall: C** (↓ from B) · **Ship gate met: NO.** A **ship-critical regression** dominates this
audit: **functional-reality dropped A+ → D**. The product's shipped default LLM model
`gemini-2.5-flash` (`src/llm.py:20`) has been **decommissioned by Google** — the auditor
reached the REAL Gemini endpoint with the live key and got a genuine `404 "This model
models/gemini-2.5-flash is no longer available"`, while `gemini-flash-latest` returned "OK"
on the same key (so this is a real model death, NOT a sandbox/proxy artifact). On 2026-07-05
these same live evals **passed**, so Google killed the model in the last four days and the
product pinned a now-dead default with **no live-model fallback**. Consequence: the entire
monetized AI surface — the VISION's north-star **mock-interview coaching** (#305/307/308),
the AI coach, prep packs, cover letters, tailored résumé, salary-negotiation, skill-gap
learning plans — **502s ("AI provider error")** against the live provider, a dead-end error
screen on the flagship paid features. Worse, `.env.example:8` steers a prod operator to the
**same dead model** (`# GEMINI_MODEL=gemini-2.5-flash`), and `gemini-2.0-flash` (the obvious
fallback) is **also dead**. The free/heuristic journeys (signup → dashboard → add job → fit
score → detail, the public demo, readiness, ATS import-preview) still work end-to-end (15/15
backend journeys pass), which keeps functional-reality off F.

Two other ship-critical dims were **tightened down A+ → A** on real (unchanged-code) findings —
correctness (the 502-burns-a-daily-AI-slot item is a real named finding, so it can't clear the
zero-findings A+ bar) and artifact-integrity (a stale ROADMAP coverage box + a ROUTE_INVENTORY
omission; honest-direction doc-lags, zero fabrications). One dim genuinely **improved A → A+**:
performance — #317 replaced `/api/analytics/pipeline`'s in-Python top-5 sort with real SQL
`GROUP BY` + `ORDER BY … LIMIT 5` (independently verified). The two standing pre-launch C's
(store-readiness, business-case) are **unchanged**. Ship gate stays NO on four grounds now:
functional-reality D, store-readiness C, business-case C.

| Dimension | Ship-critical | Grade | Δ | One-line basis |
|---|---|---|---|---|
| functional-reality | ✅ | **D** | ▼ (A+→D) | Default chat model `gemini-2.5-flash` (`src/llm.py:20`) is **decommissioned** — REAL Gemini 404 "no longer available" with the live key (auditor-run); `gemini-flash-latest` works on the same key (real model death, not proxy). Every LLM feature 502s: mock-interview `asgi.py:1952`, coach, prep pack, cover letter, tailored résumé, salary-negotiation, learning plan. `.env.example:8` steers ops to the SAME dead model; `gemini-2.0-flash` also dead; no fallback. Free/heuristic journeys (15/15 `tests/journeys`) still work → off F, not A/C. |
| correctness | ✅ | **A** | ▼ (A+→A, code unchanged) | Primitives all green + tested: `get_with_retry` bounded backoff w/ correct ConnectTimeout ordering (`src/ingestion/base.py:36-49`), per-hop redirect-SSRF (`url_guard.py:75-84`), zero-vector→0.5 (`scorer.py:63-66`), idempotency before side-effects (`asgi.py:1162-1178`), server-computed mock-interview scores clamped (`llm_workflows.py:648-665`). Held to A (not A+) by the persistent real finding: `check_llm_ceiling` consumes the daily AI slot BEFORE the call, so a provider 502 burns a legit user's quota with no refund (`asgi.py:423-429`, 1943-1952). Zero-findings bar not met. |
| security | ✅ | **A** | = | No tracked secrets; CORS `[]` in prod (`asgi.py:119-152`); #322 per-user limiter keeps expensive/auth surfaces on the pre-auth IP limiter (no new hole, `asgi.py:391-420`); public demo (#315) is key-free/local/deterministic → anon LLM spend structurally zero; Stripe `construct_event` + RevenueCat `compare_digest` verified server-side. Held off A+ by the SAME two: in-memory per-instance login lockout (`asgi.py:332`) + CAPTCHA no-op until `TURNSTILE_SECRET` connected. |
| design-taste | ✅ | **A** | = | New flagship surfaces are genuinely native + designer-grade: mobile mock-interview is real `StyleSheet`/`Pressable`/`SafeAreaView` on theme tokens (`mobile/src/app/interview/[jobId].tsx`), single accent `#6366F1` converged (`theme.ts:12`), zero emoji-as-icons, real loading/empty/error + a11y (aria-live, focus-visible, radiogroup). Held off A+ by unchanged artifact gap: `-mobile` captures are still web@390px (`visual-verification.spec.ts:18-21`), zero native captures, and NO rendered captures at all of the new interview/demo/readiness surfaces. |
| store-readiness | ✅ | **C** | = | Vercel deploy config is real/A-level (`vercel.json`), but the SAME 4 open ACCEPTANCE_AUDIT FAILs stand (A3/A4/G4/G7): `docs/store/assets/` still absent, no rendered feature graphic/screenshots, mobile IAP client absent (`react-native-purchases` not in `mobile/package.json`; `mobile/src/app/paywall.tsx:115` is a "coming soon" deferral stub). #324 embedded the AI-content disclosure (honest, but closes zero FAILs). `check_quality.py readiness` → FAIL. |
| artifact-integrity | ✅ | **A** | ▼ (A+→A) | Every spot-checked recently-ticked box maps to real, tested code (mock-interview model+migration+endpoints+evals; readiness `insights/readiness.py`; #322 diff; #320 import UI; #317 SQL; #293 floor 85). Disclosed gaps still honest (`floor_met_year1=false`, CAPTCHA no-op, SITE-GATE self-flagged). Held to A by two honest-direction doc-lags: ROADMAP Track-E coverage box still reads `fail_under=65/~69%` while setup.cfg is `85`/actual 91.8%; `docs/ci/ROUTE_INVENTORY.md` omits `/api/jobs/import-preview`. Zero fabrications. |
| business-case-strength | ✅ | **C** | = | Honest, un-gamed `analysis/arr_base.py`→**57500** < $100K floor; `floor_met_year1=false`. New funnel levers (public demo #315/316, referral, Career+ salary-negotiation) correctly UNCREDITED (anti-gaming stated `BUSINESS_CASE.md:79,88-100`). Only GTM packaging RESEARCH added for the seat tier (RiseSmart/INTOO comps) — no code. The highest-ARPA lever, the team/B2B2C seat (org) tier, is **still entirely unbuilt** (`src/db/models.py` has only a prose comment; `UserTier` binary FREE/PREMIUM). |
| tests-evals | — | **A** | = | 565 backend pass @ **91.82% cov** (floor ratcheted 75→85, #293), **62 evals** (was 46), 15 journeys — all green on the per-PR `-m "not live"` lane. Both prior A→A+ gaps materially closed: per-PR prep eval now runs the REAL pipeline + asserts persisted-artifact substance (#290); salary-negotiation eval parity (#291). Held at A (not A+) because the eval lane that would catch a live-model regression (`tests/evals/test_ai_output_evals.py`) is **nightly-only** — the `gemini-2.5-flash` decommission that broke the paid surface passes EVERY per-PR gate green; the exact "large regression lands silently green" hole. |
| performance | — | **A+** | ▲ (A→A+) | #317 verified GENUINELY closed: `/api/analytics/pipeline` now `func.count` + `GROUP BY status` + `func.avg` + `ORDER BY overall_score DESC LIMIT 5` in SQL, constant query count, no in-Python full-scan (`asgi.py:2354-2400`). #319 `create_job` re-serialize is one `joinedload` LEFT JOIN (4→1 queries). Readiness/demo endpoints pure/DB-free; caps intact (`le=500`), spend ceiling `.with_for_update()`, embedding DB-cache present. 22 perf/N+1 tests pass. No new unbounded query or N+1. |

### Mechanical signals (auditor-run this audit, HEAD `a70e20e`)
- `flake8 .` → clean · `python3 -c "import asgi"` → ok (after `pip install -r requirements*.txt`)
- `pytest -q -m "not live" --cov` → **565 passed, 21 deselected, 91.82% cov** (setup.cfg floor 85) · `pytest tests/journeys` → **15 passed** · `pytest tests/evals -m "not live"` → **62 passed**
- **`pytest tests/evals/test_ai_output_evals.py` (live key present) → 9 failed / 1 passed** — every LLM call `404 "This model models/gemini-2.5-flash is no longer available"` from the REAL Gemini endpoint
- Auditor direct probe (real `generativelanguage.googleapis.com` via live key): `gemini-2.5-flash`→404 dead · `gemini-2.0-flash`→404 dead · **`gemini-flash-latest`→"OK"** (proves endpoint+key real; model death is real, not proxy)
- `scripts/check_quality.py parse` → OK · `readiness` → **FAIL** (store-readiness C) · `scripts/check_blocks.py` → OK, `floor_met_year1=false`, `engine_pct=0`
- `analysis/arr_base.py` → **57500** (< $100K floor) · no tracked secrets (`git ls-files | grep -iE '\.env$|secret|pem|credential|key$'` → empty) · CORS `[]` in prod
- `docs/store/assets/` absent · ACCEPTANCE_AUDIT 4 open FAILs (A3/A4/G4/G7) · no `react-native-purchases` in `mobile/package.json`
- `grep -rn GEMINI_MODEL` (incl. `.github`, `vercel.json`) → only `.env.example:8` (= the dead model) — **no in-repo live-model override**
- 9 fresh subagent graders each ran their own signal + cited file/line (maker ≠ checker); web/mobile `tsc`/`lint`/`jest`/Playwright not re-run locally (node_modules absent) — relied on committed specs + required CI

### Top gaps to drive to A+ (ordered; ship-critical below-A first)
1. **functional-reality (D, ship-critical) — NEW, URGENT:** the shipped default chat model `gemini-2.5-flash` (`src/llm.py:20`) is decommissioned by Google → every monetized AI feature 502s against the live provider (mock interview, coach, prep pack, cover letter, tailored résumé, salary-negotiation, learning plan). FIX: bump the default to a current live model (`gemini-flash-latest` verified working, or the current GA flash), FIX `.env.example:8` which steers ops to the same dead model, and add a resilient fallback / startup model-liveness check so a single upstream model death can't silently 502 the whole paid surface. The live eval lane (`test_ai_output_evals.py`) must go green with a real key.
2. **store-readiness (C, ship-critical):** commit rendered store assets (1024×500 feature graphic, ≥2 screenshot image files, brand icon) + integrate the mobile IAP client (`react-native-purchases` + Play Billing + restore-purchases) to clear FAILs A3/A4/G4/G7. Both are loop-buildable now; neither moved. (Issue #93)
3. **business-case-strength (C, ship-critical):** floor unmet ($57.5K < $100K). Build the team/B2B2C seat (org) tier — the one named lever with the math to cross the floor (no `Organization`/`Seat` model; `UserTier` binary). Only sales research was added this cycle, not code. `floor_met_year1` must flip true on honest math. (Issue #92)
4. **correctness (A→A+):** refund (or don't pre-consume) the daily AI slot on a provider 502 (`asgi.py:423-429`, 1943-1952) — today a flaky provider burns a legit user's quota.
5. **artifact-integrity (A→A+):** refresh the stale ROADMAP Track-E coverage box (still `fail_under=65/~69%` vs the real 85/91.8%) and add `/api/jobs/import-preview` to `docs/ci/ROUTE_INVENTORY.md`.
6. **design-taste (A→A+):** regenerate the committed screenshots (the `-mobile` ones are web@390px) and add TRUE native-mobile captures + captures of the new interview/demo/readiness surfaces (Expo/Detox/Maestro).
7. **tests-evals (A→A+):** the model-decommission proves the gap — add a cheap per-PR (or CI-required, not nightly-only) model-liveness / real-output smoke so an upstream model death can't pass every merge gate green; consider ratcheting the coverage floor from 85 toward ~90.
8. **security (A→A+):** move the login lockout to the cross-instance store (`asgi.py:332`, still in-memory) + activate real bot-protection (CAPTCHA no-op until owner connects `TURNSTILE_SECRET`).

```yaml
QUALITY_SCORECARD:
  as_of: 2026-07-09
  overall: C
  ship_gate_met: false
  method: 9 independent adversarial per-dimension grader subagents (maker != checker); each ran its own mechanical signal + cited file/line evidence; auditor independently verified the model-decommission against the REAL Gemini endpoint
  dimensions:
    - name: functional-reality
      grade: D
      ship_critical: true
      top_gaps:
        - "Default chat model gemini-2.5-flash (src/llm.py:20) is DECOMMISSIONED by Google (real 404 'no longer available' with live key; gemini-flash-latest works on same key) -> every monetized AI feature 502s: mock interview (asgi.py:1952), coach, prep pack, cover letter, tailored resume, salary-negotiation, learning plan. NOT a proxy artifact."
        - ".env.example:8 steers prod operators to the SAME dead model; gemini-2.0-flash also dead; no live-model fallback or startup liveness check. Free/heuristic journeys (15/15 tests/journeys) still work, keeping this off F."
    - name: correctness
      grade: A
      ship_critical: true
      top_gaps:
        - "check_llm_ceiling consumes the daily AI slot BEFORE the LLM call (asgi.py:423-429), so a provider 502 burns a legit user's daily quota with no refund (e.g. answer_mock_interview asgi.py:1943->1952). Real named finding -> caps below the zero-findings A+ bar. Code unchanged since prior audit; grade corrected."
    - name: security
      grade: A
      ship_critical: true
      top_gaps:
        - "Per-account login lockout still in-memory/per-instance (asgi.py:332) -> a distributed brute-force spreads across serverless instances, each with an empty failure map; the rate counters are already cross-instance but the lockout is not."
        - "CAPTCHA is a real fail-closed Turnstile impl but a NO-OP until the owner sets TURNSTILE_SECRET + web sitekey + native widget; today's live bot defense is rate-limiting only."
    - name: design-taste
      grade: A
      ship_critical: true
      top_gaps:
        - "Committed -mobile screenshots are the web app at 390px (visual-verification.spec.ts:18-21), not regenerated since 2026-07-05; zero true native-mobile captures."
        - "The new flagship surfaces (mock-interview, demo, readiness) have NO committed rendered captures at all -> web+mobile taste on the north-star surfaces is unverifiable by artifact."
    - name: store-readiness
      grade: C
      ship_critical: true
      top_gaps:
        - "No rendered store assets: docs/store/assets/ absent -> no 1024x500 feature graphic, no store screenshot image files (A3/G7 FAIL)."
        - "Mobile IAP client not integrated: react-native-purchases absent from mobile/package.json; mobile/src/app/paywall.tsx:115 is a 'coming soon' deferral stub (A4/G4 FAIL); restore-purchases blocked. Loop-buildable; unmoved."
        - "Deploy config (vercel.json) is real + A-level, but the store half carries 4 open FAILs; #324 embedded the AI-content disclosure (honest) but closed zero FAILs."
    - name: artifact-integrity
      grade: A
      ship_critical: true
      top_gaps:
        - "ROADMAP Track-E coverage box is STALE: reads fail_under=65 / ~69% (PR #52) while setup.cfg is 85 and actual is 91.8% (code TIGHTER than doc -> honest-direction, not a false done)."
        - "docs/ci/ROUTE_INVENTORY.md omits /api/jobs/import-preview despite the route having import-journey.spec.ts coverage. Zero fabrications; two doc-lags cap below the zero-findings A+ bar."
    - name: business-case-strength
      grade: C
      ship_critical: true
      top_gaps:
        - "Team/coach/B2B2C seat tier still entirely unbuilt (no Organization/Seat/Team model in src/db/models.py; UserTier binary FREE/PREMIUM) -> the one lever with the math to flip the floor. Only GTM packaging RESEARCH added this cycle, no code."
        - "Honest planning median analysis/arr_base.py -> 57500 < $100K floor (floor_met_year1=false). New funnel levers (public demo, referral, Career+) correctly UNCREDITED (anti-gaming). Correct pre-launch state; readiness stays rejected on business-case grounds."
    - name: tests-evals
      grade: A
      ship_critical: false
      top_gaps:
        - "The eval lane that validates real AI output (tests/evals/test_ai_output_evals.py) is NIGHTLY-only; the gemini-2.5-flash decommission that broke the paid surface passes every per-PR merge gate green -> the exact 'large regression lands silently green' hole. Add a per-PR/CI-required model-liveness or real-output smoke."
        - "Coverage floor (setup.cfg fail_under=85) sits ~7pts below actual (91.8%) -> a moderate regression can still land green; consider ratcheting toward ~90."
    - name: performance
      grade: A+
      ship_critical: false
      top_gaps: []
  top_gaps:
    - "functional-reality D (NEW, ship-critical, URGENT): shipped default LLM model gemini-2.5-flash (src/llm.py:20) is decommissioned by Google -> the entire monetized AI surface 502s against the live provider. Bump to a live model, fix .env.example, add a fallback/liveness check."
    - "store-readiness C: rendered store assets + screenshots missing; mobile IAP client (react-native-purchases/Play Billing) not integrated; 4 open ACCEPTANCE_AUDIT FAILs (#93)."
    - "business-case-strength C: floor unmet ($57.5K<$100K); team/B2B2C seat tier (highest ARPA) still unbuilt in src/db/models.py; only sales research added (#92)."
    - "correctness A->A+: daily AI slot pre-consumed before the call, burned on a provider 502 with no refund (asgi.py:423-429)."
    - "artifact-integrity A->A+: stale ROADMAP coverage box (65/69% vs 85/91.8%) + ROUTE_INVENTORY omits /api/jobs/import-preview (honest-direction doc-lags)."
    - "design-taste A->A+: -mobile screenshots are web@390px; zero native captures; new flagship surfaces have no rendered captures."
    - "tests-evals A->A+: live real-output evals are nightly-only, so a live-model regression passes every per-PR gate green."
    - "security A->A+: in-memory per-instance login lockout; CAPTCHA no-op until owner connects."
```
