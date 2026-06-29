# QUALITY SCORECARD — Career Operator

> **Owner:** the INDEPENDENT Quality Auditor (maker ≠ checker). The factory loop CONSUMES
> this as DATA and must NOT author or overwrite it. Grades are backed by mechanical signals
> the auditor actually ran (see [QUALITY_RUBRIC.md](./QUALITY_RUBRIC.md)) plus file/line
> evidence. Grading method: 9 fresh, independent, adversarial per-dimension grader
> subagents (none wrote the product code), each running its own signal.

## Grade — 2026-06-29 (first independent audit / bootstrap)

**Overall: C** · **Ship gate met: NO** (4 of 7 ship-critical dimensions are below the A
ship bar). The product is genuinely well-engineered on the core loop — functional reality,
correctness, artifact integrity, and tests/evals all clear the A ship bar — but it is
**below the ship bar overall** because store-readiness and business-case strength sit at C
and security and design sit at B. None of these is a broken artifact; they are real,
named, mostly pre-launch gaps.

| Dimension | Ship-critical | Grade | One-line basis |
|---|---|---|---|
| functional-reality | ✅ | **A** | Core journey works end-to-end at runtime; tests assert the real fit-score OUTPUT renders + tier actually flips; web E2E green in CI. |
| correctness | ✅ | **A** | Zero-vector NaN guard, SSRF guard, request-id error envelope, bounded retries/timeouts, dedup, truthful LLM degradation — all real + tested. |
| security | ✅ | **B** | Auth/entitlement/secrets/receipt-verification/SSRF solid + tested; held below A by no CAPTCHA on public forms, per-instance-only spend-ceiling/rate-limit, and CORS defaulting to `*`. |
| design-taste | ✅ | **B** | Disciplined token-driven, genuinely-native-on-mobile markup clearing the slop list; capped at B by ZERO rendered screenshots (no visual proof) + unconverged cross-platform accent + template icon. |
| store-readiness | ✅ | **C** | Vercel deploy config genuinely ready, but 4 open ACCEPTANCE_AUDIT FAILs + missing rendered store assets/screenshots + mobile IAP not integrated. |
| artifact-integrity | ✅ | **A** | Every spot-checked ticked box backed by a real tested artifact; documented gaps stated honestly; honest-tick guard holds. |
| business-case-strength | ✅ | **C** | Honest, un-gamed $57.5K vs $100K floor — but 4 of 5 named revenue levers are entirely unbuilt and the 5th only cosmetic; readiness rejected on business-case grounds. |
| tests-evals | — | **A** | 163 backend pass @ 85.68% cov (floor 75); 34 mobile jest render real screens; golden scoring evals; web E2E asserts output. |
| performance | — | **B** | Strong LLM-cost/timeout/embedding-cache/bundle hygiene; dragged to B by unpaginated N+1 on `/api/jobs` + `/api/analytics/pipeline`. |

### Mechanical signals (auditor-run this audit)
- `flake8 .` → clean · `python3 -c "import asgi"` → ok
- `pytest -q --cov tests` → **163 passed, 85.68% cov** (setup.cfg floor 75) · `pytest tests/journeys` → **9 passed**
- `pytest tests/evals` → **23 passed**
- web `tsc` + `lint` → clean · mobile `tsc` + `lint` → clean · mobile `jest` → **34 passed (6 suites)**
- web `next build` → success · web Playwright → green in CI ("functional journeys (web E2E)" on main HEAD `cd56e8f`); local run blocked only by a sandbox chromium 1194≠1228 version mismatch (not a product defect)
- CORS `asgi.py:106` defaults to `["*"]`; security headers present `asgi.py:119-123`; no tracked secrets
- `docs/store/assets/` absent; no committed screenshots; ACCEPTANCE_AUDIT.md 4 open FAILs (A3/A4/G4/G7)
- `scripts/check_blocks.py` → `floor_met_year1=false`, `engine_pct=0`

### Top gaps to drive to A+ (ordered; ship-critical below-A first)
1. **business-case-strength (C, ship-critical):** floor not met ($57.5K < $100K) with the named levers unbuilt — build a **referral/share-a-prep-pack invite loop**, a **Career+ ($24) tier as a real entitlement** (the `careerplus_*` price envs are dead config with no tier), and a **team/seat B2B2C tier** (tier enum is binary FREE/PREMIUM). `floor_met_year1` must flip true on honest math.
2. **store-readiness (C, ship-critical):** commit **rendered store assets** (brand icon, 1024×500 feature graphic, screenshots as real image files) and integrate **mobile IAP** (StoreKit/RevenueCat + Play Billing client) to clear ACCEPTANCE_AUDIT FAILs A3/A4/G4/G7. (Live keys/signed build/submission remain owner Human-Core.)
3. **security (B, ship-critical):** add **CAPTCHA/bot-protection** on public forms (login/register/waitlist); move **rate-limit + per-user/day spend-ceiling + lockout to a cross-instance store** (Upstash Redis/Postgres) so they hold on serverless; **lock CORS to known origins** instead of defaulting to `*`.
4. **design-taste (B, ship-critical):** land the **dual-axis visual verification** (commit non-zero screenshots of the core-product output for every route/state + record the FUNCTIONAL+DESIGN verdict) so design is evidenced, not markup-inferred; converge the **web/mobile accent** (`#6366F1` vs `#5B8CFF`); replace the **Expo-template icon** with a brand mark.
5. **performance (B, non-critical):** paginate + eager-load (`selectinload`/`joinedload`) the unbounded N+1 list queries on `/api/jobs` (asgi.py:686) and `/api/analytics/pipeline` (asgi.py:938) — latent for unlimited-tier (Pro) users.

```yaml
QUALITY_SCORECARD:
  as_of: 2026-06-29
  overall: C
  ship_gate_met: false
  method: 9 independent adversarial per-dimension grader subagents (maker != checker); each ran its own mechanical signal + cited file/line evidence
  dimensions:
    - name: functional-reality
      grade: A
      ship_critical: true
      top_gaps:
        - "No committed/locally-reproducible E2E artifact for the browser journey's visual outcome — rests on the CI check (web/e2e/__screenshots__ empty)."
    - name: correctness
      grade: A
      ship_critical: true
      top_gaps:
        - "LLM daily-ceiling slot consumed even when the provider call fails (asgi.py:863) — no refund on 502 (minor)."
        - "Rate-limit + LLM ceiling are in-process dicts; effective limit multiplies per serverless instance (known, Track F)."
    - name: security
      grade: B
      ship_critical: true
      top_gaps:
        - "No CAPTCHA/bot-protection on public forms (login/register/waitlist) — only in-memory rate limits."
        - "Per-user/day spend-ceiling + rate-limit + lockout are in-memory per-instance — bypassable across serverless cold starts (need cross-instance store)."
        - "CORS defaults to allow_origins=['*'] (asgi.py:106) — not locked to known origins."
    - name: design-taste
      grade: B
      ship_critical: true
      top_gaps:
        - "Zero rendered screenshots committed (web/e2e/__screenshots__ + mobile/__screenshots__ absent; Track E unticked) — no visual proof, caps confidence at B."
        - "Cross-platform accent divergence: mobile #5B8CFF vs web #6366F1 (BRAND_KIT.md flags it)."
        - "App icon/splash are Expo template assets; no bespoke brand mark."
    - name: store-readiness
      grade: C
      ship_critical: true
      top_gaps:
        - "No rendered store assets committed: docs/store/assets/ (icon.png + 1024x500 feature_graphic.png) absent (G7 FAIL)."
        - "No committed screenshots for either surface (A3/G7 FAIL) — Accurate-Metadata review cannot pass."
        - "Mobile IAP not integrated: StoreKit/RevenueCat client (A4) + Play Billing (G4) — required before submission."
    - name: artifact-integrity
      grade: A
      ship_critical: true
      top_gaps: []
    - name: business-case-strength
      grade: C
      ship_critical: true
      top_gaps:
        - "Referral/share-a-prep-pack invite loop — not built (lowest-CAC lever)."
        - "Career+ ($24) tier as a real entitlement — careerplus_* price envs are dead config; tier enum is binary FREE/PREMIUM."
        - "Team/seat B2B2C tier — no org/seat model for bootcamp/outplacement resale."
        - "Founder/launch annual-first pricing mechanic that demonstrably lifts ARPA (current page is ordering-only)."
    - name: tests-evals
      grade: A
      ship_critical: false
      top_gaps:
        - "Prep-pack eval is structure/persistence-only with a _FakeLLM — no golden content-quality assertion."
        - "Coverage thin spots: greenhouse.py 53%, llm_workflows.py 61%."
    - name: performance
      grade: B
      ship_critical: false
      top_gaps:
        - "Unbounded N+1 list queries on /api/jobs (asgi.py:686) + /api/analytics/pipeline (asgi.py:938) — no pagination/limit, lazy relationships; latent for unlimited-tier users."
  top_gaps:
    - "business-case-strength C: floor not met ($57.5K<$100K); referral loop, Career+ tier, team/B2B2C tier all unbuilt."
    - "store-readiness C: rendered store assets + screenshots missing; mobile IAP (StoreKit/Play Billing) not integrated; 4 open ACCEPTANCE_AUDIT FAILs."
    - "security B: no CAPTCHA on public forms; spend-ceiling/rate-limit per-instance only; CORS defaults to '*'."
    - "design-taste B: no rendered visual-verification screenshots; web/mobile accent divergence; template icon."
    - "performance B: unpaginated N+1 on /api/jobs + /api/analytics/pipeline."
```
