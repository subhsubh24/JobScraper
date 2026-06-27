'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { Button, Card } from '@/components/ui';
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
    try {
      setJob(await api.updateJobStatus(id, status));
    } catch {
      /* keep prior state on failure */
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

  if (loading) return <p className="text-slate-400">Loading…</p>;
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
      </div>

      <div>
        <h2 className="mb-2 font-semibold">Interview prep</h2>
        <Button onClick={generatePrep} disabled={prepLoading}>
          {prepLoading ? 'Generating…' : 'Generate prep pack'}
        </Button>
        {prepMsg && <p className="mt-2 text-sm text-amber-400">{prepMsg}</p>}
        {prep && (
          <Card className="mt-4">
            <h3 className="mb-2 font-semibold">{prep.title}</h3>
            <pre className="whitespace-pre-wrap text-sm text-slate-300">{prep.content}</pre>
          </Card>
        )}
      </div>
    </div>
  );
}
