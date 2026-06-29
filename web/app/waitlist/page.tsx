import type { Metadata } from 'next';
import Link from 'next/link';
import { WaitlistForm } from './waitlist-form';

export const metadata: Metadata = {
  title: 'Join the waitlist — Career Operator',
  description:
    'Get early access to Career Operator: AI fit-scoring against your resume, role-specific interview prep, and a pipeline CRM. Join the waitlist.',
  alternates: { canonical: '/waitlist' },
};

const VALUE_PROPS = [
  ['Fit scoring', 'Every role scored against your resume — triage in seconds, not hours.'],
  ['Interview prep', 'Role-specific packs: company research, likely questions, your fit story.'],
  ['Pipeline CRM', 'Track every application from saved → applied → offer in one place.'],
];

export default function WaitlistPage() {
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

        <WaitlistForm />
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
