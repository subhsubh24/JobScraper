# QUALITY SCORECARD — Career Operator

> **Owner:** the INDEPENDENT Quality Auditor (maker ≠ checker). The factory loop CONSUMES
> this as DATA and must NOT author or overwrite it. Grades are backed by mechanical signals
> the auditor actually ran (see [QUALITY_RUBRIC.md](./QUALITY_RUBRIC.md)) plus file/line
> evidence. Grading method: 9 fresh, independent, adversarial per-dimension grader subagents
> (none wrote the product code), each running its own signal.

## Grade — 2026-07-16 (8th independent audit)

**Overall: B** (=) · **Ship gate met: NO.** No overall change, but real evidence-backed
internal movement in BOTH directions: the standing TOP ship-critical blocker **store-readiness
moved C → B** (its loop-buildable half — the mobile IAP client — genuinely landed, and the app
icon is confirmed bespoke), while **correctness moved A+ → A** on a new adversarially-surfaced
refund asymmetry. Overall holds at B because two ship-critical dims (store-readiness B,
business-case B) are still below the A ship bar.

**store-readiness C → A (real recovery, but a stale audit doc caps it at B).** The single biggest
loop-buildable store blocker is closed: #412 (`70f6ba7`) landed a REAL mobile IAP client —
`react-native-purchases ^10.4.3` (`mobile/package.json:26`) + `mobile/src/services/purchases.ts`
(genuine StoreKit/Play-Billing `purchasePlan`/`restorePurchases`/`identifyUser`, entitlement granted
SERVER-SIDE only, honest inert-when-unkeyed) + `mobile/src/app/paywall.tsx` wiring a live purchase
flow + App-Store-required Restore button (replacing the old "coming soon" Alert stub). An independent
grader also RENDERED `mobile/assets/images/icon.png` and confirmed it is a **bespoke** chevron-"A"
mark on a blueprint-grid field — NOT the Expo template the audit doc still claims. So the only
genuinely-unmet *software* artifact is store **screenshots**, which legitimately require a signed
native build (Human-Core, not producible on Linux). Held at **B not A** on two honest grounds:
(1) screenshots genuinely do not exist, so A3/G7 remain real open FAILs; and (2) **`docs/store/
ACCEPTANCE_AUDIT.md` is now STALE/inaccurate** — A4/G4 still read "mobile StoreKit/RevenueCat NOT
integrated"/"Play Billing NOT integrated" (false — the client is built; those rows should read
FAIL→OPEN, built-pending-signed-build), and G7 still says the icon is "still the Expo template"
(false). `check_quality.py readiness` → **FAIL** off that stale doc.

**correctness A+ → A (new adversarial finding).** An independent grader found a real, named,
non-blocking spend-ceiling asymmetry: `create_job` consumes a per-day embedding slot up front
(`asgi.py:1507`) but never refunds it on a Gemini **embedding OUTAGE** — `score_job` swallows the
embedding error and degrades to the neutral 0.5 heuristic (`src/ranking/scorer.py:209-216`), so the
outer catch never fires and the burned slot is silently lost even though no paid embedding call
succeeded. This contradicts the project's own stated refund principle ("count generations that
actually ran/cost money, not provider outages," `asgi.py:349-351`) that the `llm_daily` path honors.
It is defensible as a deliberate "job created unscored = graceful outcome" (`asgi.py:1527-1529`) and
`refund_llm_ceiling` can't be trivially reused (its leading `db.rollback()` would discard the pending
`JobPosting` insert) — so it is NON-blocking, but it is a genuine inconsistency, not zero-findings, so
A is the honest grade. (The prior A+ was "zero findings"; adversarial grading surfaced this pre-existing
latent asymmetry.)

**business-case B (=, honestly unmet).** `analysis/arr_base.py` → **57500** (500 subs × $115 blended
ARPA, `analysis/business_case_lib.py:11`; un-gamed — $115 sits below the $96 Pro / $192 Career+ annual
prices, an absolute sub count not an inflated conversion). `floor_met_year1=false`, `engine_pct=50`. The
team/seat B2B2C lever remains user-reachable end-to-end (`src/org_billing.py`, `/app/team`, `/pricing`
Team band, live Stripe-test coverage #383) but un-monetizable — `STRIPE_PRICE_TEAM_ANNUAL` owner-unset →
checkout 503 — and ZERO ARR is honestly credited to it or any other lever (Career+, referral, RevenueCat
IAP #412), correctly, since B2B demand is un-validated. No lever crosses $100K on honest math. Nothing
regressed or was gamed; #383/#401/#412 hardened billing infra without touching the projection.

**Unchanged this cycle:** **functional-reality A+** (zero findings — journeys assert the real fit-score
VALUE + tier flip + honest 403/501/503, entitlement round-trip verified: signature-verified webhook →
PREMIUM, forged sig → FREE, replay → 400; live Gemini probe 200/200/200, live AI-output evals 10/10).
**security A** (server-authoritative entitlement airtight incl. the new IAP path; off A+ by the SAME
CAPTCHA no-op until `TURNSTILE_SECRET`). **design-taste A** (source genuinely A-level web+native incl.
the #412 paywall; off A+ by the SAME native-capture artifact gap). **artifact-integrity A** (the prior
ROUTE_INVENTORY doc-lag is RESOLVED + now self-verifying via `tests/test_route_inventory_complete.py`;
held off A+ by a NEW same-class doc-lag — the stale ACCEPTANCE_AUDIT A4/G4/G7 text). **tests-evals A**
(#412's per-PR liveness guard is a real static config-drift guard but NOT a live smoke; whole-chain
decommission / output regression still caught nightly-only). **performance A** (#405 bounded the
`/api/jobs` scan → resolved; #389 tightened the Margin timeout 2.0s→1.0s — a real mitigation, but the
telemetry is still SYNCHRONOUS/blocking on the LLM hot path, so the A finding stands, just tighter).

**Ship gate stays NO** on two ship-critical grounds, both below the A ship bar: store-readiness **B**
and business-case **B**.

| Dimension | Ship-critical | Grade | Δ | One-line basis |
|---|---|---|---|---|
| functional-reality | ✅ | **A+** | = | `pytest tests/journeys/test_core_journey.py -v`→9/9; journeys assert fit-score VALUE (`test_core_journey.py:115,142`), honest 403 "Pro"/503-GEMINI paywall (164-171), 501 verify-purchase tier-stays-free (196-217). Entitlement round-trip in `test_billing.py`: sig-verified `checkout.session.completed`→PREMIUM+Subscription row (202-208); forged sig→400 FREE (235-248); HMAC replay→400 no-row (251-284). billing+prep+coach+ATS 47/47; live evals 10/10; live probe `gemini-flash-latest`/`gemini-2.5-flash`/`-lite`→**200**, dead `gemini-2.0-flash`→404 excluded. Zero findings. |
| correctness | ✅ | **A** | ▼ (A+→A) | `-k "retry or ssrf or scorer or ceiling or rate or idempot or dedup or webhook or replay"`→**129 passed**. SSRF re-validates every redirect hop, caps 5 (`url_guard.py:61-84`); zero-vector→0.5 (`scorer.py:101-103`); symmetric ceiling across all 9 sites with moderation-422 deliberately not refunded (`asgi.py:494-495`); insert-race retry #409 (`asgi.py:291-321`); idempotent webhook upserts. NEW non-blocking finding: `create_job` burns a per-day embedding slot (`asgi.py:1507`) but never refunds it on a Gemini embedding OUTAGE (`scorer.py:209-216` swallows→0.5), contradicting the project's own refund principle (`asgi.py:349-351`). |
| security | ✅ | **A** | = | `-k "auth or cors or captcha or webhook or idor or entitlement or billing or lockout"`→**130 passed, 11 skipped**. New IAP path server-authoritative: `purchases.ts` never flips tier locally (refetches /me), RevenueCat key public-by-design (lazy dynamic import), tier only via `/api/billing/revenuecat-webhook` verified with `secrets.compare_digest` (`mobile_billing.py:77`)→forged=401 grants nothing. Stripe `construct_event` + replay coverage; every surface `user.id`-scoped, org mutations via `owned_org` (no IDOR); DB-backed `SELECT…FOR UPDATE` daily ceiling; CORS `[]` prod. Off A+ by the SAME CAPTCHA no-op until `TURNSTILE_SECRET` (`captcha.py:53-71`). |
| design-taste | ✅ | **A** | = | Source genuinely A-level + cohesive: web `app/app/page.tsx` real skeleton/empty/error, honest free-tier quota (75-95), `role=tablist`/`focus-visible:ring`; mobile `(tabs)/index.tsx` + `interview/[jobId].tsx` real native (FlatList+RefreshControl+SafeArea, `EmptyState`/`ErrorBanner`), strong a11y (`accessibilityRole=radiogroup/radio`, live regions), Ionicons not emoji; one converged accent `#6366F1` (`mobile/src/theme.ts`=web indigo-500); #412 paywall real (selectable plan cards `accessibilityState`, Restore, honest degrade). Off A+ by the SAME gap: `visual-verification.spec.ts:20` labels a 390px WEB viewport "mobile"; zero native Expo captures of the flagship surfaces. |
| store-readiness | ✅ | **B** | ▲ (C→B) | #412 landed a REAL mobile IAP client (`react-native-purchases ^10.4.3` `package.json:26`; `services/purchases.ts` real purchase/restore/identify, server-side-only entitlement, inert-when-unkeyed; `paywall.tsx` live flow+Restore) — the biggest loop-buildable blocker, closed. Icon independently RENDERED = bespoke chevron-"A" (NOT the Expo template the doc claims). Only unmet *software* artifact = store **screenshots** (Human-Core signed build). NOT A because (1) screenshots genuinely absent (A3/G7 real FAILs) and (2) `ACCEPTANCE_AUDIT.md` is STALE — A4/G4 say IAP "NOT integrated" (false→should be OPEN), G7 says icon "still Expo template" (false). `check_quality.py readiness`→FAIL off the stale doc. Vercel deploy config A-level. |
| artifact-integrity | ✅ | **A** | = | Prior doc-lag RESOLVED + self-verifying: `tests/test_route_inventory_complete.py`→2 passed proves matrix set == `asgi.py` route set (50==50; the 4 formerly-missing routes present at `ROUTE_INVENTORY.md:107,109,111,140`). Honesty guards hold: `check_blocks`→`floor_met_year1=false` with `$100K` box unticked (`ROADMAP.md:545`); `check_quality parse` OK; CAPTCHA no-op disclosed; the #412 mobile-IAP tick is precise (client code only, keys+signed-build deferred to `PENDING_OPS.md:47`). Held off A+ by a NEW same-class doc-lag: `ACCEPTANCE_AUDIT.md` A4/G4/G7 text contradicts the code + its own sister docs (a conservative under-claim, not a fabrication). |
| business-case-strength | ✅ | **B** | = | `analysis/arr_base.py`→**57500** (< $100K; 500 subs × $115 ARPA `business_case_lib.py:11`, un-gamed — below the $96/$192 annual prices, an absolute sub count). `check_blocks`→`floor_met_year1=false`, `engine_pct=50` (matches `BUSINESS_CASE.md:158-162`). Team/seat lever built + user-reachable (`org_billing.py`, `/app/team`, /pricing band, live Stripe-test #383) but un-monetizable (`STRIPE_PRICE_TEAM_ANNUAL` owner-unset→503) with un-validated demand → ZERO ARR credited to any lever. No lever crosses $100K on honest math; nothing gamed or regressed. |
| tests-evals | — | **A** | = | 747 backend @ **91.80% cov** (floor 88, `setup.cfg`), 15 journeys, 147 non-live evals, live AI-output 10/10; evals pin exact goldens (`test_scoring_evals.py:46-58`→70.0/30.0/50.0/56.67). #412's per-PR guard runs under `-m "not live"` (`test_llm_fallback.py`, 10 passed) but is a STATIC config-drift guard — its own docstring concedes "NOT a live-deploy guard," it can't see the Vercel env, and its blocklist `_KNOWN_DECOMMISSIONED={"gemini-2.0-flash"}` knows only one id. Real live liveness/output detection stays nightly-only (`nightly.yml:28 -m live`; `ci.yml` deselects live). |
| performance | — | **A** | = | `-k "perf or n_plus or query or limit or margin"`→**153 passed**. #405 RESOLVED: `GET /api/jobs` (`asgi.py:1569-1595`) bounds to `_JOBS_LIST_DEFAULT_LIMIT=500` + `selectinload` (no N+1/unbounded); other lists bounded, analytics GROUP BY+top-5. #389 tightened Margin timeout 2.0s→1.0s clamped [0.1,5.0] with finite-guard (`llm.py:27-46`) — real mitigation. But the A finding STANDS: `_emit_call_metrics` still runs SYNCHRONOUSLY inline on success+error paths before returning (`llm.py:203-208`) and `_record_fit_outcome` blocking (`scorer.py:16-35`), stacking ~1.0s×N per multi-call workflow; a degraded ingest still inflates user p99. |

### Mechanical signals (auditor-run this audit, HEAD `add0e1c`)
- `flake8 .` → clean · `python3 -c "import asgi"` → ok (after `pip install -r requirements*.txt`)
- `pytest -q -m "not live" --cov` → **747 passed, 23 deselected, 91.80% cov** (setup.cfg floor **88**) · `pytest tests/journeys` → **15 passed** · `pytest tests/test_llm_fallback.py` → **10 passed**
- **`pytest tests/evals/test_ai_output_evals.py` (live key present) → 10 PASSED** (real Gemini output, all monetized AI surfaces, 181s)
- Auditor direct probe (real `generativelanguage.googleapis.com` via live key): default `gemini-flash-latest`→**200** · `gemini-2.5-flash`→200 · `gemini-2.5-flash-lite`→200 · dead `gemini-2.0-flash`→404 (correctly excluded)
- `scripts/check_quality.py parse` → OK · `readiness` → **FAIL** (store-readiness open FAILs, incl. rows the stale doc still marks FAIL) · `scripts/check_blocks.py` → OK, `floor_met_year1=false`, `engine_pct=50`
- `analysis/arr_base.py` → **57500** (< $100K floor) · no tracked secrets (`git ls-files | grep -iE '\.env$|secret|pem|credential|_key$'` → empty)
- `mobile/package.json:26` → `react-native-purchases ^10.4.3` (IAP client PRESENT) · `mobile/assets/images/icon.png` → bespoke (rendered, not Expo template) · `docs/store/assets/` → `feature-graphic.png` + README only, NO screenshots
- 9 fresh subagent graders each ran their own signal + cited file/line (maker ≠ checker); web/mobile `tsc`/`lint`/`jest`/Playwright not re-run locally (node_modules absent) — relied on committed specs + required CI

### Top gaps to drive to A+ (ordered; ship-critical below-A first)
1. **store-readiness (B, ship-critical) — top blocker:** (a) commit rendered store **screenshots** (≥2, from a signed native build — Human-Core) to close A3/G7; (b) **update the STALE `docs/store/ACCEPTANCE_AUDIT.md`** — A4/G4 should move FAIL→OPEN (IAP client is BUILT via #412, pending a signed-build sandbox charge), and G7's "still the Expo template" / "bespoke icon is owner work" language is now FALSE (the committed icon is bespoke). The stale doc is what keeps `check_quality.py readiness` FAILing on already-closed work. (Issue #93)
2. **business-case-strength (B, ship-critical):** floor honestly unmet ($57.5K < $100K, `floor_met_year1=false`). The seat tier is user-reachable — publish a live per-seat price (`STRIPE_PRICE_TEAM_ANNUAL`) and land validated B2B/cohort adoption so a named lever crosses the floor on un-gamed math (a market/validation step, not more building). (Issue #92)
3. **correctness (A→A+, NEW):** `create_job` burns a per-day embedding ceiling slot (`asgi.py:1507`) that is never refunded on a Gemini embedding OUTAGE (`scorer.py:209-216` swallows→0.5) — contradicting the project's own refund principle (`asgi.py:349-351`). Refund the slot on a real provider outage (or debit it only after a successful embedding), matching the `llm_daily` path.
4. **artifact-integrity (A→A+):** the SAME stale `ACCEPTANCE_AUDIT.md` (A4/G4 "NOT integrated", G7 "still Expo template") contradicts the code and its own sister docs (`ROADMAP.md:259`, `PENDING_OPS.md`). Correct the note text so the readiness audit stops misstating its own state. (Highest-leverage single fix — also unblocks #1.)
5. **performance (A→A+):** the Margin telemetry is still SYNCHRONOUS/blocking on the LLM hot path (`llm.py:203-208`, `scorer.py:16-35`), stacking ~1.0s×N per multi-call workflow; #389 tightened the timeout but not the architecture. Move the emit off the user-visible critical path (Vercel-survivable post-response drain / queue).
6. **design-taste (A→A+):** add TRUE native-mobile captures (Expo/Detox/Maestro) replacing the web@390px proxies (`visual-verification.spec.ts:20`); commit rendered native captures of the flagship surfaces (mock-interview, demo, readiness, team, the #412 paywall).
7. **tests-evals (A→A+):** add a per-PR (or CI-required, not nightly-only) real live-model liveness/output smoke — #412's static config guard can't see the deploy env or a newly-dead model, so a whole-chain decommission/output regression is still detected only nightly.
8. **security (A→A+):** activate real bot-protection — CAPTCHA is a fail-closed Turnstile impl but a no-op until the owner connects `TURNSTILE_SECRET` (+ web sitekey + native widget); public forms rely on the rate limiter alone until then.

```yaml
QUALITY_SCORECARD:
  as_of: 2026-07-16
  overall: B
  ship_gate_met: false
  method: 9 independent adversarial per-dimension grader subagents (maker != checker); each ran its own mechanical signal + cited file/line evidence; auditor independently re-probed the REAL Gemini endpoint with the live key (chain 200/200/200, dead model 404) and ran the live real-output eval suite (10 passed)
  dimensions:
    - name: functional-reality
      grade: A+
      ship_critical: true
      top_gaps: []
    - name: correctness
      grade: A
      ship_critical: true
      top_gaps:
        - "NEW non-blocking spend-ceiling asymmetry: create_job consumes a per-day embedding slot (asgi.py:1507) but never refunds it on a Gemini embedding OUTAGE -- score_job swallows the error and degrades to 0.5 (scorer.py:209-216), so the burned slot is silently lost though no paid embedding call succeeded. Contradicts the project's own refund principle (asgi.py:349-351) honored by the llm_daily path. Defensible as 'job created unscored = graceful', so non-blocking, but a genuine inconsistency."
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
        - "The flagship surfaces (mock-interview, demo, readiness, team, the #412 paywall) have NO committed native rendered captures -> the strongest design work is unbacked by an artifact a vision model can inspect."
    - name: store-readiness
      grade: B
      ship_critical: true
      top_gaps:
        - "No store screenshots (A3/G7): docs/store/assets/ has only feature-graphic.png + README; a signed native build is needed for >=2 screenshots (Human-Core, not producible on Linux)."
        - "docs/store/ACCEPTANCE_AUDIT.md is STALE: A4/G4 still say mobile StoreKit/RevenueCat/Play Billing 'NOT integrated' -- false, #412 landed the real client (react-native-purchases in mobile/package.json:26, services/purchases.ts, paywall.tsx); those rows should read FAIL->OPEN. G7 still says the icon is 'still the Expo template' -- false, the committed mobile/assets/images/icon.png is bespoke. The stale doc keeps check_quality.py readiness FAILing on already-closed work."
    - name: artifact-integrity
      grade: A
      ship_critical: true
      top_gaps:
        - "NEW same-class doc-lag: docs/store/ACCEPTANCE_AUDIT.md A4/G4 say 'mobile StoreKit/RevenueCat NOT integrated' / 'Play Billing NOT integrated' and G7 says the icon is 'still the Expo template', but #412 (70f6ba7) landed the RevenueCat client (mobile/package.json:26 + services/purchases.ts + paywall wiring + tests) and the committed icon is bespoke. A conservative under-claim (the FAIL status is defensible without a signed build), not a fabrication -- but the note text contradicts the code and its sister docs (ROADMAP.md:259, PENDING_OPS.md). The prior ROUTE_INVENTORY doc-lag is RESOLVED + self-verifying (tests/test_route_inventory_complete.py)."
    - name: business-case-strength
      grade: B
      ship_critical: true
      top_gaps:
        - "Floor still honestly unmet: analysis/arr_base.py -> 57500 < $100K; floor_met_year1=false. The seat tier is user-reachable end-to-end (org_billing.py + /app/team + /pricing Team band + live Stripe-test #383) but not MONETIZED -- STRIPE_PRICE_TEAM_ANNUAL owner-unset -> checkout 503, B2B demand un-validated -> ZERO ARR honestly credited to any lever, so none crosses $100K on un-gamed math."
    - name: tests-evals
      grade: A
      ship_critical: false
      top_gaps:
        - "Real live-model DETECTION is still nightly-only (ci.yml deselects live; nightly.yml cron -m live). #412 added a per-PR STATIC config-drift guard (test_llm_fallback.py) that asserts the committed default chain excludes a hardcoded-known-dead id, but its own docstring concedes it is NOT a live-deploy guard -- it can't see the Vercel env and its blocklist knows only gemini-2.0-flash, so a newly-decommissioned model or output regression is still caught only nightly. Add a per-PR/CI-required live liveness or real-output smoke."
    - name: performance
      grade: A
      ship_critical: false
      top_gaps:
        - "Margin telemetry (#368/#369/#382) still emits SYNCHRONOUSLY/blocking on the LLM hot path -- _emit_call_metrics (llm.py:203-208) + _record_fit_outcome (scorer.py:16-35), blocking by design (Vercel freezes post-response threads). #389 tightened the per-call timeout 2.0s->1.0s (real mitigation) but not the architecture, so a degraded ingest still inflates user p99, stacking ~1.0s*N per multi-call workflow. Move the emit off the user-visible critical path (post-response drain / queue). #405 resolved the unbounded /api/jobs scan."
  top_gaps:
    - "store-readiness B (ship-critical, TOP BLOCKER): store screenshots still absent (A3/G7, need a signed native build -- Human-Core); AND docs/store/ACCEPTANCE_AUDIT.md is STALE -- A4/G4 say IAP 'NOT integrated' (false, #412 built the client) + G7 says icon 'still Expo template' (false, it's bespoke), which keeps check_quality.py readiness FAILing on already-closed work (#93)."
    - "business-case-strength B (ship-critical): floor unmet ($57.5K<$100K, floor_met_year1=false); the seat tier is user-reachable but has no live per-seat price (STRIPE_PRICE_TEAM_ANNUAL owner-unset) and un-validated B2B demand, so no lever crosses the floor on honest math (#92)."
    - "correctness A+->A (NEW): create_job burns a per-day embedding ceiling slot (asgi.py:1507) never refunded on a Gemini embedding OUTAGE (scorer.py:209-216 swallows->0.5), contradicting the project's own refund principle (asgi.py:349-351). Non-blocking but a genuine inconsistency."
    - "artifact-integrity A->A+: the SAME stale ACCEPTANCE_AUDIT.md (A4/G4 'NOT integrated', G7 'still Expo template') contradicts the code + sister docs -- highest-leverage single fix, also unblocks the store-readiness readiness gate. Prior ROUTE_INVENTORY doc-lag RESOLVED."
    - "performance A->A+: Margin telemetry still synchronous/blocking on the LLM hot path (llm.py:203-208, scorer.py:16-35); #389 tightened the timeout but not the architecture -- move the emit off the critical path."
    - "design-taste A->A+: -mobile screenshots are web@390px; the flagship surfaces (mock-interview, demo, readiness, team, paywall) still have no true native captures."
    - "tests-evals A->A+: #412's per-PR liveness guard is static/config-only (can't see the deploy env or a newly-dead model); real live-model detection is still nightly-only."
    - "security A->A+: CAPTCHA no-op until the owner connects TURNSTILE_SECRET; public forms rely on the rate limiter alone."
```
