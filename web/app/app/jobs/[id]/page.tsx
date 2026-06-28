'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { Button, Card, Skeleton } from '@/components/ui';
import { Markdown } from '@/components/markdown';
import { api, ApiError } from '@/lib/api';
import { STATUS_LABELS, STATUS_ORDER, scoreColor, type ApplicationStatus, type Job } from '@/lib/types';

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prep, setPrep] = useState<{ title: string; content: string } | null>(null);
  const [prepLoading, setPrepLoading] = useState(false);
  const [prepMsg, setPrepMsg] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

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
    setPrepLoading(true);
    setPrepMsg(null);
    try {
      setPrep(await api.generatePrepPack(id));
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) router.push('/pricing');
      else setPrepMsg(e instanceof ApiError ? e.message : 'Could not generate.');
    } finally {
      setPrepLoading(false);
    }
  }

  if (loading) return <JobDetailSkeleton />;
  if (error || !job)
    return (
      <div className="space-y-4">
        <p className="text-red-400">{error ?? 'Job not found.'}</p>
        <Button variant="secondary" onClick={() => router.push('/app')}>Back to pipeline</Button>
      </div>
    );

  return (
    <div className="space-y-6">
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
        <h2 className="mb-2 font-semibold">Pipeline status</h2>
        <div className="flex flex-wrap gap-2">
          {STATUS_ORDER.map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={`rounded-lg border px-3 py-1.5 text-sm ${
                job.status === s
                  ? 'border-indigo-500 bg-indigo-500 text-white'
                  : 'border-slate-700 text-slate-300 hover:bg-slate-800'
              }`}
            >
              {STATUS_LABELS[s]}
            </button>
          ))}
        </div>
        {statusMsg && <p className="mt-2 text-sm text-amber-400">{statusMsg}</p>}
      </div>

      <div>
        <h2 className="mb-2 font-semibold">Interview prep</h2>
        <Button onClick={generatePrep} disabled={prepLoading}>
          {prepLoading ? 'Generating…' : 'Generate prep pack'}
        </Button>
        {prepMsg && <p className="mt-2 text-sm text-amber-400">{prepMsg}</p>}
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
    </div>
  );
}
