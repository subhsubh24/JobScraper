'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { Button, Card, ErrorText } from '@/components/ui';
import { api, ApiError, type Organization } from '@/lib/api';
import { useAuth } from '@/lib/auth';

// Team / organization seat-tier management surface. Makes the run-39 seat-tier BACKEND
// user-reachable end-to-end: create an org, buy seats (real Stripe Checkout — honest 503
// when unconfigured, never a fake purchase), and assign/free seats by email. The server is
// the source of truth: every mutation awaits the real API and re-renders from the returned
// org payload — no optimistic success. Entitlement for members is granted solely by the
// signed Stripe webhook (buying seats here only opens checkout).

const MAX_SEATS = 200;

function OrgNameCard({ onCreated }: { onCreated: (org: Organization) => void }) {
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function create() {
    const value = name.trim();
    if (value.length < 2 || creating) return;
    setCreating(true);
    setError(null);
    try {
      // Await the real create; only surface the org once the server confirms it.
      onCreated(await api.createOrg(value));
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : 'Could not create your team. Try again.',
      );
      setCreating(false);
    }
  }

  return (
    <Card>
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
        Create your team
      </h2>
      <p className="mt-2 text-sm text-slate-300">
        Buy Pro seats in bulk and assign them to your teammates. You administer the team; each
        member you add gets full Pro access.
      </p>
      <div className="mt-4 flex gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Acme Inc."
          maxLength={120}
          aria-label="Team name"
          onKeyDown={(e) => e.key === 'Enter' && create()}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
        />
        <Button onClick={create} disabled={creating || name.trim().length < 2}>
          {creating ? 'Creating…' : 'Create team'}
        </Button>
      </div>
      <ErrorText>{error}</ErrorText>
    </Card>
  );
}

function BuySeatsCard({ org }: { org: Organization }) {
  const [seats, setSeats] = useState(5);
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function buy() {
    if (pending) return;
    setPending(true);
    setNotice(null);
    try {
      const url = await api.orgCheckout(seats);
      // Hand off to Stripe's hosted Checkout — the real charge happens there; the webhook
      // then grants the seats and Stripe redirects back to /app/team?checkout=success.
      window.location.assign(url);
    } catch (e) {
      if (e instanceof ApiError && e.status === 503) {
        setNotice('Team plans aren’t live yet — no charge was made. Check back soon.');
      } else {
        setNotice(e instanceof ApiError ? e.message : 'Could not start checkout. Try again.');
      }
      setPending(false);
    }
  }

  const alreadyBought = (org.seats_purchased || 0) > 0;

  return (
    <Card>
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
        {alreadyBought ? 'Add more seats' : 'Buy seats'}
      </h2>
      <p className="mt-2 text-sm text-slate-300">
        Each seat is a full Pro subscription for one teammate, billed annually. Seats you own but
        haven’t assigned stay available to add members.
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm text-slate-300">
          <span>Seats</span>
          <input
            type="number"
            min={1}
            max={MAX_SEATS}
            value={seats}
            onChange={(e) => {
              const n = Math.floor(Number(e.target.value));
              // Clamp to the server-enforced 1–200 bound so the button never posts an invalid
              // quantity (the server would 422; clamping keeps the control honest).
              setSeats(Number.isFinite(n) ? Math.min(MAX_SEATS, Math.max(1, n)) : 1);
            }}
            aria-label="Number of seats to buy"
            className="w-20 rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500"
          />
        </label>
        <Button onClick={buy} disabled={pending}>
          {pending ? 'Starting checkout…' : `Buy ${seats} ${seats === 1 ? 'seat' : 'seats'}`}
        </Button>
      </div>
      {notice && (
        <p role="alert" className="mt-3 text-sm text-amber-400">
          {notice}
        </p>
      )}
      <p className="mt-3 text-xs text-slate-500">Secure checkout by Stripe.</p>
    </Card>
  );
}

function MembersCard({ org, onUpdated }: { org: Organization; onUpdated: (org: Organization) => void }) {
  const [email, setEmail] = useState('');
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  const members = org.members ?? [];
  const seatsUsed = org.seats_used || 0;
  const seatsPurchased = org.seats_purchased || 0;
  const seatsFree = Math.max(0, seatsPurchased - seatsUsed);

  async function add() {
    const value = email.trim();
    // Mirror the button's disabled state: with no free seats the server would 400, so don't
    // even attempt the round-trip (the Enter-key path would otherwise bypass the button guard).
    if (value.length < 3 || adding || seatsFree === 0) return;
    setAdding(true);
    setError(null);
    try {
      // Await the real assign; re-render from the returned org (roster + seat count are the
      // server's truth), then clear the input.
      onUpdated(await api.addOrgMember(value));
      setEmail('');
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : 'Could not add that member. Try again.',
      );
    } finally {
      setAdding(false);
    }
  }

  async function remove(userId: string) {
    if (removingId) return;
    setRemovingId(userId);
    setError(null);
    try {
      onUpdated(await api.removeOrgMember(userId));
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : 'Could not remove that member. Try again.',
      );
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Members</h2>
        <span className="text-sm text-slate-400">
          <span className="font-semibold text-slate-100">{seatsUsed}</span> of{' '}
          <span className="font-semibold text-slate-100">{seatsPurchased}</span> seats used
        </span>
      </div>

      <div className="mt-4 flex gap-2">
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="teammate@company.com"
          type="email"
          maxLength={255}
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
          aria-label="Teammate email to assign a seat"
          onKeyDown={(e) => e.key === 'Enter' && add()}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
        />
        <Button onClick={add} disabled={adding || email.trim().length < 3 || seatsFree === 0}>
          {adding ? 'Adding…' : 'Add member'}
        </Button>
      </div>
      {seatsFree === 0 && seatsPurchased > 0 && (
        <p className="mt-2 text-xs text-slate-500">
          All seats are assigned. Buy more seats above to add teammates.
        </p>
      )}
      <ErrorText>{error}</ErrorText>

      {members.length > 0 ? (
        <ul className="mt-4 divide-y divide-slate-800 rounded-lg border border-slate-800">
          {members.map((m) => (
            <li key={m.user_id} className="flex items-center justify-between gap-3 px-4 py-3">
              <span className="min-w-0 truncate text-sm text-slate-200">
                {m.email ?? '(unknown account)'}
              </span>
              <button
                onClick={() => remove(m.user_id)}
                disabled={removingId !== null}
                className="shrink-0 rounded text-xs text-red-400 hover:text-red-300 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
              >
                {removingId === m.user_id ? 'Removing…' : 'Remove'}
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm text-slate-500">
          No members yet — assign a seat by email above.
        </p>
      )}
    </Card>
  );
}

function OwnerView({
  org,
  onUpdated,
  checkoutNotice,
}: {
  org: Organization;
  onUpdated: (org: Organization) => void;
  checkoutNotice: string | null;
}) {
  const active = org.active && (org.seats_purchased || 0) > 0;
  return (
    <div className="space-y-6">
      <Card>
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Team</h2>
            <p className="mt-2 truncate text-lg font-semibold text-slate-100">{org.name}</p>
          </div>
          {active ? (
            <span className="shrink-0 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
              Active
            </span>
          ) : (
            <span className="shrink-0 rounded-full border border-slate-600 bg-slate-800/60 px-3 py-1 text-xs font-semibold text-slate-400">
              No seats yet
            </span>
          )}
        </div>
      </Card>

      {checkoutNotice && (
        <p role="status" className="text-sm text-emerald-400">
          {checkoutNotice}
        </p>
      )}

      <BuySeatsCard org={org} />
      {active && <MembersCard org={org} onUpdated={onUpdated} />}
    </div>
  );
}

function MemberView({ org }: { org: Organization }) {
  return (
    <Card>
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Your team</h2>
      <p className="mt-2 text-lg font-semibold text-slate-100">{org.name}</p>
      <p className="mt-2 text-sm text-slate-300">
        You have a Pro seat on this team — all Pro features are unlocked on your account. Your
        team’s owner manages seats and billing. To leave the team, contact your team owner.
      </p>
    </Card>
  );
}

export default function TeamPage() {
  const { user } = useAuth();
  // undefined = still loading; null = loaded, no org; Organization = loaded org.
  const [org, setOrg] = useState<Organization | null | undefined>(undefined);
  const [loadError, setLoadError] = useState(false);

  // Surface the Stripe redirect outcome honestly. Seats are granted by the async webhook, so a
  // "success" return may briefly precede the seat count updating — say so rather than imply the
  // seats are already live. Read once from the URL: the /app layout renders a loading fallback
  // until auth restores from localStorage, so this page only ever mounts client-side (window is
  // defined) — a lazy initializer avoids an effect + a hydration mismatch.
  const [checkoutNotice] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null;
    const checkout = new URLSearchParams(window.location.search).get('checkout');
    if (checkout === 'success') {
      return 'Payment received. Your seats activate within a moment — reload if the count hasn’t updated.';
    }
    if (checkout === 'cancel') return 'Checkout cancelled — no charge was made.';
    return null;
  });

  const load = useCallback(async () => {
    setLoadError(false);
    setOrg(undefined);
    try {
      setOrg(await api.getOrg());
    } catch {
      setLoadError(true);
    }
  }, []);

  useEffect(() => {
    // load() setStates asynchronously after the fetch resolves, not synchronously.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  function retry() {
    void load();
  }

  // The app layout guards for an authenticated user; render nothing during the brief restore.
  if (!user) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Team</h1>
        <p className="mt-1 text-sm text-slate-400">
          Buy Pro seats in bulk and manage your teammates.
        </p>
      </div>

      {loadError ? (
        <Card>
          <p className="text-sm text-slate-400">Could not load your team right now.</p>
          <div className="mt-4">
            <Button onClick={retry}>Retry</Button>
          </div>
        </Card>
      ) : org === undefined ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-800/60" aria-hidden="true" />
      ) : org === null ? (
        <OrgNameCard onCreated={setOrg} />
      ) : org.is_owner ? (
        <OwnerView org={org} onUpdated={setOrg} checkoutNotice={checkoutNotice} />
      ) : (
        <MemberView org={org} />
      )}

      <p className="text-center text-xs text-slate-500">
        Prefer an individual plan?{' '}
        <Link
          href="/pricing"
          className="rounded text-indigo-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
        >
          See Pro &amp; Career+
        </Link>
      </p>
    </div>
  );
}
