# Deploy — Vercel (serverless)

JobScraper deploys to **Vercel**. The Python FastAPI API runs as a **serverless
function**; the mobile/web frontend is a separate Vercel project.

## Architecture
```
Vercel project "career-operator-api"  (root of this repo)
  vercel.json   -> rewrites /(.*) to /api/index
  api/index.py  -> ASGI entry, re-exports `app` from asgi.py
  asgi.py       -> the FastAPI app (was api.py; renamed to avoid the /api dir clash)
  requirements.txt -> LEAN runtime deps only (size-bound: ~250MB function limit)

External: Postgres (Neon / Supabase / Vercel Postgres) — SQLite has no persistence
          on serverless. Use a POOLED connection string (pgBouncer).
```

## Hard constraints (why things are the way they are)
1. **Bundle size ≤ ~250MB.** `requirements.txt` is deliberately lean. Do NOT add
   `sentence-transformers`/torch, pandas, etc. unless actually imported — they blow the
   limit. Dev/extra deps live in `requirements-dev.txt` (CI installs that, Vercel does not).
2. **No persistent filesystem / no background workers.** No SQLite persistence, no
   Celery/Redis. Long work must be request-scoped or offloaded to a queue service.
3. **Function timeout** (`maxDuration` 60s in `vercel.json`; hobby plan caps lower).
   LLM prep-pack/coach calls can be slow — keep them within the limit or stream/queue.
4. **Per-instance in-memory state.** The rate limiter + LLM/day ceiling are per-instance
   on serverless, not global. Track F: back them with Upstash Redis / Postgres before
   relying on them as a hard guarantee.

## One-time setup (owner — Human-Core)
1. Create a Postgres DB (Neon/Supabase/Vercel Postgres). Copy the **pooled** URL.
2. In the Vercel project → Settings → Environment Variables, set:
   - `DATABASE_URL` = the pooled Postgres URL (`?sslmode=require`)
   - `JWT_SECRET` = `openssl rand -hex 32`
   - `OPENAI_API_KEY` = your key (optional — API degrades gracefully without it)
   - `ALLOWED_ORIGINS` = your web + app origins
   - `LLM_DAILY_CEILING` = e.g. `25`
   - (Track C) `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
3. **Set spend caps NOW** (OpenAI usage limit; Stripe limits). Wallet-drain defense.
4. Run migrations against the Postgres DB (alembic) before first real traffic.

## Deploy
- Connect the GitHub repo to Vercel (root = repo root). Push to `main` → Vercel builds
  `api/index.py` with `@vercel/python` and installs `requirements.txt`.
- Verify: `GET https://<deployment>/health` → `{"status":"healthy", ...}`.

## Frontend (separate Vercel project)
Create a second Vercel project with **Root Directory = `mobile`**, build = Expo web
export (`npx expo export -p web`, output `dist`). Set the API base URL via
`app.json` → `expo.extra.apiUrl` = the API deployment URL.

## Container fallback
A Docker/Railway path is preserved in `docs/legacy/` (`Dockerfile.api`, `railway.json`,
updated to `uvicorn asgi:app`) if you ever want an always-on host instead.
