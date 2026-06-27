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
      how: "DONE: Neon DB + 9 tables via pooled endpoint. TODO: in Vercel set DATABASE_URL (Neon pooled string), JWT_SECRET (openssl rand -hex 32), optional GEMINI_API_KEY + ALLOWED_ORIGINS; deploy; verify GET /health. See docs/DEPLOY_VERCEL.md. Never commit .env."
    - id: ci-wiring
      title: "Wire preflight + journey suite + mobile build into CI (needs workflow scope)"
      priority: normal
      status: open
      why: "The loop must NOT edit .github/; CI cannot be added by the loop."
      how: "Add a GitHub Actions workflow: pip install -r requirements-dev.txt, run scripts/preflight.sh ci (backend + cd mobile && npm ci && tsc/lint)."
```
