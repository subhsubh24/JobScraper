'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Button } from '@/components/ui';
import { api, ApiError, getToken } from '@/lib/api';

const FEATURES = [
  'Unlimited tracked jobs',
  'AI interview prep packs',
  'AI Career Coach',
  'Salary negotiation scripts',
  'Priority fit scoring',
];

type PlanId = 'pro_annual' | 'pro_monthly';

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
        setNotice('You’re already on Premium.');
      } else {
        setNotice(e instanceof ApiError ? e.message : 'Could not start checkout. Try again.');
      }
      setPending(null);
    }
  }

  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-center text-4xl font-extrabold">Career Operator Premium</h1>
      <p className="mt-3 text-center text-slate-400">Everything you need to land the offer, faster.</p>

      <div className="mt-10 grid gap-6 sm:grid-cols-2">
        <div className="rounded-2xl border border-indigo-500 bg-slate-900/60 p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-slate-400">Annual</h2>
            <span className="rounded-full bg-indigo-500/15 px-2 py-0.5 text-xs font-semibold text-indigo-300">
              Best value
            </span>
          </div>
          <p className="mt-1 text-4xl font-extrabold">
            $96<span className="text-base text-slate-500">/yr</span>
          </p>
          <p className="text-sm text-emerald-400">Save ~33% · 2 months free</p>
          <Button
            className="mt-4 w-full"
            onClick={() => upgrade('pro_annual')}
            disabled={pending !== null}
          >
            {pending === 'pro_annual' ? 'Starting checkout…' : 'Go Premium — annual'}
          </Button>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="text-slate-400">Monthly</h2>
          <p className="mt-1 text-4xl font-extrabold">
            $12<span className="text-base text-slate-500">/mo</span>
          </p>
          <p className="text-sm text-slate-500">Cancel anytime</p>
          <Button
            className="mt-4 w-full"
            variant="secondary"
            onClick={() => upgrade('pro_monthly')}
            disabled={pending !== null}
          >
            {pending === 'pro_monthly' ? 'Starting checkout…' : 'Go Premium — monthly'}
          </Button>
        </div>
      </div>

      <ul className="mt-8 space-y-2">
        {FEATURES.map((f) => (
          <li key={f} className="flex items-center gap-2">
            <span className="text-emerald-400">✓</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>

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
