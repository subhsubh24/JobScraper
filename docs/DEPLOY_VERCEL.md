# Deploy — Vercel

Three surfaces, all on Vercel except the native app:
1. **API** — Python FastAPI as a serverless function (this repo root).
2. **Web app** — Next.js in `/web` (a SECOND Vercel project, Root Directory = `web`).
3. **Mobile** — Expo app in `/mobile` → App Store / Play (NOT Vercel; built via EAS).

All three talk to the same FastAPI API.

## Architecture
```
Vercel project 1 — API  (Root Directory = repo root)
  vercel.json   -> rewrites /(.*) to /api/index
  api/index.py  -> ASGI entry, re-exports `app` from asgi.py
  asgi.py       -> the FastAPI app (was api.py; renamed to avoid the /api dir clash)
  requirements.txt -> LEAN runtime deps only (size-bound: ~250MB function limit)

Vercel project 2 — Web  (Root Directory = web)
  Next.js (App Router, TS, Tailwind). Auto-detected by Vercel — no extra config.
  Reads NEXT_PUBLIC_API_URL (defaults to the live API).

External: Neon Postgres — SQLite has no persistence on serverless.
          Use the POOLED endpoint (host has `-pooler`), not the direct connection.
```

## Neon (the chosen DB)
Use the **pooled connection string**, verified against current Neon docs:
- The pooled host **adds `-pooler` to the endpoint id**, e.g.
  `ep-cool-darkness-123456-pooler.us-east-2.aws.neon.tech` (the direct host omits it).
- Neon's guidance: serverless functions should use the **pooled** connection (many
  short-lived connections) to avoid exhausting `max_connections`.
- Append `?sslmode=require`.
- PgBouncer **doesn't support SQL-level `PREPARE`/`EXECUTE`**, but we don't issue those —
  psycopg2 + **NullPool** work with **no code change**.

```
DATABASE_URL=postgresql://[USER]:[PASSWORD]@ep-[ID]-pooler.[REGION].aws.neon.tech/[DB]?sslmode=require
```

(Neon has no PostgREST/Data API exposing tables — unlike Supabase — so no RLS/anon-key
hardening is needed here. Auth is enforced in the FastAPI layer.)

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
1. Create a **Neon** project. Dashboard → Connection Details → toggle **Pooled
   connection** → copy the string (host contains `-pooler`). See the Neon section above.
2. In the Vercel project → Settings → Environment Variables, set:
   - `DATABASE_URL` = the pooled Postgres URL (`?sslmode=require`)
   - `JWT_SECRET` = `openssl rand -hex 32`
   - `GEMINI_API_KEY` = your Google Gemini key (optional — API degrades gracefully
     without it; uses Gemini via its OpenAI-compatible endpoint). Optional overrides:
     `GEMINI_MODEL` (default `gemini-2.5-flash`), `GEMINI_EMBEDDING_MODEL` (default `gemini-embedding-001`).
   - `ALLOWED_ORIGINS` = your web + app origins
   - `LLM_DAILY_CEILING` = e.g. `25`
   - (Track C) `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
3. **Set spend caps NOW** (Gemini/Google AI usage limit; Stripe limits). Wallet-drain defense.
4. **Schema:** the API auto-creates missing tables on cold start (`AUTO_CREATE_TABLES=1`,
   the default), so a fresh Postgres works on first request. To create it explicitly
   instead, run once: `DATABASE_URL='postgresql://...' python scripts/init_db.py`.
   There are **no alembic migrations yet** — once you add them, set
   `AUTO_CREATE_TABLES=0` and run `alembic upgrade head`.

## Deploy
- Connect the GitHub repo to Vercel (root = repo root). Push to `main` → Vercel builds
  `api/index.py` with `@vercel/python` and installs `requirements.txt`.
- Verify: `GET https://<deployment>/health` → `{"status":"healthy", ...}`.

## Web frontend (second Vercel project — Next.js)
Create a second Vercel project from the SAME repo with **Root Directory = `web`**.
Vercel auto-detects Next.js — no build config needed. Optionally set
`NEXT_PUBLIC_API_URL` to the API deployment URL (it already defaults to the live API).
This deploys the real website + web app (login, pipeline, job detail, coach, pricing).

## Mobile (not Vercel)
The Expo app in `/mobile` ships to the App Store / Play Store via EAS — it is NOT a
Vercel deploy. Set `expo.extra.apiUrl` (or `EXPO_PUBLIC_API_URL`) to the API URL.

## Container fallback
A Docker/Railway path is preserved in `docs/legacy/` (`Dockerfile.api`, `railway.json`,
updated to `uvicorn asgi:app`) if you ever want an always-on host instead.
