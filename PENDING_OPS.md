# PENDING OPS — Owner Actions (Human-Core)

> Work the factory loop **cannot** do — owner only. The machine-readable `OWNER_ACTIONS`
> block is parsed by the shared dashboard. Honest status only.

These are the only things blocking the product the loop literally may not do for you:
billing/store accounts, signing, live keys, funding, spend caps, and the actual
submission. Everything else the factory builds.

```yaml
OWNER_ACTIONS:
  project: jobscraper
  as_of: 2026-06-29
  items:
    - id: site-gate
      title: "Pre-launch SITE GATE: set SITE_GATE_PASSWORD=deepster now; unset at launch"
      priority: high
      status: open
      why: "Don't expose the half-baked app pre-launch. The gate (web/middleware.ts) password-protects the web app but exempts the public marketing/legal routes so waitlist still works. ALSO required to flip GROWTH_STATUS.site_gate_up: true, which is the HARD precondition for the Growth Agent to do any pre-launch outreach."
      how: "In Vercel env set SITE_GATE_PASSWORD=deepster (never commit it); then set GROWTH_STATUS.site_gate_up: true. At launch (every ship-critical QUALITY_SCORECARD dim A/A+ + readiness), UNSET SITE_GATE_PASSWORD to open the app. Mobile pre-launch: distribute via TestFlight / internal track only."
    - id: spend-caps
      title: "Set HARD provider spend caps + alerts (Gemini/Google AI, Vercel, Stripe) NOW"
      priority: urgent
      status: open
      why: "LLM + scrape + hosting are wallet-drain targets; a capless loop once burned $47k."
      how: "Google AI Studio / Gemini API usage limits; Vercel usage/spend alerts; Stripe Radar/limits. Set monthly hard caps before any live traffic."
    - id: stripe-account
      title: "Create Stripe account + products/prices + wire the webhook (web billing CODE is built)"
      priority: high
      status: open
      why: "Web subscription billing CODE now ships (PR #40): POST /api/billing/checkout makes a real Stripe Checkout session; POST /api/billing/webhook verifies the signature and grants entitlement. It refuses honestly (503, no charge) until these owner-only secrets exist. Live keys + price IDs + the webhook signing secret must NOT be held by the loop."
      how: "1) Create the Stripe products/prices (Pro monthly $12 + annual $96; optionally Career+). 2) In the deploy env set STRIPE_SECRET_KEY, STRIPE_PRICE_PRO_MONTHLY, STRIPE_PRICE_PRO_ANNUAL (and STRIPE_PRICE_CAREERPLUS_* if used). 3) In the Stripe Dashboard add a webhook endpoint -> https://<deploy>/api/billing/webhook for events checkout.session.completed, customer.subscription.updated, customer.subscription.deleted; copy its signing secret into STRIPE_WEBHOOK_SECRET. 4) Optionally set WEB_APP_URL if the API origin differs from the site. Test with Stripe test-mode keys first; never commit any STRIPE_* value. Until set, the paywall stays honestly disabled (no fake charge)."
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
      why: "Growth Agent stays in prepare-mode until a connected, funded, authorized channel exists."
      how: "Follow docs/growth/CONNECT.md (~20 min). Then the Growth Agent can queue/measure for real."
    - id: deploy-env
      title: "Set Vercel env vars + deploy (Neon DB done)"
      priority: high
      status: in_progress
      why: "Neon project 'JobScraper' is provisioned and the schema is created + verified (full journey ran green against it). Remaining: set server-side env vars in Vercel and deploy."
      how: "DONE: Neon DB + 9 tables via pooled endpoint. TODO: in Vercel set DATABASE_URL (Neon pooled string), JWT_SECRET (openssl rand -hex 32), optional GEMINI_API_KEY + ALLOWED_ORIGINS; deploy; verify GET /api/health. See docs/DEPLOY_VERCEL.md. Never commit .env. ENFORCED (rule b): the API now REFUSES to start on Vercel if JWT_SECRET is unset or the dev default — set a strong JWT_SECRET BEFORE the next deploy or /api will fail loud (by design; auth tokens would be forgeable otherwise)."
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
      title: "Add GEMINI_API_KEY (test key + spend cap) to CI so the REAL AI path is validated"
      priority: urgent
      status: open
      why: "The self-validation manifest (docs/ci/VALIDATION.md) flags `ai` as validation=degraded_only: CI runs Gemini with an EMPTY key, so only the honest-503/heuristic path is exercised — the REAL Gemini call (prompt + response parsing) is never validated. A loop change that breaks the real AI call would NOT be caught by CI."
      how: "Create a Gemini API key scoped to a HARD monthly spend cap (Google AI Studio usage limits), then add it as a GitHub Actions repository secret GEMINI_API_KEY (Settings -> Secrets -> Actions). tests/test_llm_live.py auto-runs a tiny real chat+embedding call when the key is present. Wire the key into the CI jobs' env, then flip VALIDATION.md `ai`: key_in_ci: true, validation: real. To FORCE this before more AI work ships, set `ai.blocking: true` (the gate will then block merges until the key is in CI)."
    - id: email-verification-deferred
      title: "DECISION: signup is NOT gated on email verification (no email pipeline wired)"
      priority: normal
      status: done
      why: "DECISION COROLLARY (FACTORY_STANDARD §6): never gate on an unbuilt loop. Signup returns a usable session and lands the user in the working app — no 'check your email' dead-end. Audited 2026-06-28: no verification/confirmation gate exists in auth."
      how: "Re-enable email verification / password-reset / 2FA ONLY together with a real provider (or sandbox) + a round-trip journey test (F4.1) that receives the email, follows the link, and completes the flow. Until then, do not introduce the gate."
```
