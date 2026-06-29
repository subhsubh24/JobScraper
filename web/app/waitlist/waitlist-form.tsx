'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Button, Card, ErrorText } from '@/components/ui';
import { api, ApiError } from '@/lib/api';

// The interactive capture box. Kept as a separate client component so the page shell can be
// a server component that exports metadata (SEO + OG) for this acquisition surface.
export function WaitlistForm() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [joined, setJoined] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const value = email.trim();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value)) {
      setError('Enter a valid email address.');
      return;
    }
    setLoading(true);
    try {
      await api.joinWaitlist(value, 'waitlist_page');
      setJoined(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-live="polite">
      <Card className="p-7 md:p-8">
        {joined ? (
          <div>
            <h2 className="text-2xl font-bold">You&rsquo;re on the list.</h2>
            <p className="mt-3 leading-relaxed text-slate-400">
              Thanks for joining. We&rsquo;ll reach out when early access opens — no spam, just
              your invite.
            </p>
            <Link
              href="/pricing"
              className="mt-6 inline-block rounded text-sm font-semibold text-indigo-400 hover:text-indigo-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            >
              See what&rsquo;s coming →
            </Link>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <h2 className="text-xl font-bold">Get early access</h2>
              <p className="mt-1 text-sm text-slate-400">
                Drop your email and we&rsquo;ll invite you as we open up spots.
              </p>
            </div>
            <label className="block">
              <span className="mb-1 block text-sm text-slate-400">Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-slate-100 outline-none focus:border-indigo-500"
              />
            </label>
            <ErrorText>{error}</ErrorText>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Joining…' : 'Join the waitlist'}
            </Button>
            <p className="text-xs text-slate-500">
              We&rsquo;ll only email you about early access. Unsubscribe anytime.
            </p>
          </form>
        )}
      </Card>
    </section>
  );
}
