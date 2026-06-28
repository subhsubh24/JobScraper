# PENDING OPS — Owner Actions (Human-Core)

> Work the factory loop **cannot** do — owner only. The machine-readable `OWNER_ACTIONS`
> block is parsed by the shared dashboard. Honest status only.

These are the only things blocking the product the loop literally may not do for you:
billing/store accounts, signing, live keys, funding, spend caps, and the actual
submission. Everything else the factory builds.

```yaml
OWNER_ACTIONS:
  project: jobscraper
  as_of: 2026-06-28
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
      title: "Create RevenueCat account + map StoreKit/Play Billing products"
      priority: normal
      status: open
      why: "Mobile entitlement verification needs the cross-store keys + product mapping."
      how: "Create RevenueCat project; add iOS/Android API keys to mobile build env (public SDK key only on device; secret stays server-side)."
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
      how: "cd mobile; `eas init` (writes/sets EAS_PROJECT_ID); set submit secrets (APPLE_ID/ASC_APP_ID/APPLE_TEAM_ID, google-play-service-account.json); set EXPO_PUBLIC_API_URL to the live deployment in eas.json production env; `eas build --profile production` then `eas submit --profile production`."
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
    - id: legal-review
      title: "Have counsel review Privacy Policy + ToS; provision the contact inboxes"
      priority: normal
      status: open
      why: "The /privacy + /terms pages are real and code-accurate, but auto-authored (not lawyer-reviewed); they lack a governing-law/arbitration clause, and the listed contact addresses don't exist yet. Apple/Google require a working privacy contact at submission."
      how: "Have counsel review web/app/{privacy,terms}/page.tsx (add governing law + dispute resolution if desired). Provision privacy@careeroperator.app and support@careeroperator.app (or update the addresses on both pages to real ones) BEFORE store submission."
    - id: ci-wiring
      title: "Apply staged CI as REQUIRED checks (workflow scope) — docs/ci/PROPOSED_CI.md"
      priority: high
      status: open
      why: "Today PRs auto-merge via `gh pr merge --admin` with NO required status check, so a BUILDS!=WORKS / lint-dirty change could slip in. The loop must NOT edit .github/ (it hangs the headless run), so the exact workflow + required-checks list are STAGED. See loop: harness improvement proposal issue #57."
      how: "Apply docs/ci/PROPOSED_CI.md's `.github/workflows/ci.yml` (needs `workflow` scope). VERIFY both jobs go GREEN on a PR first, THEN branch-protect `main` requiring `preflight (lint + typecheck + tests)` + `functional journeys (web E2E)` — never require a red/flaky check (it blocks the loop). Then flip LOOP_HEALTH.enforced_in_ci: true and close #57."
    - id: auto-migrate
      title: "Enable auto-migrate-on-deploy (alembic upgrade head on main) — one-time setup"
      priority: high
      status: open
      why: "Real Alembic migrations now ship (initial schema committed; a gate test fails the build if models change without a migration). Auto-applying them on deploy ends the manual `python scripts/init_db.py` after every schema change. Auto-apply replaces the manual human schema checkpoint, so it needs a recoverability net + a one-time baseline; the loop cannot set GitHub secrets, enable backups, or push .github/."
      how: "1) Enable Neon PITR / daily backups FIRST (recoverability net). 2) Baseline the existing DB ONCE (it was created via create_all): `DATABASE_URL='<neon pooled>' alembic stamp head`. 3) Add a GitHub Actions secret DATABASE_URL = the Neon pooled string (never inline/commit it). 4) Set AUTO_CREATE_TABLES=0 in Vercel so Alembic is the single schema source. 5) Apply the `migrate` job from docs/ci/PROPOSED_CI.md (default-branch + post-gate + forward-only; NOT a required PR check). TRADEOFF: a destructive migration that passes review will auto-apply — PITR is how you undo it."
    - id: email-verification-deferred
      title: "DECISION: signup is NOT gated on email verification (no email pipeline wired)"
      priority: normal
      status: done
      why: "DECISION COROLLARY (FACTORY_STANDARD §6): never gate on an unbuilt loop. Signup returns a usable session and lands the user in the working app — no 'check your email' dead-end. Audited 2026-06-28: no verification/confirmation gate exists in auth."
      how: "Re-enable email verification / password-reset / 2FA ONLY together with a real provider (or sandbox) + a round-trip journey test (F4.1) that receives the email, follows the link, and completes the flow. Until then, do not introduce the gate."
```
