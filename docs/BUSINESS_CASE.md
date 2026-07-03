# BUSINESS CASE — Career Operator

> Honest, sourced, conservative. The machine-readable `BUSINESS_CASE_SUMMARY` block
> below is parsed by the shared dashboard. Real values only — a below-floor number is
> the correct pre-launch state and we state it plainly.

## Product & who pays
Career Operator is a subscription job-search platform (web + native mobile). Buyers are
active mid-to-senior job seekers who pay to save triage time (fit scoring), get
role-specific AI interview prep, an AI career coach, and a pipeline CRM.

## Pricing (the factory SETS this; growth INFORMS it)
Good-better-best + annual (annual ≈ 2 months free):

| Tier | Monthly | Annual | Who | Key gates |
|---|---|---|---|---|
| **Free** | $0 | — | Trial / casual | 5 tracked jobs, 1 prep pack/mo, no AI coach |
| **Pro** | $12 | $96 | Active seeker | Unlimited jobs, unlimited prep packs, AI cover letters + study plans, AI coach (fair-use: 25 AI actions/day, shared across AI features) |
| **Career+** | $24 | $192 | Senior / urgent | Everything in Pro + AI salary-negotiation coaching |

Blended realized revenue per paying user assumed **~$110/yr** (mix of monthly churn +
annual discount). This is the anchor for the projections.

## Year-1 ARR projection (conservative, bottom-up)
Pre-launch: **0 users, 0 revenue, no live billing.** Projections are scenarios, not
results. Assumptions: organic + content + ASO acquisition (no paid budget funded yet),
free→paid conversion 3–6% (typical freemium SaaS, conservative end), blended ~$110/yr.

| Scenario | Paying subs (end of Y1) | Blended ARPA/yr | ARR |
|---|---|---|---|
| Conservative | 150 | $110 | **$16,500** |
| Base (planning) | 500 | $115 | **$57,500** |
| Optimistic | 1,100 | $120 | **$132,000** |

**Planning case = base = $57.5K → BELOW the $100K floor. `floor_met_year1: false`.**
We say so honestly rather than inflating price, users, or conversion.

*Computation integrity (FACTORY_STANDARD §22): each scenario's ARR is produced by executed
code, not hand arithmetic — `analysis/arr_conservative.py` / `arr_base.py` / `arr_optimistic.py`
(shared inputs in `analysis/business_case_lib.py`), registered in `analysis/figures.json` and
re-verified every gate run by `scripts/validate-computation.mjs`. Update the scenario inputs
there (never hand-edit the numbers below independently) when an assumption changes.*

## Buildable levers to clear the $100K floor (each becomes ROADMAP work)
These are *named, buildable* items (the only valid weak-case loop-back triggers):

1. **Annual-first paywall + founder/launch pricing** — raise annual mix and ARPA.
2. **Team/coach/career-services B2B2C tier** — bootcamps & outplacement firms reselling
   seats (higher ARPA, lower CAC per seat).
3. **AI-prep value expansion** — the FIRST Career+ exclusive (AI salary-negotiation
   coaching) is now **BUILT** (see lever 6); mock-interview voice sessions + company-specific
   dossiers remain future Career+ wedges to raise the upgrade rate further.
4. **Mobile ASO + app-store discovery** — the new Expo app opens an acquisition channel
   the web alone doesn't have (organic store traffic).
5. **Referral loop** — "share a prep pack" invite mechanic to lower CAC. **BUILT (PR #109):**
   every user gets a referral code; a referred signup grants BOTH sides a real bonus prep
   pack (raises the actual free-tier allowance — no fake billing promise), surfaced on web +
   mobile Settings. This is a CAC/organic-pull lever; its ARR impact stays **unquantified
   until real funnel data exists** (pre-launch) — we do NOT credit it to the projection yet
   (anti-gaming).
6. **Career+ ($24) as a real, differentiated tier** — **BUILT (PRs #152 web/backend, #153
   web, #155 mobile).** Was dead config (the `careerplus_*` prices granted an identical
   PREMIUM); now a real, webhook-verified entitlement LEVEL derived from `Subscription.plan`
   (no risky enum migration — `UserTier` stays binary), with **AI salary-negotiation coaching**
   as its genuine, ADDITIVE exclusive (it had no endpoint at any tier before, so gating it to
   Career+ takes nothing from Pro — no dark pattern). Pricing page now shows two honest tiers;
   the job-detail surface gates the tool on the verified level (web + mobile). Like the referral
   loop, its incremental ARR is **real but unquantified until cohort data exists** — pre-launch
   (0 users) we do **not** inflate the projection with a Career+-mix assumption (anti-gaming),
   and on any defensible mix it is a modest diversifier, **not** a floor-flip.

**Floor still not met.** With Career+ + referral now built, the **team/B2B2C tier** remains
the primary named floor-lever (highest ARPA, lowest CAC/seat), plus annual-first/founder
pricing. Career+'s real revenue lift will be reconciled from live free→paid + tier-mix data
once it exists (metrics win over the model, §9).

When any lever is built and the honest median crosses $100K, re-run the readiness gate.
Until then, readiness is **rejected** on business-case grounds (per ROADMAP standards),
independent of code completeness.

## Costs (per-user, order of magnitude)
- LLM (scoring + prep + coach): ~$0.20–$0.60 / active user / mo (capped by a per-user/day
  spend ceiling — see Track F). Heuristic degradation keeps free-tier near-zero cost.
- Hosting (Vercel serverless + external Postgres e.g. Neon/Supabase): ~$0–$20 / mo at
  low scale (free tiers cover early usage; watch function-invocation + DB limits).
- Store + processing fees: Apple/Google 15–30%, Stripe ~2.9%+30¢.

Gross margin is healthy at subscription pricing **if** the spend ceiling is enforced
(it is a wallet-drain target — see Security track).

## Confidence
LOW for the revenue number (pre-launch, no funnel data). HIGH that the floor is **not**
met today. The honest path to the floor is the lever list above, not a spreadsheet edit.

```yaml
BUSINESS_CASE_SUMMARY:
  currency: USD
  arr_year1:
    conservative: 16500
    base: 57500
    optimistic: 132000
  planning_case: 57500
  floor_usd: 100000
  floor_met_year1: false
  time_to_floor: unknown_pre_launch
  as_of: 2026-07-01
```
