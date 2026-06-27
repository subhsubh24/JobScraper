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
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-6">
            <Link href="/app" className="font-bold">Career Operator</Link>
            <nav className="flex gap-4 text-sm text-slate-400">
              <Link href="/app" className="hover:text-slate-100">Pipeline</Link>
              <Link href="/app/coach" className="hover:text-slate-100">Coach</Link>
              <Link href="/pricing" className="hover:text-slate-100">Upgrade</Link>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-400">{user.email}</span>
            <button onClick={signOut} className="rounded-lg border border-slate-700 px-3 py-1.5 hover:bg-slate-800">
              Log out
            </button>
          </div>
        </div>
      </header>
      <div className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">{children}</div>
    </div>
  );
}
