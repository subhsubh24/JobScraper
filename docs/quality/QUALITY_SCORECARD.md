# QUALITY SCORECARD — Career Operator

> **Owner:** the INDEPENDENT Quality Auditor (maker ≠ checker). The factory loop CONSUMES
> this as DATA and must NOT author or overwrite it. Grades are backed by mechanical signals
> the auditor actually ran (see [QUALITY_RUBRIC.md](./QUALITY_RUBRIC.md)) plus file/line
> evidence. Grading method: 9 fresh, independent, adversarial per-dimension grader
> subagents (none wrote the product code), each running its own signal.

## Grade — 2026-07-11 (6th independent audit)

**Overall: B** (↑ from C) · **Ship gate met: NO.** This is a **recovery audit**: the
ship-critical **functional-reality regression that dominated the 2026-07-09 grade (D) is
resolved (D → A)**. The auditor re-probed the REAL Gemini endpoint with the live key —
`gemini-2.5-flash` now returns **200 "OK"** (it was a hard 404 two days ago), `gemini-flash-latest`
and `gemini-2.5-flash-lite` also return 200, and the live real-output eval suite
`tests/evals/test_ai_output_evals.py` now **passes 10/10** (was 9 failed / 1 passed). More
importantly the factory did not just wait for Google to un-kill the model: `src/llm.py:78`
now ships a real `resilient_chat_completion` that, on a 404 model-death **only**, falls back
through a curated verified-live chain (`gemini-flash-latest`, `gemini-2.5-flash-lite`) and
fails LOUD if the whole chain is dead — and a per-PR source-scan guard
(`tests/test_llm_nobypass_integration.py`) mechanically enforces that every AI workflow routes
through it (the sole raw `chat.completions.create` is the wrapper itself, `src/llm.py:97`).
`.env.example:11` was corrected from the dead model to the floating alias. Every AI endpoint
still degrades to an honest 503 when no key is configured. The monetized AI surface (mock
interview, coach, prep pack, cover letter, tailored résumé, salary-negotiation, learning plan)
works end-to-end against the live provider **and** is now resilient to a single model death.

Two more ship-critical dims moved up on real (evidence-backed) findings. **correctness A → A+**:
the persistent "provider 502 burns a legit user's daily AI slot with no refund" finding is
**fixed** — a symmetric `refund_llm_ceiling` (`asgi.py:491`) is wired into all 9 LLM endpoints'
failure branches (9 consume sites, 9 refund sites), correctly excluded from the success and
moderation paths, floored at 0 under `SELECT…FOR UPDATE`. **business-case-strength C → B**:
the highest-ARPA lever, the team/B2B2C seat tier, is now genuinely **built** — real
`Organization`/`OrganizationMember` models (`src/db/models.py:138,187`) + migration, a
quantity-based Stripe seat checkout + signature-verified webhook + seat-cap enforcement
(`src/org_billing.py`), owner-scoped endpoints (`asgi.py:1278-1386`), and 22 tests
(`tests/test_org_billing.py` + `test_org_hardening.py`). Honesty stays exemplary: the honest
un-gamed median `analysis/arr_base.py` → **57500** (< $100K floor), `floor_met_year1=false`,
and ZERO ARR credited to the not-yet-monetized levers.

**security** held at **A** with an improved basis (the in-memory login-lockout finding is fixed —
lockout is now DB-backed cross-instance, `asgi.py:373-431`; the new org/seat surface is
authz-clean with no entitlement bypass). **artifact-integrity** held at **A** with both prior
doc-lags fixed (ROADMAP coverage box now `fail_under=88`; `/api/jobs/import-preview` added to
ROUTE_INVENTORY). **design-taste A**, **tests-evals A** (coverage floor ratcheted 85→88),
**performance A+** — all unchanged, all backed. The two standing pre-launch gaps are
**store-readiness C** (unchanged — the same 4 open ACCEPTANCE_AUDIT FAILs) and business-case
still below the floor. **Ship gate stays NO** on two grounds: store-readiness C and
business-case B (both ship-critical, both below the A ship bar).

| Dimension | Ship-critical | Grade | Δ | One-line basis |
|---|---|---|---|---|
| functional-reality | ✅ | **A** | ▲ (D→A) | Live Gemini probe: `gemini-2.5-flash`→200 (was 404), `gemini-flash-latest`/`gemini-2.5-flash-lite`→200; `test_ai_output_evals.py`→**10 passed** (was 9 failed); resilient 404-only fallback `src/llm.py:78-112` wired into every AI workflow (enforced by `tests/test_llm_nobypass_integration.py`); `.env.example:11` fixed to `gemini-flash-latest`; 15/15 journeys pass; honest 503 without a key. Off A+ only by the code default still being the pinned `gemini-2.5-flash` (`src/llm.py:20`) — fully covered by the fallback, trivial nit. |
| correctness | ✅ | **A+** | ▲ (A→A+) | Persistent finding FIXED: `refund_llm_ceiling` (`asgi.py:491`) paired with `check_llm_ceiling` in all 9 LLM endpoints' failure branches (9/9), excluded from success + moderation, `SELECT…FOR UPDATE` floored at 0. Primitives green: bounded retry (`ingestion/base.py:22-55`), per-hop redirect SSRF (`url_guard.py:61-84`), zero-vector→0.5 (`scorer.py:63-66`), server-clamped mock scores (`llm_workflows.py:650-660`), idempotency-before-side-effects (`asgi.py:1411-1427`). `pytest -k "retry or ssrf or scorer or ceiling or rate"`→91 passed. Zero findings. |
| security | ✅ | **A** | = (improved basis) | Standing lockout finding FIXED — login lockout now DB-backed cross-instance (`asgi.py:373-431`). New org/seat tier authz-clean: `seats_purchased` webhook-only via verified `construct_event` (`asgi.py:1204-1213`, `org_billing.py`), every seat mutation owner-scoped (`asgi.py:1350,1379`), cap lock-enforced, entitlement flows to `users.tier` only via `recompute_user_tier` (Pro-only). No tracked secrets; CORS `[]` in prod; Stripe/RevenueCat sigs verified; targeted suite 98 passed. Off A+ by the SAME CAPTCHA no-op until `TURNSTILE_SECRET` connected (`captcha.py:69-71`). |
| design-taste | ✅ | **A** | = | Flagship surfaces genuinely native + designer-grade: mobile mock-interview real `SafeAreaView`/`Pressable`/`ActivityIndicator` with `radiogroup`/`alert`/`aria-live` a11y (`mobile/src/app/interview/[jobId].tsx`), single accent `#6366F1` (`theme.ts:12`), no emoji-as-icons, real loading/empty/error (web Skeleton + ErrorText+Retry, `focus-visible:ring`). Held off A+ by the SAME artifact gap: `-mobile` captures are still web@390px (`visual-verification.spec.ts:20,29`); zero true native captures; the interview/demo/readiness surfaces have NO rendered captures at any width. |
| store-readiness | ✅ | **C** | = | Vercel deploy config real/A-level (`vercel.json:3-16`), but the SAME 4 open ACCEPTANCE_AUDIT FAILs stand: A3/G7 (no rendered feature graphic/screenshots; `docs/store/assets/` absent, zero committed `.png`), A4/G4 (mobile IAP not integrated — `react-native-purchases` absent from `mobile/package.json`; `mobile/src/app/paywall.tsx:115-124` is a "coming soon" Alert stub with no charge/entitlement). `check_quality.py readiness`→FAIL. Zero of 4 FAILs closed. |
| artifact-integrity | ✅ | **A** | = (2 doc-lags fixed) | Both prior doc-lags FIXED: `ROADMAP.md:341` now `fail_under=88` matching `setup.cfg:21`; `/api/jobs/import-preview` now in `docs/ci/ROUTE_INVENTORY.md:59`. Spot-checks all map to real tested code: org seat tier (models+migration `b3d9e1f27a04`+endpoints), unique-org-owner migration `e5c1a9d7b243`, #353 entitlement-reconciliation test (`test_org_billing.py:360-412`) asserts real DB tier lifecycle. Honesty flags truthful (`floor_met_year1=false`, $100K box un-ticked, CAPTCHA no-op disclosed). Held off A+ by an honest-DIRECTION self-lag: the prior scorecard understated the now-built org tier (corrected here). Zero fabrications. |
| business-case-strength | ✅ | **B** | ▲ (C→B) | Highest-ARPA lever now BUILT not listed: `Organization`/`OrganizationMember` (`models.py:138,187`) + quantity-based Stripe seat checkout + verified webhook + seat-cap + owner-only endpoints (`org_billing.py`, `asgi.py:1278-1386`) + 22 tests. Honest un-gamed `analysis/arr_base.py`→**57500** (`business_case_lib.py:11`), `floor_met_year1=false`, ZERO ARR credited to seat/Career+/referral (anti-gaming, `BUSINESS_CASE.md:35,124`); `engine_pct=50` computed from ROADMAP checkbox ratios. Held at B: floor still honestly unmet — the built lever is not yet monetized (no admin UI, no live per-seat pricing, no validated B2B adoption), so no named lever yet produces a defensible median crossing $100K. |
| tests-evals | — | **A** | = (floor 85→88) | 609 backend pass @ **91.09% cov** (floor ratcheted 85→**88**, `setup.cfg:21`), 15 journeys, 62 evals (per-PR `-m "not live"`), live evals 10/10. Tests assert real outcomes (`journeys/test_core_journey.py:44-53` drives signup→PATCH; evals judge REAL Gemini output). New per-PR guards: `test_llm_nobypass_integration.py` (source-scan + real-workflow wiring) + `test_llm_fallback.py`. Held at A: real live-model DETECTION is still nightly-only (`ci.yml:28-30`, `nightly.yml`) — a whole-chain decommission would still be caught only nightly; `test_llm_fallback.py` is mocked so cannot catch a real dead model. Runtime impact is mitigated (fallback), detection latency is not. |
| performance | — | **A+** | = | `pytest -k "perf or n_plus or query"`→9 passed. A+ basis intact: `/api/analytics/pipeline` aggregates in-DB (`func.count`+`GROUP BY`+`func.avg`+`ORDER BY … LIMIT 5`, `asgi.py:2603-2658`), constant query count. New org/seat paths all bounded: `list_members` capped by `MAX_SEATS=200`, `_org_payload` batches member emails in one `User.id.in_(...)` (`asgi.py:1265-1270`), `seats_used` via `.count()`; per-request paid gate reads persisted `users.tier` — the org lookup runs ONLY inside event-driven `recompute_user_tier`, never on the hot path. Zero N+1, zero unbounded, zero findings. |

### Mechanical signals (auditor-run this audit, HEAD `9f119e5`)
- `flake8 .` → clean · `python3 -c "import asgi"` → ok (after `pip install -r requirements*.txt`)
- `pytest -q -m "not live" --cov` → **609 passed, 21 deselected, 91.09% cov** (setup.cfg floor **88**) · `pytest tests/journeys` → **15 passed** · `pytest tests/evals -m "not live"` → **62 passed**
- **`pytest tests/evals/test_ai_output_evals.py` (live key present) → 10 PASSED** (was 9 failed / 1 passed on 2026-07-09) — the monetized AI surface works against the REAL Gemini endpoint again
- Auditor direct probe (real `generativelanguage.googleapis.com` via live key): `gemini-2.5-flash`→**200 "OK"** (was 404 dead) · `gemini-flash-latest`→200 · `gemini-2.5-flash-lite`→200 · `gemini-2.0-flash`→404 dead · embedding `gemini-embedding-001` via `embedContent`→200 (dim 3072)
- `scripts/check_quality.py parse` → OK · `readiness` → **FAIL** (store-readiness C) · `scripts/check_blocks.py` → OK, `floor_met_year1=false`, **`engine_pct=50`** (was 0)
- `analysis/arr_base.py` → **57500** (< $100K floor) · no tracked secrets (`git ls-files | grep -iE '\.env$|secret|pem|credential|key$'` → empty) · CORS `[]` in prod
- `docs/store/assets/` absent · ACCEPTANCE_AUDIT 4 open FAILs (A3/A4/G4/G7) · no `react-native-purchases` in `mobile/package.json`
- 9 fresh subagent graders each ran their own signal + cited file/line (maker ≠ checker); web/mobile `tsc`/`lint`/`jest`/Playwright not re-run locally (node_modules absent) — relied on committed specs + required CI

### Top gaps to drive to A+ (ordered; ship-critical below-A first)
1. **store-readiness (C, ship-critical) — the top remaining blocker:** commit rendered store assets (1024×500 feature graphic, ≥2 screenshot image files, brand icon) + integrate the mobile IAP client (`react-native-purchases` + Play Billing + restore-purchases; `mobile/src/app/paywall.tsx:115` is a "coming soon" stub) to clear FAILs A3/A4/G4/G7. Both loop-buildable now; zero of 4 moved this cycle. (Issue #93)
2. **business-case-strength (B, ship-critical):** floor still unmet ($57.5K < $100K). The seat-tier BACKEND is built — now monetize it: a web/mobile org-admin surface, live per-seat pricing, and an honest cohort/pipeline signal so a named lever crosses the floor on un-gamed math (`floor_met_year1` → true). Only the backend + tests exist; no conversion path yet. (Issue #92)
3. **design-taste (A→A+):** regenerate the committed screenshots (the `-mobile` ones are web@390px) and add TRUE native-mobile captures + captures of the interview/demo/readiness surfaces (Expo/Detox/Maestro).
4. **tests-evals (A→A+):** add a per-PR (or CI-required, not nightly-only) real model-liveness / real-output smoke — the fallback mitigates a single model death at runtime, but a whole-chain decommission or output-quality regression is still detected only nightly.
5. **security (A→A+):** activate real bot-protection — CAPTCHA is a fail-closed Turnstile impl but a no-op until the owner connects `TURNSTILE_SECRET` (+ web sitekey + native widget); public forms rely on the rate limiter alone until then.
6. **functional-reality (A→A+):** align the code default `_DEFAULT_CHAT_MODEL` (`src/llm.py:20`) to the floating alias `gemini-flash-latest` so no pinned single-point-of-failure remains (the fallback already covers a re-decommission; trivial).
7. **artifact-integrity (A→A+):** no open items beyond routine doc/scorecard freshness (this audit corrects the prior self-lag on the org tier).

```yaml
QUALITY_SCORECARD:
  as_of: 2026-07-11
  overall: B
  ship_gate_met: false
  method: 9 independent adversarial per-dimension grader subagents (maker != checker); each ran its own mechanical signal + cited file/line evidence; auditor independently re-probed the REAL Gemini endpoint with the live key and confirmed the model recovery + fallback
  dimensions:
    - name: functional-reality
      grade: A
      ship_critical: true
      top_gaps:
        - "Code default _DEFAULT_CHAT_MODEL (src/llm.py:20) is still the pinned gemini-2.5-flash (the model that was decommissioned on 2026-07-09, now live again). Fully covered by the resilient 404-only fallback chain (src/llm.py:78-112) so this is a trivial non-blocking nit; aligning the default to the floating alias gemini-flash-latest would remove the last pinned single-point-of-failure."
    - name: correctness
      grade: A+
      ship_critical: true
      top_gaps: []
    - name: security
      grade: A
      ship_critical: true
      top_gaps:
        - "CAPTCHA/bot-protection on public register+login is a real fail-closed Turnstile impl but a NO-OP until the owner sets TURNSTILE_SECRET (+ web sitekey + native widget); today's live bot defense on public forms is rate-limiting alone (captcha.py:69-71)."
    - name: design-taste
      grade: A
      ship_critical: true
      top_gaps:
        - "Committed -mobile screenshots are the web app at 390px (visual-verification.spec.ts:20,29), not true native-mobile captures; zero Expo/native renders."
        - "The flagship surfaces (mock-interview, demo, readiness) have NO committed rendered captures at any width -> the strongest design work is unbacked by an artifact a vision model can inspect."
    - name: store-readiness
      grade: C
      ship_critical: true
      top_gaps:
        - "No rendered store assets: docs/store/assets/ absent -> no 1024x500 feature graphic, no store screenshot image files (A3/G7 FAIL). Zero committed .png."
        - "Mobile IAP client not integrated: react-native-purchases absent from mobile/package.json; mobile/src/app/paywall.tsx:115-124 is a 'coming soon' Alert stub with no charge/entitlement (A4/G4 FAIL); restore-purchases blocked. Loop-buildable; zero of 4 FAILs moved."
    - name: artifact-integrity
      grade: A
      ship_critical: true
      top_gaps:
        - "Both prior doc-lags fixed (ROADMAP coverage box now fail_under=88; /api/jobs/import-preview added to ROUTE_INVENTORY). Held off A+ only by an honest-direction self-lag: the prior scorecard understated the now-built org/seat tier (corrected in this audit). Zero fabrications."
    - name: business-case-strength
      grade: B
      ship_critical: true
      top_gaps:
        - "Floor still honestly unmet: analysis/arr_base.py -> 57500 < $100K; floor_met_year1=false. The highest-ARPA lever (team/B2B2C seat tier) BACKEND is now built (Organization/OrganizationMember + Stripe seat checkout + verified webhook + seat-cap + owner endpoints + 22 tests) but is not yet MONETIZED -- no admin UI, no live per-seat pricing, no validated B2B adoption -> no named lever yet produces a defensible median crossing $100K."
    - name: tests-evals
      grade: A
      ship_critical: false
      top_gaps:
        - "Real live-model DETECTION is still nightly-only (ci.yml:28-30, nightly.yml); a whole-chain decommission or output-quality regression would be caught only nightly. test_llm_fallback.py is mocked so cannot catch a real dead model. Runtime impact is now mitigated by the resilient fallback; detection latency is not. Add a per-PR/CI-required liveness or real-output smoke."
    - name: performance
      grade: A+
      ship_critical: false
      top_gaps: []
  top_gaps:
    - "store-readiness C (ship-critical, TOP BLOCKER): rendered store assets + screenshots missing; mobile IAP client (react-native-purchases/Play Billing) not integrated; 4 open ACCEPTANCE_AUDIT FAILs; zero moved this cycle (#93)."
    - "business-case-strength B (ship-critical): floor unmet ($57.5K<$100K); the seat-tier BACKEND is now built (C->B) but not yet monetized -- add org-admin UI + live per-seat pricing + a cohort signal so a lever crosses the floor on honest math; floor_met_year1 must flip true (#92)."
    - "design-taste A->A+: -mobile screenshots are web@390px; zero native captures; new flagship surfaces have no rendered captures."
    - "tests-evals A->A+: real live-model detection is nightly-only, so a whole-chain model regression is caught only nightly (the fallback mitigates a single-model death at runtime, not detection)."
    - "security A->A+: CAPTCHA no-op until the owner connects TURNSTILE_SECRET; public forms rely on the rate limiter alone."
    - "functional-reality A->A+ (RECOVERED from D): align the code default _DEFAULT_CHAT_MODEL to the floating alias gemini-flash-latest so no pinned single-point-of-failure remains (fallback already covers a re-decommission)."
```
