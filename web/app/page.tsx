import type { Metadata } from 'next';
import Link from 'next/link';
import { LinkButton } from '@/components/ui';

export const metadata: Metadata = {
  title: 'Career Operator — AI fit scoring, interview prep & pipeline CRM',
  description:
    'Run your job search like an operator: AI fit-scoring against your resume, role-specific interview prep, an AI career coach, and a pipeline CRM. Start free.',
  alternates: { canonical: '/' },
};

const FEATURES = [
  ['Fit scoring', 'Every role scored against your resume so you triage in seconds, not hours.'],
  ['AI interview prep', 'Role-specific prep packs: company research, likely questions, your fit story.'],
  ['AI career coach', 'On-demand advice on strategy, interviews, and salary negotiation.'],
  ['Pipeline CRM', 'Track every application from saved → applied → offer in one place.'],
];

export default function Landing() {
  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-16">
      <header className="flex items-center justify-between">
        <span className="text-lg font-bold">Career Operator</span>
        <nav className="flex gap-3">
          <LinkButton href="/login" variant="secondary">Log in</LinkButton>
          <LinkButton href="/register">Get started</LinkButton>
        </nav>
      </header>

      <section className="py-20 text-center">
        <h1 className="mx-auto max-w-3xl text-5xl font-extrabold leading-tight">
          Run your job search like an operator.
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400">
          AI fit-scoring, interview prep, a career coach, and a pipeline CRM — so you spend
          your energy on the roles that actually fit.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <LinkButton href="/register">Start free</LinkButton>
          <LinkButton href="/pricing" variant="secondary">See pricing</LinkButton>
        </div>
        <p className="mt-3 text-sm text-slate-500">Free: 5 tracked jobs + 1 prep pack/month.</p>
      </section>

      <section className="border-t border-slate-800/80 py-16">
        <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-400">
          What you get
        </h2>
        <div className="mt-8 grid gap-x-12 gap-y-10 sm:grid-cols-2">
          {FEATURES.map(([title, body]) => (
            <div key={title}>
              <div className="h-0.5 w-8 rounded-full bg-indigo-500" aria-hidden="true" />
              <h3 className="mt-4 text-lg font-semibold">{title}</h3>
              <p className="mt-2 leading-relaxed text-slate-400">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="mt-20 flex flex-col items-center gap-2 border-t border-slate-800 pt-8 text-sm text-slate-500 sm:flex-row sm:justify-between">
        <span>© 2026 Career Operator</span>
        <nav className="flex gap-4">
          <Link href="/privacy" className="hover:text-slate-300">Privacy</Link>
          <Link href="/terms" className="hover:text-slate-300">Terms</Link>
        </nav>
      </footer>
    </main>
  );
}
