'use client';

import { useState } from 'react';
import { Button, ErrorText } from '@/components/ui';
import { api, ApiError } from '@/lib/api';

type Reason = 'harmful' | 'inaccurate' | 'offensive' | 'other';

const REASONS: { value: Reason; label: string }[] = [
  { value: 'inaccurate', label: 'Inaccurate or misleading' },
  { value: 'harmful', label: 'Harmful or dangerous advice' },
  { value: 'offensive', label: 'Offensive or inappropriate' },
  { value: 'other', label: 'Something else' },
];

/**
 * User-facing control to report an AI-generated response (coach reply or prep pack) for
 * moderator review — the store-required (Apple/Google 2026 GenAI/UGC) counterpart to the
 * server-side output moderation. Low-emphasis by default so it never competes with the
 * content; expands to a compact form on demand. The success state is shown ONLY after the
 * real POST /api/report resolves (no optimistic "reported" claim).
 */
export function ReportButton({
  contentType,
  contentRef,
  contentExcerpt,
}: {
  contentType: 'coach' | 'prep_pack';
  contentRef?: string;
  contentExcerpt?: string;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<Reason>('inaccurate');
  const [detail, setDetail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  if (done) {
    return (
      <p className="mt-2 text-xs text-slate-500" role="status">
        Flagged for review — thank you.
      </p>
    );
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      await api.reportContent({
        content_type: contentType,
        reason,
        content_ref: contentRef,
        // Bounded server-side; trim to the API limit so a long prep pack still submits.
        content_excerpt: contentExcerpt?.slice(0, 5000),
        detail: detail.trim() || undefined,
      });
      setDone(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not send the report — try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-2 inline-flex items-center gap-1 rounded text-xs text-slate-500 transition hover:text-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
      >
        <FlagIcon />
        Report this response
      </button>
    );
  }

  return (
    <div className="mt-3 rounded-lg border border-slate-700 bg-slate-950/40 p-3">
      <fieldset>
        <legend className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Report this AI response
        </legend>
        <div className="space-y-1.5">
          {REASONS.map((r) => (
            <label key={r.value} className="flex items-center gap-2 text-sm text-slate-200">
              <input
                type="radio"
                name="report-reason"
                value={r.value}
                checked={reason === r.value}
                onChange={() => setReason(r.value)}
                className="accent-indigo-500"
              />
              {r.label}
            </label>
          ))}
        </div>
      </fieldset>
      <label className="mt-3 block">
        <span className="mb-1 block text-xs text-slate-400">Add a detail (optional)</span>
        <textarea
          value={detail}
          onChange={(e) => setDetail(e.target.value)}
          maxLength={1000}
          rows={2}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
          placeholder="What was wrong with this response?"
        />
      </label>
      {error && (
        <div className="mt-2">
          <ErrorText>{error}</ErrorText>
        </div>
      )}
      <div className="mt-3 flex gap-2">
        <Button type="button" onClick={submit} disabled={submitting} className="px-3 py-1.5">
          {submitting ? 'Sending…' : 'Submit report'}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => setOpen(false)}
          disabled={submitting}
          className="px-3 py-1.5"
        >
          Cancel
        </Button>
      </div>
    </div>
  );
}

function FlagIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
      <line x1="4" y1="22" x2="4" y2="15" />
    </svg>
  );
}
