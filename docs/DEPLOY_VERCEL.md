# Deploy — Vercel (one project, Vercel Services)

JobScraper deploys as **ONE Vercel project** using **Vercel Services**: the Next.js web
app and the Python FastAPI backend build separately but deploy together to a single
domain with shared environment variables. The Expo app is built separately for the app
stores (NOT on Vercel).

## Architecture (single deployment)
```
ONE Vercel project  (Framework Preset = "Services")
  vercel.json -> experimentalServices:
    web : entrypoint web/      routePrefix /      (Next.js — the site + web app)
    api : entrypoint asgi.py   routePrefix /api   (FastAPI — the backend)

  Same origin: the web app calls /api/* (no CORS). Vercel does NOT strip the prefix,
  so FastAPI receives /api/auth/register and matches its existing /api/* routes.

External: Neon Postgres (pooled endpoint).
Separate: /mobile (Expo) -> App Store / Play via EAS, points at this domain's /api.
```

## One-time setup (owner — Human-Core)
1. Import the repo into Vercel. **Set the project Framework Preset to `Services`** (required
   for `experimentalServices`). One project — no second project needed.
   - Note: Vercel "Services" may be gated/experimental on some plans. If it isn't
     available to you, the fallback is two projects (root = API, `web/` = Next.js) — but
     prefer Services so everything shares one domain + one env.
2. Create a **Neon** project; copy the **pooled** connection string (host has `-pooler`).
3. In the ONE project's Environment Variables (shared by both services), set:
   - `DATABASE_URL` = Neon pooled URL (`?sslmode=require`)
   - `JWT_SECRET` = `openssl rand -hex 32`
   - `GEMINI_API_KEY` = Google Gemini key (optional — degrades gracefully without it).
     Optional: `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`.
   - (No `ALLOWED_ORIGINS` needed — web and API share an origin.)
4. **Set spend caps NOW** (Gemini/Google AI usage limit; Stripe limits). Wallet-drain defense.
5. **Schema:** auto-creates on first cold start (`AUTO_CREATE_TABLES=1`, default), or run
   once: `DATABASE_URL='postgresql://...' python scripts/init_db.py`.

## Deploy & verify
- Push to `main` → Vercel builds both services. The web app is at `/`; the API at `/api/*`.
- Verify: `GET /api/health` → `{"status":"healthy",...}`; open `/` for the web UI;
  register a user to confirm the DB path.

## Neon connection (pooled, serverless-safe)
Use the pooled endpoint (`-pooler` in the host), `?sslmode=require`. We use psycopg2 +
NullPool — compatible with PgBouncer; we issue no SQL-level PREPARE, so no extra config.
```
DATABASE_URL=postgresql://[USER]:[PASSWORD]@ep-[ID]-pooler.[REGION].aws.neon.tech/[DB]?sslmode=require
```

## Hard constraints
1. **Bundle size ≤ ~250MB** for the Python service — `requirements.txt` is deliberately
   lean (no torch/sentence-transformers/celery/etc.). Dev/extra deps live in
   `requirements-dev.txt` (CI installs that, Vercel does not).
2. **No persistent filesystem / no background workers** in serverless. External Postgres
   required; no SQLite persistence; no Celery/Redis.
3. **Function timeout** (`maxDuration` 60s on the api service). Gemini prep-pack/coach
   calls can be slow — keep within the limit or stream/queue.
4. **Per-instance in-memory state** (rate limiter + LLM/day ceiling). Track F: back with a
   shared store (Upstash/Postgres) before relying on them as a hard guarantee.

## Mobile (not Vercel)
The Expo app in `/mobile` ships to the App Store / Play via EAS. Point its
`expo.extra.apiUrl` (or `EXPO_PUBLIC_API_URL`) at this deployment's base URL (the api
client appends `/api`).

## Container fallback
A Docker/Railway path is preserved in `docs/legacy/` (`Dockerfile.api`, `railway.json`,
`uvicorn asgi:app`) for an always-on host instead of serverless.
