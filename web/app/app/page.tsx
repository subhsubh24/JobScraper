'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { Button, Card, ErrorText, Field, Skeleton } from '@/components/ui';
import { api, ApiError } from '@/lib/api';
import {
  STATUS_LABELS,
  scoreColor,
  type ImportListing,
  type Job,
  type PipelineStats,
} from '@/lib/types';

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

      {showAdd && <AddSection onAdded={() => { setShowAdd(false); load(); }} />}
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

type Prefill = { title: string; company: string; location: string; url: string };

// The ATS board token ("acme", "acme-corp") is not a display name. Turn it into a best-guess
// company label ("Acme", "Acme Corp") the user confirms — never render the raw slug as the name.
function prettifyCompanySlug(slug: string | null): string {
  if (!slug) return '';
  return slug
    .split(/[-_]+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

// The add-a-job surface: a manual form OR an ATS careers-page import. Import is a two-step,
// honest flow — preview roles from a Greenhouse/Lever URL, then pick one to PRE-FILL the manual
// form. Listings carry no job description (the board's list API omits it), so we never create an
// unscoreable shell silently: the user lands in the manual form and pastes the JD before scoring.
function AddSection({ onAdded }: { onAdded: () => void }) {
  const [mode, setMode] = useState<'manual' | 'import'>('manual');
  const [prefill, setPrefill] = useState<Prefill | null>(null);

  return (
    <Card>
      <div
        role="tablist"
        aria-label="How to add a job"
        className="mb-4 flex gap-1 rounded-lg bg-slate-800/60 p-1"
      >
        <TabButton
          id="add-tab-manual"
          controls="add-panel-manual"
          selected={mode === 'manual'}
          onClick={() => setMode('manual')}
        >
          Add manually
        </TabButton>
        <TabButton
          id="add-tab-import"
          controls="add-panel-import"
          selected={mode === 'import'}
          onClick={() => setMode('import')}
        >
          Import from a careers page
        </TabButton>
      </div>

      {/* Both panels stay MOUNTED (toggled with `hidden`) so switching tabs never discards
          half-typed input — the manual form's fields and the import panel's URL/results both
          survive a round-trip. A picked listing seeds the form via `prefill` (applied by effect). */}
      <div id="add-panel-manual" role="tabpanel" aria-labelledby="add-tab-manual" hidden={mode !== 'manual'}>
        <AddJobForm prefill={prefill} onAdded={onAdded} />
      </div>
      <div id="add-panel-import" role="tabpanel" aria-labelledby="add-tab-import" hidden={mode !== 'import'}>
        <ImportPanel
          onPick={(listing) => {
            setPrefill({
              title: listing.title,
              // company_slug is the ATS BOARD TOKEN (e.g. "acme"), not a display name — prettify it
              // into a best-GUESS company ("acme-corp" → "Acme Corp") the banner asks the user to
              // confirm, rather than dumping the raw lowercase slug into the Company field.
              company: prettifyCompanySlug(listing.company_slug),
              location: listing.location ?? '',
              url: listing.url ?? '',
            });
            setMode('manual');
          }}
        />
      </div>
    </Card>
  );
}

function TabButton({
  id,
  controls,
  selected,
  onClick,
  children,
}: {
  id: string;
  controls: string;
  selected: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      id={id}
      role="tab"
      aria-selected={selected}
      aria-controls={controls}
      onClick={onClick}
      className={`flex-1 rounded-md px-3 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
        selected ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'
      }`}
    >
      {children}
    </button>
  );
}

function AddJobForm({ prefill, onAdded }: { prefill?: Prefill | null; onAdded: () => void }) {
  const [title, setTitle] = useState(prefill?.title ?? '');
  const [company, setCompany] = useState(prefill?.company ?? '');
  const [location, setLocation] = useState(prefill?.location ?? '');
  const [url, setUrl] = useState(prefill?.url ?? '');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // The form stays mounted across tab switches (so manual typing isn't lost), so re-seed the
  // fields when a NEW listing is picked (prefill identity changes) — clearing the description
  // since it belongs to the previously-picked role. A pure tab toggle leaves prefill unchanged,
  // so nothing is overwritten.
  useEffect(() => {
    if (prefill) {
      // Syncing picked-listing props into local field state (same accepted prop→state pattern
      // the pipeline/insights load() effects use).
      /* eslint-disable react-hooks/set-state-in-effect */
      setTitle(prefill.title);
      setCompany(prefill.company);
      setLocation(prefill.location);
      setUrl(prefill.url);
      setDescription('');
      setError(null);
      /* eslint-enable react-hooks/set-state-in-effect */
    }
  }, [prefill]);

  async function doCreate() {
    setLoading(true);
    try {
      await api.createJob({
        title: title.trim(),
        company_name: company.trim(),
        location: location.trim() || undefined,
        description: description.trim() || undefined,
        url: url.trim() || undefined,
      });
      onAdded();
    } catch (e2) {
      setError(e2 instanceof ApiError ? e2.message : 'Could not add this job.');
    } finally {
      setLoading(false);
    }
  }

  // "Add & score" — the scoring path. An imported listing carries NO job description, so require
  // one here (otherwise scoring on title alone is the unscoreable shell this flow avoids). The
  // manual path keeps it optional. If a user really has no JD, the "Track without a score" button
  // below is the honest, explicit opt-out (only shown on the imported path).
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!title.trim() || !company.trim()) {
      setError('Title and company are required.');
      return;
    }
    if (prefill && !description.trim()) {
      setError('Paste the job description so we can score this role — or use “Track without a score” below.');
      return;
    }
    await doCreate();
  }

  // The imported-path escape hatch the scoring gate points to: add the role now WITHOUT a fit
  // score, an EXPLICIT informed choice (not a silent shell). Keeps the already-imported
  // title/company/location/url instead of forcing the user to close and retype.
  async function trackWithoutScore() {
    setError(null);
    if (!title.trim() || !company.trim()) {
      setError('Title and company are required.');
      return;
    }
    await doCreate();
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      {prefill && (
        <p className="rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-3 py-2 text-sm text-indigo-200">
          Imported from the careers page. We guessed the company name from the board — double-check
          it, then paste the job description below to get an accurate fit score.
        </p>
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Job title *" value={title} onChange={(e) => setTitle(e.target.value)} />
        <Field label="Company *" value={company} onChange={(e) => setCompany(e.target.value)} />
      </div>
      <Field label="Location" value={location} onChange={(e) => setLocation(e.target.value)} />
      <Field label="Posting URL" value={url} onChange={(e) => setUrl(e.target.value)} />
      <label className="block">
        <span className="mb-1 block text-sm text-slate-400">
          {prefill ? 'Job description * (powers the fit score)' : 'Job description (powers the fit score)'}
        </span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-slate-100 outline-none focus:border-indigo-500"
        />
      </label>
      <ErrorText>{error}</ErrorText>
      <div className="flex flex-wrap gap-3">
        <Button type="submit" disabled={loading}>{loading ? 'Adding…' : 'Add & score'}</Button>
        {prefill && (
          <Button type="button" variant="secondary" disabled={loading} onClick={trackWithoutScore}>
            Track without a score
          </Button>
        )}
      </div>
    </form>
  );
}

// Step 1 of import: paste a Greenhouse/Lever careers URL and preview the open roles. The server
// SSRF-guards the URL and returns an HONEST state — unsupported board / unreachable / no open
// roles — which we surface verbatim rather than a generic error. Picking a role hands it up to
// AddSection to pre-fill the manual form (step 2).
function ImportPanel({ onPick }: { onPick: (listing: ImportListing) => void }) {
  const [careersUrl, setCareersUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [listings, setListings] = useState<ImportListing[] | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [truncated, setTruncated] = useState(false);

  async function preview(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!careersUrl.trim()) {
      setError('Paste a Greenhouse or Lever careers URL.');
      return;
    }
    setLoading(true);
    setListings(null);
    setMessage(null);
    try {
      const res = await api.importPreview(careersUrl.trim());
      setListings(res.jobs);
      setMessage(res.message);
      setTruncated(res.truncated);
    } catch (e2) {
      setError(e2 instanceof ApiError ? e2.message : 'Could not preview that careers page.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={preview} className="space-y-3">
        <Field
          label="Company careers URL (Greenhouse or Lever)"
          type="url"
          inputMode="url"
          placeholder="https://boards.greenhouse.io/acme"
          value={careersUrl}
          onChange={(e) => setCareersUrl(e.target.value)}
        />
        <ErrorText>{error}</ErrorText>
        <Button type="submit" disabled={loading}>{loading ? 'Previewing…' : 'Preview roles'}</Button>
      </form>

      {message && (
        <p
          role="status"
          className="rounded-lg border border-slate-700 bg-slate-800/40 px-3 py-2 text-sm text-slate-300"
        >
          {message}
        </p>
      )}

      {listings && listings.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-slate-400">
            {truncated ? 'Showing the first roles found. ' : ''}Pick a role to pre-fill the form:
          </p>
          <ul className="space-y-2">
            {listings.map((listing, i) => (
              <li
                key={listing.external_id ?? `${listing.title}-${i}`}
                className="flex items-center justify-between gap-3 rounded-xl border border-slate-700 bg-slate-800/40 px-3 py-2.5"
              >
                <div className="min-w-0">
                  <p className="truncate font-semibold text-slate-100">{listing.title}</p>
                  <p className="truncate text-sm text-slate-400">
                    {[listing.location, listing.department].filter(Boolean).join(' · ') || '—'}
                  </p>
                </div>
                <Button type="button" variant="secondary" onClick={() => onPick(listing)}>
                  Use this
                </Button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
