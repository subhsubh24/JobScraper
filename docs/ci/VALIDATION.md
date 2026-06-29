# SELF-VALIDATION MANIFEST — can the loop actually validate every capability?

The functional journey suite can pass in *degraded* mode (no key) while the *real* path was
never exercised. This manifest is the source of truth for **every external dependency**, the
keys it needs, **how it is validated**, and whether a missing key should **block**. It is
enforced by `scripts/check_validation.py` (a required CI check).

Contract (the loop MUST follow; reviewers + the gate enforce it):
- **Declare every external dependency here.** The gate scans the code for secret-like env vars
  (`*_KEY`, `*_SECRET`, `*_TOKEN`, `*_WEBHOOK`, `DATABASE_URL`, …) and FAILS if one is used but
  not declared below — so a NEW service can't ship silently.
- **Degrade gracefully** when a key is absent (honest 503/disabled, never fake success — §6
  SIDE-EFFECT INTEGRITY). A capability that can't self-validate without an owner key is a GAP:
  it MUST name an `owner_action` (so it surfaces on the dashboard).
- **`validation`** = how the real behavior is proven: `real` (exercised with a live/test key or
  a real local engine) · `mock` (library mocked / signature round-trip — logic genuinely
  covered) · `degraded_only` (only the no-key path runs in CI — a real GAP).
- **`blocking`** = if `true`, the gate FAILS (blocks ALL merges) until the capability is truly
  validated (key present / not degraded_only). Policy: a NEWLY-added `degraded_only` capability
  defaults to `blocking: true` (surface + block until the owner provides the key or consciously
  sets it `false`). Existing accepted gaps stay `false` so the loop keeps running.

```yaml
VALIDATION_CAPABILITIES:
  - id: auth
    service: "JWT auth (in-process signing)"
    env: [JWT_SECRET]
    used_for: "login/session tokens"
    validation: real          # conftest + e2e set a real signing secret; full journey exercises it
    key_in_ci: true
    blocking: false
    owner_action: null
  - id: database
    service: "Postgres (Neon) / SQLite"
    env: [DATABASE_URL]
    used_for: "all persistence"
    validation: real          # CI runs the journeys against a real sqlite engine; migrate job hits Neon
    key_in_ci: true
    blocking: false
    owner_action: null
  - id: billing
    service: "Stripe Checkout + webhook"
    env: [STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET]
    used_for: "subscription purchase + entitlement grant"
    validation: mock          # tests/test_billing.py: real checkout call mocked + a signature-VERIFIED
                              # webhook round-trip (forged/unsigned grant NOTHING). Live keys = SHIP gate.
    key_in_ci: false
    blocking: false
    owner_action: stripe-account
  - id: mobile-billing
    service: "RevenueCat webhook (mobile entitlement)"
    env: [REVENUECAT_WEBHOOK_AUTH]
    used_for: "mobile subscription entitlement grant via verified webhook"
    validation: mock          # tests/test_mobile_billing.py sets a test secret + verifies the auth
                              # round-trip (forged/missing/wrong header grants NOTHING; 503 when unset)
    key_in_ci: false
    blocking: false
    owner_action: revenuecat
  - id: ai
    service: "Google Gemini (OpenAI-compat): scoring rationale, prep packs, coach"
    env: [GEMINI_API_KEY]
    used_for: "fit-score explanation, prep-pack generation, AI coach chat"
    validation: degraded_only # CI runs with an EMPTY key, so only the honest-503/heuristic path is
                              # tested; the REAL Gemini call (prompt + response parsing) is NOT validated
    key_in_ci: false
    blocking: false           # accepted gap for now; flip true to FORCE real-AI validation before more ships
    owner_action: validate-ai-ci
```

When `GEMINI_API_KEY` is present in CI, `tests/test_llm_live.py` automatically exercises a real
Gemini chat + embedding call — so adding the (spend-capped) test key upgrades `ai` from
`degraded_only` to `real` with no further code change. Flip `ai.key_in_ci: true` +
`validation: real` then.
