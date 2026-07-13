# QUALITY SCORECARD — Career Operator

> **Owner:** the INDEPENDENT Quality Auditor (maker ≠ checker). The factory loop CONSUMES
> this as DATA and must NOT author or overwrite it. Grades are backed by mechanical signals
> the auditor actually ran (see [QUALITY_RUBRIC.md](./QUALITY_RUBRIC.md)) plus file/line
> evidence. Grading method: 9 fresh, independent, adversarial per-dimension grader
> subagents (none wrote the product code), each running its own signal.

## Grade — 2026-07-13 (7th independent audit)

**Overall: B** (=) · **Ship gate met: NO.** No overall change, but real evidence-backed
internal movement in BOTH directions this cycle — one ship-critical dim finished its recovery
UP, one non-critical dim moved DOWN on a genuine new finding, and the two standing pre-launch
blockers are unchanged, correctly holding overall at B.

**functional-reality A → A+ (recovery complete).** The last remaining A→A+ holdback from the
2026-07-11 audit — the code default `_DEFAULT_CHAT_MODEL` still being the pinned
`gemini-2.5-flash` (the model Google decommissioned on 2026-07-09) — is **resolved**: #379
(`4f5348a`) changed it to the floating alias `gemini-flash-latest` (`src/llm.py:98`), removing
the last pinned single-point-of-failure. The auditor independently re-probed the REAL Gemini
endpoint with the live key: the default `gemini-flash-latest`→**200**, both concrete fallbacks
(`gemini-2.5-flash`, `gemini-2.5-flash-lite`)→200. The live real-output eval suite
`tests/evals/test_ai_output_evals.py`→**10 passed** (real Gemini output for all 12 monetized AI
surfaces), 15/15 journeys pass, entitlement round-trip verified (signature-verified webhook
grants PREMIUM, forged sig grants nothing), honest 503 without a key. Zero findings.

**performance A+ → A (real new finding).** The Margin cost-per-outcome telemetry shipped this
window (#368/#369/#382) emits metrics **synchronously and blocking** on the LLM hot path —
`_emit_call_metrics` (`src/llm.py:47-83`) and `_record_fit_outcome` (`src/ranking/scorer.py:16-35`)
run before the handler returns, each with a per-call `MarginMeter(timeout=2.0)`. It is blocking
BY DESIGN (Vercel freezes daemon threads post-response, #369), so a slow/degraded Margin ingest
directly inflates user-facing p99 on every monetized AI request (up to ~2s/call), and it **stacks
per LLM call** in multi-call workflows (cover-letter draft+refine = 2 emits; the fallback retry
loop emits per attempt). It is bounded, fail-safe, and gated off when `MARGIN_INGEST_URL`/`_KEY`
are unset, and the one true per-row emit loop (`score_all_jobs`) is explicitly NOT HTTP-wired — so
this is a named A-level finding, not a ship blocker, but it did not exist at the 2026-07-11 A+ grade,
so A is the honest grade.

**The two standing ship-critical blockers are UNCHANGED (both hold overall at B):**
**store-readiness C** — #370 rendered + committed a real, Play-spec-correct feature graphic
(`docs/store/assets/feature-graphic.png`, 1024×500 8-bit RGB, no alpha, guarded by
`tests/test_store_assets.py`) — genuine, designer-grade work — but it closes **zero of the 4 open
ACCEPTANCE_AUDIT FAILs**: A3/G7 still require store **screenshots** (need a signed native build) +
a bespoke app icon (still the Expo template); A4/G4 still require the mobile IAP client
(`react-native-purchases` absent from `mobile/package.json`; `mobile/src/app/paywall.tsx:115-124`
is still a "coming soon" `Alert` stub). `check_quality.py readiness`→FAIL.
**business-case B** — the highest-ARPA lever (team/B2B2C seat tier) is now genuinely **user-reachable
end-to-end** (a new web admin surface `web/app/app/team/page.tsx` #356 + a `/pricing` Team band
#363 + live Stripe-test seat coverage #383), but no per-seat price is published
(`STRIPE_PRICE_TEAM_ANNUAL` is owner PENDING_OPS/unset; checkout honestly returns 503), B2B demand
is un-validated, and the honest un-gamed `analysis/arr_base.py`→**57500** (< $100K floor),
`floor_met_year1=false`, with ZERO ARR credited to any unmonetized lever. An honest below-floor
pre-launch number cannot be graded above B.

**correctness held at A+** (zero findings: the three post-audit org-billing commits #361/#365/#380
are verified correct — lock-serialized add-member race→409, Stripe timeout→honest 503, unpaid async
checkout grants nothing; symmetric `check_llm_ceiling`/`refund_llm_ceiling` exact across all 9 metered
endpoints, excluded from success + moderation). **security A** (new org/seat surface authz-clean, no
IDOR/entitlement bypass; off A+ by the SAME CAPTCHA no-op until `TURNSTILE_SECRET` is connected).
**design-taste A** (the new feature graphic + seat-tier web surface are genuinely designer-grade; held
off A+ by the SAME artifact gap — the flagship surfaces still have no true native captures).
**artifact-integrity A** (honesty guards all hold, spot-checks all backed; a specific NEW doc-lag holds
it off A+ — #384 ROUTE_INVENTORY claims "every route in asgi.py" but omits ≥4 real tested routes:
`/api/ai-consent`, `/api/report`, `/api/referrals/me`, `/api/waitlist/confirm`). **tests-evals A**
(725 backend @ 91.42% cov, floor 88; real live-model DETECTION still nightly-only — the SAME A→A+ gap).

**Ship gate stays NO** on two grounds, both ship-critical, both below the A ship bar:
store-readiness **C** and business-case **B**.

| Dimension | Ship-critical | Grade | Δ | One-line basis |
|---|---|---|---|---|
| functional-reality | ✅ | **A+** | ▲ (A→A+) | Last pinned-default holdback RESOLVED: `_DEFAULT_CHAT_MODEL="gemini-flash-latest"` (`src/llm.py:98`, #379). Live probe: default `gemini-flash-latest`→**200**, fallbacks `gemini-2.5-flash`/`gemini-2.5-flash-lite`→200. `test_ai_output_evals.py`→**10 passed** (real Gemini, all 12 AI surfaces); 15/15 journeys; entitlement round-trip verified; honest 503 without a key; resilient 404-only fallback fails LOUD if whole chain dead. Zero findings. |
| correctness | ✅ | **A+** | = | Targeted suite `-k "retry or ssrf or scorer or ceiling or rate or idempot or dedup"`→**100 passed**; full→737 passed. Symmetric ceiling: `check_llm_ceiling` last guard before try, `refund_llm_ceiling` in all 9 provider-failure branches, excluded from success + `ModeratedContentError`→422 (`asgi.py:491-503,1780-2481`). Post-audit commits verified correct: #361 lock-serialized add-member race→409 (`org_billing.py:174-219`), #365 Stripe timeout→honest 503, #380 unpaid async checkout grants nothing. Per-hop redirect SSRF (`url_guard.py:75-84`), zero-vector→0.5 (`scorer.py:100-103`). Zero findings. |
| security | ✅ | **A** | = | No tracked secrets (`git ls-files`→empty); targeted suite **107 passed**. CORS `[]` in prod (`asgi.py:120`); DB-backed cross-instance login lockout (`asgi.py:373-429`); Stripe `construct_event` + RevenueCat `compare_digest` sigs verified server-side. New org/seat surface authz-clean: all mutations owner-scoped via `owned_org` (no IDOR), `seats_purchased` webhook-only, seat cap lock-enforced, entitlement only via `recompute_user_tier`. Off A+ by the SAME CAPTCHA no-op until owner sets `TURNSTILE_SECRET` (`captcha.py:53-71`). |
| design-taste | ✅ | **A** | = | New feature graphic (`scripts/store/feature_graphic.html`→`feature-graphic.png`) is genuinely bespoke (masked grid, single accent, one focal point — not slop); new seat-tier surface `web/app/app/team/page.tsx` has real loading/empty/error + a11y; single accent `#6366F1`, no emoji-as-icons, real icon sets. Held off A+ by the SAME artifact gap: `-mobile` captures are still web@390px (`visual-verification.spec.ts:20`); the flagship surfaces (mock-interview, demo, readiness, and now team) have NO committed native rendered captures. |
| store-readiness | ✅ | **C** | = | #370 committed a REAL feature graphic (`docs/store/assets/feature-graphic.png`, 1024×500 8-bit RGB no-alpha, guarded by `test_store_assets.py`) — but it closes ZERO of the 4 open ACCEPTANCE_AUDIT FAILs: A3/G7 still need store screenshots (signed native build) + a bespoke app icon (still Expo template); A4/G4 still need the mobile IAP client (`react-native-purchases` absent from `mobile/package.json`; `paywall.tsx:115-124` is a "coming soon" Alert stub). `check_quality.py readiness`→FAIL. Vercel deploy config remains A-level. |
| artifact-integrity | ✅ | **A** | = | Honesty guards hold: `floor_met_year1=false`, `engine_pct=50`, `arr_base`→57500, no $100K box ticked, CAPTCHA no-op + mobile-IAP-not-built honestly disclosed. Spot-checks all backed: #382 Margin telemetry (real, fail-safe), #383 live seat coverage, #379 floating alias, #370 feature graphic all map to real tested code. Held off A+ by a NEW specific doc-lag: #384 `ROUTE_INVENTORY.md` claims "every route in asgi.py" but omits ≥4 real tested routes (`/api/ai-consent`, `/api/report`, `/api/referrals/me`, `/api/waitlist/confirm`). Zero fabrications. |
| business-case-strength | ✅ | **B** | = | Highest-ARPA lever now genuinely USER-REACHABLE end-to-end: web admin surface `web/app/app/team/page.tsx` (#356) + `/pricing` Team band (#363) + live Stripe-test seat coverage (#383) atop the built `Organization`/`OrganizationMember` backend. But floor still honestly unmet: `arr_base`→**57500** < $100K, `floor_met_year1=false`, ZERO ARR credited to seat/Career+/referral. No per-seat price published (`STRIPE_PRICE_TEAM_ANNUAL` owner-unset → 503), B2B demand un-validated → no named lever produces a defensible honest median crossing $100K. Margin instrumentation (#368/#382) is honest, feeds no ARR number. |
| tests-evals | — | **A** | = | 725 backend pass @ **91.42% cov** (floor 88, `setup.cfg:22`), 15 journeys, 147 evals (`-m "not live"`), live evals 10/10. Tests assert real OUTCOMES (`journeys/test_core_journey.py` asserts fit-score VALUE + tier flip + honest 403/501/503; `test_scoring_evals.py` pins exact golden 70.0/30.0/50.0; live evals judge REAL Gemini output + honesty ordering). Per-PR guards `test_llm_nobypass_integration.py` (source-scan + real-workflow wiring) strong. Held at A: real live-model DETECTION still nightly-only (`ci.yml` runs `-m "not live"`; `nightly.yml` cron `-m live`); `test_llm_fallback.py` mocked → a whole-chain decommission caught only nightly. |
| performance | — | **A** | ▼ (A+→A) | NEW finding: Margin telemetry (#368/#369/#382) emits SYNCHRONOUSLY/blocking on the LLM hot path — `_emit_call_metrics` (`src/llm.py:47-83`) + `_record_fit_outcome` (`scorer.py:16-35`), per-call `MarginMeter(timeout=2.0)`, blocking by design (Vercel freezes post-response threads) — so a degraded Margin ingest inflates user p99 up to ~2s/call, stacking per LLM call. Bounded + fail-safe + gated off when unconfigured, and `score_all_jobs` batch loop is NOT HTTP-wired, so not ship-critical. Otherwise green: `-k "perf or n_plus or query"`→9 passed; `/api/analytics/pipeline` in-DB GROUP BY+LIMIT; token-resolution `joinedload` (#362); org paths bounded (`MAX_SEATS=200`, batched `User.id.in_(...)`). |

### Mechanical signals (auditor-run this audit, HEAD `b221a03`)
- `flake8 .` → clean · `python3 -c "import asgi"` → ok (after `pip install -r requirements*.txt`)
- `pytest -q -m "not live" --cov` → **725 passed, 23 deselected, 91.42% cov** (setup.cfg floor **88**) · `pytest tests/journeys` → **15 passed** · `pytest tests/evals -m "not live"` → **147 passed**
- **`pytest tests/evals/test_ai_output_evals.py` (live key present) → 10 PASSED** (real Gemini output for all 12 monetized AI surfaces)
- Auditor direct probe (real `generativelanguage.googleapis.com` via live key): default `gemini-flash-latest`→**200** · `gemini-2.5-flash`→200 · `gemini-2.5-flash-lite`→200 · `gemini-2.0-flash`→404 dead (not in the default chain)
- `scripts/check_quality.py parse` → OK · `readiness` → **FAIL** (store-readiness C) · `scripts/check_blocks.py` → OK, `floor_met_year1=false`, `engine_pct=50`
- `analysis/arr_base.py` → **57500** (< $100K floor) · no tracked secrets (`git ls-files | grep -iE '\.env$|secret|pem|credential|key$'` → empty) · CORS `[]` in prod
- `docs/store/assets/` → `feature-graphic.png` (1024×500) + README only, NO screenshots/icon · ACCEPTANCE_AUDIT 4 open FAILs (A3/A4/G4/G7) · no `react-native-purchases` in `mobile/package.json`
- 9 fresh subagent graders each ran their own signal + cited file/line (maker ≠ checker); web/mobile `tsc`/`lint`/`jest`/Playwright not re-run locally (node_modules absent) — relied on committed specs + required CI

### Top gaps to drive to A+ (ordered; ship-critical below-A first)
1. **store-readiness (C, ship-critical) — the top remaining blocker:** commit rendered store **screenshots** (≥2, from a signed native build) + a **bespoke app icon** (replace the Expo template) and integrate the **mobile IAP client** (`react-native-purchases` + Play Billing + restore-purchases; `mobile/src/app/paywall.tsx:115` is still a "coming soon" stub) to clear FAILs A3/A4/G4/G7. #370's feature graphic is real progress but closed zero FAILs. (Issue #93)
2. **business-case-strength (B, ship-critical):** floor still honestly unmet ($57.5K < $100K, `floor_met_year1=false`). The seat tier is now user-reachable — monetize it for real: publish a live per-seat price (`STRIPE_PRICE_TEAM_ANNUAL`), then produce an honest cohort/pipeline signal so a named lever crosses the floor on un-gamed math. (Issue #92)
3. **performance (A→A+, NEW this cycle):** the synchronous/blocking Margin telemetry on the LLM hot path (`src/llm.py:47-83`, `scorer.py:16-35`) adds up to ~2s/call user-facing tail-latency, stacking per LLM call. Move it to a bounded queue / ingest-side async, or tighten the timeout, so a degraded Margin ingest never inflates p99 on a paid AI request.
4. **artifact-integrity (A→A+):** #384 `docs/ci/ROUTE_INVENTORY.md` asserts "every route in asgi.py" but omits ≥4 real tested routes (`/api/ai-consent`, `/api/report`, `/api/referrals/me`, `/api/waitlist/confirm`) — add the rows so the doc's self-description matches the real surface.
5. **design-taste (A→A+):** add TRUE native-mobile captures (Expo/Detox/Maestro) replacing the web@390px proxies, and commit rendered captures of the flagship surfaces (mock-interview web+native, demo, readiness, the new team page).
6. **tests-evals (A→A+):** add a per-PR (or CI-required, not nightly-only) real model-liveness / real-output smoke — the fallback mitigates a single model death at runtime, but a whole-chain decommission or output-quality regression is still detected only nightly.
7. **security (A→A+):** activate real bot-protection — CAPTCHA is a fail-closed Turnstile impl but a no-op until the owner connects `TURNSTILE_SECRET` (+ web sitekey + native widget); public forms rely on the rate limiter alone until then.

```yaml
QUALITY_SCORECARD:
  as_of: 2026-07-13
  overall: B
  ship_gate_met: false
  method: 9 independent adversarial per-dimension grader subagents (maker != checker); each ran its own mechanical signal + cited file/line evidence; auditor independently re-probed the REAL Gemini endpoint with the live key and ran the live real-output eval suite (10 passed)
  dimensions:
    - name: functional-reality
      grade: A+
      ship_critical: true
      top_gaps: []
    - name: correctness
      grade: A+
      ship_critical: true
      top_gaps: []
    - name: security
      grade: A
      ship_critical: true
      top_gaps:
        - "CAPTCHA/bot-protection on public register+login is a real fail-closed Turnstile impl but a NO-OP until the owner sets TURNSTILE_SECRET (+ web sitekey + native widget); today's live bot defense on public forms is rate-limiting alone (captcha.py:53-71)."
    - name: design-taste
      grade: A
      ship_critical: true
      top_gaps:
        - "Committed -mobile screenshots are the web app at 390px (visual-verification.spec.ts:20), not true native-mobile captures; zero Expo/native renders."
        - "The flagship surfaces (mock-interview, demo, readiness, and the new team page) have NO committed native rendered captures -> the strongest design work is unbacked by an artifact a vision model can inspect."
    - name: store-readiness
      grade: C
      ship_critical: true
      top_gaps:
        - "No store screenshots (A3/G7): docs/store/assets/ has only feature-graphic.png + README; a signed native build is needed for ≥2 screenshots. Bespoke app icon also missing (mobile/assets/images/icon.png still Expo template)."
        - "Mobile IAP client not integrated (A4/G4): react-native-purchases absent from mobile/package.json; mobile/src/app/paywall.tsx:115-124 is a 'coming soon' Alert stub with no charge/entitlement; restore-purchases blocked. #370's feature graphic closed ZERO of the 4 open FAILs."
    - name: artifact-integrity
      grade: A
      ship_critical: true
      top_gaps:
        - "NEW doc-lag: #384 docs/ci/ROUTE_INVENTORY.md claims 'a COMPLETE map: every route in asgi.py' but omits >=4 real tested routes: /api/ai-consent (grant/revoke), /api/report, /api/referrals/me, /api/waitlist/confirm. Underlying endpoints + proving tests all exist and pass, so it is a doc-completeness overclaim, not a fabricated tick. Add the rows to match the real ~49-route surface."
    - name: business-case-strength
      grade: B
      ship_critical: true
      top_gaps:
        - "Floor still honestly unmet: analysis/arr_base.py -> 57500 < $100K; floor_met_year1=false. The seat tier is now user-reachable end-to-end (web admin surface #356 + /pricing Team band #363 + live Stripe-test coverage #383) but not yet MONETIZED -- no published per-seat price (STRIPE_PRICE_TEAM_ANNUAL owner-unset -> checkout 503), no validated B2B adoption -> no named lever produces a defensible median crossing $100K."
    - name: tests-evals
      grade: A
      ship_critical: false
      top_gaps:
        - "Real live-model DETECTION is still nightly-only (ci.yml runs -m 'not live'; nightly.yml cron -m live); a whole-chain decommission or output-quality regression would be caught only nightly. test_llm_fallback.py is mocked so cannot catch a real dead model. Add a per-PR/CI-required liveness or real-output smoke."
    - name: performance
      grade: A
      ship_critical: false
      top_gaps:
        - "NEW: Margin telemetry (#368/#369/#382) emits synchronously/blocking on the LLM hot path -- _emit_call_metrics (src/llm.py:47-83) + _record_fit_outcome (scorer.py:16-35), per-call MarginMeter(timeout=2.0), blocking by design (Vercel freezes post-response threads). A degraded Margin ingest inflates user p99 up to ~2s/call, stacking per LLM call. Bounded + fail-safe + gated off when unconfigured; not ship-critical. Move to a bounded queue / ingest-side async."
  top_gaps:
    - "store-readiness C (ship-critical, TOP BLOCKER): store screenshots + bespoke app icon missing; mobile IAP client (react-native-purchases/Play Billing) not integrated; 4 open ACCEPTANCE_AUDIT FAILs (A3/A4/G4/G7); #370 feature graphic was real but closed zero FAILs (#93)."
    - "business-case-strength B (ship-critical): floor unmet ($57.5K<$100K, floor_met_year1=false); the seat tier is now user-reachable (web admin surface + /pricing band + Stripe-test coverage) but has no live per-seat price and no validated B2B adoption, so no lever crosses the floor on honest math (#92)."
    - "performance A+->A (NEW): synchronous/blocking Margin telemetry on the LLM hot path adds up to ~2s/call user-facing tail-latency, stacking per LLM call (src/llm.py:47-83, scorer.py:16-35)."
    - "artifact-integrity A->A+: #384 ROUTE_INVENTORY claims 'every route' but omits >=4 real tested routes (/api/ai-consent, /api/report, /api/referrals/me, /api/waitlist/confirm)."
    - "design-taste A->A+: -mobile screenshots are web@390px; the flagship surfaces (mock-interview, demo, readiness, team) still have no true native captures."
    - "tests-evals A->A+: real live-model detection is nightly-only, so a whole-chain model regression is caught only nightly (the fallback mitigates a single-model death at runtime, not detection)."
    - "security A->A+: CAPTCHA no-op until the owner connects TURNSTILE_SECRET; public forms rely on the rate limiter alone."
```
