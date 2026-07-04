'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuth } from '@/lib/auth';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, signOut } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace('/login');
  }, [loading, user, router]);

  if (loading || !user) {
    return <div className="flex flex-1 items-center justify-center text-slate-400">Loading…</div>;
  }

  return (
    <div className="flex min-h-full flex-col">
      <header className="border-b border-slate-800">
        <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-6 py-4">
          <div className="flex items-center gap-4 sm:gap-6">
            <Link href="/app" className="rounded font-bold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Career Operator</Link>
            <nav className="flex gap-3 text-sm text-slate-400 sm:gap-4">
              <Link href="/app" className="rounded hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Pipeline</Link>
              <Link href="/app/insights" className="rounded hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Skill gaps</Link>
              <Link href="/app/coach" className="rounded hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Coach</Link>
              {user.tier !== 'premium' && (
                <Link href="/pricing" className="rounded hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Upgrade</Link>
              )}
              <Link href="/app/settings" className="rounded hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Settings</Link>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm">
            {/* The account email is identity, not navigation — hide it on phones (where it
                would otherwise overflow into the nav) and truncate it on larger screens. */}
            <span className="hidden max-w-[180px] truncate text-slate-400 sm:block md:max-w-[260px]">{user.email}</span>
            <button onClick={signOut} className="rounded-lg border border-slate-700 px-3 py-1.5 hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950">
              Log out
            </button>
          </div>
        </div>
      </header>
      <div className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">{children}</div>
    </div>
  );
}
