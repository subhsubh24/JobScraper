# QUALITY MEMORY — Career Operator

> Append-only log of each independent audit: the grade, what changed since the last grade,
> and the standing gaps. Read this FIRST each run and diff vs the last grade. Owned by the
> Quality Auditor only.

## 2026-06-29 — first independent audit (bootstrap)

**Overall: C · ship_gate_met: false.** First time the rubric + scorecard exist, so there is
no prior grade to diff against — this establishes the baseline.

Per-dimension: functional-reality **A**, correctness **A**, security **B**, design-taste
**B**, store-readiness **C**, artifact-integrity **A**, business-case-strength **C**,
tests-evals **A**, performance **B**.

Method: 9 fresh independent adversarial grader subagents (maker ≠ checker), each ran its
own mechanical signal. Auditor pre-ran the full gate: flake8 clean, 163 backend tests pass
@ 85.68% cov (floor 75), 9 journey tests pass, 23 evals pass, web+mobile tsc/lint clean, 34
mobile jest pass, web `next build` succeeds, web E2E green in CI on main HEAD `cd56e8f`.

**What's genuinely strong (A):** the core user journey works end-to-end and the tests assert
the real fit-score OUTPUT renders (not HTTP 200); correctness primitives (zero-vector NaN
guard, SSRF guard, request-id error envelope, bounded retries, dedup, truthful LLM
degradation) are real + tested; every spot-checked ticked ROADMAP box is backed by a real
artifact and documented gaps are stated honestly; tests/evals are outcome-asserting with a
healthy coverage floor.

**Standing ship-critical gaps (drive these to A):**
1. **business-case-strength (C):** honest $57.5K vs $100K floor, but the named revenue levers
   (referral loop, Career+ entitlement tier, team/B2B2C tier, founder annual-first pricing)
   are essentially unbuilt — `careerplus_*` price envs are dead config; tier enum is binary
   FREE/PREMIUM. Readiness rejected on business-case grounds until a lever crosses the floor.
2. **store-readiness (C):** no rendered store assets committed (`docs/store/assets/` absent),
   no committed screenshots, mobile IAP (StoreKit/RevenueCat + Play Billing client) not
   integrated → 4 open ACCEPTANCE_AUDIT FAILs (A3/A4/G4/G7). Vercel deploy config itself is
   genuinely ready; live keys/signed build/submission stay owner Human-Core.
3. **security (B):** no CAPTCHA on public forms; spend-ceiling/rate-limit/lockout are
   in-memory per-instance (bypassable across serverless cold starts); CORS defaults to `*`.
4. **design-taste (B):** zero rendered screenshots / no dual-axis visual verification (Track E
   unticked) caps confidence; web/mobile accent divergence; Expo-template icon.

**Non-critical (≥B, passing):** tests-evals **A** (nit: fake-LLM prep eval; thin coverage on
greenhouse.py 53% / llm_workflows.py 61%); performance **B** (unpaginated N+1 on `/api/jobs`
+ `/api/analytics/pipeline`).

**Issues filed this run:** quality issues opened for the 4 ship-critical dims below A
(business-case, store-readiness, security, design-taste).

**Note for next run:** the local Playwright run could not be reproduced in-sandbox due to a
chromium build pin mismatch (project wants 1228; sandbox has 1194) — relied on the green CI
required check instead. If a future audit needs to re-run the browser journey locally, pin
the browser to a sandbox-installable build or launch with `executablePath`.

## 2026-07-01 — 2nd independent audit

**Overall: B (↑ from C) · ship_gate_met: false.** Real, evidence-backed improvement since the
baseline: **two ship-critical dimensions moved B→A** and both non-critical dims stayed strong.

Per-dimension (Δ vs 2026-06-29): functional-reality **A** (=), correctness **A** (=), security
**A** (▲ from B), design-taste **A** (▲ from B), store-readiness **C** (=), artifact-integrity
**A** (=), business-case-strength **C** (=), tests-evals **A** (=), performance **B** (~, improved
rationale — N+1 now fixed, one unbounded query remains).

Method: 9 fresh independent adversarial grader subagents (maker ≠ checker), each ran its own
mechanical signal + cited file/line. Auditor pre-ran the gate: flake8 clean, **258 backend
pass @ 90.64% cov** (was 163 @ 85.68%; floor 75), 9 journeys pass, 23 evals pass, scorecard
parses, `floor_met_year1=false`/`engine_pct=0`. web/mobile tsc/lint/jest/Playwright not
re-runnable locally (node_modules absent by design) — relied on committed artifacts + required
CI on main HEAD `c7ae017`.

**What genuinely improved (drove C→B):**
- **security B→A** — both prior B-gaps fixed: CORS now returns `[]` in prod (never `*`,
  `asgi.py:103-136`, `test_cors.py`); rate-limit + LLM spend-ceiling now Postgres cross-instance
  (`asgi.py:238-295` `RateCounter` + `SELECT…FOR UPDATE`, `test_rate_counter.py`). Only CAPTCHA +
  in-memory login lockout remain (off A+, not below A).
- **design-taste B→A** — 24 real non-zero rendered screenshots committed (was zero); accent
  converged on `#6366F1`; bespoke brand icon replaces the Expo template. Independent visual read
  clears the DESIGNER QUESTION + AI-slop list.
- **coverage** 85.68%→90.64%; greenhouse.py 53%→100%, llm_workflows.py 61%→100%.
- **performance** — N+1 genuinely eliminated on `/api/jobs`, `/api/analytics/pipeline`, and coach
  context (`selectinload` verified); `/api/jobs` gained pagination. Held at B by the still-unbounded
  `/api/analytics/pipeline` `.all()`+sort and no embedding cache.

**Standing ship-critical gaps (still C — these block the ship gate):**
1. **business-case-strength (C):** honest $57.5K < $100K floor. Referral loop now BUILT (PR #109,
   correctly uncredited), but **Career+ ($24) is dead config** — `careerplus_*` grants the identical
   `PREMIUM`; `UserTier` is binary FREE/PREMIUM; **no team/B2B2C seat model** exists. Floor unmet.
2. **store-readiness (C):** unchanged — no rendered store assets (`docs/store/assets/` absent), no
   store screenshots, mobile IAP (StoreKit/Play Billing) not integrated → 4 open ACCEPTANCE_AUDIT
   FAILs (A3/A4/G4/G7). Vercel deploy config itself is A-level.

**New named nits surfaced this run (non-blocking):** correctness — no dedup/idempotency on
persisted jobs (`create_job` inserts unconditionally, asgi.py:807); design — all `-mobile`
screenshots are the web app at 390px (zero native-mobile visual proof) + a 390px header collision.

**Issues:** updated #92 (business-case) + #93 (store-readiness), both still C. Closed #94
(security) + #95 (design-taste) — both reached A this audit; recorded the fix evidence.

## 2026-07-03 — 3rd independent audit

**Overall: B (=) · ship_gate_met: false.** No overall grade change, but real, evidence-backed
internal improvement: **three dimensions reached A+** and **performance moved B→A**. The ship
gate is still blocked by the *same two* pre-launch C's (store-readiness, business-case), so
overall is correctly held at B — the improvement is inside the passing dims, not on the two
blockers.

Per-dimension (Δ vs 2026-07-01): functional-reality **A+** (▲ from A), correctness **A+**
(▲ from A), security **A** (=), design-taste **A** (=), store-readiness **C** (=),
artifact-integrity **A+** (▲ from A), business-case-strength **C** (=), tests-evals **A** (=),
performance **A** (▲ from B).

Method: 9 fresh independent adversarial grader subagents (maker ≠ checker), each ran its own
signal + cited file/line. Auditor pre-ran the gate at HEAD `4b180a2`: flake8 clean, **387
backend pass @ 92.75% cov** (was 258 @ 90.64%; floor 75), **15 journeys** (was 9), **31 evals**
(was 23), scorecard parses, `readiness`→FAIL (store-readiness C), `floor_met_year1=false`,
`engine_pct=0`. web/mobile tsc/lint/jest/Playwright not re-runnable locally (node_modules absent)
— relied on committed artifacts + required CI on main HEAD `4b180a2`.

**What genuinely improved this run:**
- **correctness A→A+** — BOTH prior named nits now fixed WITH direct tests: job dedup/idempotency
  guard (`asgi.py:1035`, returns `{"duplicate":True}` before the cap + score-slot; `test_job_idempotency.py`
  6 tests) and a direct zero-vector→0.5 scorer assertion (`test_scoring_evals.py:135`).
- **functional-reality A→A+** — 15 journeys (was 9) assert the real fit-score VALUE + tier flip +
  honest 501/503 degradation; billing entitlement round-trip covered both grant AND refuse.
- **artifact-integrity A→A+** — every spot-checked box (Career+, cover-letter/study-plan Pro
  endpoints, CAPTCHA seam, dedup, fail-loud-serverless #228, signup no-hard-block #216) maps to a
  real tested artifact; docs honestly disclose no-op/degraded states + the unmet floor.
- **performance B→A** — `/api/jobs` paginated; resume AND JD embeddings are DB-cached
  (`ensure_user_embedding`/`ensure_job_embedding`) — the prior "no embedding cache" nit was WRONG;
  only one low-severity batched-unbounded aggregate remains (`/api/analytics/pipeline` `.all()`+sort).
- **security** — CAPTCHA seam now BUILT (`src/security/captcha.py`, wired on register/login/waitlist)
  though a NO-OP until owner sets `TURNSTILE_SECRET`; login lockout still in-memory per-instance. Stays A.

**Standing ship-critical gaps (still C — these block the ship gate):**
1. **business-case-strength (C):** honest $57.5K < $100K. Career+ ($24) is now a REAL differentiated
   webhook-verified gate (salary-negotiation exclusive) + cover-letter/study-plan Pro value-adds —
   genuine lever progress — but not a floor-flip on any defensible mix. **Team/B2B2C seat (org) tier
   is still entirely unbuilt** (highest ARPA) — the primary remaining floor-lever.
2. **store-readiness (C):** unchanged — no rendered store assets (`docs/store/assets/` absent), no
   store screenshots, mobile IAP (StoreKit/Play Billing) still only deferral comments (`paywall.tsx:41,119`)
   → 4 open ACCEPTANCE_AUDIT FAILs (A3/A4/G4/G7). Vercel deploy config itself is A-level.

**New named nit surfaced this run (non-blocking):** design — the committed `-mobile` screenshots are
STALE; they still depict the 390px header collision that the code already FIXED (`layout.tsx:38`), so
the repo's design evidence contradicts the shipped UI. Regenerate them (holds design at A, off A+).

**Issues:** #92 (business-case) + #93 (store-readiness) both remain the correct open ship-critical
issues (both still C) — updated with this audit's fresh evidence rather than duplicated. No dimension
regressed below A that lacked an issue; no new ship-critical issue needed.

## 2026-07-05 — 4th independent audit

**Overall: B (=) · ship_gate_met: false.** No overall grade change and NO dimension moved a
letter vs 2026-07-03 — but real, evidence-backed internal progress inside the passing dims, and
zero regressions. The ship gate is still blocked by the *same two* pre-launch C's
(store-readiness, business-case), correctly holding overall at B.

Per-dimension (Δ vs 2026-07-03): functional-reality **A+** (=), correctness **A+** (=, standing
retry/backoff gap now CLOSED), security **A** (=, redirect-SSRF closed), design-taste **A** (=),
store-readiness **C** (=), artifact-integrity **A+** (=), business-case-strength **C** (=),
tests-evals **A** (=, materially better within A), performance **A** (=).

Method: 9 fresh independent adversarial grader subagents (maker ≠ checker), each ran its own
signal + cited file/line. Auditor pre-ran the gate at HEAD `7572338`: flake8 clean, **484 backend
pass @ 92.21% cov** (was 387 @ 92.75%; floor 75), **15 journeys**, **46 evals** (was 31), scorecard
parses, `readiness`→FAIL (store-readiness C), `analysis/arr_base.py`→57500, `floor_met_year1=false`,
`engine_pct=0`, no tracked secrets. web/mobile tsc/lint/jest/Playwright not re-runnable locally
(node_modules absent) — relied on committed artifacts + required CI on main HEAD `7572338`. Notable:
the grader env had a live `GEMINI_API_KEY`, so the `live`-marked content evals (tailored-résumé
grounding, prep-pack real output) actually RAN and PASSED — the "AI output is real" claim was
exercised, not just nightly-theoretical.

**What genuinely improved this run (all inside already-passing dims — no letter change):**
- **correctness** — the prior standing gap ("ATS fetches have timeouts but no retry/backoff on
  transient 429/5xx") is CLOSED by #271: `get_with_retry` bounded exponential backoff, never on
  Timeout, correct ConnectTimeout hierarchy edge case (`src/ingestion/base.py:22-55`), with
  `test_ats_retry.py` asserting exact call counts. Stays A+ (was already A+ with the gap open).
- **security** — #277 closed the redirect-based SSRF in the ATS careers-page probe; `url_guard.py:74-84`
  re-validates the host on EVERY redirect hop before connect (tested). Doesn't touch the two A+
  holdbacks (CAPTCHA no-op seam, in-memory lockout), so stays A.
- **tests-evals** — eval count 31→46 with genuinely rigorous new evals (drafter→reviewer persists the
  REVIEWED text + COGS toggle `test_prep_tools_evals.py:171-258`; skill-gap ranking math; tailored-résumé
  grounding). Backend 387→484. "Better within A"; held off A+ only by the loose 75 coverage floor.
- **performance** — #266 job-detail GET eager-loads its relationships (`asgi.py:1189-1195`); new features
  (skill-gap heatmap, learning plan) are capped at 500, no new N+1. Stays A; same single
  `/api/analytics/pipeline` `.all()`+in-Python-sort gap.

**Standing ship-critical gaps (still C — these block the ship gate, both UNCHANGED):**
1. **business-case-strength (C):** honest $57.5K < $100K. Shipped Pro value-adds diversify the wedge
   but don't floor-flip and are honestly uncredited in the projection. **Team/B2B2C seat (org) tier
   still entirely unbuilt** — no `Organization`/`Seat` model in `src/db/models.py`, `UserTier` binary
   FREE/PREMIUM (`billing.py:63`). The one lever with the math to cross the floor. 15+ consecutive
   runs confirm it is genuinely owner/GTM-blocked, not code-blocked (`loop-memory.md`).
2. **store-readiness (C):** unchanged — no rendered store assets (`docs/store/assets/` absent), no
   store screenshots, mobile IAP client NOT integrated (`react-native-purchases` absent from
   `mobile/package.json`; `paywall.tsx:40,118` are deferral comments) → 4 open ACCEPTANCE_AUDIT FAILs
   (A3/A4/G4/G7). `git log` on docs/store + paywall.tsx shows ZERO store-asset/IAP movement since
   last audit. Vercel deploy config itself remains A-level.

**Issues:** #92 (business-case) + #93 (store-readiness) both remain the correct open ship-critical
issues (both still C, both unchanged) — updated with this audit's fresh evidence rather than
duplicated. No dimension regressed below A; no new ship-critical issue needed. (Latent config gaps
in #222 — Career+ prod-503 price-env validation + DATABASE_URL SQLite default — remain honestly
disclosed, keeping artifact-integrity at A+; they are tracked there, not re-filed.)

## 2026-07-09 — 5th independent audit

**Overall: C (↓ from B) · ship_gate_met: false.** First overall DROP since the bootstrap. A
ship-critical **regression** dominates: **functional-reality A+ → D**. The shipped default LLM
model `gemini-2.5-flash` (`src/llm.py:20`) was **decommissioned by Google** between 2026-07-05
(when these live evals last passed) and today. This is NOT the sandbox-proxy artifact prior
audits noted — the auditor probed the REAL `generativelanguage.googleapis.com` endpoint with the
live key: `gemini-2.5-flash`→`404 "no longer available"`, `gemini-2.0-flash`→404, but
`gemini-flash-latest`→"OK" on the same key. So every monetized AI feature (mock-interview coaching
— the VISION north-star — coach, prep pack, cover letter, tailored résumé, salary-negotiation,
learning plan) **502s against the live provider**; `.env.example:8` steers ops to the SAME dead
model; there's no live-model fallback. Free/heuristic journeys (15/15 `tests/journeys`) still work,
keeping it off F.

Per-dimension (Δ vs 2026-07-05): functional-reality **D** (▼ from A+), correctness **A** (▼ from A+,
code unchanged), security **A** (=), design-taste **A** (=), store-readiness **C** (=),
artifact-integrity **A** (▼ from A+), business-case-strength **C** (=), tests-evals **A** (=),
performance **A+** (▲ from A).

Method: 9 fresh independent adversarial grader subagents (maker ≠ checker), each ran its own signal
+ cited file/line. Auditor pre-ran the gate at HEAD `a70e20e`: flake8 clean, **565 pass @ 91.82%
cov** (floor ratcheted 75→85 in #293), **15 journeys**, **62 evals** (was 46) on the per-PR
`-m "not live"` lane; `readiness`→FAIL, `arr_base`→57500, `floor_met_year1=false`, no tracked
secrets. The auditor then **independently verified the model-decommission** by calling the real
Gemini endpoint (above) — the functional-reality grader's D is confirmed, not taken on faith.

**Grade corrections (code unchanged, tightened to the zero-findings A+ bar — anti-inflation):**
- **correctness A+→A** — the 502-burns-a-daily-AI-slot item (`asgi.py:423-429`, slot consumed
  before the call, no refund on provider 502) is a real named finding; prior audits carried it as a
  "documented tradeoff" at A+, but the rubric's A+ requires ZERO findings, so A is the honest grade.
- **artifact-integrity A+→A** — two honest-direction doc-lags found this run: ROADMAP Track-E
  coverage box still reads `fail_under=65/~69%` while setup.cfg is `85`/actual 91.8%; `ROUTE_INVENTORY.md`
  omits `/api/jobs/import-preview` (which HAS e2e coverage). Zero fabrications; code tighter than doc.

**Genuine improvement (A→A+):** performance — #317 replaced `/api/analytics/pipeline`'s in-Python
top-5 sort with real SQL `GROUP BY` + `ORDER BY … LIMIT 5` (`asgi.py:2354-2400`), independently
verified as constant-query, no in-Python full scan; #319 collapsed `create_job` re-serialize to one
`joinedload` LEFT JOIN.

**Standing ship-critical C's (unchanged, both block the gate):** store-readiness (no rendered store
assets, mobile IAP client absent, 4 open ACCEPTANCE FAILs) and business-case ($57.5K < $100K, team/
B2B2C seat tier still unbuilt — only GTM packaging research added).

**tests-evals lesson (held at A):** the live real-output evals that WOULD catch a model decommission
are nightly-only, so this product-breaking regression passed every per-PR merge gate green — the exact
"large regression lands silently green" hole. Named as the A→A+ gap: add a per-PR/CI-required model-
liveness or real-output smoke.

**Issues:** filed a NEW ship-critical issue for functional-reality D (decommissioned model). #92
(business-case) + #93 (store-readiness) remain the correct open ship-critical issues (both still C,
unchanged) — updated with this audit's fresh evidence, not duplicated.

## 2026-07-11 — 6th independent audit

**Overall: B (↑ from C) · ship_gate_met: false.** A **recovery audit**: the ship-critical
functional-reality regression that drove the 2026-07-09 D is **resolved (D → A)**, and two more
ship-critical dims moved up on real evidence (correctness A→A+, business-case C→B). Ship gate stays
NO on the two standing pre-launch gaps (store-readiness C, business-case B).

Per-dimension (Δ vs 2026-07-09): functional-reality **A** (▲ D→A), correctness **A+** (▲ A→A+),
security **A** (= improved basis), design-taste **A** (=), store-readiness **C** (=), artifact-integrity
**A** (=), business-case-strength **B** (▲ C→B), tests-evals **A** (=), performance **A+** (=).

Method: 9 fresh independent adversarial grader subagents (maker ≠ checker), each ran its own signal +
cited file/line. Auditor pre-ran the gate at HEAD `9f119e5`: flake8 clean, `import asgi` ok, **609
backend pass @ 91.09% cov** (floor ratcheted 85→**88**), 15 journeys pass, 62 evals pass, `check_quality
parse` OK / `readiness` FAIL, `check_blocks` OK (`floor_met_year1=false`, **`engine_pct=50`** was 0),
`arr_base.py`→57500, no tracked secrets, CORS `[]` in prod. web/mobile `tsc`/`lint`/`jest`/Playwright
not re-runnable locally (node_modules absent) — relied on committed specs + required CI.

**The recovery (functional-reality D→A):** auditor re-probed the REAL Gemini endpoint with the live
key — `gemini-2.5-flash` now returns **200 "OK"** (a hard 404 two days ago), `gemini-flash-latest` +
`gemini-2.5-flash-lite` also 200, embedding `gemini-embedding-001`→200 (dim 3072). Live eval suite
`test_ai_output_evals.py` → **10 passed** (was 9 failed / 1 passed). Crucially the factory did NOT just
wait for Google: `src/llm.py:78 resilient_chat_completion` falls back on a 404 model-death ONLY through a
verified-live chain and fails LOUD if all-dead; a per-PR source-scan guard
(`tests/test_llm_nobypass_integration.py`) enforces every AI workflow routes through it (sole raw
`.create` is the wrapper, `src/llm.py:97`). `.env.example:11` corrected to the floating alias. Off A+
only by the code default still being pinned `gemini-2.5-flash` (trivial — fallback covers it).

**correctness A→A+:** the persistent "provider 502 burns a legit user's daily AI slot with no refund"
finding is FIXED — symmetric `refund_llm_ceiling` (`asgi.py:491`) in all 9 LLM endpoints' failure
branches (9/9), excluded from success + moderation, `SELECT…FOR UPDATE` floored at 0. Zero findings.

**business-case C→B:** the highest-ARPA lever (team/B2B2C seat tier) is now genuinely BUILT — real
`Organization`/`OrganizationMember` models + migration (`models.py:138,187`), quantity-based Stripe seat
checkout + signature-verified webhook + seat-cap enforcement (`org_billing.py`), owner-scoped endpoints
(`asgi.py:1278-1386`), 22 tests. Last cycle's C trigger (top lever ENTIRELY unbuilt) is removed. Held at
B: floor still honestly unmet (57500 < $100K, `floor_met_year1=false`, zero ARR credited) — the backend
is built but not yet MONETIZED (no admin UI, no live per-seat pricing, no validated B2B adoption).

**security A (improved basis):** the in-memory per-instance login-lockout finding is FIXED — lockout is
now DB-backed cross-instance (`asgi.py:373-431`). The new org/seat attack surface is authz-clean
(`seats_purchased` webhook-only, seat mutations owner-scoped, cap lock-enforced, entitlement via
`recompute_user_tier` Pro-only) — zero entitlement bypass. Off A+ by the SAME CAPTCHA no-op.

**artifact-integrity A:** both prior doc-lags FIXED (ROADMAP coverage box now `fail_under=88`;
`/api/jobs/import-preview` added to ROUTE_INVENTORY). Every spot-checked ticked box maps to real tested
code; #353 entitlement-reconciliation test asserts real DB tier lifecycle. Held off A+ by an
honest-direction self-lag: the PRIOR scorecard understated the now-built org tier (corrected here).

**Standing ship-critical gaps (both block the gate, unchanged this cycle):** store-readiness C (same 4
open ACCEPTANCE FAILs A3/A4/G4/G7 — no rendered assets, mobile IAP still a "coming soon" stub) and
business-case below floor. These are the two top gaps to drive next.

**Issues:** functional-reality issue #329 (the decommissioned-model D) is RESOLVED — commented with the
recovery evidence and closed. #93 (store-readiness, still C) + #92 (business-case, C→B) updated with this
audit's fresh evidence, not duplicated. No new issue filed (no ship-critical dim newly below A).

## 2026-07-13 — 7th independent audit

**Overall: B (=) · ship_gate_met: false.** No overall change, but real evidence-backed movement in
BOTH directions: one ship-critical dim finished its recovery UP (functional-reality A→A+), one
non-critical dim moved DOWN on a genuine new finding (performance A+→A), and the two standing
pre-launch blockers (store-readiness C, business-case B) are unchanged — correctly holding overall at B.

Per-dimension (Δ vs 2026-07-11): functional-reality **A+** (▲ A→A+), correctness **A+** (=), security
**A** (=), design-taste **A** (=), store-readiness **C** (=), artifact-integrity **A** (=),
business-case-strength **B** (=), tests-evals **A** (=), performance **A** (▼ A+→A).

Method: 9 fresh independent adversarial grader subagents (maker ≠ checker), each ran its own signal +
cited file/line. Auditor pre-ran the gate at HEAD `b221a03`: flake8 clean, `import asgi` ok, **725
backend pass @ 91.42% cov** (floor 88, was 609 @ 91.09%), 15 journeys pass, 147 evals pass (was 62 —
#376 enumerated more suites), **live `test_ai_output_evals.py`→10 passed**, `check_quality parse` OK /
`readiness` FAIL, `check_blocks` OK (`floor_met_year1=false`, `engine_pct=50`), `arr_base`→57500, no
tracked secrets, CORS `[]` in prod. Auditor independently re-probed the REAL Gemini endpoint with the
live key: default `gemini-flash-latest`→200, fallbacks `gemini-2.5-flash`/`gemini-2.5-flash-lite`→200,
`gemini-2.0-flash`→404 (dead, not in default chain).

**functional-reality A→A+ (recovery complete):** the last A→A+ holdback — the code default
`_DEFAULT_CHAT_MODEL` still pinned to `gemini-2.5-flash` — is RESOLVED by #379 (`4f5348a`):
`src/llm.py:98` now reads the floating alias `gemini-flash-latest`, removing the last pinned
single-point-of-failure. Live probe + 10/10 live evals + 15/15 journeys + entitlement round-trip all
green; zero findings. The functional-reality arc since 2026-07-09 is now D→A→A+.

**performance A+→A (real new finding):** the Margin cost-per-outcome telemetry shipped this window
(#368/#369/#382) emits metrics SYNCHRONOUSLY/blocking on the LLM hot path — `_emit_call_metrics`
(`src/llm.py:47-83`) + `_record_fit_outcome` (`scorer.py:16-35`), per-call `MarginMeter(timeout=2.0)`,
blocking BY DESIGN (#369, because Vercel freezes daemon threads post-response). A slow/degraded Margin
ingest inflates user-facing p99 up to ~2s/call, stacking per LLM call in multi-call workflows. It is
bounded + fail-safe + gated off when unconfigured, and `score_all_jobs`'s batch loop is NOT HTTP-wired,
so it is a named A-level finding, not a ship blocker — but it did not exist at the 2026-07-11 A+ grade,
so A is the honest grade (anti-inflation: A+ requires ZERO findings).

**Standing ship-critical blockers (both unchanged, both hold overall at B):**
- **store-readiness C:** #370 committed a REAL, Play-spec-correct, designer-grade feature graphic
  (`docs/store/assets/feature-graphic.png`, 1024×500 8-bit RGB no-alpha, guarded by
  `tests/test_store_assets.py`) — but it closed ZERO of the 4 open ACCEPTANCE_AUDIT FAILs. A3/G7 still
  need store screenshots (signed native build) + a bespoke app icon (still Expo template); A4/G4 still
  need the mobile IAP client (`react-native-purchases` absent; `paywall.tsx:115-124` is a "coming soon"
  Alert stub). Progress on a sub-item does not raise the grade while the FAILs stand.
- **business-case B:** the highest-ARPA lever (team/B2B2C seat tier) is now genuinely user-reachable
  end-to-end (web admin surface `web/app/app/team/page.tsx` #356 + `/pricing` Team band #363 + live
  Stripe-test seat coverage #383) — but no per-seat price is published (`STRIPE_PRICE_TEAM_ANNUAL`
  owner-unset → checkout 503), B2B demand un-validated, `arr_base`→57500 < $100K, `floor_met_year1=false`,
  ZERO ARR credited. An honest below-floor pre-launch number cannot be graded above B.

**New named nit surfaced this run (holds artifact-integrity at A, off A+):** #384 `ROUTE_INVENTORY.md`
asserts "a COMPLETE map: every route in asgi.py" but omits ≥4 real, tested routes (`/api/ai-consent`,
`/api/report`, `/api/referrals/me`, `/api/waitlist/confirm`). The endpoints + their proving tests all
exist and pass, so this is a doc-completeness overclaim, not a fabricated tick — correctable in one edit.

**Issues:** #93 (store-readiness, still C) + #92 (business-case, still B) updated with this audit's fresh
evidence, not duplicated. No new ship-critical issue filed (no ship-critical dim newly below A —
functional-reality went UP; the performance A+→A drop is a non-critical dim still ≥B). The artifact-integrity
doc-lag and the performance finding are recorded here + in the scorecard top_gaps as A→A+ / non-critical
drive-work for the factory, not as ship-critical issues.
