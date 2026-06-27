# Career Operator — Web (Next.js)

The web frontend. Deploys as the `web` service of the single Vercel project (Vercel
Services) at routePrefix `/`; it calls the FastAPI backend at `/api/*` on the same origin.

## Production deploy config (the real contract)
- **Build command:** `next build` (Vercel auto-detects Next.js — no override needed).
- **Output:** Next.js managed output (Vercel handles it; do not set an output dir).
- **Env contract:**
  - `NEXT_PUBLIC_API_URL` — *optional.* Defaults to `''` (same-origin `/api`, correct for
    the unified Vercel Services deployment). Set it ONLY to point at a separate API
    origin, e.g. `http://localhost:8000` for local dev against a standalone API.
- **Routing:** the API is mounted at `/api` by Vercel Services; the web app uses relative
  `/api/...` calls, so there is no CORS and no cross-origin config.

## Local dev
```bash
npm install
npm run dev          # http://localhost:3000  (set NEXT_PUBLIC_API_URL=http://localhost:8000)
npm run build        # production build (the deploy artifact)
npm run lint
```

## Structure
```
app/            # App Router routes: /, /login, /register, /app (+ jobs/[id], coach), /pricing
components/ui.tsx
lib/            # api.ts (typed client), auth.tsx (session), types.ts
```
