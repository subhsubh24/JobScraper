# Career Operator — Mobile (Expo / React Native, TypeScript)

Native iOS + Android app for Career Operator. Full-parity client for the Python
backend API (`/api/*`). Replaces the earlier Flutter prototype (now in
`../mobile-flutter-legacy/`).

## Stack
- Expo SDK 56, React Native 0.85, React 19, TypeScript (strict)
- expo-router (file-based routing), expo-secure-store (token storage)

## Run
```bash
npm install
npm run typecheck   # tsc --noEmit
npm run lint        # expo lint
npm start           # then press i / a, or scan in Expo Go
```

## Configure the API URL
Set `expo.extra.apiUrl` in `app.json` to your backend:
- local dev: `http://localhost:8000` (default)
- production: your Vercel API deployment URL, e.g. `https://career-operator-api.vercel.app`
  (see `../docs/DEPLOY_VERCEL.md`)

The base URL is read in `src/services/api.ts` via `expo-constants`.

## Structure
```
src/
  app/                 # expo-router routes
    _layout.tsx        # root stack + AuthProvider
    index.tsx          # auth gate / redirect
    (auth)/            # login, register
    (tabs)/            # Pipeline (jobs+stats), Coach, Settings
    job/new.tsx        # add a job
    job/[id].tsx       # job detail + status + prep pack
    paywall.tsx        # subscription paywall (purchase flow = Track C)
  contexts/auth.tsx    # session state
  services/api.ts      # typed API client + secure token storage
  components/ui.tsx    # Button / Field / Card / EmptyState
  theme.ts, types.ts
```

## Status (honest)
- ✅ Typecheck-clean, lint-clean. Auth + pipeline + job detail + coach + paywall UI
  wired to the real API with real loading/empty/error states.
- ⏳ In-app purchase (RevenueCat/StoreKit/Play Billing) — Track C, needs owner store
  accounts + product IDs.
- ⏳ Account-deletion server endpoint — Track D (required before store submission).
- ⏳ Component/integration test suite + native device runs — Track E / human checklist.
- ⏳ Real rendered store assets (icon/screenshots/feature graphic) — Track D.
