# SUCCESS PATTERNS — Career Operator (reuse what worked)

FACTORY_STANDARD §20: a curated, deduplicated list of PROVEN approaches — read it FIRST each run
(with loop-memory), reuse a matching pattern instead of reinventing. Write SPARINGLY (only a
genuinely reusable win with real evidence), compress near-duplicates, cap the file. Honest only:
every entry cites a real merged PR / measured result.

Format: `[id] PATTERN — CONTEXT — WHY IT WORKS — EVIDENCE`

- **[sp-1] Backend-first, file-DISJOINT N-PR split for a cross-stack feature.** — Building one
  feature across backend + web (+ mobile). — Ship the backend endpoint FIRST as its own PR; once it
  merges, branch the web/mobile surfaces off the updated main so their E2E/journey suites boot the
  REAL route (no 404 on the fetch), and each PR stays independently reviewable + auto-mergeable. Banks
  backend value regardless of frontend outcomes and matches the disjoint rule. — EVIDENCE: #305→#307/#308
  (mock-interview), #310→#312/#313 (readiness), #315→#316 (public demo).

- **[sp-2] Validate a browser E2E in the routine env with the PREINSTALLED Chromium.** — The web
  functional-journey suite must actually RUN (BUILDS≠WORKS), but the npm-installed `@playwright/test`
  wants a browser build the cloud routine env lacks (`chrome-headless-shell-<n>` missing). — Point
  Playwright at the preinstalled full Chromium via a THROWAWAY local config that spreads the committed
  one and injects `launchOptions.executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'`
  (`npx playwright test <spec> --config pw.local.ts`, then `rm` it — never commit it). The config's
  webServer already boots uvicorn + next, so the journey drives the real backend. — EVIDENCE: #316
  (the /demo journey ran 5/5 green against the live endpoint + a route-intercepted 500 for the degrade path).

- **[sp-3] DECISION COROLLARY: ship the KEY-FREE slice when the richer version needs an owner-blocked
  secret.** — A feature's headline version depends on a secret only the owner can set (e.g. `GEMINI_API_KEY`),
  which would 503 or wallet-drain if exposed. — Build the deterministic, local slice that delivers the
  same real signal with NO secret (it works the moment the app deploys and can never 503), and record the
  call explicitly. — EVIDENCE: #315 (public demo = the local skills-match, not the Gemini semantic fit-score).

- **[sp-4] Concurrent PR work without disturbing reviewers: DIFF-as-source-of-truth + a git worktree.** —
  Reviewers are reading the main tree for PR A while you want to build PR B. — Hand reviewers the captured
  `git diff` as the source of truth (they don't depend on the working tree), and build PR B in
  `git worktree add /tmp/wt-* <branch>` (symlink node_modules for JS validation) so the main tree stays put.
  Caveat: a symlinked node_modules breaks Turbopack `next build` ("points out of filesystem root") though
  tsc/eslint pass — run the real build/E2E in the actual tree once the branch is free. — EVIDENCE: run 33
  (#315/#316/#317 shipped concurrently; run-28 shared-tree hazard avoided).

- **[sp-5] After auto-merges, HARD-SYNC local main to origin/main.** — Squash-merges happen server-side;
  a local `git checkout main` / `git pull` can land on a stale or divergent local main and hide the just-
  merged work. — `git fetch origin main && git reset --hard origin/main` before branching the next PR. —
  EVIDENCE: run 32 recovery note; used cleanly throughout run 33.
