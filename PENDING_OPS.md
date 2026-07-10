# PENDING OPS — Owner Actions (Human-Core)

> Work the factory loop **cannot** do — owner only. The machine-readable `OWNER_ACTIONS`
> block is parsed by the shared dashboard. Honest status only.

These are the only things blocking the product the loop literally may not do for you:
billing/store accounts, signing, live keys, funding, spend caps, and the actual
submission. Everything else the factory builds.

```yaml
OWNER_ACTIONS:
  project: jobscraper
  as_of: 2026-07-04
  items:
    - id: site-gate
      title: "DECISION NEEDED: the pre-launch SITE GATE was REMOVED at owner request 2026-07-02 — the app is PUBLIC. Re-instate it, or drop the gated-beta track?"
      priority: high
      status: open
      why: "CORRECTION (run 34, 2026-07-09): the earlier version of this item was STALE and would silently no-op. web/middleware.ts is now an INTENTIONAL pass-through — the SITE GATE was deleted 2026-07-02 at owner request ('the app is PUBLIC') and the middleware NO LONGER honors SITE_GATE_PASSWORD. So setting that env var today does NOTHING. Meanwhile ROADMAP:421 (SITE GATE) + ROADMAP:458 (§34 gated-beta invite mechanism, which DEPENDS on the gate) + GROWTH_STATUS.site_gate_up still assume a gate exists. The factory will NOT autonomously re-add a gate the owner explicitly removed — this needs an owner decision."
      how: "Choose one: (A) RE-INSTATE a pre-launch gate — restore the HTTP Basic Auth / cookie check against process.env.SITE_GATE_PASSWORD in web/middleware.ts (exempt /, /waitlist, /coming-soon, /privacy, /terms, /legal; see git history pre-2026-07-02), THEN the factory can build the §34 gated-beta invite mechanism on top and flip GROWTH_STATUS.site_gate_up: true after setting the password in Vercel env. (B) KEEP the app PUBLIC — then the §34 gated-beta track (waitlist→codes→gated app) is moot and should be dropped from the roadmap; pre-launch outreach discipline then rests on the demo/waitlist funnel, not a gate. Tell the factory which, and it will reconcile ROADMAP + GROWTH_STATUS accordingly."
    - id: spend-caps
      title: "Set HARD provider spend caps + alerts (Gemini/Google AI, Vercel, Stripe) NOW"
      priority: urgent
      status: open
      why: "LLM + scrape + hosting are wallet-drain targets; a capless loop once burned $47k."
      how: "Google AI Studio / Gemini API usage limits; Vercel usage/spend alerts; Stripe Radar/limits. Set monthly hard caps before any live traffic."
    - id: stripe-account
      title: "Create Stripe account + products/prices + wire the webhook (web billing CODE is built) — HALF-DONE: Pro test prices set, Career+ NOT (nightly RED)"
      priority: high
      status: open
      nightly_state: "As of run 38 (2026-07-10) the nightly live lane is RED on exactly this: 4 failed / 17 passed, all 4 = tests/test_billing_live.py careerplus_monthly+annual (STRIPE_PRICE_CAREERPLUS_MONTHLY/ANNUAL unset). The Gemini AI-output evals + the Pro-plan billing checks PASS — so the sk_test key + STRIPE_PRICE_PRO_* ARE already provisioned; only the 2 Career+ test-mode price secrets remain. Setting them (Settings->Secrets->Actions) greens the nightly AND unblocks selling Career+. This RED is intended fail-loud (§28: a sellable tier with no price = a prod 503, #222) — do NOT expect the loop to 'fix' it; it is one owner step from green."
      why: "Web subscription billing CODE now ships (PR #40): POST /api/billing/checkout makes a real Stripe Checkout session; POST /api/billing/webhook verifies the signature and grants entitlement. Career+ is now a REAL tier (PRs #152/#153/#155) — its entitlement level is derived from a webhook-verified careerplus_* Subscription.plan — so the CAREERPLUS_* price IDs are now REQUIRED to sell Career+ (no longer optional). It refuses honestly (503, no charge) until these owner-only secrets exist. Live keys + price IDs + the webhook signing secret must NOT be held by the loop."
      how: "1) Create the Stripe products/prices: Pro monthly $12 + annual $96, AND Career+ monthly $24 + annual $192 (needed for the live Career+ tier). 2) In the deploy env set STRIPE_SECRET_KEY, STRIPE_PRICE_PRO_MONTHLY, STRIPE_PRICE_PRO_ANNUAL, STRIPE_PRICE_CAREERPLUS_MONTHLY, STRIPE_PRICE_CAREERPLUS_ANNUAL. 3) In the Stripe Dashboard add a webhook endpoint -> https://<deploy>/api/billing/webhook for events checkout.session.completed, customer.subscription.updated, customer.subscription.deleted; copy its signing secret into STRIPE_WEBHOOK_SECRET. 4) Optionally set WEB_APP_URL if the API origin differs from the site. Test with Stripe test-mode keys first; never commit any STRIPE_* value. Until set, the paywall stays honestly disabled (no fake charge). CI REAL-VALIDATION (optional, upgrades `billing` mock->real): also add the SAME test-mode secrets as GitHub Actions repository secrets (Settings->Secrets->Actions) — STRIPE_SECRET_KEY (a sk_test_ key ONLY), STRIPE_PRICE_PRO_MONTHLY (and/or ANNUAL), STRIPE_PRICE_CAREERPLUS_MONTHLY + STRIPE_PRICE_CAREERPLUS_ANNUAL (now covered by the live lane), STRIPE_WEBHOOK_SECRET — and tests/test_billing_live.py will create a REAL test-mode Checkout Session for EVERY sellable plan in CI (no money). NOTE (PR #229, §26/§28): the nightly live lane now validates ALL 4 plans, so if the CAREERPLUS_* test-mode prices are absent while REQUIRE_LIVE_TESTS=1, the nightly will RED — this is intended (Career+ is a live sellable tier; an unset price is a prod 503 dead-end). Set all four price secrets, or the nightly reddens by design. Then the loop flips VALIDATION.md `billing` -> real. FOLLOW-UP (loop, code — not owner): a Pro->Career+ IN-PLACE upgrade needs the Stripe billing portal (avoids double-billing); today a Pro user is shown an honest 'switch on the web / coming soon' message rather than a second checkout."
    - id: apple-developer
      title: "Enroll Apple Developer Program ($99/yr) + App Store Connect app record"
      priority: high
      status: open
      why: "Required to sign and submit the iOS app; loop cannot create accounts or sign."
      how: "developer.apple.com enroll; create the app record + bundle id; add to EAS/credentials."
    - id: google-play
      title: "Create Google Play Console account ($25 one-time) + app listing"
      priority: high
      status: open
      why: "Required to submit the Android app."
      how: "play.google.com/console; create app; set up Play Billing products."
    - id: revenuecat
      title: "Create RevenueCat account + map StoreKit/Play Billing products + set the webhook secret"
      priority: normal
      status: open
      why: "Mobile entitlement verification needs the cross-store keys + product mapping. The SERVER half is now BUILT (PR #87): POST /api/billing/revenuecat-webhook verifies a shared-secret Authorization header and flips users.tier ONLY from a verified event (grant on purchase/renewal, revoke on EXPIRATION/PAUSED); forged/missing grants nothing (401); unset secret refuses honestly (503). It stays inert until the owner-only secret + keys exist. The on-device client SDK (react-native-purchases) to INITIATE purchases is still owner-blocked/native."
      how: "1) Create the RevenueCat project; map the StoreKit + Play Billing products to a 'premium' entitlement. 2) In the deploy env set REVENUECAT_WEBHOOK_AUTH to a strong random secret (never commit it). 3) In the RevenueCat dashboard add a webhook -> https://<deploy>/api/billing/revenuecat-webhook with that same Authorization header value. 4) Add the public iOS/Android SDK keys to the mobile build env (public SDK key only on device; never the secret). 5) Configure the app to set RevenueCat's appUserID to our User.id so events map back. FOLLOW-UPS (loop, code — not owner): wire the on-device react-native-purchases SDK to initiate purchases (Track C line 114); handle the TRANSFER event (revoke the source user) and add event-ordering/idempotency (store last-event timestamp) before high-volume go-live."
    - id: app-signing
      title: "App signing / EAS credentials for iOS + Android"
      priority: normal
      status: open
      why: "Loop runs on Linux/CI and cannot hold signing identities."
      how: "Configure EAS credentials or upload keystores; the loop builds, you sign/submit."
    - id: eas-build-submit
      title: "EAS: eas init (project id) + production build + store submit"
      priority: high
      status: open
      why: "eas.json profiles + app.config.ts exist and are validated, but the actual signed cloud build and store submission are Human-Core (signing, store accounts, project creation)."
      how: "cd mobile; `eas init` (writes/sets EAS_PROJECT_ID); set submit secrets (APPLE_ID/ASC_APP_ID/APPLE_TEAM_ID, google-play-service-account.json); set EXPO_PUBLIC_API_URL to the live API deployment AND EXPO_PUBLIC_WEB_URL to the live web-app origin (used by the mobile 'Refer a friend' share link so /register resolves; falls back to the API origin, correct only for the unified Vercel deploy) in eas.json production env; `eas build --profile production` then `eas submit --profile production`."
    - id: connect-marketing
      title: "Connect + authorize marketing channels (email provider, analytics) to enable execute-mode"
      priority: normal
      status: open
      why: "Growth Agent stays in prepare-mode until a connected, funded, authorized channel exists. The email SEAM is now BUILT (PR #187, src/email): waitlist double-opt-in dispatches a confirmation email + a signed confirm link, but the default backend is DRY-RUN (logs, delivers nothing) — so no confirmation email actually leaves the system until a real provider is connected. The app is fully functional without it (the waitlist row is captured either way); this only activates confirmation delivery."
      how: "Follow docs/growth/CONNECT.md (~20 min). To ACTIVATE waitlist-confirmation email delivery specifically: a real delivering backend now EXISTS (src/email SMTPBackend) — no code needed. Set EMAIL_BACKEND=smtp + the SMTP_* config (SMTP_HOST, SMTP_FROM, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD; STARTTLS on by default) for your ESP (SendGrid/Mailgun/SES all speak SMTP), AND set WEB_APP_URL to the live public origin (the confirm LINK is built ONLY from WEB_APP_URL — never the request Host, an anti-phishing measure — so double-opt-in emails are silently NOT sent until WEB_APP_URL is set). Never commit any SMTP_* value. Then the Growth Agent can queue/measure for real."
    - id: connect-captcha
      title: "Connect Cloudflare Turnstile — set the keys ONLY after a mobile widget ships (else native auth 403s)"
      priority: normal
      status: open
      why: "The bot-protection seam is BUILT (PR #226, src/security/captcha.py): register/login/waitlist verify a Turnstile token server-side, and the web forms render the widget. It is DISABLED until TURNSTILE_SECRET is set, so pre-launch nothing is gated (per-IP rate limits are the always-on baseline). ORDERING RISK — enforcement fails CLOSED, so: (a) the NATIVE mobile app sends NO captcha_token, so setting TURNSTILE_SECRET before a mobile challenge flow ships would 403 EVERY native register/login (a mobile-auth outage); (b) setting TURNSTILE_SECRET without the web NEXT_PUBLIC_TURNSTILE_SITEKEY would 403 the web forms too (the widget never renders, so no token). This is defense-in-depth vs distributed/IP-rotating signup+login floods — not required for launch."
      how: "1) Create a free Cloudflare Turnstile widget → get the SITEKEY (public) + SECRET (server). 2) FIRST ship a NATIVE mobile Turnstile/challenge flow that sends captcha_token on the mobile register/login calls (react-native-turnstile or a webview) — this is a LOOP/native follow-up, not owner work. 3) ONLY THEN, and TOGETHER: set NEXT_PUBLIC_TURNSTILE_SITEKEY (web build env) + TURNSTILE_SECRET (server env; never commit). Never set the server secret alone. Until all three are done the seam stays inert + safe. (Optional CI real-validation: none needed — the logic is fully covered by the mocked round-trip in tests/test_captcha.py.)"
    - id: analytics-read-token
      title: "OPTIONAL: set ANALYTICS_READ_TOKEN to enable the aggregate growth-metrics read endpoint"
      priority: normal
      status: open
      why: "The privacy-safe aggregate analytics (PR #146) RECORD path needs no key and runs automatically. The READ endpoint GET /api/analytics/summary (aggregate counts + activation funnel, no PII) is gated by a server-side shared secret and returns an honest 503 until it's set — the product is fully functional without it; this only unlocks the owner/growth dashboard read."
      how: "In the deploy env set ANALYTICS_READ_TOKEN to a strong random value (openssl rand -hex 32; never commit it). Then read metrics with `Authorization: Bearer <token>` against GET /api/analytics/summary. Rotate freely — no data migration needed. Not required for launch."
    - id: deploy-env
      title: "Set Vercel env vars + deploy (Neon DB done)"
      priority: high
      status: in_progress
      why: "Neon project 'JobScraper' is provisioned and the schema is created + verified (full journey ran green against it). Remaining: set server-side env vars in Vercel and deploy."
      how: "DONE: Neon DB + 9 tables via pooled endpoint. TODO: in Vercel set DATABASE_URL (Neon pooled string), JWT_SECRET (openssl rand -hex 32), optional GEMINI_API_KEY + ALLOWED_ORIGINS; deploy; verify GET /api/health. See docs/DEPLOY_VERCEL.md. Never commit .env. ENFORCED (rule b, §28 fail-loud): the API now REFUSES to start on Vercel if (a) JWT_SECRET is unset or the dev default (auth tokens would be forgeable), OR (b) DATABASE_URL is not a postgresql:// URL — added PR #228, because SQLite has no persistence on serverless and would SILENTLY WIPE all user data on every cold start. So DATABASE_URL MUST be set to the Neon pooled Postgres string BEFORE the next deploy or /api will fail loud (by design — a loud boot failure beats silent data loss)."
    - id: texas-age-assurance
      title: "DECISION: Texas SB 2420 age-assurance (effective 2026-06-04) — build / rate-gate 17+ / defer"
      priority: normal
      status: open
      why: "Surfaced by the run-8 store scout (WebSearch of current 2026 Apple/Google policy). Apple states new accounts in Texas are subject to age assurance + parental-consent for minors under 18; the app currently collects no age at signup. This is a legal/positioning decision the loop must NOT make: (a) build age verification (birthday + a verification partner), (b) rate the app 17+ (sidesteps minor consent, narrows the market), or (c) defer/accept the risk for a non-TX or post-launch launch. Not a hard code blocker today, but a real store-acceptance + legal exposure to decide before a US launch."
      how: "Decide a/b/c with counsel. If (a): the loop can build the signup age field + integrate a verification provider (e.g. Veriff) behind an env flag + a round-trip test — open it as ROADMAP work. If (b): set the age rating in App Store Connect / Play Console + update ASO. If (c): document the accepted risk + the non-TX scope. Re-evaluate as Apple/Google age-rating questionnaires update through 2026."
    - id: legal-review
      title: "Have counsel review Privacy Policy + ToS; provision the contact inboxes"
      priority: normal
      status: open
      why: "The /privacy + /terms pages are real and code-accurate, but auto-authored (not lawyer-reviewed); they lack a governing-law/arbitration clause, and the listed contact addresses don't exist yet. Apple/Google require a working privacy contact at submission."
      how: "Have counsel review web/app/{privacy,terms}/page.tsx (add governing law + dispute resolution if desired). Provision privacy@careeroperator.app and support@careeroperator.app (or update the addresses on both pages to real ones) BEFORE store submission."
    - id: ci-wiring
      title: "CI as REQUIRED checks — DONE + enforced (2026-06-29)"
      priority: normal
      status: done
      why: "`.github/workflows/ci.yml` is live; branch protection on main requires `preflight (lint + typecheck + tests)` + `functional journeys (web E2E)` with enforce_admins=ON; auto-merge enabled; loop merges via `gh pr merge --squash --auto`. Validated end-to-end (PR #61 blocked until green, then auto-merged). Proposal #57 closed; LOOP_HEALTH.enforced_in_ci=true."
      how: "Done. NOTE (residual fragility): if the CI workflow itself breaks (action deprecation/flake), required checks block ALL merges and the loop can't fix .github/ — that needs the owner. The Node-20→24 deprecation warning is benign for now; bump action versions when convenient."
    - id: auto-migrate
      title: "Auto-migrate-on-deploy — ENABLED + verified (2026-06-29)"
      priority: normal
      status: done
      why: "Real Alembic migrations ship + a gate test fails the build on model/migration drift. The migrate job (.github/workflows/ci.yml) applies `alembic upgrade head` on push to main, post-gate, forward-only. DONE: Neon PITR enabled (owner); DATABASE_URL GitHub Actions secret set; existing DB stamped at head via the manual db-stamp workflow and VERIFIED against the models (LIVE TABLES == MODEL TABLES, MISSING/EXTRA empty, alembic_version=head). Future migrations now self-apply on merge."
      how: "Optional cleanup (not required for correctness): set AUTO_CREATE_TABLES=0 in Vercel so Alembic is the single schema source (create_all still only ADDS missing tables, and the CI drift gate catches a missing migration, so leaving it on is safe). Re-baseline anytime via the manual `DB stamp (one-time baseline)` workflow. TRADEOFF (accepted): a destructive migration that passes review auto-applies — Neon PITR is the undo."
    - id: rotate-db-credential
      title: "SECURITY: rotate the Neon DB password (it appeared in a chat transcript)"
      priority: urgent
      status: open
      why: "During auto-migrate setup the Neon connection string (incl. password) was pasted into an assistant chat several times, so it must be treated as compromised. The DB is SSL-gated by this password; anyone with the string could connect."
      how: "Neon Console -> Roles -> reset neondb_owner password. Then update the NEW pooled string in BOTH places via UI (no terminal/transcript): GitHub repo Settings -> Secrets -> Actions -> DATABASE_URL, and Vercel env DATABASE_URL -> redeploy. The DB stays stamped (the marker lives in the DB, survives password change); no re-stamp needed."
    - id: validation-capability-gemini
      title: "GEMINI_API_KEY in CI — DONE (real AI path validated) 2026-07-02"
      priority: normal
      status: done
      why: "The `ai` capability was validation=degraded_only (CI ran Gemini with an EMPTY key, so only the honest-503/heuristic path was exercised). Owner added a GEMINI_API_KEY Actions secret; the preflight-ci job passes it to pytest so tests/test_llm_live.py now exercises a REAL Gemini chat+embedding round-trip — a loop change that breaks the real AI call is now caught by CI."
      how: "DONE: secret added (2026-07-02); ci.yml passes secrets.GEMINI_API_KEY to the preflight-ci job (PR #160); VALIDATION.md `ai` flipped to validation: real / key_in_ci: true after the live test was verified running green in CI. Keep the key's spend cap in place; rotate if it ever leaks (same UI path)."
    - id: require-live-tests
      title: "OPTIONAL: set REQUIRE_LIVE_TESTS=1 in the nightly workflow so a missing live key REDDENS (not skips)"
      priority: normal
      status: open
      why: "FACTORY_STANDARD §28: the nightly `live` lane (real Gemini + Stripe test-mode round-trips) uses skipif(not KEY) — so if a secret is rotated away or never set in the nightly env, the 'real' lane passes having validated NOTHING (a synthetic green). The loop built the fail-loud mechanism (tests/live_guard.py): with REQUIRE_LIVE_TESTS set, a missing key becomes a hard FAILURE instead of a silent skip. The loop cannot edit .github, so wiring the env is owner-only."
      how: "In .github/workflows/nightly.yml, add REQUIRE_LIVE_TESTS: '1' to the live job's `env:` block (alongside GEMINI_API_KEY/STRIPE_*). Then a nightly run with a missing/rotated secret fails loudly (GitHub emails you) instead of green-passing. Keep the secrets present so the real round-trips actually run. If you intentionally drop a live lane, remove its secret AND leave REQUIRE_LIVE_TESTS unset for that run, or the lane will (correctly) redden."
    - id: email-verification-deferred
      title: "DECISION: signup is NOT gated on email verification (no email pipeline wired)"
      priority: normal
      status: done
      why: "DECISION COROLLARY (FACTORY_STANDARD §6): never gate on an unbuilt loop. Signup returns a usable session and lands the user in the working app — no 'check your email' dead-end. Audited 2026-06-28: no verification/confirmation gate exists in auth."
      how: "Re-enable email verification / password-reset / 2FA ONLY together with a real provider (or sandbox) + a round-trip journey test (F4.1) that receives the email, follows the link, and completes the flow. Until then, do not introduce the gate."
```
