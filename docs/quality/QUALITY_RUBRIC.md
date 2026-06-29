# QUALITY RUBRIC — Career Operator (A+ → F)

> **Owner:** the INDEPENDENT Quality Auditor (maker ≠ checker). The factory loop
> **consumes** the grade as DATA and may NOT author or overwrite this file or
> [QUALITY_SCORECARD.md](./QUALITY_SCORECARD.md). The auditor grades the product on a
> schedule, starting cold (the git repo is the only memory), backs every letter with a
> mechanical signal it actually ran plus file/line evidence, and files the top gaps as
> issues for the factory to fix.

This rubric is the product-specific adaptation of the shared factory rubric standard to
**Career Operator's real stack**: a Python **FastAPI** backend (`asgi.py` + `src/`), a
**Next.js** (App Router, TypeScript, Tailwind) web app (`web/`), and an **Expo / React
Native** mobile app (`mobile/`), deployed on **Vercel Services** with **Neon Postgres**,
**Stripe** (web billing) + **RevenueCat** (mobile billing), and **Google Gemini** for
LLM features (degrading to a deterministic heuristic key-free).

---

## Grade scale (per dimension)

| Grade | Meaning |
|---|---|
| **A+** | Exemplary — all mechanical signals green + zero findings + clears the VISION taste/quality bar with room to spare. |
| **A** | World-class; the **ship bar**. Trivial nits only. |
| **B** | Solid with a real, named, non-blocking gap. |
| **C** | Works but has notable gaps — **below the ship bar**. |
| **D** | Significant problems. |
| **F** | Broken / unsafe / absent. **A ticked box with no real artifact is an F.** |

**Hard rules (anti-inflation is the whole job):**
1. Graded by an INDEPENDENT party — never the maker.
2. A grade may **NOT** exceed what the mechanical signals support.
3. Every grade cites concrete evidence (a bare letter is rejected).
4. Below A ⇒ name the **specific, actionable** gap.
5. Drive-to-A+ is **bounded**: named, value-bar-clearing improvements only — no gold-plating.
6. A null/ungraded dimension is **NOT** a pass.

**Ship gate:** A/A+ on **every** ship-critical dimension **and** ≥ B on all others (or a
named, justified reason). Mechanically re-checked by `scripts/check_quality.py readiness`
inside the full preflight gate.

---

## Dimensions

The canonical dimension set (shared across sibling factories; matches
`scripts/check_quality.py`):

### Ship-critical

1. **functional-reality** — the real user journeys actually WORK end-to-end at runtime, as
   a user, asserting the intended outcome (not `HTTP < 400`, not "the handler is wired").
   For Career Operator: **signup → dashboard → add job → fit score renders → job detail**
   (web Playwright `web/e2e/core-journey.spec.ts` + backend `tests/journeys/`), prep-pack
   generation, AI coach, ATS import-preview, and the billing entitlement round-trip.
   BUILDS ≠ WORKS. A dead end / error screen / button-that-does-nothing / wrong result is
   a release-blocking FAIL equal to a red test.

2. **correctness** — scrape/ingestion robustness (Greenhouse/Lever, SSRF-guarded), fit-score
   determinism + edge cases (zero-vector guard), dedup, rate-limit/backoff, graceful LLM
   degradation, error handling, the consistent error envelope + request-id correlation.

3. **security** — auth/entitlement enforced **server-side** (no client trust); every data
   surface protected; secrets never committed and never shipped to the mobile app;
   per-user/day spend ceiling (wallet-drain defense); CORS locked to known origins +
   security headers; CAPTCHA/bot-protection on public forms; lawful/ToS-respecting
   ingestion. Receipt/signature verification server-side for both Stripe and RevenueCat.

4. **design-taste** — clears the VISION/README **DESIGNER QUESTION** ("would an experienced
   product designer intentionally choose this?"); no generated-looking AI slop (the avoid
   list in VISION.md); real loading/empty/error states; accessibility (keyboard focus,
   alt text, contrast); web + mobile cohesion; not a thin-wrapper mobile app.

5. **store-readiness / launch-readiness** — what shipping THIS product requires: a REAL
   Vercel Services deploy config (build command + env contract + `/` web `/api` FastAPI
   routing) AND App Store / Play readiness for the mobile app — rendered store assets (icon,
   feature graphic, screenshots as committed image files), privacy/data-safety, account
   deletion, ASO copy, and `docs/store/ACCEPTANCE_AUDIT.md` with **ZERO open FAILs** vs
   CURRENT Apple/Google guidelines. Owner-only Human-Core items (live keys, store accounts,
   signed build, actual submission) are tracked honestly, not faked.

6. **artifact-integrity** — every ticked ROADMAP box is backed by a real artifact on the
   default branch; docs match code; no fabricated "done", metric, review, or store-readiness.
   Honest > flashy. The honest-tick guards (preflight visual-verification guard, etc.) hold.

7. **business-case-strength** — an HONEST path to the revenue floor (≥ $100K/yr ARR FLOOR),
   with high-ROI levers **built**, not just listed. Never inflate price/users/conversion to
   clear a target — a higher number that isn't real is a FAILURE. A below-floor honest number
   pre-launch is the correct state, but readiness stays REJECTED on business-case grounds
   until a named buildable lever crosses the floor.

### Not ship-critical (still graded; ≥ B to pass)

8. **tests-evals** — backend pytest + coverage floor, mobile jest-expo component tests, web
   Playwright E2E, LLM golden evals (scoring/prep/coach). Tests assert real outcomes, not
   that code compiles. Coverage floor enforced in the gate.

9. **performance** — serverless cold-start sanity, no N+1 / unbounded queries, LLM spend
   ceiling, payload sizes, web bundle / Lighthouse-ish budget, no obvious hot-path waste.

---

## Mechanical signals the auditor RUNS before grading

- `scripts/preflight.sh ci` — backend deps + flake8 + asgi import smoke + pytest (+coverage
  floor from `setup.cfg`) + mobile `tsc`/lint/jest + web `tsc`/lint + source-tracked guard.
- `python3 -m pytest -q tests` and `tests/journeys` — backend unit + functional journeys.
- `cd web && npx tsc --noEmit && npm run lint && npx playwright test` — web typecheck, lint,
  browser-level E2E journey (the core-product OUTPUT renders).
- `cd mobile && npx tsc --noEmit && npm run lint && npx jest --ci` — mobile typecheck, lint,
  component tests.
- `python3 scripts/check_quality.py parse` / `readiness` — scorecard validity + ship gate.
- `python3 scripts/check_blocks.py` — YAML invariants (business case, growth engine).
- Code/security inspection: secrets (`git ls-files`), CORS/headers/CAPTCHA/spend-ceiling in
  `asgi.py`/`src/`, SSRF guard in `src/ingestion/url_guard.py`.
- Store/launch: presence of `docs/store/assets/*.png`, committed screenshots, open FAILs in
  `docs/store/ACCEPTANCE_AUDIT.md`.
- Design: read the web pages (`web/app/**/page.tsx`) + mobile screens + theme tokens against
  the VISION DESIGNER QUESTION + AI-slop avoid list.

A grade above the evidence is a FAILURE. When evidence is thin, grade LOWER and say why.
