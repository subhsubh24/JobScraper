'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Button, Card, ErrorText } from '@/components/ui';
import { api, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';

export default function SettingsPage() {
  const { user, signOut } = useAuth();
  const router = useRouter();
  const [confirm, setConfirm] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  // The app layout already guards for an authenticated user, but render nothing rather than
  // flash empty fields during the brief auth-restore window.
  if (!user) return null;

  const canDelete = confirm.trim().toUpperCase() === 'DELETE' && !deleting;
  const planLabel = user.tier === 'premium' ? 'Premium' : 'Free';

  async function handleDelete() {
    if (!canDelete) return;
    setError(null);
    setDeleting(true);
    try {
      // Real side-effect: await the server cascade-delete; only on confirmed success do we
      // clear local state and leave. No optimistic "deleted" message.
      await api.deleteAccount();
      signOut();
      router.replace('/');
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.message
          : 'Could not delete your account. Please try again.';
      setError(msg);
      setDeleting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="mt-1 text-sm text-slate-400">Manage your account and subscription.</p>
      </div>

      <Card>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Account</h2>
        <dl className="mt-4 space-y-3 text-sm">
          <div className="flex items-center justify-between gap-4">
            <dt className="text-slate-400">Name</dt>
            <dd className="text-slate-100">{user.full_name || '—'}</dd>
          </div>
          <div className="flex items-center justify-between gap-4">
            <dt className="text-slate-400">Email</dt>
            <dd className="break-all text-slate-100">{user.email}</dd>
          </div>
        </dl>
        <div className="mt-5">
          <Button variant="secondary" onClick={signOut}>
            Log out
          </Button>
        </div>
      </Card>

      <Card>
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Plan</h2>
            <p className="mt-2 text-lg font-semibold text-slate-100">{planLabel}</p>
          </div>
          {user.tier === 'premium' ? (
            <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
              Active
            </span>
          ) : (
            <Link
              href="/pricing"
              className="inline-flex items-center justify-center rounded-lg bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-400"
            >
              Upgrade
            </Link>
          )}
        </div>
        {user.tier === 'premium' && (
          <p className="mt-3 text-sm text-slate-400">
            Manage or cancel your subscription anytime from the receipt email&rsquo;s billing
            portal link.
          </p>
        )}
      </Card>

      <Card className="border-red-900/60">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-red-400">Danger zone</h2>
        <p className="mt-3 text-sm text-slate-300">
          Delete your account and <span className="font-semibold">all</span> your data — tracked
          jobs, scores, prep packs, and coach history. This is permanent and cannot be undone.
        </p>

        {!showConfirm ? (
          <button
            onClick={() => setShowConfirm(true)}
            className="mt-4 inline-flex items-center justify-center rounded-lg border border-red-700 px-4 py-2.5 text-sm font-semibold text-red-300 transition hover:bg-red-950/50"
          >
            Delete account
          </button>
        ) : (
          <div className="mt-4 space-y-3">
            <label className="block">
              <span className="mb-1 block text-sm text-slate-400">
                Type <span className="font-mono font-semibold text-slate-200">DELETE</span> to
                confirm
              </span>
              <input
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                autoComplete="off"
                aria-label="Type DELETE to confirm account deletion"
                className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-slate-100 outline-none focus:border-red-500"
              />
            </label>
            <ErrorText>{error}</ErrorText>
            <div className="flex gap-3">
              <button
                onClick={handleDelete}
                disabled={!canDelete}
                className="inline-flex items-center justify-center rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-red-500 disabled:opacity-50"
              >
                {deleting ? 'Deleting…' : 'Permanently delete account'}
              </button>
              <Button
                variant="secondary"
                onClick={() => {
                  setShowConfirm(false);
                  setConfirm('');
                  setError(null);
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
