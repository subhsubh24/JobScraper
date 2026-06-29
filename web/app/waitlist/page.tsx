'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Button, ErrorText } from '@/components/ui';
import { api, ApiError } from '@/lib/api';

const VALUE_PROPS = [
  ['Fit scoring', 'Every role scored against your resume — triage in seconds, not hours.'],
  ['Interview prep', 'Role-specific packs: company research, likely questions, your fit story.'],
  ['Pipeline CRM', 'Track every application from saved → applied → offer in one place.'],
];

export default function WaitlistPage() {
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
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-6 py-10">
      <header className="flex items-center justify-between">
        <span className="text-lg font-bold">Career Operator</span>
        <Link href="/login" className="text-sm font-semibold text-slate-300 hover:text-white">
          Log in
        </Link>
      </header>

      <div className="grid flex-1 items-center gap-16 py-16 md:grid-cols-[1.1fr_0.9fr]">
        <section>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-400">
            Early access
          </p>
          <h1 className="mt-4 text-5xl font-extrabold leading-[1.05] tracking-tight">
            Run your job search like an operator.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-400">
            AI fit-scoring against your resume, role-specific interview prep, and a pipeline CRM —
            so your energy goes to the roles that actually fit. Join the waitlist for early access.
          </p>

          <dl className="mt-10 space-y-5">
            {VALUE_PROPS.map(([title, body]) => (
              <div key={title} className="flex gap-3">
                <span aria-hidden className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-400" />
                <div>
                  <dt className="font-semibold text-slate-100">{title}</dt>
                  <dd className="text-slate-400">{body}</dd>
                </div>
              </div>
            ))}
          </dl>
        </section>

        <section
          aria-live="polite"
          className="rounded-2xl border border-slate-800 bg-slate-900/60 p-7 md:p-8"
        >
          {joined ? (
            <div>
              <h2 className="text-2xl font-bold">You&rsquo;re on the list.</h2>
              <p className="mt-3 leading-relaxed text-slate-400">
                Thanks for joining. We&rsquo;ll reach out when early access opens — no spam, just
                your invite.
              </p>
              <Link
                href="/pricing"
                className="mt-6 inline-block text-sm font-semibold text-indigo-400 hover:text-indigo-300"
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
                <span className="mb-1 block text-sm text-slate-400">Work email</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
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
        </section>
      </div>

      <footer className="flex flex-col items-center gap-2 border-t border-slate-800 pt-8 text-sm text-slate-500 sm:flex-row sm:justify-between">
        <span>© 2026 Career Operator</span>
        <nav className="flex gap-4">
          <Link href="/privacy" className="hover:text-slate-300">Privacy</Link>
          <Link href="/terms" className="hover:text-slate-300">Terms</Link>
        </nav>
      </footer>
    </main>
  );
}
