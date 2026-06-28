'use client';

import { LinkButton } from '@/components/ui';

export default function BillingCancelPage() {
  return (
    <main className="mx-auto flex w-full max-w-lg flex-col items-center px-6 py-24 text-center">
      <h1 className="text-3xl font-extrabold">Checkout cancelled</h1>
      <p className="mt-3 text-slate-400">
        No charge was made. You can upgrade any time — your tracked jobs are right where you left
        them.
      </p>
      <div className="mt-6 flex gap-3">
        <LinkButton href="/pricing">See plans</LinkButton>
        <LinkButton href="/app" variant="secondary">
          Back to the app
        </LinkButton>
      </div>
    </main>
  );
}
