# SELF-VALIDATION MANIFEST — can the loop actually validate every capability?

The functional journey suite can pass in *degraded* mode (no key) while the *real* path was
never exercised. This manifest is the source of truth for **every external dependency**, the
keys it needs, **how it is validated**, where it's `covered_by`, and whether a missing key
should **block**. Enforced by `scripts/check_validation.py` (run inside the required `preflight`
check).

Two modes (pitfall: keep them distinct):
- **per-PR (default)** — declaration + surfacing + honesty guards always; an unmet `blocking`
  capability fails ONLY if the PR *touches* it (scoped via the base diff — CI checks out with
  `fetch-depth: 0`), so an unmet capability never halts unrelated work.
- **`--readiness`** — the ship gate (full `preflight`): any UNMET capability fails regardless of
  touch (you cannot ship an unvalidated capability).

Contract (the loop MUST follow; reviewers + the gate enforce it):
- **Declare every external dependency.** The gate scans RUNTIME code (`src/` + `asgi.py`, never
  tests/scripts/CI) for secret-like env vars (`*_KEY/_SECRET/_TOKEN/_WEBHOOK/DATABASE_URL`) and
  FAILS on any not declared — a NEW service can't ship unvalidated.
- **Degrade gracefully** when a key is absent (honest 503/disabled, never fake success — §6).
- **`validation`** = `real` (live/test key or real local engine) · `mock` (library mocked /
  signature round-trip — logic genuinely covered) · `degraded_only` (only the no-key path runs
  in CI — a real GAP that MUST name an `owner_action`).
- **`covered_by`** = the test that genuinely exercises it (required for `real`/`mock`). HONESTY:
  a `mock`/`real` claim is only valid if the flow is REALLY covered — readiness auditors
  reconcile that a "validated" capability isn't an un-exercised critical path hiding behind a
  stub (the email-verification trap in a new form).
- **`blocking`** = if `true`, the gate FAILS until the capability is truly validated. Policy: a
  NEWLY-added `degraded_only` capability defaults to `blocking: true` (surface + block); existing
  accepted gaps stay `false`. Every gap is ALSO surfaced as an urgent `OWNER_ACTION`
  (`validation-capability-<service>`) AND in the LOOP_HEALTH `validation` block — present in BOTH
  or it's invisible to the owner.

```yaml
VALIDATION_CAPABILITIES:
  - id: auth
    service: "JWT auth (in-process signing)"
    env: [JWT_SECRET]
    used_for: "login/session tokens"
    validation: real
    covered_by: tests/journeys/test_core_journey.py
    key_in_ci: true
    blocking: false
    owner_action: null
  - id: database
    service: "Postgres (Neon) / SQLite"
    env: [DATABASE_URL]
    used_for: "all persistence"
    validation: real
    covered_by: tests/journeys/test_core_journey.py
    key_in_ci: true
    blocking: false
    owner_action: null
  - id: billing
    service: "Stripe Checkout + webhook"
    env: [STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET]
    used_for: "subscription purchase + entitlement grant"
    validation: mock          # real checkout call mocked + a signature-VERIFIED webhook round-trip
    covered_by: tests/test_billing.py
    key_in_ci: false
    blocking: false
    owner_action: stripe-account
  - id: mobile-billing
    service: "RevenueCat webhook (mobile entitlement)"
    env: [REVENUECAT_WEBHOOK_AUTH]
    used_for: "mobile subscription entitlement grant via verified webhook"
    validation: mock          # auth round-trip verified; forged/missing/wrong grants NOTHING; 503 unset
    covered_by: tests/test_mobile_billing.py
    key_in_ci: false
    blocking: false
    owner_action: revenuecat
  - id: ai
    service: "Google Gemini (OpenAI-compat): scoring rationale, prep packs, coach"
    env: [GEMINI_API_KEY]
    used_for: "fit-score explanation, prep-pack generation, AI coach chat"
    validation: degraded_only # CI runs with an EMPTY key — only the honest-503/heuristic path is
                              # tested; the REAL Gemini call (prompt + response parsing) is NOT validated
    covered_by: tests/test_llm_live.py  # auto-runs the REAL call once GEMINI_API_KEY is in CI
    key_in_ci: false
    blocking: false           # accepted gap for now; flip true to FORCE real-AI validation before more ships
    owner_action: validation-capability-gemini
```

When `GEMINI_API_KEY` is present in CI, `tests/test_llm_live.py` automatically exercises a real
Gemini chat + embedding call — so adding the (spend-capped) test key upgrades `ai` from
`degraded_only` to `real` with no further code change. Then flip `ai.key_in_ci: true` +
`validation: real`.
