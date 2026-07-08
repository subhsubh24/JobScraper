import type { Metadata } from 'next';
import Link from 'next/link';
import { DemoClient } from './demo-client';

export const metadata: Metadata = {
  title: 'Try it free — skill match | Career Operator',
  description:
    'Paste a job description and your résumé to instantly see which skills you already have and which you are missing. No account, free, from Career Operator.',
  alternates: { canonical: '/demo' },
};

export default function DemoPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-6 py-10">
      <header className="flex items-center justify-between">
        <Link href="/" className="text-lg font-bold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">
          Career Operator
        </Link>
        <nav className="flex items-center gap-4 text-sm font-semibold">
          <Link href="/waitlist" className="rounded text-slate-300 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">
            Join waitlist
          </Link>
          <Link href="/login" className="rounded text-slate-300 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">
            Log in
          </Link>
        </nav>
      </header>

      <div className="py-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-400">
          Try it free — no account
        </p>
        <h1 className="mt-4 max-w-2xl text-4xl font-extrabold leading-[1.1] tracking-tight sm:text-5xl">
          See how you match a role — instantly.
        </h1>
        <p className="mt-4 max-w-xl text-lg leading-relaxed text-slate-400">
          Paste a job description and your résumé. Career Operator shows the skills you already have,
          the ones the role wants that you&apos;re missing, and your coverage — the same read that
          powers the full product.
        </p>
      </div>

      <section className="pb-16">
        <DemoClient />
      </section>

      <footer className="mt-auto flex flex-col items-center gap-2 border-t border-slate-800 pt-8 text-sm text-slate-500 sm:flex-row sm:justify-between">
        <span>© 2026 Career Operator</span>
        <nav className="flex gap-4">
          <Link href="/waitlist" className="rounded hover:text-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Waitlist</Link>
          <Link href="/privacy" className="rounded hover:text-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Privacy</Link>
          <Link href="/terms" className="rounded hover:text-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Terms</Link>
        </nav>
      </footer>
    </main>
  );
}
