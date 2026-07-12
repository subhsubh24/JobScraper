'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Button } from '@/components/ui';
import { api, ApiError, getToken } from '@/lib/api';

const PRO_FEATURES = [
  'Unlimited tracked jobs',
  'AI interview prep packs',
  'AI tailored résumés, cover letters & study plans',
  'AI Career Coach',
];

// Career+ is a strict SUPERSET of Pro. Salary-negotiation coaching is the real, additive
// exclusive (it had no endpoint at any tier before — no existing plan loses it).
const CAREERPLUS_FEATURES = [
  'Everything in Pro',
  'AI salary-negotiation coaching',
];

// An inline check glyph — a real icon, not an emoji (which renders inconsistently across
// platforms and reads as generated). Decorative, so hidden from assistive tech.
function CheckIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 20 20"
      className="h-5 w-5 shrink-0 text-emerald-400"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.25"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4 10.5l4 4 8-9" />
    </svg>
  );
}

type PlanId = 'pro_annual' | 'pro_monthly' | 'careerplus_annual' | 'careerplus_monthly';

export default function PricingPage() {
  const router = useRouter();
  const [pending, setPending] = useState<PlanId | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function upgrade(plan: PlanId) {
    setNotice(null);
    if (!getToken()) {
      // Checkout requires an account; send them to sign up, then back to pricing.
      router.push('/register?next=/pricing');
      return;
    }
    setPending(plan);
    try {
      const url = await api.startCheckout(plan);
      // Hand off to Stripe's hosted Checkout — the real charge happens there.
      window.location.assign(url);
    } catch (e) {
      if (e instanceof ApiError && e.status === 503) {
        setNotice('Subscriptions aren’t live yet — no charge was made. Check back soon.');
      } else if (e instanceof ApiError && e.status === 400) {
        // Honest: an existing subscriber can't start a second checkout (that would
        // double-bill). In-app plan changes via the Stripe billing portal are coming soon.
        setNotice(
          'You already have an active subscription. To switch plans, contact support — in-app plan changes are coming soon.',
        );
      } else {
        setNotice(e instanceof ApiError ? e.message : 'Could not start checkout. Try again.');
      }
      setPending(null);
    }
  }

  function goToTeam() {
    setNotice(null);
    // The seat tier is self-serve inside the app (create org -> buy seats -> assign members).
    // No account yet -> sign up first, then land on the team dashboard (register honors ?next).
    router.push(getToken() ? '/app/team' : '/register?next=/app/team');
  }

  return (
    <main className="mx-auto w-full max-w-4xl px-6 py-16">
      <h1 className="text-center text-4xl font-extrabold">Pricing</h1>
      <p className="mt-3 text-center text-slate-400">
        Everything you need to land the offer, faster. Cancel anytime.
      </p>

      <div className="mt-10 grid gap-6 md:grid-cols-2">
        {/* Pro */}
        <div className="flex flex-col rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="text-base font-semibold text-slate-100">Pro</h2>
          <p className="mt-1 text-4xl font-extrabold">
            $96<span className="text-base text-slate-500">/yr</span>
          </p>
          <p className="text-sm text-emerald-400">Save ~33% · 2 months free · or $12/mo</p>
          <ul className="mt-5 space-y-2.5">
            {PRO_FEATURES.map((f) => (
              <li key={f} className="flex items-center gap-3">
                <CheckIcon />
                <span>{f}</span>
              </li>
            ))}
          </ul>
          <div className="mt-auto space-y-2 pt-6">
            <Button
              className="w-full"
              onClick={() => upgrade('pro_annual')}
              disabled={pending !== null}
            >
              {pending === 'pro_annual' ? 'Starting checkout…' : 'Get Pro — annual'}
            </Button>
            <Button
              className="w-full"
              variant="secondary"
              onClick={() => upgrade('pro_monthly')}
              disabled={pending !== null}
            >
              {pending === 'pro_monthly' ? 'Starting checkout…' : 'Get Pro — $12/mo'}
            </Button>
          </div>
        </div>

        {/* Career+ (superset of Pro) */}
        <div className="relative flex flex-col rounded-2xl border border-indigo-500 bg-slate-900/60 p-6">
          <span className="absolute right-4 top-4 rounded-full bg-indigo-500/15 px-2 py-0.5 text-xs font-semibold text-indigo-300">
            For senior seekers
          </span>
          <h2 className="text-base font-semibold text-slate-100">Career+</h2>
          <p className="mt-1 text-4xl font-extrabold">
            $192<span className="text-base text-slate-500">/yr</span>
          </p>
          <p className="text-sm text-emerald-400">Save ~33% · 2 months free · or $24/mo</p>
          <ul className="mt-5 space-y-2.5">
            {CAREERPLUS_FEATURES.map((f) => (
              <li key={f} className="flex items-center gap-3">
                <CheckIcon />
                <span>{f}</span>
              </li>
            ))}
          </ul>
          <div className="mt-auto space-y-2 pt-6">
            <Button
              className="w-full"
              onClick={() => upgrade('careerplus_annual')}
              disabled={pending !== null}
            >
              {pending === 'careerplus_annual' ? 'Starting checkout…' : 'Get Career+ — annual'}
            </Button>
            <Button
              className="w-full"
              variant="secondary"
              onClick={() => upgrade('careerplus_monthly')}
              disabled={pending !== null}
            >
              {pending === 'careerplus_monthly' ? 'Starting checkout…' : 'Get Career+ — $24/mo'}
            </Button>
          </div>
        </div>
      </div>

      {/* Team & Organizations — the B2B2C seat tier, set apart from the individual plans so
          the two audiences (job seekers vs. orgs buying for their people) read distinctly. */}
      <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 md:flex md:items-center md:justify-between md:gap-8">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-semibold text-slate-100">Team &amp; Organizations</h2>
            <span className="rounded-full bg-slate-700/40 px-2 py-0.5 text-xs font-semibold text-slate-300">
              For bootcamps, employers &amp; outplacement firms
            </span>
          </div>
          <p className="mt-2 max-w-xl text-sm text-slate-400">
            Buy a pool of seats and assign them to your members — everyone gets Pro. One
            subscription, centralized billing, and an admin dashboard to add or remove people as
            your cohort changes. Per-seat annual pricing that scales with your team.
          </p>
        </div>
        <div className="mt-4 shrink-0 md:mt-0">
          <Button className="w-full md:w-auto" onClick={goToTeam}>
            Set up your team
          </Button>
        </div>
      </section>

      {notice && (
        <p role="alert" className="mt-6 text-center text-sm text-amber-400">
          {notice}
        </p>
      )}

      <p className="mt-6 text-center text-xs text-slate-500">
        Secure checkout by Stripe. Subscriptions renew automatically until cancelled.
      </p>
    </main>
  );
}
