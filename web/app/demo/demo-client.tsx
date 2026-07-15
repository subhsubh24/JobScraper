'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button, Card, ErrorText } from '@/components/ui';
import { scoreColor } from '@/lib/types';

// The public demo talks to the KEY-FREE, no-account endpoint (FACTORY_STANDARD §34). It is a
// deliberately self-contained fetch — the demo is a public, unauthenticated funnel page, so it
// does not pull in the authed api client (no token, no shared session coupling). Mirrors the
// api client's timeout + honest-error posture so a slow/failed call never traps the visitor.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';
const REQUEST_TIMEOUT_MS = 15000;
const MAX_JD = 25000;
const MAX_RESUME = 30000;

interface MatchResult {
  matching_skills: string[];
  missing_skills: string[];
  role_skill_count: number;
  matching_count: number;
  missing_count: number;
  coverage: number; // 0..1
  has_resume: boolean;
}

async function fetchMatch(jobDescription: string, resumeText: string): Promise<MatchResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/demo/skill-match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_description: jobDescription,
        resume_text: resumeText || undefined,
      }),
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new Error('That took too long — please try again.');
    }
    throw new Error('Network error — check your connection and try again.');
  } finally {
    clearTimeout(timer);
  }
  let data: Record<string, unknown> = {};
  let parsedOk = true;
  try {
    data = (await res.json()) as Record<string, unknown>;
  } catch {
    parsedOk = false;
  }
  if (!res.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : 'Something went wrong. Please try again.';
    throw new Error(detail);
  }
  if (!parsedOk) {
    // A 2xx whose body isn't valid JSON (e.g. an edge/proxy HTML error page) must surface as an
    // HONEST error — never a silent {} that Results would render as fake success ("your résumé
    // already covers every skill this role names"). See loop-memory 2026-07-15.
    throw new Error('That result could not be read — please try again.');
  }
  return data as unknown as MatchResult;
}

function SkillChips({ skills, tone }: { skills: string[]; tone: 'have' | 'gap' }) {
  const styles =
    tone === 'have'
      ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
      : 'border-indigo-500/30 bg-indigo-500/10 text-indigo-200';
  return (
    <div className="flex flex-wrap gap-2">
      {skills.map((s) => (
        <span
          key={s}
          className={`inline-flex items-center rounded-full border px-3 py-1 text-sm capitalize ${styles}`}
        >
          {s}
        </span>
      ))}
    </div>
  );
}

function Results({ result }: { result: MatchResult }) {
  const pct = Math.round(result.coverage * 100);
  return (
    <div className="space-y-5">
      {result.role_skill_count === 0 ? (
        <Card>
          <p className="text-slate-300">
            We couldn&apos;t spot any recognized skills in that job description. Paste the full
            requirements section for a sharper read.
          </p>
        </Card>
      ) : (
        <>
          {result.has_resume && (
            <Card className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-wide text-slate-400">Skill coverage</p>
                <p className="mt-1 text-sm text-slate-400">
                  Your résumé shows {result.matching_count} of {result.role_skill_count} skills this
                  role names.
                </p>
              </div>
              <div
                className={`text-4xl font-extrabold tabular-nums ${scoreColor(pct)}`}
                aria-label={`${pct} percent skill coverage`}
              >
                {pct}%
              </div>
            </Card>
          )}

          {result.matching_count > 0 && (
            <Card className="space-y-2">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                Skills you already have
              </h2>
              <SkillChips skills={result.matching_skills} tone="have" />
            </Card>
          )}

          <Card className="space-y-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
              {result.has_resume ? 'Skills to highlight or build' : 'Skills this role wants'}
            </h2>
            {!result.has_resume && (
              <p className="text-sm text-slate-400">
                Paste your résumé above to see which of these you already cover.
              </p>
            )}
            {result.missing_count > 0 ? (
              <SkillChips skills={result.missing_skills} tone="gap" />
            ) : (
              <p className="text-sm text-emerald-300">
                Nice — your résumé already covers every skill this role names.
              </p>
            )}
          </Card>
        </>
      )}
    </div>
  );
}

// Static upsell — deliberately OUTSIDE the aria-live results region so it is not re-announced
// to assistive tech on every submit (it never changes).
function UpsellCard() {
  return (
    <Card className="space-y-3 border-indigo-500/30 bg-indigo-500/[0.06]">
      <p className="font-semibold text-slate-100">This is a taste of the full operator.</p>
      <p className="text-sm text-slate-400">
        Career Operator scores every role against your résumé across your whole pipeline, finds the
        skills your saved jobs repeatedly demand, and drafts role-specific interview prep. Join the
        waitlist for early access.
      </p>
      <Link
        href="/waitlist"
        className="inline-flex items-center justify-center rounded-lg bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
      >
        Join the waitlist
      </Link>
    </Card>
  );
}

export function DemoClient() {
  const [jd, setJd] = useState('');
  const [resume, setResume] = useState('');
  const [result, setResult] = useState<MatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!jd.trim()) {
      setError('Paste a job description to see your match.');
      return;
    }
    setLoading(true);
    try {
      const r = await fetchMatch(jd.trim(), resume.trim());
      setResult(r);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-8 md:grid-cols-2">
      <Card>
        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-sm text-slate-400">Job description *</span>
            <textarea
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              maxLength={MAX_JD}
              rows={8}
              placeholder="Paste the role's description or requirements…"
              className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-slate-100 outline-none focus:border-indigo-500"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm text-slate-400">
              Your résumé <span className="text-slate-500">(optional — for your match %)</span>
            </span>
            <textarea
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              maxLength={MAX_RESUME}
              rows={8}
              placeholder="Paste your résumé to see which skills you already cover…"
              className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-slate-100 outline-none focus:border-indigo-500"
            />
          </label>
          <ErrorText>{error}</ErrorText>
          <Button type="submit" disabled={loading}>
            {loading ? 'Analyzing…' : 'See your match'}
          </Button>
          <p className="text-xs text-slate-500">
            Free, no account, and your text never leaves the analysis — it isn&apos;t stored.
          </p>
        </form>
      </Card>

      <div className="space-y-5">
        {/* Persistent live region: always mounted (even empty) so the FIRST result is reliably
            announced by assistive tech — a region that appears in the same paint as its content
            is often not announced. Only the dynamic match summary lives here; the static upsell
            is rendered outside it. */}
        <div aria-live="polite">
          {result ? (
            <Results result={result} />
          ) : (
            <Card className="flex min-h-[16rem] items-center justify-center text-center">
              <p className="max-w-xs text-sm text-slate-400">
                Your instant skill match appears here — matching skills, gaps, and a coverage %
                against the role.
              </p>
            </Card>
          )}
        </div>
        {result && <UpsellCard />}
      </div>
    </div>
  );
}
