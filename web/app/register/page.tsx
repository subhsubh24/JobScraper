'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Button, Card, ErrorText, Field } from '@/components/ui';
import { api, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';

export default function RegisterPage() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [resume, setResume] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
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
        }),
      );
      router.push('/app');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
      <h1 className="mb-1 text-3xl font-extrabold">Create your account</h1>
      <p className="mb-6 text-slate-400">Free to start — 5 tracked jobs and a prep pack on us.</p>
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
          <ErrorText>{error}</ErrorText>
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Creating…' : 'Create account'}
          </Button>
        </form>
      </Card>
      <p className="mt-5 text-center text-sm text-slate-400">
        Already have an account?{' '}
        <Link href="/login" className="font-semibold text-indigo-400">Log in</Link>
      </p>
    </main>
  );
}
