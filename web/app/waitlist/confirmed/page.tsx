import type { Metadata } from 'next';
import Link from 'next/link';
import { LinkButton } from '@/components/ui';

export const metadata: Metadata = {
  title: 'Waitlist confirmed — Career Operator',
  description: 'Your Career Operator waitlist spot is confirmed.',
  robots: { index: false, follow: false },
};

// Server component: the double-opt-in confirm endpoint (GET /api/waitlist/confirm) verifies the
// signed token, stamps confirmed_at, then redirects here with ?status=ok|invalid.
export default async function WaitlistConfirmedPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { status } = await searchParams;
  const confirmed = status === 'ok';

  return (
    <main
      aria-live="polite"
      className="mx-auto flex w-full max-w-lg flex-col items-center px-6 py-24 text-center"
    >
      {confirmed ? (
        <>
          <span
            aria-hidden
            className="mb-6 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-500/15 text-indigo-400"
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6 9 17l-5-5" />
            </svg>
          </span>
          <h1 className="text-3xl font-extrabold tracking-tight">You&apos;re confirmed</h1>
          <p className="mt-3 text-slate-400">
            Thanks for confirming your spot on the Career Operator waitlist. We&apos;ll email you
            the moment early access opens.
          </p>
        </>
      ) : (
        <>
          <h1 className="text-3xl font-extrabold tracking-tight">This link didn&apos;t work</h1>
          <p className="mt-3 text-slate-400">
            The confirmation link is invalid or has expired. You can rejoin the waitlist below —
            if you&apos;re already on it, you&apos;ll stay on it.
          </p>
        </>
      )}
      <div className="mt-8">
        <LinkButton href="/waitlist">{confirmed ? 'Back to Career Operator' : 'Back to the waitlist'}</LinkButton>
      </div>
      <p className="mt-8 text-xs text-slate-500">
        Questions?{' '}
        <Link href="/privacy" className="underline">
          Privacy
        </Link>
      </p>
    </main>
  );
}
