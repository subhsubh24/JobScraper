# DEEP DIAGNOSIS — "it builds/deploys but the user hits an error"

The method for any reported runtime failure. **Observe the real environment first; never
read code and theorize.** Record each incident in `docs/loop-memory.md` (a dated entry:
symptom → evidence → root cause → fix → proof).

This repo's stack: **Vercel** (Next.js web at `/`, FastAPI API at `/api` via Vercel
Services) + **Neon Postgres** + **Gemini** (OpenAI-compat). Adapt the tools below to it.

## The method

1. **Observe the REAL environment — don't theorize.** Read the failure from the running
   system first; the logs usually name the cause in seconds.
   - **Vercel runtime logs:** dashboard → the deployment → Logs (or `vercel logs <url>`).
   - **Live DB (Neon):** `npx neonctl connection-string --pooled` → then `psql "$CS"` or a
     throwaway SQLAlchemy session: query the table, `count(*)`, inspect rows, `\dt`/`\d`
     the schema. (Neon has no Supabase-style `get_advisors`; use `EXPLAIN`/`psql` + the
     Neon console for connection/usage health.)
   - **Reproduce the exact user journey:** `curl` the live `/api/...` (or the web flow) and
     read the real status + body.

2. **BUILDS ≠ WORKS — separate three layers with evidence before changing anything:**
   - **code** (a real bug), **data** (schema/migration drift, bad rows), **config**
     (missing/wrong env var, connecting as the wrong DB role / wrong `DATABASE_URL`).
   - Heuristic: *"no new row + no DB error + no app→DB connection" → it's config.*
     *"row created but the API 500s" → code. "insert errors on a column" → data/schema."*

3. **Form ONE hypothesis, then PROVE it against the live system.** Run the exact failing
   operation under the real conditions (e.g. the exact INSERT via the live `DATABASE_URL`;
   diff the code's SQLAlchemy models vs the live DB column-by-column; confirm a row
   is/isn't created). If you can't prove it, you don't understand it yet.

4. **Find the UNCAUGHT throw.** A try/catch that degrades gracefully can't be the source of
   a hard error screen — hunt the unguarded call: a bare auth/session/token read, a
   `load_dotenv()`/env access, a DB call outside the try, an LLM/3rd-party call with no
   timeout. The error-boundary / 500 copy + the Vercel log stack tell you which route threw.

5. **Verify the fix in the REAL system, not the build.** Watch the new row appear / the
   query succeed / the journey complete (curl the live endpoint; query Neon). "Tests pass"
   is necessary, not sufficient. If you can't click it, verify in the data and say so.

6. **Fix the ROOT cause, add a regression test, make it fail LOUD next time.** Never paper a
   config bug with a code workaround. Turn the silent trap that hid it into a loud error or
   a bounded call (a preflight guard, a startup assertion, a timeout).

7. **Peel the layers.** Fixing one error reveals the next (this product hit a stacked chain
   in one outage: Vercel prefix-strip 404 → multi-method 405 → openai/httpx `proxies`
   crash). Keep going until the real journey works end-to-end, not until the first error
   disappears.

8. **Stay honest.** Change the diagnosis when evidence contradicts it; never claim "fixed"
   without proof.

## Two hard rules (from real outages)

- **(a) Every external/LLM call MUST have a timeout shorter than the serverless function
  budget.** A graceful try/catch is useless if the runtime kills the function first. Here
  the function budget is `vercel.json` `maxDuration` (60s); LLM calls use
  `LLM_TIMEOUT_SECONDS` (default 45s) + bounded retries in `src/llm.py`. Any new
  third-party write/read gets an explicit, sub-budget timeout.
- **(b) An optional env var that a critical path actually requires is a latent outage —
  make it fail LOUD.** Don't sign tokens with a known default, don't connect to a default
  DB, in production. Here `asgi.py` refuses to start on Vercel if `JWT_SECRET` is unset or
  the dev default; `DATABASE_URL` must be a real Postgres. Surface missing prod secrets
  loudly (startup raise / preflight), never a silent insecure default.
