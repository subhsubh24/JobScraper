'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Button, Card, ErrorText, Field } from '@/components/ui';
import { Turnstile, captchaConfigured } from '@/components/turnstile';
import { api, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (captchaConfigured && !captchaToken) {
      setError('Please complete the captcha.');
      return;
    }
    setLoading(true);
    try {
      setUser(await api.login(email.trim(), password, captchaToken ?? undefined));
      router.push('/app');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
      <h1 className="mb-1 text-3xl font-extrabold">Welcome back</h1>
      <p className="mb-6 text-slate-400">Log in to your Career Operator account.</p>
      <Card>
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Field label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <Turnstile onToken={setCaptchaToken} />
          <ErrorText>{error}</ErrorText>
          <Button type="submit" disabled={loading || (captchaConfigured && !captchaToken)} className="w-full">
            {loading ? 'Logging in…' : 'Log in'}
          </Button>
        </form>
      </Card>
      <p className="mt-5 text-center text-sm text-slate-400">
        New here?{' '}
        <Link href="/register" className="rounded font-semibold text-indigo-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400">Create an account</Link>
      </p>
    </main>
  );
}
