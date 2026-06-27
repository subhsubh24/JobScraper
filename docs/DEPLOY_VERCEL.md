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

External: Supabase Postgres — SQLite has no persistence on serverless.
          Use the Transaction pooler (Supavisor, port 6543), not the direct 5432 conn.
```

## Supabase (the chosen DB — consistent with the other products)
Use the **Transaction pooler (Supavisor)** connection string, verified against current
Supabase docs:
- **Port 6543**, host `aws-[REGION].pooler.supabase.com`, username `postgres.[PROJECT-REF]`.
- It is **IPv4-only on every tier** → works from Vercel without the IPv4 add-on.
  (The direct `:5432` connection is IPv6 and the *session* pooler is not ideal for
  short-lived functions — use the transaction pooler.)
- Append `?sslmode=require`.
- Transaction mode **does not support prepared statements**, but we use **psycopg2**
  (no persistent prepared statements) + **NullPool**, so it works with **no code change**.

```
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
```

### Security hardening (defense in depth)
The app connects as Supabase's privileged `postgres` role, so it **bypasses RLS** and our
own JWT auth (in FastAPI) is the real gate. But our tables (incl. `users.password_hash`)
live in the `public` schema, which Supabase's **Data API (PostgREST)** can expose. By
default SQLAlchemy-created tables are NOT granted to `anon`/`authenticated`, so they are
not reachable via the Data API — but enable RLS anyway (free, since the app's role
bypasses it) so a future misconfig can't leak data. In the Supabase SQL editor:
```sql
alter table users            enable row level security;
alter table job_postings     enable row level security;
alter table job_scores       enable row level security;
alter table applications     enable row level security;
alter table prep_artifacts   enable row level security;
alter table chat_messages    enable row level security;
alter table companies        enable row level security;
alter table contacts         enable row level security;
alter table outreach_sequences enable row level security;
-- no policies needed for `anon`/`authenticated`: this app does not use the Data API.
```
Alternatively, disable the Data API entirely for this project if you only ever reach
Postgres via this backend.

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
1. Create a **Supabase** project. Settings → Database → Connection string → **Transaction
   pooler** (port 6543). Copy it (see the Supabase section above for the exact shape).
2. In the Vercel project → Settings → Environment Variables, set:
   - `DATABASE_URL` = the pooled Postgres URL (`?sslmode=require`)
   - `JWT_SECRET` = `openssl rand -hex 32`
   - `OPENAI_API_KEY` = your key (optional — API degrades gracefully without it)
   - `ALLOWED_ORIGINS` = your web + app origins
   - `LLM_DAILY_CEILING` = e.g. `25`
   - (Track C) `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
3. **Set spend caps NOW** (OpenAI usage limit; Stripe limits). Wallet-drain defense.
4. **Schema:** the API auto-creates missing tables on cold start (`AUTO_CREATE_TABLES=1`,
   the default), so a fresh Postgres works on first request. To create it explicitly
   instead, run once: `DATABASE_URL='postgresql://...' python scripts/init_db.py`.
   There are **no alembic migrations yet** — once you add them, set
   `AUTO_CREATE_TABLES=0` and run `alembic upgrade head`.

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
