import { LinkButton } from '@/components/ui';

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

      <section className="grid gap-4 sm:grid-cols-2">
        {FEATURES.map(([title, body]) => (
          <div key={title} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h3 className="text-lg font-semibold">{title}</h3>
            <p className="mt-2 text-slate-400">{body}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
