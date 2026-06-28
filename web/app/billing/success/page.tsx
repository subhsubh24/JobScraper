'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { LinkButton } from '@/components/ui';
import { api } from '@/lib/api';

type Status = 'checking' | 'active' | 'pending';

export default function BillingSuccessPage() {
  const [status, setStatus] = useState<Status>('checking');

  useEffect(() => {
    let cancelled = false;
    // Entitlement is granted by Stripe's signed webhook, which can land a moment after the
    // redirect. Poll /me a few times before telling the user it's "activating" — never
    // claim Premium is live until the server actually reports it.
    async function check(attempt: number) {
      try {
        const user = await api.me();
        if (cancelled) return;
        if (user.tier === 'premium') {
          setStatus('active');
          return;
        }
      } catch {
        // ignore — fall through to retry / pending
      }
      if (cancelled) return;
      if (attempt < 4) {
        setTimeout(() => check(attempt + 1), 1500);
      } else {
        setStatus('pending');
      }
    }
    check(0);
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-lg flex-col items-center px-6 py-24 text-center">
      {status === 'active' ? (
        <>
          <h1 className="text-3xl font-extrabold">You’re Premium 🎉</h1>
          <p className="mt-3 text-slate-400">
            Your subscription is active. Unlimited jobs, AI prep packs, and the Career Coach are
            unlocked.
          </p>
          <div className="mt-6">
            <LinkButton href="/app">Go to your pipeline</LinkButton>
          </div>
        </>
      ) : status === 'pending' ? (
        <>
          <h1 className="text-3xl font-extrabold">Payment received</h1>
          <p className="mt-3 text-slate-400">
            Thanks! Your Premium access is activating and should appear within a minute. If it
            doesn’t, refresh this page or sign out and back in.
          </p>
          <div className="mt-6">
            <LinkButton href="/app">Back to the app</LinkButton>
          </div>
        </>
      ) : (
        <>
          <h1 className="text-3xl font-extrabold">Confirming your subscription…</h1>
          <p className="mt-3 text-slate-400">One moment while we activate your Premium access.</p>
        </>
      )}
      <p className="mt-8 text-xs text-slate-500">
        Need help?{' '}
        <Link href="/pricing" className="underline">
          Back to pricing
        </Link>
      </p>
    </main>
  );
}
