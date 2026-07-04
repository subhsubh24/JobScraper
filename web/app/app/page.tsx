'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { Button, Card, ErrorText, Field, Skeleton } from '@/components/ui';
import { api, ApiError } from '@/lib/api';
import { STATUS_LABELS, scoreColor, type Job, type PipelineStats } from '@/lib/types';

export default function PipelinePage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [j, s] = await Promise.all([api.listJobs(), api.pipeline()]);
      setJobs(j);
      setStats(s);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load your pipeline.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // load() setStates asynchronously after the fetch resolves, not synchronously.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  if (loading) return <PipelineSkeleton />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-extrabold">Your pipeline</h1>
        <Button onClick={() => setShowAdd((v) => !v)}>{showAdd ? 'Close' : '+ Add a job'}</Button>
      </div>

      {stats && (
        <div className="grid grid-cols-3 gap-2 sm:gap-4">
          <Stat label="Tracked" value={String(stats.total_jobs)} />
          <Stat label="Avg fit" value={stats.average_score ? String(stats.average_score) : '—'} />
          <Stat label="Active" value={String(activeCount(stats))} />
        </div>
      )}

      {showAdd && <AddJobForm onAdded={() => { setShowAdd(false); load(); }} />}
      <ErrorText>{error}</ErrorText>

      {jobs.length === 0 ? (
        <Card>
          <p className="text-slate-300">No jobs yet.</p>
          <p className="text-slate-500">Add a role you&apos;re chasing and we&apos;ll score how well it fits you.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <Link
              key={job.id}
              href={`/app/jobs/${job.id}`}
              className="block rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
            >
              <Card className="flex items-center justify-between transition hover:border-slate-600">
                <div>
                  <p className="font-semibold">{job.title}</p>
                  <p className="text-sm text-slate-400">
                    {job.company ?? 'Unknown'}{job.location ? ` · ${job.location}` : ''}
                  </p>
                  <span className="mt-1 inline-block rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
                    {STATUS_LABELS[job.status]}
                  </span>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-extrabold ${scoreColor(job.score == null ? job.score : Math.round(job.score))}`}>
                    {job.score == null ? '—' : Math.round(job.score)}
                  </div>
                  <div className="text-xs text-slate-500">fit</div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function PipelineSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading your pipeline">
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-44" />
        <Skeleton className="h-10 w-28" />
      </div>
      <div className="grid grid-cols-3 gap-2 sm:gap-4">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-20" />
        ))}
      </div>
      <div className="space-y-3">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-[88px]" />
        ))}
      </div>
    </div>
  );
}

function activeCount(s: PipelineStats): number {
  const b = s.status_breakdown;
  return (b.applied ?? 0) + (b.phone_screen ?? 0) + (b.interview ?? 0) + (b.offer ?? 0);
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card className="text-center">
      <div className="text-xl font-extrabold sm:text-2xl">{value}</div>
      <div className="text-xs text-slate-400">{label}</div>
    </Card>
  );
}

function AddJobForm({ onAdded }: { onAdded: () => void }) {
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!title.trim() || !company.trim()) {
      setError('Title and company are required.');
      return;
    }
    setLoading(true);
    try {
      await api.createJob({
        title: title.trim(),
        company_name: company.trim(),
        location: location.trim() || undefined,
        description: description.trim() || undefined,
      });
      onAdded();
    } catch (e2) {
      setError(e2 instanceof ApiError ? e2.message : 'Could not add this job.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <form onSubmit={submit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Job title *" value={title} onChange={(e) => setTitle(e.target.value)} />
          <Field label="Company *" value={company} onChange={(e) => setCompany(e.target.value)} />
        </div>
        <Field label="Location" value={location} onChange={(e) => setLocation(e.target.value)} />
        <label className="block">
          <span className="mb-1 block text-sm text-slate-400">Job description (powers the fit score)</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-slate-100 outline-none focus:border-indigo-500"
          />
        </label>
        <ErrorText>{error}</ErrorText>
        <Button type="submit" disabled={loading}>{loading ? 'Adding…' : 'Add & score'}</Button>
      </form>
    </Card>
  );
}
