'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { Button, Card } from '@/components/ui';
import { api, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';

interface Msg {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

// Stable per-conversation id used to thread multi-turn context server-side. Uses the
// browser crypto UUID where available (secure context / localhost) with a safe fallback.
function newSessionId(): string {
  const c = typeof globalThis !== 'undefined' ? (globalThis.crypto as Crypto | undefined) : undefined;
  if (c?.randomUUID) return c.randomUUID();
  return `s-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export default function CoachPage() {
  const { user } = useAuth();
  const router = useRouter();
  const isPremium = user?.tier === 'premium';
  const [messages, setMessages] = useState<Msg[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const counter = useRef(0);
  const endRef = useRef<HTMLDivElement>(null);
  // One stable session id for this conversation so the coach can thread multi-turn context.
  // Created once and never re-generated on re-render (ref, not state).
  const sessionId = useRef<string>(newSessionId());

  useEffect(() => {
    api.coachSuggestions().then(setSuggestions).catch(() => setSuggestions([]));
  }, []);

  // Keep the latest message / typing indicator in view as the conversation grows — without
  // this the user has to manually scroll to see each new reply (broken chat UX on long threads).
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, sending]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setError(null);
    setInput('');
    setMessages((m) => [...m, { id: `u${counter.current++}`, role: 'user', content: trimmed }]);
    setSending(true);
    try {
      const reply = await api.coachChat(trimmed, sessionId.current);
      setMessages((m) => [...m, { id: `a${counter.current++}`, role: 'assistant', content: reply }]);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Coach is unavailable.');
    } finally {
      setSending(false);
    }
  }

  if (!isPremium) {
    return (
      <Card className="mx-auto max-w-lg text-center">
        <h1 className="text-2xl font-extrabold">Your AI Career Coach</h1>
        <p className="mt-2 text-slate-400">
          On-demand advice on strategy, interviews, and salary negotiation. The Coach is a
          Premium feature.
        </p>
        <div className="mt-5">
          <Button onClick={() => router.push('/pricing')}>Upgrade to unlock</Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold">AI Career Coach</h1>
      {messages.length === 0 && (
        <div className="space-y-2">
          <p className="text-sm text-slate-400">Ask anything about your search:</p>
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="block w-full rounded-lg border border-slate-700 bg-slate-900/60 p-3 text-left hover:bg-slate-800"
            >
              {s}
            </button>
          ))}
        </div>
      )}
      <div className="space-y-3">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`max-w-[85%] rounded-2xl p-3 ${
              m.role === 'user' ? 'ml-auto bg-indigo-500 text-white' : 'bg-slate-900/60 border border-slate-800'
            }`}
          >
            <p className="whitespace-pre-wrap">{m.content}</p>
          </div>
        ))}
        {sending && (
          <div
            className="max-w-[85%] rounded-2xl border border-slate-800 bg-slate-900/60 p-3"
            aria-live="polite"
          >
            <span className="sr-only">Coach is typing…</span>
            <span aria-hidden="true" className="inline-flex gap-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.3s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.15s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500" />
            </span>
          </div>
        )}
        <div ref={endRef} />
      </div>
      {error && (
        <p className="text-sm text-red-400" role="alert">
          {error}
        </p>
      )}
      <form
        onSubmit={(e) => { e.preventDefault(); send(input); }}
        className="flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={sending}
          aria-label="Message to your AI career coach"
          placeholder="Type a message…"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 outline-none focus:border-indigo-500 disabled:opacity-50"
        />
        <Button type="submit" disabled={sending}>{sending ? 'Sending…' : 'Send'}</Button>
      </form>
    </div>
  );
}
