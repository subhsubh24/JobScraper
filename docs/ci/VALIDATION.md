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
  - id: email
    service: "Email provider abstraction (Track H): waitlist double-opt-in confirmation"
    env: [EMAIL_BACKEND, SMTP_HOST, SMTP_PORT, SMTP_FROM, SMTP_USERNAME, SMTP_PASSWORD, SMTP_STARTTLS, SMTP_TIMEOUT]
                              # EMAIL_BACKEND selects the backend: dryrun (default) | capture (tests) | smtp (real).
                              # SMTP_* configure the real SMTPBackend (owner-provided; NEVER committed). The confirm
                              # token reuses JWT_SECRET (declared under `auth`) — no new token secret.
    used_for: "dispatching the waitlist confirmation email + the double-opt-in round-trip"
    validation: real          # BOTH paths exercised in CI without any live secret: (1) the send + confirm
                              # round-trip via the in-memory capture backend (tests/journeys/test_waitlist_double_optin.py);
                              # (2) the real SMTPBackend envelope/STARTTLS/login/failure-handling via a monkeypatched
                              # smtplib.SMTP (tests/test_email_smtp.py). Default prod backend is dry-run: it degrades
                              # HONESTLY (row captured, no fake 'sent' claim; delivered=False), so the app is fully
                              # functional with NO provider connected. EMAIL_BACKEND=smtp with incomplete SMTP_* config
                              # fails LOUD (explicit log) and falls back to dry-run — never a silent no-op (§28).
    covered_by: tests/journeys/test_waitlist_double_optin.py   # + tests/test_email_smtp.py (SMTPBackend)
    key_in_ci: false
    blocking: false           # non-critical: no provider -> honest dry-run; signup still works, no dead-end.
                              # Real production deliverability needs the owner's SMTP_* config (OWNER_ACTION connect-marketing).
    owner_action: null
  - id: captcha
    service: "Cloudflare Turnstile bot/abuse protection on public forms (Track F)"
    env: [TURNSTILE_SECRET]   # server-side secret ONLY (never in a client); the public sitekey is a
                              # separate NEXT_PUBLIC_TURNSTILE_SITEKEY the web widget uses.
    used_for: "verifying the client captcha token on register / login / waitlist"
    validation: mock          # The verification LOGIC is fully exercised without a live secret: the
                              # siteverify round-trip is mocked (tests/test_captcha.py) across the
                              # disabled-no-op, enabled-valid, enabled-invalid, missing/oversized-token,
                              # and verifier-error (fail-closed) branches, PLUS HTTP tests proving
                              # register/login/waitlist enforce it when enabled and are unchanged when
                              # disabled. Analogous to billing's mocked webhook-signature coverage.
    covered_by: tests/test_captcha.py
    key_in_ci: false
    blocking: false           # DECISION COROLLARY: disabled by default (no TURNSTILE_SECRET) -> pure no-op,
                              # so no pre-launch form is gated and nothing dead-ends. Rate limits are the
                              # always-on baseline. CONNECT ORDER (owner — a `connect-captcha` OWNER_ACTION
                              # covering this is filed in PENDING_OPS via the accompanying bookkeeping PR):
                              # the NATIVE mobile app sends NO captcha_token, so enabling TURNSTILE_SECRET
                              # BEFORE a mobile Turnstile/challenge flow ships would 403 every native
                              # register/login; setting it without the web NEXT_PUBLIC_TURNSTILE_SITEKEY would
                              # 403 the web forms too. Set the secret ONLY after BOTH the web sitekey and a
                              # mobile widget are deployed. (owner_action stays null here — non-blocking
                              # connect step, same pattern as `email`; the gate never blocks unrelated work.)
    owner_action: null
  - id: github_enrichment
    service: "Profile enrichment from a user's public GitHub profile (Track A /expand)"
    env: []                    # NO secret: reads the PUBLIC GitHub REST API (fixed host
                               # api.github.com) — no key, no user data sent anywhere.
    used_for: "importing the user's own repo languages/topics as source-tagged competencies that feed fit-scoring + cover letters"
    validation: mock           # The full flow is exercised without any live call: mocked
                               # api.github.com round-trips (tests/test_github_enrichment.py)
                               # pin username parsing, language/topic aggregation, fork exclusion,
                               # the Pro+ gate, honest found=0, re-import REPLACE semantics, and
                               # that discovered skills raise the fit score. NO live happy-path
                               # test: the UNAUTHENTICATED GitHub API is rate-limited (60/hr per
                               # IP) so from shared CI IPs it 403s unpredictably — a live test
                               # would be a flaky false-red, not a reliable real lane (§28). The
                               # graceful-DEGRADE path (403/network -> empty, never a raise) IS
                               # real-observable and is the mocked coverage above.
    covered_by: tests/test_github_enrichment.py
    key_in_ci: false
    blocking: false            # non-critical: any failure degrades to found=0 with an honest
                               # message; the core product is unchanged without it.
    owner_action: null
```

When `GEMINI_API_KEY` is present in CI, `tests/test_llm_live.py` automatically exercises a real
Gemini chat + embedding call — so adding the (spend-capped) test key upgrades `ai` from
`degraded_only` to `real` with no further code change. Then flip `ai.key_in_ci: true` +
`validation: real`.
