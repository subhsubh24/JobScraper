# Store Listing Copy (ASO) — Career Operator

> Text assets for the App Store + Play Console listings. Honest to what the app does today
> (no fabricated features). Voice per VISION.md: operator-grade, calm, outcome-focused — not
> hypey. Character limits noted are the current store maxima; trim at submission if they
> change. Rendered screenshots/feature graphics are a separate, NOT-yet-buildable artifact
> (need a running signed build) — tracked as FAIL in ACCEPTANCE_AUDIT.

## App name / title
- **App Store name** (≤ 30 chars): `Career Operator`
- **App Store subtitle** (≤ 30 chars): `AI job search & prep`
- **Play title** (≤ 30 chars): `Career Operator: Job Search`

## Promotional text (App Store, ≤ 170 chars, updatable without review)
> Run your job search like an operator: score fit, generate role-specific interview prep,
> and keep every application on track. Free to start.

## Keywords (App Store keyword field, ≤ 100 chars, comma-separated, no spaces)
`job search,interview prep,career coach,resume,job tracker,application tracker,job fit,offer,hiring`

## Short description (Play, ≤ 80 chars)
> Score job fit, generate prep, and track every application in one place.

## Full description (App Store ≤ 4000 chars / Play ≤ 4000 chars)

**Career Operator turns a messy job search into a system you can run.**

Job hunting is a high-stakes, time-boxed project. Career Operator gives you the operator's
toolkit to run it well — so you spend your energy on the roles that matter and walk into
every interview prepared.

**Score fit before you apply.**
Paste a role and your resume; Career Operator scores how well you match and explains why —
matching strengths and the gaps to address. Triage your list in minutes instead of guessing.

**Generate interview prep tied to the actual role.**
One tap turns a job description into a focused prep pack: the themes to expect, likely
questions, and how to frame your experience. Built for the specific role, not generic advice.

**Coach in your corner.**
Ask the AI Career Coach about strategy, tradeoffs, tough interview questions, or salary
negotiation — with the context of your search.

**Keep the whole pipeline on track.**
Track every application through saved → applied → phone screen → interview → offer. See what
needs attention so nothing slips.

**Built to respect you.**
- Clear free tier — start with no card.
- Your data is yours: export-free deletion in one tap removes everything.
- Encrypted in transit. No ads. No data sold. No tracking.

**Plans**
- **Free:** track up to 5 jobs, 1 prep pack/month, fit scoring.
- **Pro — $12/mo or $96/yr:** unlimited jobs, unlimited prep packs, and the AI Career Coach.
- **Career+ — $24/mo or $192/yr:** everything in Pro, plus the AI salary-negotiation coaching
  tool. (Annual saves ~33%.)

Start free today and run your search like an operator.

---

## Subscription disclosure (required near the paywall + in the listing)
> Career Operator offers auto-renewing subscriptions: Pro ($12/month or $96/year) and
> Career+ ($24/month or $192/year). Payment is charged to your account at confirmation. Subscriptions renew automatically
> unless cancelled at least 24 hours before the end of the period; manage or cancel in your
> account settings. **Restore purchases will be available in the app** (Settings → Restore)
> once mobile in-app subscriptions are integrated (StoreKit/Play Billing — not yet landed).
> The subscription Terms of Use and Privacy Policy are linked at the point of purchase
> (Apple 3.1.2 requires the functional Terms + Privacy links + a Restore action in the
> paywall UI, not just this text — wire them when StoreKit lands).

## Release notes — v1.0.0
> First release. Score job fit, generate role-specific interview prep, chat with the AI
> Career Coach, and track your whole pipeline in one place. We'd love your feedback.

## Category / age rating
- **Primary category:** Business (alt: Productivity)
- **Age rating:** 4+ / Everyone — no objectionable content. *Note:* the AI coach produces
  free-form text; the content-safety guardrail (audit item A1) **shipped** (PR #51 — moderates
  coach input AND output), so this is mitigated, not just planned.

## AI & generated content (disclosure)
> Both stores expect apps that produce AI-generated content to disclose it, and Apple's
> UGC guidelines (§1.2) expect a content-safety mechanism. State this in the listing and
> near the relevant features:
> *Career Operator uses generative AI (Google Gemini) to produce interview prep packs and
> career-coach replies, and to compute resume↔job fit. AI output can be imperfect — treat it
> as guidance, not professional, legal, or financial advice. Generated content is filtered by
> an in-app safety guardrail (audit item A1: self-harm input returns crisis resources;
> disallowed categories are blocked), the AI Coach is for career topics only, and you can
> report any AI response for review with the "Report this response" control on every coach
> reply and prep pack.*

This is code-accurate: Gemini powers prep packs (`src/enrichment/llm_workflows.py`), the coach
(`src/ai_coach/career_coach.py`), and fit embeddings; the `ContentModerator` guardrail runs on
coach input AND output. Honest degradation when no Gemini key is configured is **not uniform**,
so state it precisely: AI prep packs and the AI Coach return a truthful "needs configuration"
(HTTP 503, no output); **fit scoring degrades to keyword-heuristics** — the embedding-based
semantic component defaults to a neutral value (`src/ranking/scorer.py`), so a score is still
shown but it is heuristic-only, not AI-derived. The listing copy should therefore say AI fit
scoring requires the AI service and otherwise falls back to heuristic matching — never imply the
shown score is always AI-computed.

## Owner notes (Human-Core)
- Final character-limit trim happens in the console at submission (limits drift).
- Rendered screenshots + feature graphic require a signed build — not buildable in-repo yet.
- Localize beyond en-US later (ASO roadmap item).
