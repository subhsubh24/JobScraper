'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Button, Card, ErrorText, Field } from '@/components/ui';
import { Turnstile, captchaConfigured } from '@/components/turnstile';
import { api, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';

// Where to send the user after signup. Honors a ?next=/path param (e.g. coming from the
// pricing upgrade flow) but ONLY for internal paths — an open-redirect guard rejects
// absolute URLs and protocol-relative ("//evil.com") targets.
function postSignupPath(): string {
  if (typeof window === 'undefined') return '/app';
  const next = new URLSearchParams(window.location.search).get('next');
  if (next && next.startsWith('/') && !next.startsWith('//')) return next;
  return '/app';
}

// A referral code arrives as ?ref=CODE on a shared invite link. Captured here and sent with
// signup so the inviter gets credited; a missing/invalid code is harmless (server no-ops it).
function referralCode(): string | undefined {
  if (typeof window === 'undefined') return undefined;
  const ref = new URLSearchParams(window.location.search).get('ref');
  return ref ? ref.trim().slice(0, 32) : undefined;
}

export default function RegisterPage() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [resume, setResume] = useState('');
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  // Read the referral code once at mount (not at submit) so we can both acknowledge the
  // invite in the copy AND send it with signup — and so the URL can't change underneath us.
  // The value is window-only, so it must be read after mount (avoids an SSR hydration
  // mismatch); the post-mount setState is intentional.
  const [ref, setRef] = useState<string | undefined>(undefined);
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setRef(referralCode()), []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (captchaConfigured && !captchaToken) {
      setError('Please complete the captcha.');
      return;
    }
    setLoading(true);
    try {
      setUser(
        await api.register({
          email: email.trim(),
          password,
          full_name: fullName.trim() || undefined,
          resume_text: resume.trim() || undefined,
          referral_code: ref,
          captcha_token: captchaToken ?? undefined,
        }),
      );
      router.push(postSignupPath());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
      <h1 className="mb-1 text-3xl font-extrabold">Create your account</h1>
      {ref ? (
        <p className="mb-6 text-slate-300">
          A friend invited you — sign up and you <span className="font-semibold text-slate-100">both</span> get
          a bonus interview prep pack.
        </p>
      ) : (
        <p className="mb-6 text-slate-400">Free to start — 5 tracked jobs and a prep pack on us.</p>
      )}
      <Card>
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <Field label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Field label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <label className="block">
            <span className="mb-1 block text-sm text-slate-400">Paste your resume (optional — powers fit scoring)</span>
            <textarea
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              rows={4}
              className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-slate-100 outline-none focus:border-indigo-500"
            />
          </label>
          <Turnstile onToken={setCaptchaToken} />
          <ErrorText>{error}</ErrorText>
          <Button type="submit" disabled={loading || (captchaConfigured && !captchaToken)} className="w-full">
            {loading ? 'Creating…' : 'Create account'}
          </Button>
        </form>
      </Card>
      <p className="mt-5 text-center text-sm text-slate-400">
        Already have an account?{' '}
        <Link href="/login" className="rounded font-semibold text-indigo-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Log in</Link>
      </p>
    </main>
  );
}
