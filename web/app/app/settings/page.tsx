'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { Button, Card, ErrorText, LinkButton } from '@/components/ui';
import { AiConsentSetting } from '@/components/ai-consent';
import { api, ApiError, type Competency, type ReferralStats } from '@/lib/api';
import { useAuth } from '@/lib/auth';

// Self-serve subscription management for an active subscriber: opens Stripe's hosted Billing
// Portal (change plan / update card / cancel). Replaces the old "email support" dead-end. Honest
// degradation: if the portal isn't live yet the server returns 503 and we say so — no fake success.
function ManageSubscriptionButton() {
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function openPortal() {
    setBusy(true);
    setNotice(null);
    try {
      const url = await api.startBillingPortal();
      window.location.assign(url); // hand off to Stripe's hosted portal
    } catch (e) {
      setNotice(
        e instanceof ApiError && e.status === 503
          ? 'Self-serve plan management isn’t live yet — check back soon.'
          : 'Could not open subscription management. Please try again.',
      );
      setBusy(false);
    }
  }

  return (
    <div className="mt-3">
      <Button variant="secondary" onClick={openPortal} disabled={busy}>
        {busy ? 'Opening…' : 'Manage subscription'}
      </Button>
      <p className="mt-2 text-sm text-slate-400">
        Change your plan, update your payment method, or cancel — anytime.
      </p>
      {notice && (
        <div className="mt-2">
          <ErrorText>{notice}</ErrorText>
        </div>
      )}
    </div>
  );
}

function ResumeCard() {
  const [resume, setResume] = useState<string | null>(null); // null = still loading
  const [saved, setSaved] = useState('');
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .getResume()
      .then((text) => {
        if (!active) return;
        setResume(text);
        setSaved(text);
      })
      .catch(() => active && setError('Could not load your résumé. Reload to try again.'));
    return () => {
      active = false;
    };
  }, []);

  const dirty = resume !== null && resume !== saved;

  async function save() {
    if (resume === null || saving || !dirty) return;
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      // Await the real PATCH; only reflect "saved" once the server confirms it.
      const hasResume = await api.saveResume(resume);
      setSaved(resume);
      setNotice(hasResume ? 'Résumé saved.' : 'Résumé cleared.');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not save your résumé. Try again.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Résumé</h2>
      <p className="mt-2 text-sm text-slate-300">
        Paste your résumé as text. It powers your fit scores, tailored résumés, cover letters, and
        your skill-gap heatmap — the more complete it is, the sharper they get.
      </p>

      {resume === null && error ? (
        // Load failed: surface the error + recovery path instead of a skeleton that spins forever
        // (the textarea/error below only render once resume is a string). Quiet/gray, no alert
        // role — matching the on-mount load-failure convention (team, referral, enrichment cards);
        // the red ErrorText below is reserved for the user-initiated SAVE action.
        <p className="mt-4 text-sm text-slate-500">{error}</p>
      ) : resume === null ? (
        <div className="mt-4 h-40 animate-pulse rounded-lg bg-slate-800/60" aria-hidden="true" />
      ) : (
        <>
          <label className="mt-4 block">
            <span className="sr-only">Your résumé text</span>
            <textarea
              value={resume}
              onChange={(e) => {
                setResume(e.target.value);
                setNotice(null);
              }}
              rows={10}
              maxLength={50000}
              placeholder="Paste your résumé here — experience, skills, achievements…"
              aria-label="Your résumé text"
              className="w-full resize-y rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-sm leading-relaxed text-slate-200 outline-none focus:border-indigo-500"
            />
          </label>
          <div className="mt-3 flex items-center justify-between gap-4">
            <span className="text-xs text-slate-500">{resume.length.toLocaleString()} / 50,000</span>
            <Button onClick={save} disabled={!dirty || saving}>
              {saving ? 'Saving…' : 'Save résumé'}
            </Button>
          </div>
          {notice && <p className="mt-2 text-sm text-emerald-400">{notice}</p>}
          <ErrorText>{error}</ErrorText>
        </>
      )}
    </Card>
  );
}

function GithubEnrichmentCard() {
  const { user } = useAuth();
  const isPro = user?.tier === 'premium';
  const [competencies, setCompetencies] = useState<Competency[] | null>(null);
  const [handle, setHandle] = useState('');
  const [importing, setImporting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  // Latch: once the user has taken over the skills list (imported or cleared), a SLOW initial
  // load that resolves afterwards must NOT clobber that action. Without this, a 3s getEnrichment
  // that lands after a fast clear silently re-populates the just-cleared skills — reversing an
  // explicit user action with no feedback. A ref (not state) so the load's stale closure reads
  // the live value, and setting it never triggers a re-render.
  const userMutatedRef = useRef(false);

  useEffect(() => {
    if (!isPro) return;
    // Reset the latch per load cycle: this effect re-fires on an isPro transition (e.g. a tier
    // lapses then renews in the same session), and that fresh getEnrichment SHOULD win. Resetting
    // here — synchronously, before any user mutation can occur — scopes the latch to THIS load
    // and still guards the in-flight race, without permanently suppressing later legitimate loads.
    userMutatedRef.current = false;
    let active = true;
    api
      .getEnrichment()
      .then((c) => active && !userMutatedRef.current && setCompetencies(c))
      // Distinguish a load FAILURE from a genuinely empty result: setting competencies to []
      // here would render "No skills imported yet", masking the error as an empty state.
      .catch(() => active && setLoadFailed(true));
    return () => {
      active = false;
    };
  }, [isPro]);

  async function importGithub() {
    const value = handle.trim();
    if (!value || importing) return;
    setImporting(true);
    setError(null);
    setNotice(null);
    try {
      // Await the real result and report it honestly — the message reflects what was actually
      // imported (or that nothing was found), never an optimistic "done".
      const result = await api.enrichGithub(value);
      userMutatedRef.current = true; // a stale initial load must not overwrite a fresh import
      setCompetencies(result.competencies);
      setNotice(result.message);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not import from GitHub. Try again.');
    } finally {
      setImporting(false);
    }
  }

  async function clearAll() {
    try {
      await api.clearEnrichment();
      userMutatedRef.current = true; // a stale initial load must not re-populate cleared skills
      setCompetencies([]);
      setNotice(null);
    } catch {
      setError('Could not clear your imported skills. Try again.');
    }
  }

  return (
    <Card>
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
        Profile enrichment
      </h2>
      <p className="mt-2 text-sm text-slate-300">
        Import skills from your public GitHub — the languages and topics from your own
        repositories sharpen your fit scores and cover letters. Nothing is invented; we only read
        your public repos.
      </p>

      {!isPro ? (
        <div className="mt-4 flex items-center justify-between gap-4 rounded-lg border border-slate-700 bg-slate-800/40 px-4 py-3">
          <p className="text-sm text-slate-400">A Pro feature.</p>
          <LinkButton href="/pricing">Upgrade</LinkButton>
        </div>
      ) : (
        <>
          <div className="mt-4 flex gap-2">
            <input
              value={handle}
              onChange={(e) => setHandle(e.target.value)}
              placeholder="github.com/yourname"
              aria-label="Your GitHub username or profile URL"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              onKeyDown={(e) => e.key === 'Enter' && importGithub()}
              className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
            />
            <Button onClick={importGithub} disabled={importing || !handle.trim()}>
              {importing ? 'Importing…' : 'Import'}
            </Button>
          </div>

          {notice && <p className="mt-3 text-sm text-slate-400">{notice}</p>}
          <ErrorText>{error}</ErrorText>

          {competencies === null && loadFailed ? (
            <p className="mt-4 text-sm text-slate-500">
              Could not load your imported skills. Reload to try again.
            </p>
          ) : competencies === null ? (
            <div className="mt-4 h-8 animate-pulse rounded-lg bg-slate-800/60" aria-hidden="true" />
          ) : competencies.length > 0 ? (
            <>
              <ul className="mt-4 flex flex-wrap gap-2">
                {competencies.map((c) => (
                  <li
                    key={`${c.source_type}:${c.skill}`}
                    title={c.evidence ?? undefined}
                    className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-200"
                  >
                    {c.skill}
                  </li>
                ))}
              </ul>
              <button
                onClick={clearAll}
                className="mt-3 rounded text-xs text-slate-500 hover:text-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
              >
                Clear imported skills
              </button>
            </>
          ) : (
            <p className="mt-4 text-sm text-slate-500">
              No skills imported yet — add your GitHub above.
            </p>
          )}
        </>
      )}
    </Card>
  );
}

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
        {user.tier === 'premium' && <ManageSubscriptionButton />}
      </Card>

      <ResumeCard />

      <AiConsentSetting />

      <GithubEnrichmentCard />

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
