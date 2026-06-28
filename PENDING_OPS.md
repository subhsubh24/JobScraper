# PENDING OPS — Owner Actions (Human-Core)

> Work the factory loop **cannot** do — owner only. The machine-readable `OWNER_ACTIONS`
> block is parsed by the shared dashboard. Honest status only.

These are the only things blocking the product the loop literally may not do for you:
billing/store accounts, signing, live keys, funding, spend caps, and the actual
submission. Everything else the factory builds.

```yaml
OWNER_ACTIONS:
  project: jobscraper
  as_of: 2026-06-27
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
      title: "Create Stripe account + products/prices (Pro/Career+ monthly+annual)"
      priority: high
      status: open
      why: "Web subscription billing needs live keys + price IDs the loop must not hold."
      how: "Create products in Stripe; copy price IDs into deploy env (STRIPE_*). Never commit them."
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
      title: "Wire preflight + journey suite + mobile build into CI (needs workflow scope)"
      priority: normal
      status: open
      why: "The loop must NOT edit .github/; CI cannot be added by the loop."
      how: "Add a GitHub Actions workflow: pip install -r requirements-dev.txt, run scripts/preflight.sh ci (backend + cd mobile && npm ci && tsc/lint)."
    - id: email-verification-deferred
      title: "DECISION: signup is NOT gated on email verification (no email pipeline wired)"
      priority: normal
      status: done
      why: "DECISION COROLLARY (FACTORY_STANDARD §6): never gate on an unbuilt loop. Signup returns a usable session and lands the user in the working app — no 'check your email' dead-end. Audited 2026-06-28: no verification/confirmation gate exists in auth."
      how: "Re-enable email verification / password-reset / 2FA ONLY together with a real provider (or sandbox) + a round-trip journey test (F4.1) that receives the email, follows the link, and completes the flow. Until then, do not introduce the gate."
```
