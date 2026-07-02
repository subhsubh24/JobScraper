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
- **Cadence:** `real` capabilities whose validation makes LIVE external calls (`ai`, `billing`)
  are exercised by `live`-marked tests that run NIGHTLY (`.github/workflows/nightly.yml`), NOT
  per-PR — so PRs stay fast + make no live calls. Per-PR runs the deterministic/mock layer; the
  real layer is still CI-validated, just on a nightly cadence (a real break is caught nightly,
  not on the PR).

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
    validation: real          # test-mode: a REAL checkout.Session.create against Stripe's TEST API
                              # (tests/test_billing_live.py) + the signature-VERIFIED webhook round-trip
                              # (tests/test_billing.py, real crypto). LIVE prod keys tracked separately.
    covered_by: tests/test_billing_live.py
    key_in_ci: true
    blocking: false
    owner_action: null
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
    validation: real          # GEMINI_API_KEY is set in CI; tests/test_llm_live.py exercises a real
                              # Gemini chat+embedding round-trip (verified running green in CI 2026-07-02)
    covered_by: tests/test_llm_live.py
    key_in_ci: true
    blocking: false
    owner_action: null
  - id: analytics
    service: "Privacy-safe aggregate analytics (internal counts; shared-secret read API)"
    env: [ANALYTICS_READ_TOKEN]
    used_for: "PMF measurement — aggregate product-event counts (no PII); owner/growth read endpoint"
    validation: real          # record path needs NO key; the shared-secret read path is fully
                              # exercised in CI by setting the token in-test (503 unset / 401 wrong / 200 right)
    covered_by: tests/test_analytics.py
    key_in_ci: false
    blocking: false           # non-critical: absence disables only the opt-in read endpoint; record_event no-ops safely
    owner_action: analytics-read-token
```

When `GEMINI_API_KEY` is present in CI, `tests/test_llm_live.py` automatically exercises a real
Gemini chat + embedding call — so adding the (spend-capped) test key upgrades `ai` from
`degraded_only` to `real` with no further code change. Then flip `ai.key_in_ci: true` +
`validation: real`.
