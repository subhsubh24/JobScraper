# QUALITY SCORECARD — Career Operator

> **Owner:** the INDEPENDENT Quality Auditor (maker ≠ checker). The factory loop CONSUMES
> this as DATA and must NOT author or overwrite it. Grades are backed by mechanical signals
> the auditor actually ran (see [QUALITY_RUBRIC.md](./QUALITY_RUBRIC.md)) plus file/line
> evidence. Grading method: 9 fresh, independent, adversarial per-dimension grader subagents
> (none wrote the product code), each running its own signal.

## Grade — 2026-07-23 (9th independent audit)

**Overall: B** (=) · **Ship gate met: NO.** No overall change since the 8th audit, but real
evidence-backed internal movement: **artifact-integrity moved A → A+** (the stale
`ACCEPTANCE_AUDIT.md` doc-lag that capped it is genuinely CLOSED, #419), and the 8th-audit
**correctness finding is RESOLVED** (#419/#458 refund the embedding slot on outage AND on a
no-spend throw). Overall holds at **B** because the SAME two ship-critical dims —
**store-readiness B** and **business-case B** — are still below the A ship bar, both for reasons
outside the loop's reach (Human-Core signed-build screenshots; un-validated B2B demand + an
owner-unset seat price).

**artifact-integrity A → A+ (the doc-lag closed).** The single item that held it at A last
cycle — `docs/store/ACCEPTANCE_AUDIT.md` A4/G4 reading mobile IAP "NOT integrated" and G7
reading the icon "still the Expo template", both false after #412 — was corrected by #419
(`2f5b4ad`). Grep for "NOT integrated" / "still the Expo template" over the audit doc now returns
nothing; A4/G4 read **OPEN** ("client integrated; sandbox round-trip pending", `ACCEPTANCE_AUDIT.md:33,49`)
and G7 states the icon is "bespoke … NOT the Expo template" (`:52`). The old phrases survive only
inside this scorecard's / QUALITY_MEMORY's own historical record (quoting the now-fixed finding),
not as live contradictions. Spot-checked ticks all back to real artifacts (#465 team read-only lock
`web/app/app/team/page.tsx:211`; #463 job-status serialize latch `web/app/app/jobs/[id]/page.tsx:100`
+ mobile twin; IAP client `mobile/package.json:26`). Honesty guards hold (`floor_met_year1=false`
with the $100K box UNticked `ROADMAP.md:555`; CAPTCHA no-op disclosed; `check_blocks`/`check_quality parse`
OK; `test_route_inventory_complete.py`→2 passed). Zero findings → A+.

**correctness A (=) — old finding fixed, one NEW non-blocking finding.** The 8th-audit finding
(a burned `score_daily` embedding slot never refunded on a Gemini embedding OUTAGE) is genuinely
CLOSED: #419 added `JobScorer.embedding_failed` (`scorer.py:243`) + a post-commit `_refund_counter`
(`asgi.py:1611-1613`), and #458 extended it to the THROW path, refunding only when
`_billable_embeddings == 0` (`asgi.py:1592-1593`) — with load-bearing, revert-provable regression
tests asserting the `RateCounter` row nets to 0 on outage (`test_scoring_ceiling.py:160`) and on a
no-spend throw (`:210`), and staying burned on real spend (`:250`, asserts `calls == 2`). That fix
alone would earn A+. It holds at **A** on a NEW adversarially-surfaced, non-blocking inconsistency:
the `create_job` dedup guard is a read-then-write TOCTOU (`asgi.py:1497-1512`, `.first()` then INSERT)
with **no backing DB unique constraint** — `JobPosting.__table_args__` declares only a *non-unique*
`Index("ix_job_user_company")` (`src/db/models.py:344-346`), no `UniqueConstraint(user_id,title,company_name,url)`.
Two truly-simultaneous identical POSTs both pass `existing is None` and both INSERT, double-firing
exactly the side-effects the guard's own comment claims to prevent — in contrast to the `score_daily`
counter, which IS concurrency-safe via `SELECT … FOR UPDATE`. Non-blocking (client-side double-submit
serialization #463 + sequential-retry both catch the common cases; only genuinely concurrent requests
slip through), but a real named inconsistency, so A not A+.

**store-readiness B (=) — the stale-doc half is fixed; the Human-Core half persists.** Last cycle
held it at B on TWO grounds: (1) store SCREENSHOTS genuinely absent (A3/G7 real FAILs, need a signed
native build) and (2) the STALE audit doc. Ground (2) is now RESOLVED by #419 (see artifact-integrity).
Ground (1) genuinely persists: `docs/store/assets/` holds only `feature-graphic.png` + `README.md` —
no screenshots; A3 (`ACCEPTANCE_AUDIT.md:32`) and G7 (`:52`) remain **FAIL**, and the audit's own
verdict is "Submission readiness: NO" (`:80`). Store screenshots require a signed native build (RevenueCat
keys + store products + an EAS signed build — Human-Core, not producible on Linux; honestly tracked in
`PENDING_OPS.md:47-64`). Everything the Linux factory *can* produce is done (Vercel deploy config
`vercel.json`; the real IAP client `mobile/src/services/purchases.ts` + Restore `paywall.tsx:253`; the
feature graphic + bespoke icon). The rubric requires ZERO open FAILs for A; two real open FAILs remain,
so **B** is the honest call — the Human-Core carve-out does not erase a real, honestly-carried FAIL.
`check_quality.py readiness`→FAIL (now off the scorecard's own B grade, a self-referential gate, not a
false doc claim).

**business-case B (=, honestly unmet).** `analysis/arr_base.py` → **57500** (500 subs × $115 blended
ARPA, `business_case_lib.py:9-13` — $115 sits between the real $96 Pro / $192 Career+ annual prices, an
absolute sub count, NOT an inflated conversion). `floor_met_year1=false`, `engine_pct=50`. The team/seat
B2B2C lever remains user-reachable end-to-end (`src/org_billing.py`, `/app/team`, `/pricing` Team band,
live Stripe-test #383) but un-monetizable — `STRIPE_PRICE_TEAM_ANNUAL` owner-unset → `price_id_for_org_plan`
raises `BillingNotConfigured` → checkout 503 (`org_billing.py:76-83`) — and B2B demand is un-validated,
so ZERO ARR is honestly credited to it or any other lever (Career+, referral, RevenueCat IAP). No lever
crosses $100K on honest math. Nothing regressed or was gamed; the #452–#467 billing commits are
test-nets / race+serialization hardening, not a new floor-lever.

**Unchanged this cycle (all re-verified mechanically):** **functional-reality A+** (`pytest tests/journeys`→15
passed; billing round-trip→19 passed; **live AI-output evals 10/10 in 188s** — journeys assert real
fit-score VALUE, DB tier flip, honest 403/501/503, forged sig→400 FREE, replay→400 no-row).
**security A** (149 passed/11 skipped; RevenueCat `compare_digest` `mobile_billing.py:77`, Stripe
`construct_event`, CORS `[]` prod, SSRF redirect re-validation, DB `FOR UPDATE` ceiling, no IDOR, no
tracked secrets — off A+ by the SAME CAPTCHA no-op until `TURNSTILE_SECRET`). **design-taste A**
(source genuinely A-level web+native, single accent `#6366F1`, Ionicons-not-emoji, real a11y — off A+
by the SAME artifact gap: zero TRUE native Expo captures; `visual-verification.spec.ts:20` still labels a
390px WEB viewport "mobile"). **tests-evals A** (787 passed @ **92.48% cov**, floor 88; evals pin EXACT
numeric goldens `test_scoring_evals.py:50,71`; off A+ by the SAME nightly-only live-model detection —
`ci.yml` deselects live, `test_llm_fallback.py` is a static config-drift guard blind to the deploy env).
**performance A** (156 passed; N+1 kills #437/#444 confirmed real + bounded lists/analytics — off A+ by
the SAME synchronous Margin telemetry on the LLM hot path `llm.py:203-208`, `scorer.py:16-35`; #389
tightened the timeout, not the architecture).

**Ship gate stays NO** on two ship-critical grounds, both below the A ship bar: store-readiness **B**
and business-case **B** — both blocked on non-loop-buildable inputs (a Human-Core signed build;
validated B2B demand + an owner-set seat price).

| Dimension | Ship-critical | Grade | Δ | One-line basis |
|---|---|---|---|---|
| functional-reality | ✅ | **A+** | = | `pytest tests/journeys`→**15 passed**; `test_billing.py -k webhook/entitlement/replay/forged`→**19 passed**; live `test_ai_output_evals.py` (live key)→**10 passed/188s**. Journeys assert real OUTCOMES: heuristic fit-score `score>0` (`test_core_journey.py:115`), analytics `average_score>0` (:142), free coach→403 "Pro" + no-key prep→503 GEMINI (:165-171), unverified purchase→501 + tier stays free (:212-217); signed webhook→DB `tier==PREMIUM`+Subscription row (`test_billing.py:203-209`), forged sig→400 FREE (:510), ancient replay→400 no-row (:541-547); ATS preview asserts parsed titles/slug/external_id (`test_ingestion_endpoint.py:88-97`). Zero findings. |
| correctness | ✅ | **A** | = | `-k "retry or ssrf or scorer or ceiling or rate or idempot or dedup or webhook or replay or refund or embedding"`→**144 passed**. 8th-audit finding CLOSED: `embedding_failed` (`scorer.py:243`) + refund on outage (`asgi.py:1581,1611-1613`, #419) & no-spend throw (`asgi.py:1592-1593`, #458), revert-provable tests net the counter to 0 (`test_scoring_ceiling.py:160,210`) and keep it burned on real spend (:250). SSRF re-validates every redirect hop (`url_guard.py:61-84`); zero-vector→0.5 (`scorer.py:120-122`). NEW non-blocking finding: `create_job` dedup guard is a read-then-write TOCTOU (`asgi.py:1497-1512`) with NO backing unique constraint (`models.py:344-346` non-unique index only) — concurrent identical POSTs both INSERT, unlike the `FOR UPDATE` ceiling. |
| security | ✅ | **A** | = | `-k "auth or cors or captcha or webhook or idor or entitlement or billing or lockout or ssrf or secret"`→**149 passed, 11 skipped**. RevenueCat webhook `secrets.compare_digest` (`mobile_billing.py:77`)→forged=401 grants nothing; tier only via `recompute_user_tier`, never client (`purchases.ts:79,107` refetch /me). Stripe `construct_event` (`billing.py:315-327`) + replay. CORS prod→`[]` never `*` (`asgi.py:118-153`) + HSTS/CSP frame-ancestors none. SSRF allowlist + per-hop re-validate (`url_guard.py:47-90`). DB `with_for_update` daily ceiling. Every job surface compound `id AND user_id`-scoped (no IDOR); org mutations `owner_id==user.id`. No tracked secrets. Off A+ by the SAME CAPTCHA no-op until `TURNSTILE_SECRET` (`captcha.py:69,78`). |
| design-taste | ✅ | **A** | = | Source genuinely A-level + cohesive. Web: real skeleton/error-not-empty/false-empty guards + focus-visible rings + `role=tablist` (`app/app/page.tsx:120-141,153,239-314`), honest quota `role=status` (:87). Mobile: native FlatList+RefreshControl+SafeArea + EmptyState/ErrorBanner (`(tabs)/index.tsx:60-109`), interview `radiogroup`/`radio` + `alert`+liveRegion (`interview/[jobId].tsx:188-205,214`), paywall honest tier branch + Terms/Privacy links + Restore (`paywall.tsx:159-211,253`). Slop sweep clean: NO emoji-as-icon (Ionicons throughout), no decorative gradients/blobs; one accent `#6366F1` converged web↔native (`theme.ts:12`). Off A+ by the SAME artifact gap: zero TRUE native Expo captures; `visual-verification.spec.ts:20` labels a 390px WEB viewport "mobile". |
| store-readiness | ✅ | **B** | = | Ground-(2) staleness RESOLVED (#419): `grep "NOT integrated"`→0 hits; A4/G4→OPEN (`ACCEPTANCE_AUDIT.md:33,49`), G7 icon corrected to "bespoke … NOT the Expo template" (:52). Ground-(1) persists: `docs/store/assets/` = feature-graphic.png + README only, NO screenshots → A3 (:32) + G7 (:52) stay **FAIL**; verdict "Submission readiness: NO" (:80). Screenshots need a signed native build (Human-Core, honestly tracked `PENDING_OPS.md:47-64`). Loop-buildable half complete: Vercel config (`vercel.json`), real IAP client (`purchases.ts:67,81,108` + Restore `paywall.tsx:253`), feature graphic + bespoke icon. Rubric wants ZERO open FAILs for A → B. `readiness`→FAIL (self-referential off the B grade). |
| artifact-integrity | ✅ | **A+** | ▲ (A→A+) | The A-capping doc-lag is CLOSED (#419): `grep "NOT integrated"/"still the Expo template"` over `ACCEPTANCE_AUDIT.md`→0 hits; A4/G4 OPEN (:33,49), G7 corrected (:52) — matches `mobile/package.json:26` (react-native-purchases ^10.4.3) + bespoke `icon.png` (1024² RGBA). `check_blocks`→OK `floor_met_year1=false`/`engine_pct=50`; `check_quality parse`→OK; `test_route_inventory_complete.py`→2 passed; `test_store_assets.py`→2 passed. Spot-checked ticks real: #465 read-only lock (`team/page.tsx:211`), #463 serialize latch (`jobs/[id]/page.tsx:100` + mobile twin). Honesty guards hold ($100K box UNticked `ROADMAP.md:555`, CAPTCHA disclosed). Zero findings. |
| business-case-strength | ✅ | **B** | = | `analysis/arr_base.py`→**57500** (<$100K; 500 subs × $115 blended ARPA `business_case_lib.py:9-13`, un-gamed — between $96/$192 annual prices, absolute sub count; conversion stated 3–6% conservatively `BUSINESS_CASE.md:27`). `check_blocks`→`floor_met_year1=false`, `engine_pct=50`. Team/seat lever built + user-reachable (`org_billing.py`, `/app/team`, /pricing band, live Stripe-test #383) but un-monetizable (`STRIPE_PRICE_TEAM_ANNUAL` owner-unset → `BillingNotConfigured`→503, `org_billing.py:76-83`) with un-validated demand → ZERO ARR credited to any lever (`BUSINESS_CASE.md:56-59,93-100`). No lever crosses $100K on honest math; #452–#467 billing commits are test-nets/hardening, not a floor-lever. |
| tests-evals | — | **A** | = | `pytest -m "not live" --cov`→**787 passed, 92.48% cov** (floor **88** `setup.cfg:22`, enforced `preflight.sh:58-59` + `ci.yml`); `test_scoring_evals.py`→19 passed. Evals pin EXACT goldens: `assert found == {"python","react","sql","postgresql"}` (:50, comment rejects `<=` subset), `overall_score == approx(expected,0.01)` (:71). Web E2E: 6 required Playwright specs (`ci.yml` e2e blocks deploy); mobile: 13 jest-expo tests, absence = gate FAIL (`preflight.sh:85-89`). Off A+ by the SAME nightly-only live detection: `ci.yml` deselects live, `test_llm_fallback.py:168` is a static blocklist guard (docstring concedes it can't see runtime) → a newly-dead model / broken Vercel env caught only nightly. |
| performance | — | **A** | = | `-k "perf or n_plus or query or limit or margin"`→**156 passed**. N+1 kills confirmed real: #437 job_public single JOIN + concurrent-PATCH guard (`7ba57f5`), #444 org-webhook bulk `in_()` (`c5ceefc`, revert-proven `FROM users`=1). GET /api/jobs bounded `_JOBS_LIST_DEFAULT_LIMIT=500`+selectinload (`asgi.py:1653,1671-1680`); analytics GROUP BY+top-5; org email bulk `in_()`. No new unbounded scan/N+1. Off A+ by the SAME synchronous Margin telemetry: `_emit_call_metrics` blocks inline before return (`llm.py:203-208`) + `_record_fit_outcome` "BLOCKING by design" (`scorer.py:16-35`), ~1.0s×N tail; #389 tightened the timeout, not the architecture. |

### Mechanical signals (auditor-run this audit, HEAD `ff11b84`)
- `flake8`-clean baseline · `python3 -c "import asgi"` → ok (after `pip install -r requirements*.txt`)
- **`pytest -q -m "not live" --cov` → 787 passed, 23 deselected, 92.48% cov** (setup.cfg floor **88**) · `pytest tests/journeys` → **15 passed** · billing round-trip `-k webhook/entitlement/replay/forged` → **19 passed**
- **`pytest tests/evals/test_ai_output_evals.py` (live GEMINI key present) → 10 PASSED** (real Gemini output across monetized AI surfaces, 188s)
- per-dimension targeted suites: correctness **144 passed** · security **149 passed/11 skipped** · performance **156 passed** · scoring evals **19 passed** · route-inventory **2 passed** · store-assets **2 passed**
- `scripts/check_quality.py parse` → OK · `readiness` → **FAIL** (store-readiness B, self-referential) · `scripts/check_blocks.py` → OK, `floor_met_year1=false`, `engine_pct=50`
- `analysis/arr_base.py` → **57500** (< $100K floor) · no tracked secrets (`git ls-files | grep -iE '\.env$|secret|pem|credential|_key$'` → empty)
- `docs/store/ACCEPTANCE_AUDIT.md`: `grep "NOT integrated"/"still the Expo template"` → 0 hits (stale doc-lag CLOSED, #419) · `docs/store/assets/` → feature-graphic.png + README only, **NO screenshots** (A3/G7 real FAILs, Human-Core)
- 9 fresh subagent graders each ran their own signal + cited file/line (maker ≠ checker); web/mobile `tsc`/`lint`/`jest`/Playwright not re-run locally (node_modules absent) — relied on committed specs + required CI

### Top gaps to drive to A+ (ordered; ship-critical below-A first)
1. **store-readiness (B, ship-critical) — top blocker:** the last open FAIL is store **screenshots** (A3/G7, `ACCEPTANCE_AUDIT.md:32,52`) — ≥2 rendered from a SIGNED native build (RevenueCat keys + store products + an EAS signed build). This is Human-Core, not producible on Linux; the entire loop-buildable half (Vercel config, IAP client, feature graphic, bespoke icon, corrected audit doc) is DONE. No further loop work moves this — it needs the owner's signed-build round-trip. (Issue #93)
2. **business-case-strength (B, ship-critical):** floor honestly unmet ($57.5K < $100K, `floor_met_year1=false`). The seat tier is user-reachable but has no live per-seat price (`STRIPE_PRICE_TEAM_ANNUAL` owner-unset → 503) and un-validated B2B demand → ZERO ARR credited. Crossing the floor needs REAL adoption data + a published seat price, not more code — a market/validation step. (Issue #92)
3. **correctness (A→A+, NEW):** the `create_job` dedup guard (`asgi.py:1497-1512`) is a read-then-write TOCTOU with no backing DB unique constraint (`models.py:344-346` has only a non-unique index). Add `UniqueConstraint(user_id,title,company_name,url)` + catch IntegrityError to make the guard atomic (matching the `FOR UPDATE` ceiling path). Non-blocking; #463 client serialization catches the common case.
4. **performance (A→A+):** Margin telemetry still emits SYNCHRONOUSLY on the LLM hot path (`llm.py:203-208`, `scorer.py:16-35`), ~1.0s×N tail; #389 tightened the timeout but not the architecture. Move the emit off the user-visible critical path (post-response drain / `waitUntil`-style deferral).
5. **design-taste (A→A+):** add TRUE native-mobile captures (Expo/Detox/Maestro) of the flagship surfaces (mock-interview, paywall, pipeline, team) committed under `mobile/__screenshots__/`, and rename the 390px web viewport in `visual-verification.spec.ts:20` so no web shot masquerades as native.
6. **tests-evals (A→A+):** add a per-PR (CI-required, not nightly-only) real live-model liveness/output smoke — a single 1-token live call (`continue-on-error`) — so a decommissioned model or broken deploy env reddens per-PR, not only nightly.
7. **security (A→A+):** activate real bot-protection — CAPTCHA is a fail-closed Turnstile impl but a no-op until the owner connects `TURNSTILE_SECRET` (+ web sitekey + native widget); public forms rely on the rate limiter alone until then.

```yaml
QUALITY_SCORECARD:
  as_of: 2026-07-23
  overall: B
  ship_gate_met: false
  method: 9 independent adversarial per-dimension grader subagents (maker != checker); each ran its own mechanical signal + cited file/line evidence; auditor independently re-ran the full suite (787 passed, 92.48% cov) and the live real-output eval suite with the live Gemini key (10 passed, 188s)
  dimensions:
    - name: functional-reality
      grade: A+
      ship_critical: true
      top_gaps: []
    - name: correctness
      grade: A
      ship_critical: true
      top_gaps:
        - "NEW non-blocking dedup TOCTOU: create_job's read-then-write duplicate guard (asgi.py:1497-1512) has NO backing DB unique constraint -- JobPosting.__table_args__ declares only a non-unique Index (models.py:344-346), no UniqueConstraint(user_id,title,company_name,url). Two truly-simultaneous identical POSTs both pass 'existing is None' and both INSERT, double-firing the very side-effects the guard comment claims to prevent -- unlike the score_daily ceiling which is concurrency-safe via SELECT...FOR UPDATE. Non-blocking (client-side serialization #463 + sequential retries catch the common cases). The 8th-audit embedding-refund finding is RESOLVED (#419/#458, revert-provable tests test_scoring_ceiling.py:160,210,250)."
    - name: security
      grade: A
      ship_critical: true
      top_gaps:
        - "CAPTCHA/bot-protection on public register+login is a real fail-closed Turnstile impl but a NO-OP until the owner sets TURNSTILE_SECRET (+ web sitekey + native widget); today's live bot defense on public forms is the DB rate-limiter alone (captcha.py:69,78)."
    - name: design-taste
      grade: A
      ship_critical: true
      top_gaps:
        - "Zero TRUE native Expo captures exist; visual-verification.spec.ts:20 labels a 390px WEB viewport 'mobile'. The flagship surfaces (mock-interview, paywall, pipeline, team) have no committed native rendered captures -> the strongest design work is unbacked by an artifact a vision model can inspect."
    - name: store-readiness
      grade: B
      ship_critical: true
      top_gaps:
        - "Ground (2) RESOLVED: the stale ACCEPTANCE_AUDIT doc-lag is fixed (#419) -- A4/G4 now OPEN, G7 icon corrected, grep 'NOT integrated'/'still the Expo template' = 0 hits. Ground (1) persists: store SCREENSHOTS genuinely absent (docs/store/assets/ = feature-graphic.png + README only) -> A3 (ACCEPTANCE_AUDIT.md:32) + G7 (:52) stay FAIL, verdict 'Submission readiness: NO' (:80). Needs a SIGNED native build (RevenueCat keys + store products + EAS build) -- Human-Core, not producible on Linux, honestly tracked PENDING_OPS.md:47-64. The rubric requires ZERO open FAILs for A; the Human-Core carve-out does not erase a real FAIL, so B."
    - name: artifact-integrity
      grade: A+
      ship_critical: true
      top_gaps: []
    - name: business-case-strength
      grade: B
      ship_critical: true
      top_gaps:
        - "Floor still honestly unmet: analysis/arr_base.py -> 57500 < $100K; floor_met_year1=false. The seat tier is user-reachable end-to-end (org_billing.py + /app/team + /pricing Team band + live Stripe-test #383) but not MONETIZED -- STRIPE_PRICE_TEAM_ANNUAL owner-unset -> price_id_for_org_plan raises BillingNotConfigured -> checkout 503 (org_billing.py:76-83), B2B demand un-validated -> ZERO ARR honestly credited to any lever, so none crosses $100K on un-gamed math. Needs real adoption data + a published seat price, not more code."
    - name: tests-evals
      grade: A
      ship_critical: false
      top_gaps:
        - "Real live-model DETECTION is still nightly-only (ci.yml deselects live; nightly.yml cron -m live). The per-PR guard test_llm_fallback.py:168 is a STATIC config-drift guard (hardcoded blocklist _KNOWN_DECOMMISSIONED={'gemini-2.0-flash'}; docstring concedes it can't see runtime), so a newly-decommissioned model or broken Vercel env is caught only nightly. Add a per-PR/CI-required live liveness or real-output smoke (one 1-token call, continue-on-error)."
    - name: performance
      grade: A
      ship_critical: false
      top_gaps:
        - "Margin telemetry still emits SYNCHRONOUSLY/blocking on the LLM hot path -- _emit_call_metrics inline before return (llm.py:203-208) + _record_fit_outcome 'BLOCKING by design' (scorer.py:16-35), stacking ~1.0s*N per multi-call workflow. #389 tightened the per-call timeout 2.0s->1.0s (real mitigation) but not the architecture. Move the emit off the user-visible critical path (post-response drain / waitUntil deferral). N+1 kills #437/#444 confirmed real; GET /api/jobs bounded."
  top_gaps:
    - "store-readiness B (ship-critical, TOP BLOCKER): the last open FAIL is store SCREENSHOTS (A3/G7, ACCEPTANCE_AUDIT.md:32,52) -- need a SIGNED native build (Human-Core, not producible on Linux). Ground-(2) staleness is now RESOLVED (#419); the whole loop-buildable half is done. No further loop work moves this. (#93)"
    - "business-case-strength B (ship-critical): floor unmet ($57.5K<$100K, floor_met_year1=false); the seat tier is user-reachable but has no live per-seat price (STRIPE_PRICE_TEAM_ANNUAL owner-unset -> 503) and un-validated B2B demand, so no lever crosses the floor on honest math. Needs adoption data + a published seat price, not code. (#92)"
    - "correctness A->A+ (NEW, non-blocking): create_job dedup guard is a read-then-write TOCTOU (asgi.py:1497-1512) with no backing unique constraint (models.py:344-346 non-unique index only) -> concurrent identical POSTs both INSERT. Add UniqueConstraint + IntegrityError catch. The 8th-audit embedding-refund finding is RESOLVED (#419/#458)."
    - "performance A->A+: Margin telemetry still synchronous/blocking on the LLM hot path (llm.py:203-208, scorer.py:16-35); #389 tightened the timeout but not the architecture -- move the emit off the critical path."
    - "design-taste A->A+: no true native Expo captures; visual-verification.spec.ts:20 labels a 390px web viewport 'mobile'. The flagship surfaces still have no committed native captures."
    - "tests-evals A->A+: real live-model detection is still nightly-only; the per-PR guard is static/config-only (can't see the deploy env or a newly-dead model). Add a per-PR live smoke."
    - "security A->A+: CAPTCHA no-op until the owner connects TURNSTILE_SECRET; public forms rely on the rate limiter alone."
    - "artifact-integrity A->A+ ACHIEVED this cycle: the stale ACCEPTANCE_AUDIT doc-lag is CLOSED (#419); zero findings remain."
```
