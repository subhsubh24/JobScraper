'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { Button, Card, ErrorText, Skeleton } from '@/components/ui';
import { ReportButton } from '@/components/report-button';
import { AiConsentCard, hasAiConsent } from '@/components/ai-consent';
import {
  api,
  ApiError,
  type MockInterviewAnswer,
  type MockInterviewSession,
  type MockInterviewSummary,
} from '@/lib/api';
import { useAuth } from '@/lib/auth';
import type { Job } from '@/lib/types';

// The interview-coaching pillar (north-star surface 3): a realistic, role-specific mock interview.
// The coach asks JD-derived questions one at a time; the user answers; each answer is scored
// (relevance / specificity / STAR) with concrete feedback + a model answer. Honest by design — a
// weak answer scores low; the score is the server's, shown only after the real POST resolves.

export default function MockInterviewPage() {
  const params = useParams<{ id: string }>();
  const jobId = params.id;
  const router = useRouter();
  const { user } = useAuth();
  const isPaid = user?.tier === 'premium';
  const consented = hasAiConsent(user);

  const [job, setJob] = useState<Job | null>(null);
  const [sessions, setSessions] = useState<MockInterviewSummary[]>([]);
  const [interview, setInterview] = useState<MockInterviewSession | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [starting, setStarting] = useState(false);
  const [startMsg, setStartMsg] = useState<string | null>(null);
  const [numQuestions, setNumQuestions] = useState(5);

  const load = useCallback(async () => {
    try {
      const [j, list] = await Promise.all([api.getJob(jobId), api.listMockInterviews(jobId)]);
      setJob(j);
      setSessions(list);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load this interview.');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    // load() setStates asynchronously after the fetch resolves, not synchronously.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  function retry() {
    setLoading(true);
    setError(null);
    void load();
  }

  async function start() {
    setStartMsg(null);
    setStarting(true);
    try {
      const iv = await api.startMockInterview(jobId, numQuestions);
      setInterview(iv);
      setActiveIndex(0);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        // Tier gate (consent is handled by the AiConsentCard before this button renders).
        router.push('/pricing');
        return;
      }
      setStartMsg(e instanceof ApiError ? e.message : 'Could not start the interview — try again.');
    } finally {
      setStarting(false);
    }
  }

  async function openSession(interviewId: string) {
    setStartMsg(null);
    try {
      const iv = await api.getMockInterview(interviewId);
      setInterview(iv);
      // Jump to the first unanswered question, or the last one if the session is complete.
      const answered = new Set(iv.answers.map((a) => a.question_index));
      const firstUnanswered = iv.questions.findIndex((_q, i) => !answered.has(i));
      setActiveIndex(firstUnanswered === -1 ? Math.max(iv.questions.length - 1, 0) : firstUnanswered);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        router.push('/pricing');
        return;
      }
      setStartMsg(e instanceof ApiError ? e.message : 'Could not open that session.');
    }
  }

  function exitSession() {
    setInterview(null);
    void load(); // refresh the session list (status may have advanced)
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-6 w-56" />
        <Card className="space-y-3">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-24 w-full" />
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <ErrorText>{error}</ErrorText>
        <div className="mt-4">
          <Button onClick={retry}>Retry</Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <Link href={`/app/jobs/${jobId}`} className="text-sm text-indigo-400 hover:text-indigo-300">
          ← Back to job
        </Link>
        <h1 className="text-2xl font-extrabold text-slate-100">Mock interview</h1>
        {job && (
          <p className="text-sm text-slate-400">
            {job.title}
            {job.company ? ` · ${job.company}` : ''}
          </p>
        )}
      </header>

      {interview ? (
        <InterviewRunner
          interview={interview}
          activeIndex={activeIndex}
          onSetActiveIndex={setActiveIndex}
          onUpdate={setInterview}
          onExit={exitSession}
        />
      ) : (
        <StartScreen
          isPaid={isPaid}
          consented={consented}
          sessions={sessions}
          numQuestions={numQuestions}
          starting={starting}
          startMsg={startMsg}
          onSetNumQuestions={setNumQuestions}
          onStart={start}
          onOpen={openSession}
          onUpgrade={() => router.push('/pricing')}
        />
      )}
    </div>
  );
}

function StartScreen({
  isPaid,
  consented,
  sessions,
  numQuestions,
  starting,
  startMsg,
  onSetNumQuestions,
  onStart,
  onOpen,
  onUpgrade,
}: {
  isPaid: boolean;
  consented: boolean;
  sessions: MockInterviewSummary[];
  numQuestions: number;
  starting: boolean;
  startMsg: string | null;
  onSetNumQuestions: (n: number) => void;
  onStart: () => void;
  onOpen: (id: string) => void;
  onUpgrade: () => void;
}) {
  return (
    <div className="space-y-6">
      <Card className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100">Practice for this role</h2>
          <p className="mt-1 text-sm text-slate-400">
            The coach asks questions drawn from this job, one at a time. Answer in your own words and
            get scored feedback — relevance, specificity, and structure — plus a model answer.
          </p>
        </div>

        {!isPaid ? (
          <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/5 p-4">
            <p className="text-sm text-slate-300">
              Mock interviews are a <span className="font-semibold text-indigo-300">Pro</span>{' '}
              feature.
            </p>
            <div className="mt-3">
              <Button onClick={onUpgrade}>Upgrade to Pro</Button>
            </div>
          </div>
        ) : !consented ? (
          // Premium but not yet consented: the interview sends the JD + answers to the third-party
          // AI, so require explicit consent first (Apple 5.1.2(i)) rather than dead-ending on a 403.
          <AiConsentCard />
        ) : (
          <div className="space-y-3">
            <label className="block text-sm text-slate-400">
              <span className="mb-1 block">Number of questions</span>
              <select
                value={numQuestions}
                onChange={(e) => onSetNumQuestions(Number(e.target.value))}
                className="rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-slate-100 outline-none focus:border-indigo-500"
              >
                {[3, 4, 5, 6, 7, 8].map((n) => (
                  <option key={n} value={n}>
                    {n} questions
                  </option>
                ))}
              </select>
            </label>
            <Button onClick={onStart} disabled={starting}>
              {starting ? 'Preparing your questions…' : 'Start mock interview'}
            </Button>
            {startMsg && <ErrorText>{startMsg}</ErrorText>}
          </div>
        )}
      </Card>

      {sessions.length > 0 && (
        <Card className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Your past sessions
          </h2>
          <ul className="space-y-2">
            {sessions.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => onOpen(s.id)}
                  className="flex w-full items-center justify-between rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-3 text-left hover:border-indigo-500/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
                >
                  <span className="text-sm text-slate-200">
                    {s.status === 'completed' ? 'Completed' : 'In progress'} · {s.answered_count}/
                    {s.total} answered
                  </span>
                  <span className="text-xs text-indigo-400">
                    {s.status === 'completed' ? 'Review →' : 'Resume →'}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

function InterviewRunner({
  interview,
  activeIndex,
  onSetActiveIndex,
  onUpdate,
  onExit,
}: {
  interview: MockInterviewSession;
  activeIndex: number;
  onSetActiveIndex: (i: number) => void;
  onUpdate: (iv: MockInterviewSession) => void;
  onExit: () => void;
}) {
  const router = useRouter();
  const [answer, setAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [reAnswer, setReAnswer] = useState(false);

  const total = interview.questions.length;
  const question = interview.questions[activeIndex];
  const scored = interview.answers.find((a) => a.question_index === activeIndex) ?? null;
  const answeredCount = interview.answers.length;

  // Reset the local draft state whenever the active question changes.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAnswer('');
    setMsg(null);
    setReAnswer(false);
  }, [activeIndex]);

  async function submit() {
    if (!answer.trim()) {
      setMsg('Type your answer first.');
      return;
    }
    setMsg(null);
    setSubmitting(true);
    try {
      const submitted = answer.trim();
      const res = await api.answerMockInterview(interview.id, activeIndex, submitted);
      // Merge the scored result into the session (overwrite any prior answer at this index). The
      // POST result echoes the scores but not the answer text; carry the answer we just submitted
      // so the in-memory entry is complete and type-accurate (GET returns it on reload).
      const scoredEntry: MockInterviewAnswer = { ...res.result, answer: submitted };
      const next: MockInterviewSession = {
        ...interview,
        status: res.status,
        answers: [
          ...interview.answers.filter((a) => a.question_index !== activeIndex),
          scoredEntry,
        ].sort((a, b) => a.question_index - b.question_index),
        answered_count: res.answered_count,
      };
      onUpdate(next);
      setReAnswer(false);
    } catch (e) {
      // Server is the source of truth: a 403 mid-session (Pro lapsed / consent revoked elsewhere)
      // routes to pricing, never traps the user with an inline-only error and no way forward.
      if (e instanceof ApiError && e.status === 403) {
        router.push('/pricing');
        return;
      }
      setMsg(e instanceof ApiError ? e.message : 'Could not score your answer — try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (!question) return null;

  return (
    <div className="space-y-5">
      <ProgressBar answered={answeredCount} total={total} completed={interview.status === 'completed'} />

      <Card className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs font-semibold uppercase tracking-wide text-indigo-400">
            {question.category === 'technical' ? 'Technical' : 'Behavioral'} · Question{' '}
            {activeIndex + 1} of {total}
          </span>
        </div>
        <p className="text-lg font-medium text-slate-100">{question.question}</p>

        {scored && !reAnswer ? (
          <ScoreResult
            scored={scored}
            contentRef={`${interview.id}:${activeIndex}`}
            onPracticeAgain={() => setReAnswer(true)}
          />
        ) : (
          <div className="space-y-3">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={6}
              maxLength={8000}
              aria-label="Your answer"
              placeholder="Answer in your own words — be specific, use a real example."
              className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-slate-100 outline-none focus:border-indigo-500"
            />
            <div className="flex items-center gap-3">
              <Button onClick={submit} disabled={submitting}>
                {submitting ? 'Scoring…' : scored ? 'Re-submit answer' : 'Submit answer'}
              </Button>
              {scored && (
                <button
                  type="button"
                  onClick={() => setReAnswer(false)}
                  className="rounded text-sm text-slate-400 hover:text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
                >
                  Cancel
                </button>
              )}
            </div>
            {msg && <ErrorText>{msg}</ErrorText>}
          </div>
        )}
      </Card>

      <div className="flex items-center justify-between">
        <Button
          variant="secondary"
          onClick={() => onSetActiveIndex(Math.max(activeIndex - 1, 0))}
          disabled={activeIndex === 0}
        >
          ← Previous
        </Button>
        {activeIndex < total - 1 ? (
          <Button variant="secondary" onClick={() => onSetActiveIndex(activeIndex + 1)}>
            Next →
          </Button>
        ) : (
          <Button variant="secondary" onClick={onExit}>
            Done
          </Button>
        )}
      </div>
    </div>
  );
}

function ProgressBar({
  answered,
  total,
  completed,
}: {
  answered: number;
  total: number;
  completed: boolean;
}) {
  const pct = total > 0 ? Math.round((answered / total) * 100) : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>
          {completed ? 'Interview complete' : `${answered} of ${total} answered`}
        </span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800" role="img" aria-label={`${pct}% complete`}>
        <div
          className={`h-full rounded-full ${completed ? 'bg-emerald-500' : 'bg-indigo-500'}`}
          style={{ width: `${Math.max(pct, 4)}%` }}
        />
      </div>
    </div>
  );
}

function ScoreResult({
  scored,
  contentRef,
  onPracticeAgain,
}: {
  scored: MockInterviewAnswer;
  contentRef: string;
  onPracticeAgain: () => void;
}) {
  return (
    <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm font-semibold text-slate-300">Your answer scored</span>
        <span className="text-2xl font-extrabold text-slate-100">
          {Math.round(scored.overall)}
          <span className="text-sm font-medium text-slate-500">/100</span>
        </span>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <ScoreBar label="Relevance" value={scored.relevance} />
        <ScoreBar label="Specificity" value={scored.specificity} />
        <ScoreBar label="Structure" value={scored.star} />
      </div>
      <div>
        <h4 className="text-sm font-semibold text-slate-200">Feedback</h4>
        <p className="mt-1 whitespace-pre-line text-sm text-slate-300">{scored.feedback}</p>
      </div>
      {scored.model_answer && (
        <div>
          <h4 className="text-sm font-semibold text-slate-200">A strong answer</h4>
          <p className="mt-1 whitespace-pre-line text-sm text-slate-400">{scored.model_answer}</p>
        </div>
      )}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onPracticeAgain}
          className="rounded text-sm text-indigo-400 hover:text-indigo-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
        >
          Practice this answer again
        </button>
        <ReportButton
          contentType="mock_interview"
          contentRef={contentRef}
          contentExcerpt={`${scored.feedback}\n\n${scored.model_answer}`}
        />
      </div>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round((Math.max(0, Math.min(value, 5)) / 5) * 100);
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-xs text-slate-400">{label}</span>
        <span className="text-xs font-semibold text-slate-300">{value}/5</span>
      </div>
      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
        <div className="h-full rounded-full bg-indigo-500" style={{ width: `${Math.max(pct, 4)}%` }} />
      </div>
    </div>
  );
}
