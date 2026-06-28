# IMPROVEMENT LOG

Per-run handoff log for the autonomous factory loop (the RECORD step). One line per merged
change: date · area · what shipped · PR. Newest first. Lessons go in `docs/loop-memory.md`;
this is the trajectory so the next run hill-climbs instead of repeating work.

- 2026-06-28 · deps/gate · Pinned httpx==0.27.2 — unpinned httpx floated to 0.28, which
  removed the Client(app=...) kwarg starlette 0.35's TestClient passes, erroring the ENTIRE
  test/journey suite (Track E gate could not run). Prod-looked-fine/test-broken drift. (#25)
- 2026-06-27 · apparatus · Factory-process parity with sibling products: full DESIGN BAR in
  VISION (anti-generic-frontend AVOID/GENERATE/TASTE-AUDIT), preflight security + stub-marker
  guards, autonomous-loop charter (docs/autonomous-loop/PROMPT.md), AGENTS.md, this log.
- 2026-06-27 · bootstrap · See git history (#2–#17): apparatus install, working backend slice,
  Next.js web + Expo mobile, Neon DB, Gemini LLM, single Vercel Services deploy, quality-grade
  wiring, release-config, gitignore/web-lib fix.
