import Link from 'next/link';
import type { ReactNode } from 'react';

/** Shared chrome for legal pages: brand header, readable prose column, footer nav. */
export function LegalPage({
  title,
  updated,
  children,
}: {
  title: string;
  updated: string;
  children: ReactNode;
}) {
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-16">
      <header className="flex items-center justify-between border-b border-slate-800 pb-6">
        <Link
          href="/"
          className="rounded text-lg font-bold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
        >
          Career Operator
        </Link>
        <nav className="flex gap-4 text-sm text-slate-400">
          <Link
            href="/privacy"
            className="rounded hover:text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
          >
            Privacy
          </Link>
          <Link
            href="/terms"
            className="rounded hover:text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
          >
            Terms
          </Link>
        </nav>
      </header>

      <h1 className="mt-10 text-3xl font-extrabold">{title}</h1>
      <p className="mt-2 text-sm text-slate-500">Last updated: {updated}</p>

      <div className="mt-8 space-y-8 leading-relaxed text-slate-300">{children}</div>

      <footer className="mt-16 border-t border-slate-800 pt-6 text-sm text-slate-500">
        © {updated.split(' ').pop()} Career Operator.{' '}
        <Link href="/" className="hover:text-slate-300">
          Back to home
        </Link>
      </footer>
    </main>
  );
}

export function Section({ heading, children }: { heading: string; children: ReactNode }) {
  return (
    <section>
      <h2 className="mb-2 text-lg font-semibold text-slate-100">{heading}</h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}
