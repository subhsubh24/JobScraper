'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Button, Card, ErrorText, LinkButton } from '@/components/ui';
import { AiConsentSetting } from '@/components/ai-consent';
import { api, ApiError, type ReferralStats } from '@/lib/api';
import { useAuth } from '@/lib/auth';

function ReferAFriendCard() {
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [failed, setFailed] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let active = true;
    api
      .referralStats()
      .then((s) => active && setStats(s))
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
    };
  }, []);

  const link =
    stats && typeof window !== 'undefined'
      ? `${window.location.origin}/register?ref=${stats.code}`
      : '';

  async function copy() {
    if (!link) return;
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <Card>
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Refer a friend</h2>
      <p className="mt-2 text-sm text-slate-300">
        Share your link. When a friend signs up, you <span className="font-semibold">both</span> get a
        free interview prep pack on us.
      </p>

      {failed ? (
        <p className="mt-4 text-sm text-slate-500">Your invite link is unavailable right now.</p>
      ) : !stats ? (
        <div className="mt-4 h-10 animate-pulse rounded-lg bg-slate-800/60" aria-hidden="true" />
      ) : (
        <>
          <div className="mt-4 flex gap-2">
            <input
              readOnly
              value={link}
              aria-label="Your referral link"
              onFocus={(e) => e.target.select()}
              className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
            />
            <Button variant="secondary" onClick={copy}>
              {copied ? 'Copied' : 'Copy'}
            </Button>
          </div>
          <p className="mt-3 text-sm text-slate-400">
            <span className="font-semibold text-slate-200">{stats.total_referred}</span>{' '}
            {stats.total_referred === 1 ? 'friend has' : 'friends have'} joined ·{' '}
            <span className="font-semibold text-slate-200">{stats.bonus_prep_packs}</span> bonus prep
            {stats.bonus_prep_packs === 1 ? ' pack' : ' packs'} earned
          </p>
        </>
      )}
    </Card>
  );
}

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
  const planLabel = user.tier === 'premium' ? (user.career_plus ? 'Career+' : 'Pro') : 'Free';

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
        <p className="mt-1 text-sm text-slate-400">Manage your account and plan.</p>
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
            <LinkButton href="/pricing">Upgrade</LinkButton>
          )}
        </div>
        {user.tier === 'premium' && (
          <p className="mt-3 text-sm text-slate-400">
            To change or cancel your plan, email{' '}
            <a href="mailto:support@careeroperator.app" className="rounded text-indigo-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">
              support@careeroperator.app
            </a>{' '}
            and we&rsquo;ll take care of it.
          </p>
        )}
      </Card>

      <AiConsentSetting />

      <ReferAFriendCard />

      <Card className="border-red-900/60">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-red-400">Danger zone</h2>
        <p className="mt-3 text-sm text-slate-300">
          Delete your account and <span className="font-semibold">all</span> your data — tracked
          jobs, scores, prep packs, and coach history. This is permanent and cannot be undone.
        </p>

        {!showConfirm ? (
          <div className="mt-4">
            <Button variant="dangerOutline" onClick={() => setShowConfirm(true)}>
              Delete account
            </Button>
          </div>
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
              <Button variant="danger" onClick={handleDelete} disabled={!canDelete}>
                {deleting ? 'Deleting…' : 'Permanently delete account'}
              </Button>
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
