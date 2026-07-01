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
