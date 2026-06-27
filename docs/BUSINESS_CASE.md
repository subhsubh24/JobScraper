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
| **Pro** | $12 | $96 | Active seeker | Unlimited jobs, 10 prep packs/mo, AI coach (100 msg/mo) |
| **Career+** | $24 | $192 | Senior / urgent | Everything unlimited, salary negotiation, outreach, priority |

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

## Buildable levers to clear the $100K floor (each becomes ROADMAP work)
These are *named, buildable* items (the only valid weak-case loop-back triggers):

1. **Annual-first paywall + founder/launch pricing** — raise annual mix and ARPA.
2. **Team/coach/career-services B2B2C tier** — bootcamps & outplacement firms reselling
   seats (higher ARPA, lower CAC per seat).
3. **AI-prep value expansion** — mock-interview voice sessions + company-specific
   dossiers as a Career+ wedge raising upgrade rate.
4. **Mobile ASO + app-store discovery** — the new Expo app opens an acquisition channel
   the web alone doesn't have (organic store traffic).
5. **Referral loop** — "share a prep pack" invite mechanic to lower CAC.

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
  as_of: 2026-06-27
```
