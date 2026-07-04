'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { Button, Card, Field, Skeleton } from '@/components/ui';
import { Markdown } from '@/components/markdown';
import { ReportButton } from '@/components/report-button';
import { useAiConsent } from '@/components/ai-consent';
import { api, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { STATUS_LABELS, STATUS_ORDER, scoreColor, type ApplicationStatus, type Job } from '@/lib/types';

// A small lock glyph for the Career+-gated affordance — a real icon, not an emoji. Decorative.
function LockIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 20 20"
      className="h-5 w-5 shrink-0 text-indigo-300"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="4" y="9" width="12" height="8" rx="1.5" />
      <path d="M7 9V6.5a3 3 0 0 1 6 0V9" />
    </svg>
  );
}

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();
  const { user } = useAuth();
  const isCareerPlus = user?.career_plus === true;
  // Pro (paid) tier: Pro AND Career+ are both PREMIUM. Gates the cover-letter + study-plan tools.
  const isPaid = user?.tier === 'premium';
  // Third-party-AI consent gate (Apple 5.1.2(i)) — every prep tool sends resume/JD to Gemini.
  const { ensureConsent, dialog: consentDialog } = useAiConsent();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prep, setPrep] = useState<{ title: string; content: string } | null>(null);
  const [prepLoading, setPrepLoading] = useState(false);
  const [prepMsg, setPrepMsg] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [neg, setNeg] = useState<{ title: string; content: string } | null>(null);
  const [negLoading, setNegLoading] = useState(false);
  const [negMsg, setNegMsg] = useState<string | null>(null);
  const [targetSalary, setTargetSalary] = useState('');
  const [letter, setLetter] = useState<{ title: string; content: string } | null>(null);
  const [letterLoading, setLetterLoading] = useState(false);
  const [letterMsg, setLetterMsg] = useState<string | null>(null);
  const [studyPlan, setStudyPlan] = useState<{ title: string; content: string } | null>(null);
  const [studyLoading, setStudyLoading] = useState(false);
  const [studyMsg, setStudyMsg] = useState<string | null>(null);
  const [studyDays, setStudyDays] = useState('7');
  const [resume, setResume] = useState<{ title: string; content: string } | null>(null);
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeMsg, setResumeMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setJob(await api.getJob(id));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load this job.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    // load() setStates asynchronously after the fetch resolves, not synchronously.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  async function setStatus(status: ApplicationStatus) {
    setStatusMsg(null);
    try {
      setJob(await api.updateJobStatus(id, status));
    } catch (e) {
      // Don't silently swallow: a status button that does nothing is a broken affordance.
      setStatusMsg(e instanceof ApiError ? e.message : "Couldn't update status — try again.");
    }
  }

  async function generatePrep() {
    setPrepMsg(null);
    // Get explicit AI consent before sending resume/job text to the AI provider.
    if (!(await ensureConsent())) return;
    setPrepLoading(true);
    try {
      setPrep(await api.generatePrepPack(id));
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) router.push('/pricing');
      else setPrepMsg(e instanceof ApiError ? e.message : 'Could not generate.');
    } finally {
      setPrepLoading(false);
    }
  }

  async function generateCoverLetter() {
    setLetterMsg(null);
    if (!(await ensureConsent())) return;
    setLetterLoading(true);
    try {
      setLetter(await api.generateCoverLetter(id));
    } catch (e) {
      // A free user should never reach here (the UI gates it), but the server is the source of
      // truth — a 403 routes to pricing rather than dead-ends.
      if (e instanceof ApiError && e.status === 403) router.push('/pricing');
      else setLetterMsg(e instanceof ApiError ? e.message : 'Could not generate.');
    } finally {
      setLetterLoading(false);
    }
  }

  async function generateStudyPlan() {
    // Bound days client-side to match the server (1–30) so a bad value never burns an LLM call.
    const days = Math.round(Number(studyDays));
    if (!Number.isFinite(days) || days < 1 || days > 30) {
      setStudyMsg('Enter how many days you have to prep (1–30).');
      return;
    }
    setStudyMsg(null);
    if (!(await ensureConsent())) return;
    setStudyLoading(true);
    try {
      setStudyPlan(await api.generateStudyPlan(id, days));
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) router.push('/pricing');
      else setStudyMsg(e instanceof ApiError ? e.message : 'Could not generate.');
    } finally {
      setStudyLoading(false);
    }
  }

  async function generateTailoredResume() {
    setResumeMsg(null);
    if (!(await ensureConsent())) return;
    setResumeLoading(true);
    try {
      setResume(await api.generateTailoredResume(id));
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) router.push('/pricing');
      // 400 (no saved résumé), 503 (no key), and other API errors surface honestly inline.
      else setResumeMsg(e instanceof ApiError ? e.message : 'Could not generate.');
    } finally {
      setResumeLoading(false);
    }
  }

  async function generateNegotiation() {
    // Round BEFORE validating: "0.4" is > 0 but rounds to 0, which the backend (ge=0) would
    // accept — burning an LLM call on a nonsensical "$0" guide. Validate the value we send.
    const parsed = Math.round(Number(targetSalary));
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setNegMsg('Enter your target salary (a positive number).');
      return;
    }
    if (parsed > 10_000_000) {
      setNegMsg('Enter a realistic target salary.');
      return;
    }
    setNegMsg(null);
    if (!(await ensureConsent())) return;
    setNegLoading(true);
    try {
      setNeg(await api.generateSalaryNegotiation(id, parsed));
    } catch (e) {
      // A non-Career+ user should never reach this (the UI gates it), but the server is the
      // source of truth — if it says 403, route to pricing rather than dead-end.
      if (e instanceof ApiError && e.status === 403) router.push('/pricing');
      else setNegMsg(e instanceof ApiError ? e.message : 'Could not generate.');
    } finally {
      setNegLoading(false);
    }
  }

  if (loading) return <JobDetailSkeleton />;
  if (error || !job)
    return (
      <div className="space-y-4">
        <p role="alert" className="text-red-400">{error ?? 'Job not found.'}</p>
        <Button variant="secondary" onClick={() => router.push('/app')}>Back to pipeline</Button>
      </div>
    );

  return (
    <div className="space-y-6">
      {consentDialog}
      <div>
        <h1 className="text-2xl font-extrabold">{job.title}</h1>
        <p className="text-slate-400">{job.company}{job.location ? ` · ${job.location}` : ''}</p>
      </div>

      <Card className="text-center">
        <div className={`text-5xl font-extrabold ${scoreColor(job.score)}`}>
          {job.score == null ? '—' : Math.round(job.score)}
          <span className="text-xl text-slate-500"> / 100</span>
        </div>
        <p className="mt-1 text-sm text-slate-400">Fit score</p>
        {job.score_explanation && <p className="mt-3 text-slate-300">{job.score_explanation}</p>}
      </Card>

      <div>
        <h2 className="mb-2 text-lg font-semibold">Pipeline status</h2>
        <div className="flex flex-wrap gap-2">
          {STATUS_ORDER.map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={`rounded-lg border px-3 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 ${
                job.status === s
                  ? 'border-indigo-500 bg-indigo-500 text-white'
                  : 'border-slate-700 text-slate-300 hover:bg-slate-800'
              }`}
            >
              {STATUS_LABELS[s]}
            </button>
          ))}
        </div>
        {statusMsg && <p role="alert" className="mt-2 text-sm text-amber-400">{statusMsg}</p>}
      </div>

      <div>
        <h2 className="mb-2 text-lg font-semibold">Interview prep</h2>
        <Button onClick={generatePrep} disabled={prepLoading}>
          {prepLoading ? 'Generating…' : 'Generate prep pack'}
        </Button>
        {prepMsg && <p role="alert" className="mt-2 text-sm text-amber-400">{prepMsg}</p>}
        {prepLoading && !prep && (
          <Card className="mt-4 space-y-3" aria-busy="true" aria-label="Generating prep pack">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-11/12" />
            <Skeleton className="h-4 w-4/5" />
          </Card>
        )}
        {prep && (
          <Card className="mt-4">
            <h3 className="mb-2 font-semibold">{prep.title}</h3>
            <Markdown content={prep.content} />
            <ReportButton contentType="prep_pack" contentRef={id} contentExcerpt={prep.content} />
          </Card>
        )}
      </div>

      <div>
        <h2 className="mb-2 text-lg font-semibold">Application tools</h2>
        {isPaid ? (
          <div className="space-y-6">
            <div>
              <p className="mb-2 text-sm text-slate-400">
                Your résumé rewritten for this role — your real experience reordered and reworded
                to match the posting. Never invents anything you didn&apos;t do.
              </p>
              <Button onClick={generateTailoredResume} disabled={resumeLoading}>
                {resumeLoading ? 'Tailoring…' : resume ? 'Regenerate tailored résumé' : 'Generate tailored résumé'}
              </Button>
              {resumeMsg && <p role="alert" className="mt-2 text-sm text-amber-400">{resumeMsg}</p>}
              {resumeLoading && !resume && (
                <Card className="mt-4 space-y-3" aria-busy="true" aria-label="Tailoring résumé">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-11/12" />
                  <Skeleton className="h-4 w-4/5" />
                </Card>
              )}
              {resume && (
                <Card className="mt-4">
                  <h3 className="mb-2 font-semibold">{resume.title}</h3>
                  <Markdown content={resume.content} />
                  <ReportButton contentType="prep_pack" contentRef={id} contentExcerpt={resume.content} />
                </Card>
              )}
            </div>

            <div>
              <p className="mb-2 text-sm text-slate-400">
                A tailored cover letter for this role, drawn from your resume.
              </p>
              <Button onClick={generateCoverLetter} disabled={letterLoading}>
                {letterLoading ? 'Generating…' : letter ? 'Regenerate cover letter' : 'Generate cover letter'}
              </Button>
              {letterMsg && <p role="alert" className="mt-2 text-sm text-amber-400">{letterMsg}</p>}
              {letterLoading && !letter && (
                <Card className="mt-4 space-y-3" aria-busy="true" aria-label="Generating cover letter">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-11/12" />
                  <Skeleton className="h-4 w-4/5" />
                </Card>
              )}
              {letter && (
                <Card className="mt-4">
                  <h3 className="mb-2 font-semibold">{letter.title}</h3>
                  <Markdown content={letter.content} />
                  <ReportButton contentType="prep_pack" contentRef={id} contentExcerpt={letter.content} />
                </Card>
              )}
            </div>

            <div>
              <p className="mb-2 text-sm text-slate-400">
                A day-by-day study plan paced to the time you have before the interview.
              </p>
              <div className="mb-3 max-w-xs">
                <Field
                  label="Days to prep (1–30)"
                  type="number"
                  min={1}
                  max={30}
                  inputMode="numeric"
                  value={studyDays}
                  onChange={(e) => setStudyDays(e.target.value)}
                  placeholder="7"
                />
              </div>
              <Button onClick={generateStudyPlan} disabled={studyLoading}>
                {studyLoading ? 'Generating…' : studyPlan ? 'Regenerate study plan' : 'Generate study plan'}
              </Button>
              {studyMsg && <p role="alert" className="mt-2 text-sm text-amber-400">{studyMsg}</p>}
              {studyLoading && !studyPlan && (
                <Card className="mt-4 space-y-3" aria-busy="true" aria-label="Generating study plan">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-11/12" />
                  <Skeleton className="h-4 w-4/5" />
                </Card>
              )}
              {studyPlan && (
                <Card className="mt-4">
                  <h3 className="mb-2 font-semibold">{studyPlan.title}</h3>
                  <Markdown content={studyPlan.content} />
                  <ReportButton contentType="prep_pack" contentRef={id} contentExcerpt={studyPlan.content} />
                </Card>
              )}
            </div>
          </div>
        ) : (
          <Card className="flex flex-col items-start gap-3">
            <div className="flex items-center gap-2">
              <LockIcon />
              <p className="text-slate-300">
                Tailored <span className="font-semibold text-indigo-300">résumés</span>,{' '}
                <span className="font-semibold text-indigo-300">cover letters</span>, and{' '}
                <span className="font-semibold text-indigo-300">study plans</span> are a Pro feature.
              </p>
            </div>
            <Button onClick={() => router.push('/pricing')}>Upgrade to Pro</Button>
          </Card>
        )}
      </div>

      <div>
        <h2 className="mb-2 text-lg font-semibold">Salary negotiation</h2>
        {isCareerPlus ? (
          <div className="space-y-3">
            <div className="max-w-xs">
              <Field
                label="Your target salary (USD)"
                type="number"
                min={0}
                inputMode="numeric"
                value={targetSalary}
                onChange={(e) => setTargetSalary(e.target.value)}
                placeholder="180000"
              />
            </div>
            <Button onClick={generateNegotiation} disabled={negLoading}>
              {negLoading ? 'Generating…' : 'Generate negotiation guide'}
            </Button>
            {negMsg && <p role="alert" className="mt-1 text-sm text-amber-400">{negMsg}</p>}
            {negLoading && !neg && (
              <Card className="space-y-3" aria-busy="true" aria-label="Generating negotiation guide">
                <Skeleton className="h-5 w-56" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-11/12" />
                <Skeleton className="h-4 w-4/5" />
              </Card>
            )}
            {neg && (
              <Card>
                <h3 className="mb-2 font-semibold">{neg.title}</h3>
                <Markdown content={neg.content} />
                <ReportButton contentType="prep_pack" contentRef={id} contentExcerpt={neg.content} />
              </Card>
            )}
          </div>
        ) : (
          <Card className="flex flex-col items-start gap-3">
            <div className="flex items-center gap-2">
              <LockIcon />
              <p className="text-slate-300">
                AI salary-negotiation coaching is a{' '}
                <span className="font-semibold text-indigo-300">Career+</span> feature — scripts and
                strategies tailored to this offer.
              </p>
            </div>
            <Button onClick={() => router.push('/pricing')}>Upgrade to Career+</Button>
          </Card>
        )}
      </div>
    </div>
  );
}

function JobDetailSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading job">
      <div className="space-y-2">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-4 w-40" />
      </div>
      <Card className="flex flex-col items-center gap-2">
        <Skeleton className="h-12 w-24" />
        <Skeleton className="h-4 w-20" />
      </Card>
      <div className="space-y-2">
        <Skeleton className="h-5 w-32" />
        <div className="flex flex-wrap gap-2">
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-8 w-24" />
          ))}
        </div>
      </div>
      <div className="space-y-2">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-10 w-44" />
      </div>
    </div>
  );
}
