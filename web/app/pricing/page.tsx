import { LinkButton } from '@/components/ui';

const FEATURES = [
  'Unlimited tracked jobs',
  'AI interview prep packs',
  'AI Career Coach',
  'Salary negotiation scripts',
  'Priority fit scoring',
];

export default function PricingPage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-center text-4xl font-extrabold">Career Operator Premium</h1>
      <p className="mt-3 text-center text-slate-400">Everything you need to land the offer, faster.</p>

      <div className="mt-10 grid gap-6 sm:grid-cols-2">
        <div className="rounded-2xl border border-indigo-500 bg-slate-900/60 p-6">
          <h2 className="text-slate-400">Annual</h2>
          <p className="mt-1 text-4xl font-extrabold">$96<span className="text-base text-slate-500">/yr</span></p>
          <p className="text-sm text-emerald-400">Save ~33% · best value</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="text-slate-400">Monthly</h2>
          <p className="mt-1 text-4xl font-extrabold">$12<span className="text-base text-slate-500">/mo</span></p>
          <p className="text-sm text-slate-500">Cancel anytime</p>
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

      <div className="mt-8 flex justify-center gap-3">
        <LinkButton href="/register">Start free</LinkButton>
        <LinkButton href="/app" variant="secondary">Back to app</LinkButton>
      </div>
      <p className="mt-4 text-center text-xs text-slate-500">
        Checkout (Stripe) is coming soon. Subscriptions renew automatically until cancelled.
      </p>
    </main>
  );
}
