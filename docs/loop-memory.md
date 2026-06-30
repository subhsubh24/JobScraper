# LOOP MEMORY — Career Operator (cross-run lessons)

Durable lessons for the factory loop. Append dated entries. Keep it honest and short.

---

### 2026-06-30 (run 9) — Maximal run: 5 PRs (input-bounds wallet-drain, billing + mobile-billing money-path tests, web + mobile coach a11y) + 8-scout sweep
Ran the full 8-scout sweep (functional-reality / security / performance / backend-tests /
web-frontend / mobile / store+artifact-freshness / business-case+PMF) doubling as the ~daily
DEEP AUDIT. Functional-reality found NO ship-critical bug (job_public is None-guarded, the
LLM-ceiling consume-before-call is the documented wallet-drain design, delete_user already
purges referrals first — all three "findings" were verified false positives). `asgi.py` was
the single contended backend file → owned by exactly ONE PR (the input-bounds hardening).
Shipped 5 file-disjoint PRs through 2 Sonnet reviewers each + the CI gate, all merged:
- **#126 input-bounds wallet-drain hardening** (security §12, the asgi.py owner): `resume_text`/
  `description`/`requirements` feed LLM prompts VERBATIM but the per-day ceiling is a CALL count,
  not a token budget — an unbounded field let one account drive the per-call token bill arbitrarily
  high (real money risk, spend caps still owner-pending). Added max_length (50k/20k/20k) + salary
  `ge=0/le=10M` + a `min<=max` model_validator + `job_id<=64` + `location/url` bounded to DB column
  widths (422 at the edge vs a 500 at the DB write). New `tests/test_input_bounds.py` (8): each
  bound rejects AND a within-bounds value still succeeds. BOTH reviewers APPROVE first pass
  (independently verified the vuln against llm_workflows.py + that bounds match DB widths).
- **#127 billing money-path tests** (test coverage, src/billing.py): the webhook decides entitlement
  on subscription STATUS but the suite only ever used active/paid — added trialing→GRANT,
  past_due-via-.updated→REVOKE (the else-branch), no_payment_required checkout→GRANT. Reviewer B
  MUTATION-TESTED each (broke the branch, only the matching test failed) — proven load-bearing, not
  padding. BOTH APPROVE first pass.
- **#128 mobile-billing event-set tests** (coverage, src/mobile_billing.py): parametrized over the
  ACTUAL `_GRANT_EVENTS`/`_REVOKE_EVENTS` (4 grant events had ZERO direct coverage) + a multi-alias
  resolution test (primary + first alias unknown, a later alias matches — a distinct loop-continuation
  branch). Reviewer A mutation-tested: a `return None`-on-first-miss bug passes the old single-alias
  test but fails the new one. BOTH APPROVE.
- **#129 web coach a11y + auto-scroll** (web/app/app/coach/page.tsx): aria-label on the input,
  role=alert on the error, a bottom-anchor + scrollIntoView on [messages,sending] (was: manual scroll
  on every reply), "…"→"Sending…". BOTH APPROVE first pass.
- **#130 mobile a11y** (mobile coach.tsx + the shared Field component): bound `accessibilityLabel` on
  Field (labels all ~10 login/register/new-job inputs that announced as bare "text field") + made the
  coach chat screen-reader operable (input label, Send role/name/state, suggestion buttons, error
  alert role). New jest assertion; reviewer A reproduced 51/51 + tsc + lint clean. BOTH APPROVE.
LESSONS: (1) **maker≠checker confirmed the work but, unusually, drew ZERO REQUEST_CHANGES this run —
all 10 reviewers APPROVED first pass.** Not a free pass: the verification was rigorous (two reviewers
ran MUTATION tests in isolated worktrees to prove the new money-path tests aren't tautological; two
independently re-ran the mobile gate; one re-verified the wallet-drain vuln against llm_workflows.py).
The clean sweep reflects tightly-scoped, single-concern, pre-verified PRs — not lax review. (2)
**SKEPTICISM rejected three functional-reality false positives** before building: job_public's
"lazy-load crash" (it's None-guarded), the LLM-ceiling "consume before call" (documented wallet-drain
design — an expensive ATTEMPT must count), and the delete_user "referral FK 500" (it purges referrals
FIRST). Verified each against the code, built none. (3) **BRANCH CONTAMINATION via a reviewer's local
checkout (recovered):** a PR-128 reviewer transiently applied the diff to the SHARED working tree to
mutation-test, leaving `tests/test_mobile_billing.py` dirty on my local `main`; I caught it via
`git status` and `git reset --hard origin/main`. The remote PR branches were never affected (all merges
used the GitHub API, not the local tree). RULE: reviewers that need a local checkout should use an
isolated worktree (one did); when the local tree is dirty with work you didn't author, trust origin and
reset. (4) **CHOSE security-input-bounds over analytics-instrumentation for the single asgi.py slot:**
both are real, but the wallet-drain bounds defend live money the moment any traffic hits (spend caps
owner-unset), while PMF analytics produces NO signal pre-launch (0 users) — instrumenting now vs next
run changes nothing measurable. Analytics deferred again, honestly (see below).
ARTIFACT FRESHNESS: fixed VISION.md's stale "Honest current state (bootstrap)" section (claimed the
backend "does not yet fully work — api.py … only /health is real" + mobile "being re-platformed" — both
false now: asgi.py is deployed + passing E2E, Flask api.py retired #70, Expo re-platform done). Bumped
PENDING_OPS as_of. NOTE: docs/quality/QUALITY_SCORECARD.md is STALE (as_of 2026-06-29) — its named gaps
CORS (fixed #96), perf N+1 (#121), referral loop (#109), cross-instance limiter (#114) are CLOSED; the
independent Quality Auditor should re-grade (consumed as data, NOT self-edited — maker≠checker).
DEFERRED (named, buildable — next clean-asgi.py run): privacy-safe analytics instrumentation (PMF
foundation, deferred 6+ runs now; same design as before — AggregateEvent table keyed by
event_type+cohort_date+window_date, NO PII, best-effort record_event() at signup/job-add/fit-score, read
endpoint behind an env shared-secret bearer, 503 when unset; wants asgi.py + 1 migration). CAPTCHA
(owner Turnstile/hCaptcha keys; multi-surface). Career+ ($24) + TEAM/B2B2C tiers (business-case levers;
multi-run). GenAI user-report affordance (Track D; sprawls asgi.py+web+mobile → dedicated run). Prompt-
injection delimiter-escaping of resume_text in the coach prompt (career_coach.py; deferred — weak
without an eval + risks shifting LLM output; the max_length bound already caps the token-drain half).


### 2026-06-30 (run 8) — Maximal run: 3 PRs (perf N+1 eager-load, scorer coverage, mobile a11y) + 8-scout sweep
Ran the full 8-scout sweep (security / functional-reality / business-case / performance /
mobile+TrackE / store / tests-quality-reconcile / growth-PMF) doubling as the ~daily DEEP
AUDIT. Functional-reality found NO ship-critical bug (core web+mobile loops + side-effects
sound). `asgi.py` was the single contended backend file → owned by exactly ONE PR (the perf
N+1, the scorecard's NAMED performance top-gap). Shipped 3 file-disjoint PRs through 2 Sonnet
reviewers each + the CI gate, all merged:
- **#121 perf N+1 eager-load** (performance B → drives toward A): `job_public` + the
  pipeline-analytics loop lazy-loaded each job's application/score/company → 3N+1 on /api/jobs,
  2N+1 on /api/analytics/pipeline (unbounded for unlimited-tier). Added selectinload on both
  endpoints (NO migration — JobScore.job_id/Application.job_id are unique=True, already indexed)
  + an OPTIONAL additive limit/offset on /api/jobs (default returns all → no client truncation).
  `tests/test_perf_n1.py` asserts a CONSTANT query count as job count grows. Reviewer A
  (REQUEST_CHANGES, 1 cycle): pipeline_stats missed selectinload(company) (job_public reads it
  on the top-5 slice) AND the guard had a blind spot — every seeded job shared company_name="Acme"
  so job.company was never dereferenced. Fixed both: distinct companies + company_name=None makes
  the guard tight (verified it FAILS without the company eager-load, passes with it).
- **#122 scorer batch-helper coverage** (tests): `score_all_jobs` + `get_top_jobs` had ZERO
  coverage (the "score everything new" entry point + the ranked-pipeline query).
  `tests/test_scorer_workflow.py`: unscored-only filter + idempotency, DESC ordering + limit,
  per-user isolation. Reviewer B (REQUEST_CHANGES): the endpoint free-tier-cap test I bundled
  was a DUPLICATE of the journey suite's test_free_tier_job_limit_enforced (same HTTP layer) →
  removed it; PR is now scorer-only (both reviewers approved that file).
- **#123 mobile a11y** (Track B / store review): job-detail pipeline status chips → radio group
  (accessibilityRole=radio + selected state + label) so the core job-tracking loop is
  screen-reader-operable; paywall plan cards + feature rows announce as single descriptive
  elements (decorative checkmark hidden). jest-expo asserts the roles/labels. BOTH reviewers
  (REQUEST_CHANGES, 1 cycle): my replace_all feature-row edit matched only the PREMIUM branch's
  10-space indent, missing the free-tier branch's 8-space indent (the high-traffic path) — and
  it was untested. Applied the fix to the free-tier block + added a free-tier test.
LESSONS: (1) **BRANCH CONTAMINATION via a stale index — caught by a reviewer, recovered cleanly.**
After committing the perf change on its branch, the scorer-test branch's amend somehow captured
asgi.py + test_perf_n1.py (the perf files) into its single commit — Reviewer B's re-review (which
reads the DIFF, not my claim) flagged that the "scorer-only" branch carried the entire perf change.
FIX/RULE: when a branch diff doesn't match what you believe you committed, TRUST the diff — I
hard-reset the branch to origin/main and re-applied ONLY the intended file (git reset --hard
origin/main; restore the one file; add explicit path; commit; force-with-lease). Verified the
remote diff was a single file before relying on it. The perf change was safe on its own PR the
whole time. maker≠checker caught a real merge-hygiene defect a self-review would have missed.
(2) **replace_all is indentation-sensitive** — two "identical" JSX blocks at DIFFERENT nesting
depths are NOT identical strings, so replace_all hit only one. BOTH reviewers independently caught
the half-applied a11y fix. When a value appears in two render branches, edit/verify EACH explicitly.
(3) **A scout's "untested" can be wrong** — the test scout called the free-tier job cap "only
unit-tested," but the journey suite already covered it at the HTTP layer (Reviewer B's catch).
Verify a claimed gap against ALL test dirs (tests/journeys too), not just the obvious unit file.
(4) **Greenhouse departments[0] is a FALSE positive** — a bonus scout flagged "departments[0]
crashes on []" but the code is `departments[0]["name"] if departments else None` (guarded);
skepticism over the scout, no churn fix.
DEFERRED (named, buildable — next clean-asgi.py run): privacy-safe analytics instrumentation
(the PMF measurement foundation, deferred 5+ runs; NEXT-RUN DESIGN: AggregateEvent table keyed by
event_type+cohort_date+window_date, NO PII/raw events; best-effort record_event() at signup/job-add/
fit-score; a read endpoint GATED behind an env shared-secret bearer token — NOT any-authed-user — to
avoid leaking aggregate user counts; 503 when the secret is unset; wants asgi.py + 1 migration).
CAPTCHA (owner Turnstile/hCaptcha keys; multi-surface web+mobile+asgi). Career+ ($24) tier — the
"genuine exclusive feature" problem is REAL (PREMIUM is already unlimited-everything incl. salary
negotiation), so a real Career+ entitlement needs metering PREMIUM down OR a new exclusive — a
multi-run design, NOT a clean one-PR change; do NOT rush it. TEAM/B2B2C tier (the floor-flip lever;
2-3 PRs + owner GTM). NEW 2026 STORE-COMPLIANCE FINDINGS (store scout, WebSearch): Apple App Review
+ Google Play now require a USER-REPORT/FLAGGING affordance for AI-generated content (GenAI/UGC
guidelines) — the app moderates output but has no user-facing "report this response" — added to
ROADMAP Track D (loop-buildable: report endpoint + coach/prep UI, but sprawls asgi.py+web+mobile →
dedicated run). Texas SB2420 age-assurance (effective 2026-06-04) → owner legal decision (build age
verification / rate-gate 17+ / defer) — added to PENDING_OPS. OWNER-BLOCKED: store asset IMAGES +
brand icon; mobile Track-E snapshot PIXELS (jest serializes trees, not pixels) + prep-pack vision
verdict (needs LLM key).


### 2026-06-30 (run 7) — Maximal run: 6 PRs (cross-instance limiter, client timeout, coach N+1, mobile screen tests, backend coverage, README honesty) + 8-scout sweep
Ran the full 8-scout sweep (security / functional-reality / business-case / mobile+TrackE /
performance / store / tests-freshness / growth) doubling as the ~daily DEEP AUDIT. `asgi.py`
was the single contended backend file → owned by exactly ONE PR (the cross-instance limiter,
the security ship-critical + lowest-incomplete Track F item). Shipped 6 file-disjoint PRs
through 2 Sonnet reviewers each + the CI gate, all merged:
- **#114 cross-instance rate-limit + LLM spend-ceiling** (Track F line 229 → TICKED; security
  ship-critical, wallet-drain). In-memory `_RATE_BUCKET`/`_LLM_DAY_COUNT` were per-instance on
  Vercel → the LLM spend ceiling MULTIPLIED per instance (real money risk). New `RateCounter`
  table + Alembic `993d75032689` (drift-gated) + `_consume_counter()`: atomic fixed-window
  count, committed immediately so it's cross-instance-durable AND survives a later request
  error (an expensive LLM attempt still counts — no fake under-count). Login lockout LEFT
  in-memory on purpose (scope = line 229; a shared store doesn't fix its targeted-DoS, CAPTCHA
  does). Reviewers (1 REQUEST_CHANGES): redundant index (UniqueConstraint already creates it)
  → dropped from model+migration; comment clarity. Both confirmed the early-commit-on-shared-
  session is CORRECT.
- **#115 client fetch timeout** (functional-reality ship-critical). BOTH web + mobile fetch
  clients had NO timeout → a hung API on launch stranded the user on a stuck "Loading…"/spinner
  forever (session restore awaits `api.me()`). Added an AbortController bound. Reviewer B flagged
  20s would prematurely abort legit slow AI calls (server LLM timeout 45s, Vercel budget 60s) →
  bumped to 60s (tied to maxDuration so it NEVER false-aborts a legit response, only a true hang).
  Reviewer A: wrap the fake-timers test in try/finally so it can't poison the suite.
- **#116 coach-context N+1** (performance). `_get_user_context` did one `JobPosting.get()` per
  recent application on every coach message → selectinload. Query-count regression test (2 vs 5
  apps → CONSTANT). Both APPROVE. (Honest: the scorecard's NAMED perf top-gaps are /api/jobs +
  /api/analytics/pipeline — still open; this is an ADDITIONAL N+1, bounded at 5.)
- **#119 mobile screen tests** (Track B coverage). jest-expo component tests for the untested
  Coach/Settings/NewJob screens (premium gating; HONEST account deletion — real DELETE then
  signOut, ORDER pinned; validation; honest error paths). Reviewer A: mock
  `react-native-safe-area-context` (jest-expo stubs only the native bridge) + settle coach's
  unconditional suggestion load inside act(). Reviewer B: pin delete→signOut order.
- **#117 backend coverage** (tests-evals). check_usage_limits monthly reset/non-reset/premium +
  greenhouse fetch_jobs unreachable-vs-empty honesty. BOTH reviewers: cut a referral-bonus test
  that DUPLICATED test_referral.py (already on main) + trim a parse test overlapping the
  detail-fetch test → did both.
- **#118 README Career+ honesty** (artifact freshness §14). The pricing table listed Career+ as a
  live tier, but tiers are binary FREE/PREMIUM (careerplus_* = dead config). Marked "(planned)".
  Both APPROVE.
LESSONS: (1) **FastAPI caches `Depends(get_db)` per request** — so the `rate_limit` dependency
and the endpoint body share the SAME session; the limiter's early commit persists only the
counter row (nothing else pending before the body runs). Both reviewers independently confirmed
this; it's why the shared-session early-commit design is correct (and why there's ONE connection,
not two). (2) **A module-level `TestClient` against the default on-disk DB is fragile**:
test_error_envelope used `TestClient(asgi.app)` (no fixture/override), so when `rate_limit` newly
started touching the DB, its `register` test 500'd on a missing `rate_counters` table — fixed by
switching that one test to the seeded `client` fixture. A dependency that NEWLY touches the DB can
break any test using a non-fixture client against a schema-stale DB. (3) **Skepticism beat a false
bug**: the security scout flagged an "off-by-one monthly-reset overage" then admitted the code was
"semantically correct" — verified it's a legitimate rolling 30-day reset, NOT a bug, and did not
build the "fix" (would have been churn). (4) **maker≠checker earned its keep**: 5 of 6 PRs drew a
REQUEST_CHANGES, every one a REAL improvement (redundant index, fake-timer suite-poisoning,
duplicate test, mobile mock/act-leak), all resolved within ONE cycle. (5) **Reviewer disagreement
is a signal to refine, not to pick a side**: on the greenhouse parse test (A: keep as non-dup; B:
cut as overlapping) I trimmed it to a distinct populated-board smoke that satisfied both.
DEFERRED (named, buildable — next clean-asgi.py run): N+1 on /api/jobs + /api/analytics/pipeline
(scorecard's named perf top-gap; wants asgi.py — the limiter owned it + the single migration slot);
privacy-safe analytics instrumentation (PMF foundation; wants asgi.py + a 2nd migration); Career+
($24) + TEAM/B2B2C tiers (the remaining business-case levers for the floor-flip); CAPTCHA (owner
Turnstile/hCaptcha keys, multi-surface). OWNER-BLOCKED/not-loop: store assets + brand icon; mobile
Track-E snapshot IMAGES (can't render headlessly — jest-expo serializes trees, not pixels) + the
prep-pack vision verdict (needs an LLM key). Email-provider abstraction stays deferred (speculative
— no consumer until double-opt-in lands).


### 2026-06-30 — Authenticated journey tier enforced in CI (BUILDS!=WORKS for the logged-in product)
The web E2E already covered signup->dashboard->core loop, but the logged-in tier was thin (the
2nd test only checked the login PAGE renders, not a real sign-in; no account/paywall). Added
web/e2e/authed-journey.spec.ts (runs in the required `functional journeys (web E2E)` check vs the
REAL FastAPI+JWT backend on a seeded throwaway DB): (1) real SIGN-IN — seed a confirmed user via
the register service path, then log in through the UI -> dashboard renders real content; (2)
ACCOUNT — /app/settings shows real email + plan, not an error boundary; (3) PAYWALL -> checkout
HONEST — free user clicks Go Premium; with no Stripe key it must show an honest notice (never a
fake upgrade, never a crash) and settings still shows Free. EVIDENCE-ON-FAILURE pattern: each flow
attaches page.on('console')+page.on('pageerror') and, if sign-in misses the dashboard, reads the
login error text and throws with both — debug from evidence, never a guess. Caught the ACCOUNT
failure that way: strict-mode violation (email renders in BOTH the header nav AND settings) -> a
SELECTOR fix (.first()), not a product bug. CSP NOTE: the directive's connect-src trap does NOT
apply here — asgi.py sets only `Content-Security-Policy: frame-ancestors 'none'` (no connect-src),
and the web app sets no connect-src CSP, so the cross-origin local-backend fetch was never blocked
(that's why E2E worked from the start). required_status_checks unchanged: the authed tier is folded
into the existing required `functional journeys (web E2E)`. Proved green (9/9) before relying on it.


### 2026-06-30 (run 6) — Maximal run: 3 PRs (referral invite loop, LLM fail-loud, mobile design polish) + 8-scout sweep
Ran the full 8-scout sweep (business-case / security / design-taste / functional-reality /
store / mobile / marketing-growth / tests-perf-freshness) which doubled as the ~daily DEEP
AUDIT. Functional-reality found NO ship-critical crash in the live loops but surfaced a real
latent bug (empty/None LLM completion). Selected a maximal file-disjoint set; `asgi.py` was
the single contended backend file → owned by exactly ONE PR (the referral loop). Shipped 3
through 2 Sonnet reviewers each + the CI gate:
- **#109 referral invite loop** (business-case-strength #1 named lever, the LOWEST ship-critical
  grade C): every user gets a `referral_code`; a referred signup grants BOTH sides a real bonus
  prep pack (raises the actual free-tier allowance via `check_usage_limits` — NOT a fake billing
  promise, DECISION COROLLARY). New `src/referrals.py` + `users.referral_code/bonus_prep_packs`
  + `referrals` table + Alembic migration `c3f2a9b41d77` (drift-gated, auto-applies) + `GET
  /api/referrals/me` + web register `?ref=` + web/mobile Settings share cards. Reviewers
  REQUEST_CHANGES (BOTH, then 1 re-review) — every find was REAL: (A) referral processing could
  500 a signup on a code-collision IntegrityError → fixed by committing the user FIRST and
  running referral best-effort in its own tx + a SAVEPOINT retry in `ensure_code`; (B) register
  copy was blind to `?ref` (and inaccurate — referred users get 2 prep packs) + mobile had NO
  referral surface → added the invite-aware subtitle + the mobile "Refer a friend" card;
  (re-review) the mobile share link used the **API** origin but `/register` is on the **web**
  frontend → use `EXPO_PUBLIC_WEB_URL` (fallback to API origin for the unified deploy). All
  resolved within the 2-cycle cap.
- **#110 LLM fail-loud** (correctness / SIDE-EFFECT INTEGRITY): an empty/None/no-choices
  completion flowed through the shared `_call_llm` chokepoint → crashed `json.loads(None)` in
  `parse_job_description` OR persisted a BLANK prep pack reported as "generated" (fake success).
  Now raises `RuntimeError` (→ honest 502, no blank artifact). Added the missing
  persistence-contract tests for the 3 previously-untested generators (study_plan/cover_letter/
  salary_negotiation) + empty/None/no-choices cases. Clean first pass both reviewers.
- **#111 mobile design polish** (Track B line 94 → TICKED + design-taste B→A work): converged the
  brand accent (mobile `#5B8CFF`→`#6366F1` = web indigo-500); reusable `ErrorBanner` with in-place
  **Retry** wired into pipeline + job-detail load failures (recoverable, not a dead end); a11y
  labels; markdown overflow fix. tsc + expo lint + jest-expo 34/34 green. Clean first pass.
LESSONS: (1) **maker≠checker earned its keep HARD** — the two most dangerous bugs this run were
reviewer finds, not maker finds: a referral path that could break a stranger's signup (concurrent
code collision → unhandled IntegrityError → 500), and a mobile invite link that would 404 every
share. Both shipped fixed. (2) **A best-effort sub-operation inside a signup must not be able to
poison the signup**: commit the critical thing FIRST, then run the optional thing in its own tx
(swallow failures) + use a SAVEPOINT (`begin_nested`) for any unique-constraint race so the outer
tx survives. (3) **MERGE MECHANICS**: `enable_pr_auto_merge` (MCP) refuses when `mergeable_state`
is `unstable` — which it is whenever the non-required **Vercel preview** is pending/failed, even
with the required checks green. `merge_pull_request` (squash) is still branch-protection-gated (it
returned 405 "2 of 2 required status checks in progress" until preflight+journeys went green), so
it merges through the SAME gate without `--admin` — use it when auto-merge is blocked only by the
non-required Vercel status. (4) **Bash cwd persists across calls** (again): a stale `cd web`/`cd
mobile` silently ran a later `git add`/`npm install` from the wrong dir — use absolute paths.
DEFERRED (named, buildable — next clean-asgi.py run): cross-instance rate-limit/spend-ceiling
(Postgres-backable, no owner key), CAPTCHA (owner Turnstile/hCaptcha keys + web+mobile+asgi),
N+1 eager-load on /api/jobs + /api/analytics/pipeline, privacy-safe analytics instrumentation
(PMF measurement foundation), Career+ tier + team/B2B2C tier (the remaining business-case levers).

### 2026-06-29 — validate-gtm honesty gate (GTM rigor parity with validate-capabilities)
Built the GTM analog of the capability gate: scripts/validate_gtm.py (Python port of
AptDesignerAI's validate-gtm.mjs; my stack is python+bash, no root node, so I ported it and
reused the declared pyyaml). Fails CLOSED on: (a) METRIC-WITHOUT-A-SOURCE — any non-zero
GROWTH_STATUS funnel/acquisition/pmf/channels metric while channels_connected is falsy AND no
sources/validation entry is connected/available (a real number with no source = fabrication
risk); (b) a GTM_SCORECARD (when present) that doesn't parse / has invalid grades / lacks
ship_gate_met. --readiness additionally requires a graded GTM_SCORECARD (ship-critical >= A).
Wired into preflight (per-PR in the required `ci` gate; --readiness in the full ship gate).
Proved green on the pre-launch feed (all []/null/none) BEFORE relying on it; verified the
tripwire fires on a fabricated funnel.signups=142, and --readiness fails honestly with no
scorecard. Enforced via the existing required `preflight` check (not a separate required check).
CORRECTION (2026-06-30): an earlier note here wrongly said "no GTM Auditor yet" — it relied on a
stale routine list. A GTM AUDITOR routine DOES exist (trig_0151oAtyorpyqZ3z6s38rrL8, created
2026-06-30 02:45, cron 30 18 */2, enabled): an independent adversarial grader (maker!=checker)
that owns docs/growth/GTM_RUBRIC.md + GTM_SCORECARD.md + GTM_AUDIT_MEMORY.md and writes a fenced
GTM_SCORECARD block (per-dim grades + ship_gate_met). The former "Growth Agent" routine
(trig_01Pntig) is now the "GTM FACTORY" (maker) — restructured AFTER the Gmail-prefix fix, which
SURVIVED (still mcp__claude_ai_Gmail__*). So the GTM architecture mirrors the Quality side:
GTM Factory (maker → GROWTH_STATUS) + GTM Auditor (checker → GTM_SCORECARD) + validate_gtm.py
(deterministic hard gate, consumes both, never writes the scorecard). The GTM_SCORECARD isn't in
the repo YET (the auditor hasn't run/merged) — when it lands, validate_gtm parses+grade-checks it
and --readiness becomes satisfiable (no new auditor to build; it already exists). Always re-list
routines before asserting one doesn't exist — they change between turns. Discipline in ROADMAP +
ANALYSIS_PLAYBOOK so the GTM Factory keeps metrics 0/null until sourced.


### 2026-06-29 — Self-validation gate: convergence addendum (modes + surfacing + honesty)
Aligned the gate to the cross-factory addendum. SURFACING (A): unmet capabilities now live in
BOTH the dashboard channels — an URGENT OWNER_ACTION `validation-capability-<service>` in
PENDING_OPS (renamed validate-ai-ci -> validation-capability-gemini, urgent) AND a LOOP_HEALTH
`validation` sub-block (enforced_in_ci/capabilities_total/unmet) computed via
`check_validation.py --report` each bookkeeping run. CORRECTNESS (B): (1) scan is runtime-only
(src/+asgi.py) already; (2) PyYAML is a DECLARED dep (requirements-dev) not transitive; (3)
per-PR scoped block needs the base diff -> ci.yml preflight checkout now fetch-depth:0, and the
gate diffs against origin/$GITHUB_BASE_REF (conservative block if unavailable); (4) TWO modes:
default per-PR (declaration+surfacing+honesty always; blocking caps fail only if the PR TOUCHES
them) vs --readiness (any unmet fails — wired into the FULL preflight ship gate); (5) HONESTY: a
real/mock claim must name a covered_by test that EXISTS (gate-checked) and readiness auditors
reconcile it genuinely exercises the path (email-verify trap). Verified: per-PR green, --report
emits total=5/unmet=[ai], --readiness FAILS on the ai gap, honesty FAILS on a bad covered_by.
validate-capabilities is enforced via the existing required `preflight` check (not a separate
required check). required_status_checks unchanged: preflight + functional journeys.


### 2026-06-29 — Self-validation gate: the loop must be able to validate every capability
Owner concern: the journey suite can pass in DEGRADED mode (no key) while the REAL path was
never exercised — so a broken integration could ship green. Built a self-validation gate:
docs/ci/VALIDATION.md declares every external dependency + HOW it's validated (real/mock/
degraded_only); scripts/check_validation.py (wired into preflight ci, REQUIRED check)
(1) scans src/+asgi.py and FAILS on any secret-like env var not declared — proven: it caught
the loop's own undeclared REVENUECAT_WEBHOOK_AUTH (added in #87) on first run; (2) FAILS/blocks
for any blocking:true cap not truly validated; (3) requires each degraded_only GAP to name a
real OWNER_ACTION. Capabilities seeded: auth=real, database=real, billing(Stripe)=mock(signed
round-trip), mobile-billing(RevenueCat)=mock, ai(Gemini)=degraded_only GAP. Closed the AI gap
mechanism: tests/test_llm_live.py (skipif no GEMINI_API_KEY) runs a REAL chat+embedding call
once a spend-capped key is in CI + OWNER_ACTION validate-ai-ci. POLICY (owner-chosen): new
can't-self-validate caps default blocking:true (surface+block until keyed); existing accepted
gaps stay false so the loop isn't halted. PROCESS LESSON: I started editing on a stale already-
merged branch (21 commits behind); the loop had edited the shared ledger files since, so I moved
the work to a fresh branch off main and RE-APPLIED the ledger edits rather than clobber newer
loop changes. Always branch off CURRENT main before editing shared files.


### 2026-06-29 (run 5) — Maximal run: 4 PRs (CORS-lock, Track E visual verification, mobile-nav fix, test coverage) + 8-scout sweep, consuming the first QUALITY_SCORECARD
First run after the independent Quality Auditor bootstrapped docs/quality/QUALITY_SCORECARD.md
(Overall C, ship gate NOT met; 4 ship-critical dims below A: business-case-strength C, store-
readiness C, security B, design-taste B) + opened issues #92–#95. Consumed it as DATA, ran the
full 8-scout sweep (Career+ / referral / security / store-assets / Track-E / accent /
functional-reality / tests-perf) doubling as the ~daily DEEP AUDIT. Functional-reality found
NO critical bugs (core web+mobile loops + side-effects sound). Shipped 4 file-disjoint PRs
through 2 Sonnet reviewers each + the CI gate (all merged), then this bookkeeping PR:
- **#96 CORS-lock** (Track F → TICKED line 206): `asgi.py` no longer defaults to
  `allow_origins=["*"]`; new testable `resolve_cors_origins()` → explicit when set, `[]` on
  Vercel (same-origin web + native mobile unaffected), localhost otherwise; never `*`.
  `tests/test_cors.py` pins it. Clean first pass both reviewers. (Security B→ one of 3 gaps closed.)
- **#97 Track E visual verification** (design-taste #1 lever): `web/e2e/visual-verification.spec.ts`
  captures + commits 24 non-zero screenshots (10 routes/states × desktop+mobile + the 4 legacy
  core-journey shots) incl. the fit-score OUTPUT; un-ignored `web/e2e/__screenshots__` (scoped
  to *.png). Reviewer A REQUEST_CHANGES (1 cycle): scope the un-ignore to PNGs only + assert the
  job-detail heading rendered before the shot. I VISUALLY reviewed the images (vision model) and
  recorded the dual-axis verdict (below).
- **#98 authed-nav mobile fix** (design, SURFACED BY #97's visual review): the authed app header
  crammed brand+nav+email+logout into one non-wrapping row → overlapped at 390px. Made it
  flex-wrap + tighter mobile gaps + hide the email on phones (truncate on larger). Rebuilt +
  re-captured at 390px to PROVE the overlap is gone. Clean first pass both reviewers.
- **#99 test coverage**: greenhouse detail-parse + partial-failure resilience + llm_workflows
  parse_job_description + key-absent guard. Reviewer B REQUEST_CHANGES (1 cycle): CUT a
  tautological prep-pack "golden content" eval (faked LLM returns the golden string verbatim →
  asserts input==output; content quality can't be evaluated key-free) and CUT two
  output-moderation tests that DUPLICATED the existing tests/test_prep_moderation.py.
DUAL-AXIS VISION VERDICT (run 5, web; reviewed a representative set on the vision model):
landing (desktop+mobile), pricing, login/register, dashboard-empty, **job-scored (fit=70 amber)**,
**job-detail (70/100 + "Good match | Matching skills: sql, docker, aws, python, fastapi")**,
coach-gated (honest "Upgrade to unlock"), settings — ALL **FUNCTIONAL PASS** (intended output
visible, real artifact, no dead-end/placeholder) and **DESIGN PASS** (strong type hierarchy,
intentional dark theme, on-brand, not slop) EXCEPT the authed nav overlapped at 390px (DESIGN
FAIL) → FIXED in #98. The web product genuinely clears the VISION design bar — strongly addresses
the design-taste "no visual proof" cap.
DEFERRED (named, buildable — NOT abandoned; recorded so the next run executes cleanly):
- **business-case-strength (#1 ship-critical gap) — Career+ tier as a real entitlement**:
  deferred to a DEDICATED next run, NOT rushed alongside 3 PRs. WHY: the `tier` column is a
  native PG Enum (FREE/PREMIUM), so adding CAREERPLUS needs a live `ALTER TYPE` migration AND a
  real value-differentiation (PREMIUM is already unlimited-everything, so a $24 tier sprawls into
  metering Pro down + a Career+-exclusive feature). NEXT-RUN DESIGN (no enum migration): keep tier
  binary, identify Career+ via the verified `Subscription.plan` prefix (`careerplus_*`, already in
  billing config + written only by a verified webhook), add ONE genuine Career+-exclusive gate +
  the pricing card + checkout. Even then it adds ~$3.6K — the floor-flip ($100K) needs the
  TEAM/B2B2C tier (biggest build). Business-case-strength → A is multi-run convergence work.
- **store assets / brand icon (#93/#95)**: OWNER-BLOCKED per the repo's own standard — BRAND_KIT
  + ACCEPTANCE_AUDIT explicitly say the loop must NOT auto-generate a brand mark ("would read as
  generic-AI slop, fails the DESIGNER QUESTION"); also NO image tooling installed. Did NOT fabricate slop.
- **accent convergence (#95)**: dropped this run — 13-file web find-replace + stale-screenshot
  coherence friction vs the Track E capture; low value vs the screenshots. Clean standalone follow-up.
- **CAPTCHA + cross-instance rate-limit (#94)**: CAPTCHA wants asgi.py (CORS owned it) + owner keys;
  cross-instance needs owner Upstash. Defer.
- **N+1 pagination**: wants asgi.py (CORS owned it); non-critical. Defer.
LESSONS: (1) **Playwright runs headlessly here** despite the version skew — local PW 1.61 wants
chromium build 1228 but only 1194 is pre-installed; launch with `executablePath:'/opt/pw-browsers/chromium'`
(temporary, reverted before commit so CI uses its own download). Also use the LOCAL `./node_modules/.bin/playwright`,
not `npx` (which grabbed a broken global). (2) **maker≠checker earned its keep**: every must-fix
was a reviewer find — the gitignore junk-commit trap + the missing render-assert (#97 Rev A), the
TAUTOLOGICAL golden eval + DUPLICATE moderation tests (#99 Rev B). A faked-LLM "golden content"
test is input==output — content quality needs a real LLM eval (owner key). (3) **Dual-axis visual
review caught a real bug DOM tests missed** — the authed nav overlap at 390px passed every DOM
assertion; only LOOKING at the pixels revealed it. This is exactly what §6 visual verification is for.
(4) **A scout can over-scope** — the store-assets scout proposed installing cairosvg to render a
brand icon; the repo standard explicitly forbids loop-generated brand marks, so I did NOT (respecting
the anchor over the scout).

### 2026-06-29 (run 4) — Maximal run: 5 PRs (mobile monetization server-side, paywall entitlement, prep moderation, scorer bug, web hierarchy) + 8-scout sweep
Ran the full 8-scout sweep (mobile-paywall / mobile-monetization / web-security / store / marketing /
web-design / backend-tests / functional-reality) which doubled as the ~daily DEEP AUDIT.
Functional-reality found NO critical bugs (core web+mobile loops + side-effects sound). asgi.py was
the single contended backend file → owned by exactly ONE PR (mobile monetization, the lowest-incomplete
+ biggest product gap); CAPTCHA, CORS-lock, and privacy-analytics (all want asgi.py) deferred again,
correctly. Shipped 5 file-disjoint value-bar PRs through 2 Sonnet reviewers each + the CI gate:
- **#87 server-side RevenueCat webhook** (Track C → ticked 115+116): `src/mobile_billing.py` +
  `POST /api/billing/revenuecat-webhook` — verifies a shared-secret Authorization header
  (constant-time) and flips `users.tier` ONLY from a verified event (grant on purchase/renewal,
  revoke on EXPIRATION/PAUSED); forged/missing → 401 grant-nothing; unset → 503. Mirrors the Stripe
  webhook's SIDE-EFFECT INTEGRITY; no new table (RevenueCat events carry `app_user_id` = our User.id,
  so user resolution needs no durable row — smallest implementation that fully delivers). Reviewer A
  (REQUEST_CHANGES → 1 cycle): add PAUSED to the revoke set (a paused Android sub must lose access) +
  a malformed-JSON 400 test; documented TRANSFER as an intentional no-op (can only under-grant).
- **#88 mobile paywall ↔ entitlement** (Track B line 88 → ticked): reads tier + refreshes on open;
  PREMIUM → confirmation state (no buy CTA, fixes a real stale-prompt bug), FREE → honest offer (no
  fake purchase success). jest-expo test both states + refresh + honest-purchase. Clean first pass.
- **#86 prep-pack output moderation** (Apple §1.2): the coach moderated output but prep packs/cover
  letters/etc. did not — closed the asymmetry at the single `_call_llm` chokepoint (json-mode parsing
  skipped to avoid false positives). Clean first pass both reviewers.
- **#85 scorer zero-vector guard** (real bug): `cosine_similarity` did `0/0 == nan` on a degenerate
  embedding — NOT an exception, so it slipped past `score_job`'s try/except into a `nan` fit score.
  Reviewer B (REQUEST_CHANGES → 1 cycle): dropped an out-of-scope normal-path test + a redundant assert.
- **#89 web visual hierarchy** (design): pricing plan NAMES were muted to the same gray as helper text
  (hierarchy inversion on a conversion surface) → promoted; job-detail section headers had no size →
  text-lg; "Salary negotiation scripts" → "coaching" (honesty; no standalone scripts artifact). Both
  reviewers APPROVE; B confirmed it's a real taste fix, not churn.
LESSONS: (1) **`git add -A` is a foot-gun while reviewer worktrees live under `.claude/worktrees/`.**
During a post-review trim commit, `git add -A` swept the reviewers' worktree gitlinks AND cross-branch
files into the scorer branch (the commit showed `.claude/worktrees/*` + asgi.py + mobile_billing.py +
other branches' tests). Self-caught via the push warning + a `git show --stat`. FIX/RULE: after the
first push, NEVER `git add -A` — stage explicit paths only (`git add src/x.py tests/y.py`); reset the
contaminated commit with `git reset --hard <prev>` then re-add explicitly. Recovered cleanly, no bad
merge. (2) **maker≠checker earned its keep again** — both must-fixes (PAUSED revoke + the 400 test;
the padding test) were reviewer finds, resolved in 1 cycle; 3 of 5 PRs were clean first pass. (3)
**Smallest-implementation call paid off**: skipping a MobileSubscription table (no new migration/cascade
risk) because RevenueCat events carry `app_user_id` kept #87 a clean 3-file PR; both reviewers agreed it's
sound for the server half (out-of-order/TRANSFER flagged as named follow-ups, not blockers).
FOLLOW-UPS (named, buildable): (a) **on-device react-native-purchases SDK** to initiate mobile purchases
(Track C line 114) — needs owner RevenueCat keys, native. (b) **CAPTCHA** as a coherent web+mobile+api
unit (still wants asgi.py). (c) **privacy-safe server-side analytics** (aggregate counters, no PII) — the
marketing scout's top pick, wants asgi.py + a new table/migration (defer to a clean-asgi.py run; PMF
measurement foundation). (d) **TRANSFER handling + event idempotency** in the RC webhook before go-live.

### 2026-06-29 (run 3) — Maximal run: 7 PRs (README, mobile-auth tests, billing tests, coach/scorer tests, store docs, web a11y, brand kit) + 8-scout sweep
Ran the full 8-scout sweep (mobile / backend-security / store / README-freshness / marketing /
web-design / backend-tests / functional-reality) which doubled as the ~daily DEEP AUDIT.
Functional-reality found NO critical bugs (core web+mobile loops + side-effects sound; signup→
dashboard→fit score→detail, billing webhook-gated, account-deletion cascade all solid). Selected
the MAXIMAL file-disjoint value-bar set across 7 PRs (+ this bookkeeping), each through 2 Sonnet
reviewers + the CI gate. NO PR owned `asgi.py` this run (see CAPTCHA decision below):
- **#77 README + setup.sh freshness** (Track A/§14): the README was a stale prototype doc
  ($4.99 one-time / $350K / Flutter / Railway, linking dead files). Rewrote to reality
  (subscription $12/$24, Expo/Next/FastAPI/Vercel/Neon/Gemini, honest $57.5K planning case).
  Reviewer A: mobile quick-start said `npm run dev` (no such script) → `npm run start`.
- **#78 mobile auth-screen tests** (Track B → TICKED "auth wired"): jest-expo tests render the
  REAL Login/Register screens, assert validation/API-call/navigation/error. Reviewer A: assert
  `signUp` WAS called in the ApiError test (not a validation short-circuit) + add a blank-email
  case to pin the `||` guard + collapse a two-`waitFor` race.
- **#79 billing webhook test hardening** (Track C/F): the webhook user-mapping FALLBACKS
  (by customer_id, by subscription_id) were untested — every existing test passed
  `metadata.user_id`, but Stripe's own renewal/dunning events omit it (silent entitlement-loss
  risk). + `_period_end` edge cases. Both reviewers APPROVE first pass.
- **#80 coach/scorer deterministic tests** (Track E): scorer explanation rating bands +
  truncation (tested DIRECTLY — the key-free heuristic caps overall at 70, so the ≥80
  "Excellent" band is only reachable with embeddings), coach context-omits-missing + history
  chronological-order + session-scoping. Both reviewers APPROVE first pass.
- **#81 store-docs accuracy** (Track D/§14): APP_PRIVACY_LABELS claimed the subscription cascade
  "not yet asserted" — but `test_billing.py::test_account_deletion_cascades_subscription` ALREADY
  proves it (a stale note that would send a future loop to redo done work). Corrected + refreshed
  ACCEPTANCE_AUDIT G7 to current Play asset spec (feature graphic required, 2026 alt text).
- **#82 web a11y focus rings** (Track A/E): WCAG 2.4.7 — buttons + nav/footer/auth/legal links
  had hover-only styles (unusable for keyboard users). Added focus-visible rings (offset on
  bordered buttons, snug on inline text links). Reviewer A caught 2 missed links (waitlist-form,
  login) → completed coverage across register/settings/terms/privacy too.
- **#83 brand kit** (Track G → TICKED): `docs/brand/BRAND_KIT.md` codifying the real palette/
  type/voice. Reviewer A: cite the real file for the web accent (`web/components/ui.tsx`
  `bg-indigo-500`), not just "Tailwind indigo-500".
ROADMAP ticked this run: Track A auto-migrate (owner done + verified), Track B auth-wired (#78),
Track E gates-enforced-in-CI (verified live: a merge was BLOCKED "2 of 2 required checks in
progress"), Track G brand kit (#83).
LESSONS: (1) **maker≠checker earned its keep again** — every must-fix (the `npm run dev` ghost
script, the validation-short-circuit blind spot in the register test, 2 missed a11y links, the
uncited accent token) was a reviewer find, not a maker find; 4 PRs drew a REQUEST_CHANGES, all
resolved in ONE cycle. (2) **A scout can be WRONG — verify before building.** The store scout
recommended adding a "subscription cascade assertion" test; it ALREADY existed
(test_account_deletion_cascades_subscription). Caught it by reading the file end before writing →
dropped the redundant test (value bar forbids duplicate coverage) and instead fixed the STALE doc
note that had sent the scout down that path. (3) **CAPTCHA deferred, on purpose (DECISION
COROLLARY).** Track F's only remaining buildable security item is CAPTCHA, but a server-side
verify that becomes a hard gate the moment the owner sets the secret would dead-end signup unless
the web+mobile widgets send a token too — so it's a coherent web+mobile+api unit, not a clean
single-file PR, and it sprawls into web/app (colliding with the a11y PR). Deferred as a dedicated
future run rather than shipped half-wired; recorded in PENDING_OPS. So NO PR owned asgi.py this
run — and that's correct, not artificial scarcity (security headers + CORS-lock mechanism already
shipped; the audit-suggested CORS "validation/`default-src 'none'`" was REJECTED as padding/risky:
`default-src 'none'` would break the Swagger /docs CDN assets the existing CSP comment explains).
FOLLOW-UPS (named, buildable, next runs): (a) **CAPTCHA** as a coherent web+mobile+api unit
(Cloudflare Turnstile, env-gated no-op, round-trip-tested with the test keys) on a clean-asgi.py
run. (b) **mobile RevenueCat/StoreKit + Play Billing + server-side receipt verification** (Track
C, store FAIL A4/G4) — the big remaining product gap; needs asgi.py + owner RevenueCat keys. (c)
**ASO/SEO plan + Launch plan docs** (Track G) — deferred this run as lower-priority pre-PMF
planning to avoid doc-padding; brand kit was the one genuine Track G asset. (d) **mobile/web
accent convergence** (pick one canonical accent hex). (e) **scorer heuristic-only flag** surfaced
to the UI (needs frontend coupling).

### 2026-06-29 (run 2) — Maximal run: 4 PRs (waitlist, mobile screen tests, design, retire Flask) + 8-scout sweep
Ran the full 8-scout sweep (mobile / waitlist+email / web design / security / scorer-honesty /
tests / store / functional-reality). Picked the MAXIMAL file-disjoint set; `asgi.py` was the
single contended backend file → owned by exactly ONE PR (waitlist, the binding growth
constraint). Shipped 4 through 2 Sonnet reviewers each + the CI gate:
- **#68 waitlist capture** (Track G/H, the binding pre-launch growth constraint per
  GROWTH_STATUS): NEW `waitlist` table (NEW table ⇒ AUTO_CREATE_TABLES-safe; a column-add would
  NOT be) + autogenerated Alembic migration (drift test detected ONLY the new table) +
  `POST /api/waitlist/join` (validation, 5/hr rate limit, enumeration defense, IntegrityError-
  idempotent) + premium `web/app/waitlist` page. NO email sent (DECISION COROLLARY — gating on
  an unbuilt email loop would dead-end the visitor; the DB row is the real side-effect). Reviewer
  B: "Work email"/`you@company.com` filters out unemployed seekers → "Email"/`you@example.com`;
  reuse `<Card>`; add `/waitlist` to sitemap + a `metadata` export (split into a server page +
  client form). Email-provider abstraction + double-opt-in DEFERRED (speculative until a real/
  sandbox provider + round-trip test — Track H / F4.1; do NOT build the unused abstraction now).
- **#71 mobile component tests** (Track B/E): the screens were built+wired but had only the
  markdown test. Added jest-expo tests for the API client + Pipeline + Job-detail (21 green) that
  render the REAL screens with mocked I/O and assert real data + empty/error/paywall states.
  Reviewer B: don't re-test markdown hash-stripping (mock the Markdown component, assert the
  screen's title/content integration); assert the offline message. Ticked Track B "jobs/detail
  render real data", "pipeline screen", "component tests green" (device run stays human/CI).
- **#70 retire legacy Flask `app.py`** (Track A — the lowest incomplete item, "keep or retire"
  → RETIRE): deleted `app.py` + `start_webapp.sh` + the 5 flask dev deps + the flake8 ignore;
  fixed the README entrypoint line. Kept `src/main.py`/`src/crm` (still used by `cli.py`).
- **#69 design**: removed the emoji (🎉) from the post-checkout "Welcome to Premium" headline —
  emoji-as-iconography on a first-class conversion surface (§6b avoid-list).
LESSONS: (1) **jest-expo + ES-import hoisting foot-gun**: `import ScreenUnderTest` hoists ABOVE
`const mockPush = jest.fn()`, so an `expo-router` mock written as `router: { push: mockPush }`
captures the fn while still `undefined` (the screen's `router.push` is then undefined at call
time). FIX/RULE: in a jest.mock factory, reference test-scope mocks via a LAZY arrow
(`push: (...a) => mockPush(...a)`), never a direct value — resolves at call time. (Isolation
debug passed because it required the module lazily inside the test body, hiding the bug.) (2)
`global` isn't typed without @types/node in the mobile tsconfig → use `globalThis.fetch` in RN
tests. (3) maker≠checker earned its keep AGAIN: every must-fix (the exclusionary "Work email"
copy, the markdown-duplication test, the missing SEO metadata, the offline-message gap) was a
reviewer find, not a maker find. (4) A NEW table is deploy-safe under AUTO_CREATE_TABLES; the
scorer "heuristic-only" honesty flag was DEFERRED precisely because it needs a JobScore COLUMN,
which create_all won't apply on the live Neon DB until auto-migrate is enabled (OWNER_ACTION).
FOLLOW-UPS (named, buildable, next runs): (a) **scorer heuristic-only flag** — surface it once
auto-migrate is live (needs a JobScore column) OR via a key-absent global "heuristic mode"
signal needing no column. (b) **mobile RevenueCat/StoreKit + Play Billing + server-side receipt
verification** — a coherent monetization unit (Track C, store FAIL A4); its server receipt
check needs `asgi.py`, so run it on a clean-asgi.py run; never ship a client-trusted unlock. (c)
**Track F (CAPTCHA, CORS-lock, cross-instance rate-limit)** — all want `asgi.py`; the
cross-instance store also needs owner-provisioned Upstash. (d) **README is badly stale** (still
the $4.99/Flutter/Railway/$350K prototype README — contradicts the current subscription/Expo/
Vercel reality + business case) → a dedicated rewrite PR (artifact-freshness, high value). (e)
double-opt-in + email-provider abstraction once a sandbox email round-trip exists.

### 2026-06-29 — Maximal run: 5 feature PRs (security, tests, design, store docs, mobile harness) + DEEP AUDIT
First product-feature run after ~6 runs of pure CI/enforcement plumbing. Ran the full 8-scout
sweep (which doubled as the ~daily DEEP AUDIT — functional-reality + security + store + quality +
design lenses; gate confirmed GREEN: 94 tests, ~78% cov, 9 journeys). Selected a maximal
file-disjoint set; asgi.py was the single contended file → owned by exactly ONE PR (the security
fix, the lowest-incomplete Track). Shipped 5 through 2 Sonnet reviewers each + the CI gate:
- **#62 rate-limit proxy-IP + Permissions-Policy** (Track F): `request.client.host` is the PROXY
  IP on Vercel, so per-IP limits collapsed every user into one bucket. New
  `src/api/ip_extraction.get_client_ip()` reads platform forwarding headers ONLY behind a trusted
  proxy (TRUST_PROXY_HEADERS, default ON under VERCEL); off-proxy uses the un-spoofable peer (NOT
  trusting headers is the point — else a client spoofs XFF to bypass the limiter). + a default-deny
  Permissions-Policy header. Reviewers: added the explicit-opt-out test + swapped dead
  `interest-cohort` for live `browsing-topics`.
- **#63 endpoint outcome tests** (Track A/C/E/F): jobs AUTHZ BOUNDARY (user B can't GET/PATCH user
  A's job → 404, no leak; A's data untouched), all status transitions persist, prep-pack
  free-tier limit WITH key present + premium-unlimited + honest 503, coach success contract +
  daily LLM ceiling 429. BOTH reviewers flagged 4 tests already covered in test_core_journey /
  test_coach_safety → removed (value bar forbids re-testing covered behavior); 12 kept.
- **#64 design** (Track A/E): killed landing card-spam (avoid-list) → content-first section;
  pricing emoji `✓` → inline SVG. Reviewer B (taste) rejected a decorative accent bar I added
  (not a system motif) → removed; let type weight + spacing carry it.
- **#65 store compliance docs** (Track D): data-retention disclosure (honest, with the PITR/backup
  caveat) + AI-content disclosure (Apple §1.2). Reviewer A caught 2 HONESTY overclaims →
  corrected: "no fabricated AI output" is FALSE (fit scoring silently falls back to a neutral
  semantic score with no key); and the deletion test doesn't assert the Subscription cascade.
- **#66 mobile jest-expo harness** (Track B/E): FIRST mobile test infra — jest-expo 56.0.5 + RTL +
  a component test of the Markdown prep-renderer asserting intended output (hashes/bold stripped,
  lists render). Wired into preflight ci (CI runs it). Reviewer A: jest absence must FAIL the gate
  (added else-fail) + strengthened the empty-render assertion. VERIFIED locally: npm install + jest
  4/4 green + tsc clean — bleeding-edge RN 0.85/React 19.2/Expo 56 DID have a matching jest-expo.
LESSONS: (1) **maker≠checker earned its keep hard this run** — EVERY PR drew a real reviewer
REQUEST_CHANGES (4 duplicate tests, a taste-failing accent bar, 2 honesty overclaims, a silent-pass
gate guard); none were maker finds. (2) **`cmd && echo … ; git push` foot-gun**: a `;` after a
failing `&&` flake8 let an F401 push anyway — use `&&` through the whole chain or check exit
explicitly. (3) The mobile toolchain IS reachable headlessly (jest-expo pinned to the SDK) — mobile
component tests are now a real, gated BUILDS≠WORKS path, not just tsc/lint. FOLLOW-UPS (named,
buildable, next runs): (a) **scorer honest-degradation flag** — fit scoring silently shows a
heuristic-only score when no Gemini key (src/ranking/scorer.py ~109); surface a "heuristic-only"
signal to the UI so the score isn't implied AI-derived (a real BUILDS≠WORKS/honesty gap). (b) add a
Subscription seed+assertion to the account-deletion test so the cascade proof is exhaustive. (c)
**waitlist landing + capture + email-provider abstraction** (Track G/H) is the next asgi.py owner —
binding growth constraint, deferred this run because security owned the asgi.py slot. (d) more
mobile screen tests before ticking Track B's component-tests box (one renderer = a start).

### 2026-06-28 — Enforcement turned ON: required checks (admins included) + `--auto` merge protocol
After CI was verified GREEN on the first run, the owner authorized turning enforcement on.
Changes: (1) branch protection on `main` requires `preflight (lint + typecheck + tests)` +
`functional journeys (web E2E)` with enforce_admins=ON, and repo auto-merge enabled; (2) the
merge protocol changed from `gh pr merge --admin` (bypasses checks) to `gh pr merge --squash
--auto --delete-branch` (WAITS for required CI). KEY CONSEQUENCE for the loop: `--admin` no
longer bypasses — a red required check BLOCKS merge for admins too, so the loop MUST fix a red
gate (≤2 cycles) or abandon, never force. PROMPT.md + ROADMAP shipping protocol updated to say
this. enforce_admins means even an emergency needs the owner to (temporarily) relax protection —
that's intentional (the rail is the point). strict=false so file-disjoint parallel PRs still
auto-merge without serial rebases. The `migrate` job is push-to-main only, so it is NOT a
required PR check.

### 2026-06-28 — Applied .github/workflows/ci.yml (owner-authorized, interactive — a deliberate exception)
STANDING RULE is the loop NEVER edits .github/ (hangs the headless run; it's the tamper-proof
enforcement rail). The OWNER explicitly asked, in an interactive session, to create the workflow
file — so I did (the rule's hazard is headless hangs + self-weakening enforcement; neither
applies when the human directs it live). Committed `ci.yml` with the 3 jobs from PROPOSED_CI.md;
added a guard so the `migrate` job SKIPS cleanly when the DATABASE_URL secret is unset (so the
first push to main doesn't redden over a missing secret). What the loop STILL can't do (truly
owner-only): set the DATABASE_URL Actions secret (never paste a secret to the loop), enable Neon
PITR, run `alembic stamp head` against prod, set Vercel AUTO_CREATE_TABLES=0, and mark the two
checks REQUIRED in branch protection (do that only AFTER they're green on a PR). enforced_in_ci
stays false until the checks are required — a committed workflow ≠ an enforced gate.

### 2026-06-28 — Auto-migrate-on-deploy: real Alembic migrations + a drift gate (Part B)
Part A (gates as required CI checks) already shipped (PR #56, #57) — skipped per directive.
Part B = end the manual `init_db.py` schema push. The DB was being created by
`Base.metadata.create_all` on boot (AUTO_CREATE_TABLES=1) — fine for NEW tables but it never
ALTERs, so column changes would silently not migrate. SHIPPED (through the gate): `alembic.ini`
+ `migrations/env.py` (reads DATABASE_URL at runtime, normalizes postgres://, no committed
creds) + autogenerated initial migration (all 10 tables); verified `alembic upgrade head` on a
fresh DB builds the full schema with ZERO drift. KEY GUARD: `tests/test_migrations.py` fails the
build if the models change without a matching migration (the "forgot the migration" mistake) —
this is the precondition that makes auto-apply SAFE (a schema that doesn't match the code can't
reach main). STAGED the `migrate` job in PROPOSED_CI.md: push-to-main + `needs:[gate jobs]` +
forward-only `alembic upgrade head` (NEVER downgrade/reset); NOT a required PR check. LESSONS:
(1) excluded `migrations/versions` from flake8 (autogenerated; env.py stays linted) — generated
files shouldn't fail a zero-warning lint. (2) The existing prod DB was bootstrapped via
create_all, so the owner must `alembic stamp head` ONCE before enabling the job, else the initial
migration re-runs and errors on existing tables. (3) Auto-apply removes the manual schema
checkpoint — the replacement net is PITR/backups, so the OWNER_ACTION says enable them FIRST and
states the tradeoff. Tracked: OWNER_ACTION `auto-migrate`, LOOP_HEALTH `auto_migrate_on_deploy:
staged`, ROADMAP Track A.

### 2026-06-28 — Quality gates staged as REQUIRED CI checks (resolves the "not enforced in CI" wall)
The gate runs locally + in the routine but does NOT block `gh pr merge --admin` — a BUILDS≠WORKS
/ lint-failing change could slip in. Mirrored GroceryManager's OUTCOME, adapted to this stack.
SHIPPED (product side, through the gate): (1) browser-level functional journey
`web/e2e/core-journey.spec.ts` + `web/playwright.config.ts` — boots a running web build + running
FastAPI + seeded throwaway sqlite, asserts the core-product OUTPUT renders (signup → working
dashboard, no dead-end → add job → **fit SCORE renders as a real number** → detail); self-seeds;
verified GREEN locally (2 passed). (2) lint at zero warnings (`eslint --max-warnings=0`).
(3) `docs/ci/ROUTE_INVENTORY.md`. (4) TEST-ONLY rate-limit bypass `E2E_DISABLE_RATE_LIMIT` in
asgi.py, HARD-REFUSED on Vercel (`_assert_required_secrets` raises; regression-tested).
STAGED (can't push `.github/` — it trips a sensitive-file prompt that hangs the headless run):
`docs/ci/PROPOSED_CI.md` = exact `ci.yml` + the branch-protection required-checks list. Carried
GroceryManager's two gotchas: (a) `NEXT_PUBLIC_API_URL` is baked at BUILD time → CI builds with
it set (no next-auth here, so no trusted-host callback — pointing the build at the local API is
the equivalent); (b) one runner IP trips the per-IP limiter → the test-only bypass on the E2E
API server. RAISED the META proposal (LOOP_HEALTH.harness_proposals_open: 1,
`enforced_in_ci: false`). LESSON: a green LOCAL gate ≠ an enforced gate — "merged" without
required CI is an honor-system gate; the only durable fix is required status checks, and the
loop can stage everything but the `.github/` push + the branch-protection toggle (owner-only).
NEVER mark a red/flaky check required (would block the loop) — verify green in CI first.

### 2026-06-28 — LOOP HEALTH made measurable (self-improving ≠ busy) + META self-check
Added FACTORY_STANDARD §10b (byte-identical): the deep audit grades the PRODUCT; LOOP_HEALTH
grades the LOOP. Seeded `docs/autonomous-loop/LOOP_HEALTH.md` (signal: bootstrapping) — update
EVERY bookkeeping run with REAL counts; CLASSIFY every abandoned change
(gate_tsc/gate_pytest/gate_flake8/gate_lint/gate_build/review_value/review_correctness/
circuit_breaker/conflict/dead_end/blocked_owner) so the loop never re-attempts the same
dead-end; `churning`/`stuck` → open ONE "loop: harness improvement proposal" issue (the only
channel to improve the loop's own rules — it can't edit its routine/.claude/.github). Added the
file to ROADMAP's shared-ledger (bookkeeping-PR-only) list + a LOOP HEALTH bullet. META
SELF-CHECK done now over the last ~14 loop-memory entries: NO wall recurred ≥2 runs unaddressed
— httpx-unpinned and gitignored-source were each ONE-TIME walls (fixed + a permanent preflight
guard each); the only "again" pattern is reviewers catching must-fixes (a feature, not a wall).
So opening a proposal would manufacture a fake signal — did NOT. Honest counts only;
observability, NOT a ship gate. Going forward a churning/stuck reading MUST raise a proposal.

### 2026-06-28 — Maximal run: 4 feature PRs (API hardening, web Settings, coach safety, evals)
Ran the full ~8-scout sweep, selected a file-disjoint set, shipped 4 PRs through 2 Sonnet
reviewers each + the gate, then this bookkeeping PR. asgi.py was the single contended file →
exactly ONE PR owned it; mobile-billing + waitlist (both want asgi.py) were deferred as a
coherent next unit.
- **#47 API hardening** (Track A/F): consistent error envelope (additive — keeps `detail`,
  adds `error{code,message,request_id}`), request-id middleware (`X-Request-ID` + log
  contextvar), stdlib JSON logging (no new dep), CORS prod-warning. Both reviewers caught a
  real JsonFormatter reserved-key collision (extra= merged after fixed fields → could drop
  the traceback) → fixed (merge extra first, fixed fields win) + regression test.
- **#49 web Settings/account deletion** (Track D): the page the Privacy Policy already
  promised; deletes via the real DELETE /api/auth/me (verified round-trip: account+data gone,
  token 401s, login fails). Reviewer B: reuse the design system (added Button danger variants)
  + the billing copy over-claimed a portal that doesn't exist → honest support-email copy.
- **#51 coach safety guardrail** (Track D/Apple §1.2, A1): conservative ContentModerator on
  input+output (self-harm→crisis resources; violence/hate/sexual-gen blocked; legit career
  topics pass). Reviewers found real gaps: method phrasings bypassed (hang/od/etc.), negation
  FPs ("I'm not suicidal"), and a CRITICAL ordering bug — the client-None check ran BEFORE
  moderation, so crisis resources were unreachable with no key → moderation now runs first.
- **#52 eval suite + coverage floor** (Track E): golden-expectation evals for the
  deterministic heuristic scorer (30+40*skills_score → 70/30/50) + coach suggestions;
  coverage floor fail_under=65 wired into preflight ci (branch coverage ~69%).
LESSONS: (1) **CONCURRENT GIT IN ONE WORKING TREE CORRUPTS BRANCHES.** Background reviewers
launched WITHOUT isolation ran `cd web && tsc` / `git checkout`, which switched the MAIN
tree's HEAD out from under the maker mid-edit — a commit landed on the wrong branch and a
branch got reset to a stale ref (no-diff PR-create error). FIX/RULE: any reviewer/agent that
must check out a branch or run build/test commands MUST use Agent `isolation: "worktree"`
(separate working dir + HEAD). Reviewers that only need the diff should use remote refs
(`git diff origin/main...origin/<branch>`) and NEVER `git checkout`. After switching to
worktree-isolated reviewers, zero further corruption. (2) **A desynced working tree can read
clean** — `git status` showed clean while files differed from HEAD (stat-cache race from the
concurrent checkout); recover with `git checkout -B <branch> origin/<branch> --force`. (3)
Reviewers earned their keep again: every must-fix this run (the formatter collision, the
billing over-claim, the coach ordering bug + self-harm bypasses) was a reviewer find. (4)
DEFERRED (next run, asgi.py now free): alembic migrations + AUTO_CREATE_TABLES cutover; CAPTCHA
+ cross-instance rate-limit + waitlist capture (all want asgi.py); mobile RevenueCat/StoreKit
+ server-side receipt verification (coherent monetization unit); prep-pack generator output
moderation; web Stripe billing-portal endpoint.

---

### 2026-06-28 — Maximal run: 4 feature PRs (web billing, web polish, mobile markdown, store docs)
Ran the ~8-scout sweep, selected a file-disjoint set, and shipped 4 PRs through 2 Sonnet
reviewers each + the gate, then this bookkeeping PR:
- **#40 web Stripe billing** (Track C, the business-case lever #1): `src/billing.py` +
  `/api/billing/checkout` (real `stripe.checkout.Session.create`) + `/api/billing/webhook`
  (signature-verified) + a NEW `subscriptions` table (not a new `users` column) + `User.subscription`
  cascade. SIDE-EFFECT INTEGRITY: entitlement flips ONLY from a verified webhook; checkout
  refuses honestly (503) when unconfigured. Reviewer A caught a real gap — `checkout.session.completed`
  fires `payment_status="unpaid"` for async methods (bank/ACH) and would grant free Premium →
  guarded on `payment_status` + regression test. Reviewer B caught a broken `?next` upgrade
  funnel (register ignored it) → fixed with an open-redirect guard.
- **#41 web polish** (Track A/E): Skeleton primitive + composed pipeline/job/prep skeletons,
  and a dependency-free **Markdown renderer** (`web/components/markdown.tsx`) so prep packs
  render structured (was raw `<pre>`). Reviewer B → semantic `<h2/h3/h4>` (was `<p>`) + a11y.
- **#42 mobile prep markdown** (Track B): a zero-dependency native `Markdown` (Text/View) —
  conservative, no new native dep. Reviewer B → full-contrast body for paid content + wider
  numbered-list marker. Reviewer A verified RN nesting valid (no `<View>`-in-`<Text>`).
- **#43 store docs** (Track D): code-accurate App Privacy labels + Google Data Safety + ASO
  copy + permissions audit; corrected ACCEPTANCE_AUDIT to shipped state (kept honest FAILs:
  mobile billing + rendered screenshots → readiness still NO). Reviewer A caught an over-claim
  ("10 prep packs/mo" but Premium is unlimited in code) → matched to code. Reviewer B caught
  console-rejection issues (keyword >100 chars, short desc >80, mis-categorized Data-Safety
  User ID) → all fixed.
LESSONS: (1) **STALE `origin/*` ref silently resets your worktree.** A fresh container's
`origin/main` ref was 6 commits behind the real remote (PRs #34–#39 unfetched). `git checkout
-B branch origin/main` reset the working tree to that OLD commit, so edits got anchored to
stale file text that would have REVERTED #34–#39. Caught it because asgi.py/conftest looked
different than the first reads. **FIX/RULE: always `git fetch origin main` BEFORE branching,
and branch from the freshly-fetched ref** — never trust a clone's `origin/*` ref age. (2)
**A leftover remote branch can block a push** — an old `feat/web-polish-states` (PR #35's head)
existed remotely; reused-name push was rejected (non-fast-forward). Use a unique branch name
per run or delete stale ones. (3) **Bash cwd persists between calls** — a `cd mobile` made a
later `find docs` fail from the wrong dir; cd back to the repo root (or use absolute paths).
(4) Reviewers earned their keep again: every must-fix this run (unpaid-grant, `?next` funnel,
semantic headings, the unlimited-vs-10 over-claim, the char-limit/category store defects) was
a reviewer find, not a maker find. maker≠checker holds.
FOLLOW-UPS (scouted, deferred — collide with asgi.py which billing owned this run, so next
run when asgi.py is free): CAPTCHA on public forms (new `src/security/captcha.py` + register/
login edits); cross-instance rate-limit + spend-ceiling (Upstash/Postgres); consistent error
envelope + structured logging; web account-deletion UI (web has no Settings page); waitlist
landing + email-provider abstraction (Track G/H); mobile StoreKit/Play Billing (Track C).

---

### 2026-06-27 — Bootstrap lesson
- **The repo wins over assumptions.** The bootstrap charter assumed "Python SaaS, NO
  mobile app." Reality: a **Flutter** prototype existed in `/mobile`. Owner chose to
  re-platform to **Expo/React Native + TypeScript** (matches the apparatus: preflight
  `tsc`, mobile CI). Flutter was moved to `/mobile-flutter-legacy` for reference, not
  deleted blindly. **Always orient against the real tree before building.**
- **BUILDS ≠ WORKS is not theoretical here.** `import api` exits 0, but `api.py` calls
  `AuthService.create_user/generate_token/authenticate_user`, `JobScorer().score_job(job=dict)`,
  `workflows.workflow_company_dossier`, `coach.chat(db=...)` — **none exist with those
  signatures** in `src/`. Only `/health` is functionally real. Import-success and
  HTTP-200 prove nothing; assert the user-visible outcome.
- **Graceful degradation is a release gate, not a nicety.** Scoring/prep/coach hard-fail
  with no `GEMINI_API_KEY`. The core journey must work (heuristic fallback) in a seeded
  env with no paid key, so the journey suite can run anywhere.
- **No CI exists and the loop may not add it** (`.github/` is off-limits). The gate is
  `scripts/preflight.sh` run locally + the two-gate readiness audit. CI wiring is an
  owner action (workflow scope) in PENDING_OPS.
- **Honest baseline beats a green-looking fake.** DoD starts all `[ ]`; business case is
  honestly below the $100K floor (`floor_met_year1: false`); growth is `pre_launch`,
  engine 0%. Convergence happens over scheduled runs, not by ticking boxes early.

### 2026-06-28 — Maximal run: 5 feature PRs (ATS, web SEO, account/security, mobile, legal)
Ran the full ~8-scout sweep and shipped 5 file-disjoint, value-bar-clearing PRs through
2 Sonnet reviewers each + the gate:
- **#34 ATS import-preview** (Track A): wired the existing-but-unused Greenhouse/Lever
  ingestion into `POST /api/jobs/import-preview` (preview-only, no side effects). Returns
  REAL listings or a TRUTHFUL empty/unreachable/unsupported state — clients now set
  `last_error` so "unreachable" is never reported as "no jobs." Reviewer A caught a
  **CRITICAL SSRF** (we fetch a user-supplied URL server-side) → added `url_guard.py`
  (block non-http(s) + private/loopback/link-local resolved IPs) at the endpoint + detector.
- **#35 web SEO/states** (Track A/E): metadata (title template, OG/twitter, metadataBase
  gated on env), sitemap.ts/robots.ts (disallow /app + /api), honest status-update error.
- **#36 account deletion + lockout + headers** (Track D/F): real `DELETE /api/auth/me`
  (cascade), per-account login lockout, HSTS + frame-ancestors CSP. **No schema change on
  purpose** — AUTO_CREATE_TABLES only creates missing *tables*, so adding User columns would
  break the live Neon DB; lockout uses in-memory state like the rate limiter.
- **#37 mobile** (Track B): prep packs render inline (was a 600-char-truncated Alert =
  BUILDS≠WORKS dead-end); paywall emoji→Ionicons.
- **#38 legal** (Track D/G): /privacy + /terms, code-accurate. Reviewer A caught two honesty
  bugs: embeddings (resume_embedding/jd_embedding ARE computed via Gemini + stored) were
  undisclosed, and Stripe was listed as active though verify-purchase is a 501 — both fixed.
LESSONS: (1) **Process-global in-memory state leaks across tests** — the rate-limit buckets
accumulated and tripped a spurious 429 in a later test once the suite grew; fixed with an
autouse conftest reset (now also clears `_LOGIN_FAILURES`). Any module-level dict the app
mutates needs a per-test reset. (2) **A server-side fetch of a user URL is an SSRF hole** —
always guard scheme + resolved IP; residual DNS-rebinding/redirect risk needs a validating
transport (FOLLOW-UP, code not owner). (3) **Reviewers as honesty check** — both legal
honesty bugs and the SSRF were reviewer finds, not maker finds; maker≠checker earned its keep.
FOLLOW-UPS for next runs (not blocking): waitlist landing + capture + email-provider
abstraction (Track G/H — scouted, deferred as a coherent larger unit); markdown renderer for
mobile prep content; full structured-logging/error-envelope across the API; web account-
deletion UI (web has no Settings page yet); SSRF validating-transport for redirect/rebinding.

### 2026-06-28 — Unpinned transitive httpx silently broke the whole test suite
A fresh container install floated the (unpinned, transitive-via-openai) `httpx` to 0.28.1.
httpx 0.28 dropped the `Client(app=...)` shortcut that starlette 0.35.1's `TestClient`
still passes, so `TestClient(app=...)` raised `TypeError` at construction — EVERY test in
`tests/journeys` errored before running. The preflight CI gate and the Track E journey suite
(`E2E_JOURNEYS_PASSED`) could not run at all, while a production deploy looked fine because
`TestClient` is test-only. Same local-green/repo-or-prod-broken family as the
gitignored-source foot-gun. Fix: pin `httpx==0.27.2` in `requirements.txt` (prod==dev, zero
drift; `requirements-dev.txt` inherits via `-r`). openai 1.59.6 supports httpx >=0.23,<1, so
the old `proxies` crash stays fixed. LESSONS: (1) on a fresh clone the gate runs against
LATEST floating transitives — pin anything whose major/minor API your tooling depends on,
even transitive ones; (2) a green local checkout with stale wheels hides this — the bug only
appears on a clean install, so treat "fresh-container CI red" as signal, not noise. Upgrade
path: lift the pin once fastapi/starlette are bumped to a TestClient that uses ASGITransport
(bumping fastapi from 0.109.0 risks asgi.py route-mirroring internals — deferred).

### 2026-06-27 — Cloud routines + dashboard wired (handoff)
The three scheduled cloud routines that drive this repo (source = this GitHub repo,
env FactoryDashboard) are LIVE. Future runs: do not recreate them; update via the
schedule skill if needed.
- **product factory** — `trig_01E9AFM1m7ZVJXHSzFswhYUD`, cron `0 */6 * * *`, Opus.
- **Growth Agent** — `trig_01PntigzEpuhp7wBxQNHzJvy`, cron `0 14 * * *`, Sonnet + Gmail.
- **daily digest** — `trig_01XfvH9BbgDNzEau6jBU7QRa`, cron `0 13 * * *`, Sonnet + Gmail.
JobScraper is registered in subhsubh24/AutoFactoryDashboard `config/projects.ts`
(slug `jobscraper`, kind `web+mobile`). Manage routines at
https://claude.ai/code/routines. Owner-only (Human-Core) steps remain in PENDING_OPS —
spend caps are 🔴 urgent before any live traffic.

### 2026-06-27 — Reconciled ROADMAP track ticks to real verified state (dashboard 0%)
AutoFactoryDashboard showed JobScraper at 0%. Diagnosis: the dashboard's headline % =
percentToSubmission = the Definition-of-Done checkboxes (submission readiness). DoD is
0/9 ticked — ACCURATE: the product is built + deployed + live-E2E-verified, but NOT
submission-ready (no monetization, no store assets, business case below $100K floor,
no independent A/A+ quality grade). Separately, build progress also read 0 because the
bootstrap left ALL Track boxes unticked — that understated reality. Fixed: ticked 19
Track boxes that are genuinely done WITH on-branch artifacts + this-session live
verification (backend e2e, Next.js web live, Neon, Gemini scoring+prep, gates green).
Left partial items (web SEO/polish, mobile device screens, auth lockout, CORS-locked,
migrations, evals, coverage, visual screenshots) and ALL DoD boxes unticked. Headline
stays 0% until the two-gate readiness passes — correct.

### 2026-06-28 — Outreach drafts surface on the dashboard via OWNER_ACTIONS
Added a "Surfacing on the factory dashboard" note to docs/growth/OUTREACH.md: when outreach
drafts await the owner, file/refresh ONE PENDING_OPS OWNER_ACTIONS item (id:
review-outreach-drafts, "Review + send N strategic outreach drafts (Gmail)"), decrement N
as the owner sends and close it at zero — honest counts, never stale. The dashboard already
renders OWNER_ACTIONS, so this makes the review surface there; keep GROWTH_STATUS.outreach
current for the tile. Doc-only; CI green.

### 2026-06-28 — Visual verification made DUAL-AXIS (functional AND design)
Replaced FACTORY_STANDARD §6 "SEE WHAT THE USER SEES" paragraph VERBATIM with the dual-axis
version: the journey suite screenshots every page AND every key journey STEP + key states at
mobile+desktop widths; the deep-audit lens + readiness gate JUDGE each image on a
vision-capable model on TWO axes — (1) FUNCTIONAL REALITY (does the screen visibly show the
intended outcome / the REAL produced artifact, not a placeholder/empty/wrong/broken/dead-end
the DOM missed) and (2) DESIGN (on-brand, not slop). A FAIL on EITHER axis is release-
blocking. Sharpened the ROADMAP Track E item to BOTH: (1) ARTIFACTS = non-zero committed
screenshots for every route/state + journey step (web Playwright -> web/e2e/__screenshots__,
mobile -> mobile/__screenshots__) incl. the core-product OUTPUT (the populated fit score +
the rendered prep pack); (2) DUAL-AXIS VISION VERDICT recorded per screenshot (capture-and-
forget doesn't count). Added a preflight honest-tick guard: if the box is [x] but <5
committed non-zero screenshots -> FAIL; no-op while [ ] (proved it fires on a fake-tick).
Build ORDER: this comes AFTER the functional journey suite; spec+gate hardened now, code
when the item is reached. CI green.

### 2026-06-28 — Strategic outreach (curated, DRAFT-ONLY) for the Growth Agent
PART 1 (repo, PR pending): created docs/growth/OUTREACH.md (RAILS verbatim — DRAFT ONLY /
agent never sends; high-confidence + strategic only; a few/run max; real published contacts
only, never invent/scrape; honest + opt-out CAN-SPAM/GDPR; pre-launch links -> waitlist;
maker!=checker review); target types adapted to Career Operator (careers/HR-tech/AI press,
ATS/bootcamp/career-center partners, career creators + newsletter curators). Added a
"Strategic outreach" pointer to ANALYSIS_PLAYBOOK and an outreach block to GROWTH_STATUS
(drafted_7d, owner_sent_7d, replies_7d, signal; 0/none pre-launch) + preflight check_blocks
validates it. PART 2 (routine): added OUTREACH.md to the Growth Agent ORIENT reads + a (3b)
STRATEGIC OUTREACH draft-only step + reconciled HARD BOUNDARIES (one drafting exception:
creates Gmail DRAFTS for the owner to send; still never auto-sends). model/cron/sources/
tools/MCP preserved. The Gmail tool stays create_draft only — no send capability.

### 2026-06-28 — PMF as the leading indicator + FACTORY_STANDARD first-class read
PART 1 (repo): added the PMF bullet VERBATIM to FACTORY_STANDARD §9 (canonical; revenue
follows PMF; pre-PMF prioritize the product/retention not acquisition; metrics win over the
model). Product-specific: ANALYSIS_PLAYBOOK "Product-market fit — the leading indicator"
section (Career Operator activation = add a job + get a fit score in session 1; retention =
returns to work the pipeline; organic = shared prep packs; signal ladder governs the rec,
pre-PMF = product fixes). ROADMAP growth note: "PMF FIRST" bullet. GROWTH_STATUS: pmf block
(activation_rate, retention_d1/d7/d30, organic_share_rate, signal none|weak|emerging|strong;
0/null pre-launch) + preflight check_blocks validates it. PART 2: FACTORY_STANDARD.md added
as the FIRST orient-read in the product-factory + growth routines (digest untouched).
DEEP_DIAGNOSIS in practice: gate went red on tests/test_billing.py -> diagnosed CONFIG not
code (stripe not installed locally; factory shipped real Stripe Track C in PRs #40-44, moved
stripe to runtime requirements.txt). Installed stripe -> green.

### 2026-06-28 — DECISION COROLLARY: never gate on an unbuilt loop
A sibling outage: signup required email verification + showed "check your email" but no
email pipeline was wired -> every new user dead-ended. The bug under the bug was a DECISION
(a hard gate on a loop never built). Added the DECISION COROLLARY to FACTORY_STANDARD §6
(canonical, verbatim). Audited JobScraper auth (2026-06-28): NO gate-on-unbuilt-loop —
signup returns a JWT and lands the user in the working app (web /app, mobile /(tabs)); no
"check your email" screen; no password-reset flow (absent, not a dead-end); verify-purchase
already refuses honestly (501). Nothing to un-gate. Codified the invariant with
test_signup_reaches_working_app_no_verification_deadend (fresh signup -> usable token ->
/me + create job work, no pending-verification state). Recorded the decision in PENDING_OPS
(email-verification-deferred: re-enable ONLY with the round-trip test, F4.1). Generalizes:
any gate-on-unbuilt-loop (notify-me w/o sender, share w/o backend, paywall stub) is barred.

### 2026-06-28 — Deep-diagnosis discipline + the two hard rules applied
Added docs/autonomous-loop/DEEP_DIAGNOSIS.md (observe the real env first via Vercel logs +
Neon psql/SQLAlchemy or reproduce the journey; separate code/data/config with evidence;
one hypothesis proven against the live system; find the UNCAUGHT throw; verify the fix in
the real system not the build; root-cause + regression test + fail loud; peel the layers;
stay honest). Adapted to Neon (no Supabase MCP). Applied both hard rules to real latent
traps found in JobScraper:
- (a) LLM timeout: the Gemini client had NO timeout (openai default ~600s) vs Vercel
  maxDuration 60s — a hung call would be killed before the graceful except ran. Added
  timeout=LLM_TIMEOUT_SECONDS (default 45s) + max_retries=1 in src/llm.py.
- (b) JWT_SECRET silently defaulted to "dev-secret-change-in-production" → forgeable tokens
  in prod. asgi.py now RAISES on Vercel if JWT_SECRET is unset/dev-default (fail loud).
  OWNER must set a strong JWT_SECRET in Vercel before the next deploy or /api fails loud.
Regression tests in tests/test_hardening.py (timeout+retries set; fail-loud raises in prod,
no-op locally). 11 tests green. Each future "builds but errors" incident -> follow
DEEP_DIAGNOSIS.md + record here.

### 2026-06-28 — SIDE-EFFECT INTEGRITY: a "success" the user can't verify is a LIE
A sibling product shipped "confirmation email sent" while no email was delivered (provider
in dry-run) — BUILDS≠WORKS missed it because the guard asserts SCREEN outcomes, not
side-effects. Closed the blind spot:
- FACTORY_STANDARD §6: appended the verbatim SIDE-EFFECT INTEGRITY paragraph (canonical
  sync) — no fake success; verify the EFFECT end-to-end in sandbox; narrow escape hatch.
- ROADMAP: two-rule bullet in the Builds≠works standard + Track F item **F4.1 Side-effect
  round-trip** (enforced).
- **P0 fix this run:** `verify-purchase` was fake-granting premium on an UNVERIFIED receipt
  (returned success without checking) — a billing-path lie. Now it refuses honestly (501,
  grants nothing) until real receipt verification (Track C) exists. Guarded by
  `test_no_fake_success_on_unverified_purchase` (gate-enforced). Audited all other
  `success:True` paths (register/login/jobs/coach/prep) — those are genuinely downstream of
  the real op (DB write / real Gemini reply), not optimistic.
- Generalization: JobScraper has no email flow yet, so the email Mailpit round-trip is part
  of F4.1 for WHEN email/2FA/reset is added; same for the Stripe/RevenueCat sandbox charge
  assertion when Track C lands. No routine change (factory reads FACTORY_STANDARD + ROADMAP).

### 2026-06-27 — Canonical sync: FACTORY_STANDARD §6b design-taste standard
Sanctioned canonical sync (the only way the stable anchor changes). Inserted §6b "Design
taste — ELIMINATE generic-AI frontend" VERBATIM between §6 and §7, byte-identical across
all factories (THE DESIGNER QUESTION kill-switch on every UI change; AVOID-BY-DEFAULT slop
list; GENERATE-BETTER targets; audit lenses; "simplicity without blandness…"; ENFORCED via
Reviewer B + §10 deep-audit design lens + §7 readiness visual review; optional Taste Skill
but the in-repo standard + gates are the guarantee). Product brand/voice/tokens stay in
VISION.md. JobScraper HAS user-facing surfaces (Next.js web + Expo mobile) so it fully
applies (not N/A). Treat FACTORY_STANDARD.md as a stable anchor again.

### 2026-06-27 — Marketing maturity gate + pre-launch SITE GATE
Growth markets autonomously but never before the product is ready, and never exposes a
half-baked app. Added: (1) ANALYSIS_PLAYBOOK marketing maturity gate (pre_launch
WAITLIST-ONLY with a HARD BLOCK on execute-mode until a channel is connected AND
GROWTH_STATUS.site_gate_up==true; launching; post_launch) — gated on the independent
QUALITY_SCORECARD + readiness, never eagerness. (2) GROWTH_STATUS.site_gate_up: false
(preflight check_blocks now requires it as a bool). (3) web/middleware.ts SITE GATE:
SITE_GATE_PASSWORD set -> Basic-auth the web app, EXEMPT marketing/legal routes (/,
/waitlist, /coming-soon, /privacy, /terms, /legal); ROADMAP Track G item (BLOCKING note)
+ PENDING_OPS site-gate owner action (set SITE_GATE_PASSWORD=deepster pre-launch, unset at
launch; mobile via TestFlight). (4) Growth Agent ROUTINE reinforced via /schedule:
execute-mode requires engine+channel AND (pre_launch => site_gate_up==true), else stay
PREPARE / zero external traffic; routine also writes site_gate_up each run. The SITE GATE
gates the Next.js web only; the FastAPI /api is a separate Vercel service (own JWT auth);
mobile pre-launch via TestFlight. Follow-up (Track G): build the waitlist landing + legal
pages the gate exempts, and repoint the pre-launch landing CTA to the waitlist.

### 2026-06-27 — Synced FACTORY_STANDARD.md to canonical (visual verification)
Canonical sync (kept byte-identical across factories): added visual-verification to the
shared standard — §6 "SEE WHAT THE USER SEES" (journey suite captures + commits a
screenshot of every page/state; design-audit + readiness gate VISUALLY review them on a
vision model; blank/broken/unstyled/off-brand/"vibe-coded" = release-blocking FAIL even if
DOM assertions pass; bounded to deep-audit + readiness, not every micro-change), §7 Gate-2
functional-reality lens now includes visually reviewing the screenshots, §10 design/taste
lens now visually reviews the screenshots. This is a deliberate canonical sync, NOT loop
work — FACTORY_STANDARD.md remains a stable anchor. FOLLOW-UP for the factory (ROADMAP/
product work, not this file): make the journey suite actually capture + commit page
screenshots (web: Playwright/screenshot; mobile: component snapshots) so the new lenses
have artifacts to judge.

### 2026-06-27 — Adopted the shared FACTORY_STANDARD.md (stable anchor)
Created `FACTORY_STANDARD.md` at the repo root with the canonical, product-agnostic
operating standard — copied BYTE-IDENTICAL (no paraphrase/trim/reorder/adaptation) so it
stays the same across every factory repo. Added the "Operating standard (read every run)"
pointer under the ROADMAP intro and a STABLE ANCHORS / do-not-churn entry. Referenced it in
the orient-read set of docs/autonomous-loop/PROMPT.md + AGENTS.md.
RULE: FACTORY_STANDARD.md is READ-ONLY context every run — NEVER edit or paraphrase it to
fit this product (product-specifics live in ROADMAP/VISION, which win on any specific). It
changes ONLY by a deliberate canonical cross-factory sync, never as loop work.

### 2026-06-27 — Factory-process parity with the sibling products
Aligned JobScraper's FACTORY (not product) to AptDesignerAI / GroceryManager /
HighlightMagic so all four run the identical process, building different things. Ported:
the full DESIGN BAR into VISION.md (THE DESIGNER QUESTION + AVOID-BY-DEFAULT AI-slop list +
GENERATE-BETTER + RECURRING TASTE AUDIT + "a surface that reads as AI-generated is a design
BUG"), enforced by Reviewer B + the deep-audit design lens; preflight security guards
(spend-ceiling/circuit-breaker, security headers, captcha) + a stub/placeholder-marker guard
on critical paths; the loop charter `docs/autonomous-loop/PROMPT.md` (ORIENT→HILL-CLIMB→
BOOTSTRAP→PICK ONE→IMPLEMENT→VERIFY→REVIEW(maker≠checker)→MERGE→RECORD→STOP); `AGENTS.md`
(gate commands + conventions + the ratchet); `IMPROVEMENT_LOG.md`. Documented the canonical
quality-rubric dimension set in check_quality.py.
DELIBERATELY NOT done (maker ≠ checker): did NOT create docs/quality/QUALITY_RUBRIC.md or
QUALITY_SCORECARD.md — the independent Quality Auditor routine owns/bootstraps them. Our
guard already handles their absence. The sibling AptDesignerAI ships the rubric because its
grader bootstrapped it there; ours will appear when the auditor runs.

### 2026-06-27 — Gitignored-source foot-gun broke the Vercel build
The first Vercel deploy failed: `Can't resolve @/lib/api|auth|types`. Cause: the root
.gitignore's Python `lib/` pattern (unanchored) ALSO matched `web/lib/`, so those 3 web
source files were never committed. It built locally (files on disk) but Vercel clones a
repo missing them — a local-green-but-repo-broken trap, same family as BUILDS ≠ WORKS.
Fix: anchored the Python packaging ignores to repo root (`/lib/`, `/lib64/`, `/build/`,
`/dist/`), committed `web/lib/*`, and verified with a CLEAN-ROOM build from `git archive
HEAD` (committed files only) — the real replica of a Vercel clone. Added a preflight
guard asserting critical source dirs (web/lib, web/app, web/components, mobile/src, src)
have tracked files. LESSON: a local gate can pass while the repo is missing gitignored
source; validate from a clean checkout, and never use unanchored generic ignore patterns
(`lib/`, `build/`, `dist/`) in a polyglot repo.

### 2026-06-27 — Consume the independent Quality grade (maker ≠ checker)
A separate Quality Auditor routine grades the product A+→F and OWNS
docs/quality/{QUALITY_RUBRIC,QUALITY_SCORECARD}.md — the factory must NOT author or
overwrite them (it would be self-grading). We only CONSUME: read the scorecard as DATA,
and when a ship-critical dimension is below A, turn its `top_gaps` into named
value-bar-clearing work and drive to A/A+. Wiring added:
- `scripts/check_quality.py`: `parse` (CI — OK if absent, FAIL if present+malformed;
  grades ∈ {A+,A,B,C,D,F,null}) and `readiness` (full gate — require present, ship-critical
  A/A+, others ≥ B). Tested absent/valid/failing/malformed; the throwaway scorecard used
  for testing was deleted, NOT committed (the grader owns that file).
- preflight: parse guard in CI; grade requirement in the full readiness gate.
- ROADMAP: QUALITY RUBRIC (A+→F) note, a DoD box (A/A+ ship-critical, ≥ B else,
  mechanically backed), and the deep audit must reconcile against the scorecard (lower
  view wins). Bounded drive-to-A+ (named fixes only; converge when no value-bar lever left).
Rule: never self-grade; never tick the quality DoD box unless the independent scorecard +
`check_quality.py readiness` back it.

### 2026-06-27 — Distribution/release config must be REAL (checkbox blind spot)
A checkbox-driven loop won't fix a build/deploy-readiness gap hidden under a parent box
that already reads done (ticked-box-not-backed-by-artifact / BUILDS ≠ WORKS). Defenses
added: explicit UNCHECKED ROADMAP items for (a) mobile release config and (b) web deploy
config, each requiring an ARTIFACT, not self-assessment. Built the buildable parts:
`mobile/eas.json` (build+submit profiles), `mobile/app.config.ts` (env overlay:
EAS_PROJECT_ID, EXPO_PUBLIC_API_URL), app.json bundle id + buildNumber/versionCode +
runtimeVersion. Validated WITHOUT a signed build: `expo config` resolves the merged
config, `eas.json` parses, env overlay overrides confirmed; web `next build` produces
`.next`. Signed cloud build + store submit stay Human-Core (PENDING_OPS: eas-build-submit).
Rule: never tick a "build/deploy-ready" box unless an artifact backs it; un-tick otherwise.

### 2026-06-27 — ONE Vercel deployment via Vercel Services (web + API together)
Owner wants a single Vercel project (like the other products), not two. Implemented with
**Vercel Services** (`experimentalServices` in vercel.json): `web` (Next.js) at routePrefix
`/` + `api` (FastAPI, entrypoint asgi.py) at routePrefix `/api`, one domain, shared env.
Vercel does NOT strip the route prefix, so FastAPI's existing `/api/*` routes match as-is.
Web app calls `/api/*` same-origin (api base URL = ''), so no CORS needed. Removed the
old `api/index.py` single-function shim (Services loads `asgi.py:app` directly) and added
`/api/health`. Caveat: Services is experimental/permission-gated — if unavailable, fall
back to two projects. The owner must set the project's Framework Preset to "Services".
Mobile (Expo) is NOT in this project — it points at the deployment's `/api`.
LESSON (process): always `git checkout -b <branch>` BEFORE editing — a prior run committed
to main then `git reset --hard origin/main` and lost the work. Branch first, then edit.

### 2026-06-27 — Frontend split: Next.js web (/web) + Expo mobile (/mobile)
Owner chose a Next.js web app over the React-Native-Web export. Architecture now:
- `/web` = Next.js (App Router, TS, Tailwind) → Vercel project #2 (Root Directory = web),
  the real website + web app. Reads NEXT_PUBLIC_API_URL (defaults to live API).
- `/mobile` = Expo → App Store / Play only (NOT Vercel). Removed mobile/vercel.json.
- API stays as Vercel project #1. Three surfaces, one FastAPI backend.
- preflight `ci` now gates web too (tsc + lint). CORS opened (Bearer-token API: any
  origin, no credentials, unless ALLOWED_ORIGINS is set) so the web app calls the API
  cross-origin. Two frontends = the cost; each best-in-class per platform = the benefit.

### 2026-06-27 — Provider/DB choices: Gemini (LLM) + Neon (Postgres) + Vercel
- LLM = Google Gemini via the OpenAI-compatible endpoint (key GEMINI_API_KEY). No OpenAI.
- DB = Neon Postgres (pooled endpoint). Supabase was dropped (per-instance charges).

### 2026-06-27 — Deploy target = Vercel (serverless), NOT Railway
Owner chose Vercel-for-everything (serverless Python API). Consequences baked into the
repo (see docs/DEPLOY_VERCEL.md):
- `api.py` → renamed `asgi.py` (FastAPI `app`), Vercel entry at `api/index.py`,
  `vercel.json` rewrites all routes there. The `/api` dir is the Vercel functions dir,
  hence the rename to avoid a package/module clash.
- `requirements.txt` slimmed to LEAN runtime deps (Vercel ~250MB function limit);
  full set moved to `requirements-dev.txt` (CI installs that). Removed unused heavy
  deps (sentence-transformers/torch, celery, redis, pandas, etc.) — they had ZERO
  imports and would blow the size limit.
- Serverless realities: external **Postgres required** (no SQLite persistence);
  `src/db` uses NullPool on serverless+Postgres; in-memory rate-limit/spend-ceiling are
  per-instance (Track F: move to shared store); watch the 60s function timeout for LLM
  calls. Railway/Docker configs kept as a fallback in `docs/legacy/`.
