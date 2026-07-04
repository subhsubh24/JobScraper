'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { Button, Card, ErrorText, Skeleton } from '@/components/ui';
import { Markdown } from '@/components/markdown';
import { ArtifactActions } from '@/components/artifact-actions';
import { AiConsentCard, hasAiConsent } from '@/components/ai-consent';
import { api, ApiError, type SkillGapAnalysis, type SkillStat } from '@/lib/api';
import { useAuth } from '@/lib/auth';

// Cross-pipeline skill-gap heatmap (free, computed locally on the server) + an AI learning plan
// (Pro). The heatmap is the retention hook: it looks across the user's WHOLE pipeline and shows
// which recurring skills their tracked jobs demand that their résumé is missing — something a
// single per-job fit score can't. The learning plan turns the top gaps into a prioritised plan.

export default function InsightsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const isPremium = user?.tier === 'premium';

  const [analysis, setAnalysis] = useState<SkillGapAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [plan, setPlan] = useState<{ title: string; content: string } | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [planMsg, setPlanMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setAnalysis(await api.skillGaps());
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load your skill gaps.');
    } finally {
      setLoading(false);
    }
  }, []);

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

  async function generatePlan() {
    setPlanLoading(true);
    setPlanMsg(null);
    setPlan(null);
    try {
      const result = await api.generateLearningPlan();
      setPlan(result);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        // 403 here is the tier gate (consent is obtained before this button renders).
        router.push('/pricing');
        return;
      }
      // 400 (no jobs / no résumé / no gaps) and 503 (no key) carry an honest, actionable message.
      setPlanMsg(e instanceof ApiError ? e.message : 'Could not generate a learning plan — try again.');
    } finally {
      setPlanLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-extrabold text-slate-100">Skill gaps</h1>
        <p className="mt-1 text-sm text-slate-400">
          Across every job you&rsquo;re tracking — the skills they demand most that your résumé is
          missing, ranked by how often they come up.
        </p>
      </header>

      {loading ? (
        <Card className="space-y-3">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-11/12" />
          <Skeleton className="h-8 w-4/5" />
        </Card>
      ) : error ? (
        <Card>
          <ErrorText>{error}</ErrorText>
          <div className="mt-4">
            <Button onClick={retry}>Retry</Button>
          </div>
        </Card>
      ) : analysis && analysis.total_jobs === 0 ? (
        <Card className="text-center">
          <p className="text-slate-300">Track a few jobs to see your cross-pipeline skill gaps.</p>
          <p className="mt-1 text-sm text-slate-500">
            Your gaps are computed from the skills your saved jobs ask for.
          </p>
          <div className="mt-4">
            <Link href="/app" className="text-indigo-400 hover:text-indigo-300">
              Go to your pipeline →
            </Link>
          </div>
        </Card>
      ) : analysis ? (
        <>
          {!analysis.has_resume && (
            <Card className="border-amber-500/30 bg-amber-500/5">
              <p className="text-sm text-amber-200/90">
                Add your résumé in{' '}
                <Link href="/app/settings" className="underline hover:text-amber-100">
                  Settings
                </Link>{' '}
                to see which of these skills you already cover — right now every demanded skill
                shows as a gap.
              </p>
            </Card>
          )}

          <GapHeatmap gaps={analysis.gaps} />

          {analysis.strengths.length > 0 && <Strengths strengths={analysis.strengths} />}

          <LearningPlanSection
            isPremium={isPremium}
            hasConsent={hasAiConsent(user)}
            hasGaps={analysis.gaps.length > 0}
            plan={plan}
            planLoading={planLoading}
            planMsg={planMsg}
            onGenerate={generatePlan}
            onUpgrade={() => router.push('/pricing')}
          />
        </>
      ) : null}
    </div>
  );
}

function GapHeatmap({ gaps }: { gaps: SkillStat[] }) {
  if (gaps.length === 0) {
    return (
      <Card>
        <p className="text-slate-300">
          No skill gaps — your résumé already covers the skills your tracked jobs demand. Nice.
        </p>
      </Card>
    );
  }
  return (
    <Card className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
        Your top gaps
      </h2>
      <ul className="space-y-2.5">
        {gaps.map((g) => (
          <GapRow key={g.skill} stat={g} />
        ))}
      </ul>
    </Card>
  );
}

// One skill row: the name over a bar whose width encodes how much of the pipeline demands it.
// The bar IS the data (not decoration) — most-demanded gaps read first, strongest bar first.
function GapRow({ stat }: { stat: SkillStat }) {
  const pct = Math.round(stat.coverage * 100);
  return (
    <li>
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-medium capitalize text-slate-100">{stat.skill}</span>
        <span className="shrink-0 text-xs text-slate-500">
          {stat.job_count} of {stat.total_jobs} {stat.total_jobs === 1 ? 'job' : 'jobs'}
        </span>
      </div>
      <div
        className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-800"
        role="img"
        aria-label={`${stat.skill}: demanded by ${stat.job_count} of ${stat.total_jobs} tracked jobs`}
      >
        <div
          className="h-full rounded-full bg-indigo-500"
          style={{ width: `${Math.max(pct, 6)}%` }}
        />
      </div>
    </li>
  );
}

function Strengths({ strengths }: { strengths: SkillStat[] }) {
  return (
    <Card className="space-y-2">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
        Skills you already have
      </h2>
      <div className="flex flex-wrap gap-2">
        {strengths.map((s) => (
          <span
            key={s.skill}
            className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-sm capitalize text-emerald-200"
          >
            {s.skill}
            <span className="text-xs text-emerald-400/70">×{s.job_count}</span>
          </span>
        ))}
      </div>
    </Card>
  );
}

function LearningPlanSection({
  isPremium,
  hasConsent,
  hasGaps,
  plan,
  planLoading,
  planMsg,
  onGenerate,
  onUpgrade,
}: {
  isPremium: boolean;
  hasConsent: boolean;
  hasGaps: boolean;
  plan: { title: string; content: string } | null;
  planLoading: boolean;
  planMsg: string | null;
  onGenerate: () => void;
  onUpgrade: () => void;
}) {
  if (!hasGaps) return null;

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-slate-100">Turn your gaps into a plan</h2>
        <p className="mt-1 text-sm text-slate-400">
          A prioritised, week-by-week learning plan for your top gaps — what to learn, in what
          order, with realistic time estimates.
        </p>
      </div>

      {!isPremium ? (
        <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/5 p-4">
          <p className="text-sm text-slate-300">
            AI learning plans are a <span className="font-semibold text-indigo-300">Pro</span>{' '}
            feature.
          </p>
          <div className="mt-3">
            <Button onClick={onUpgrade}>Upgrade to Pro</Button>
          </div>
        </div>
      ) : !hasConsent ? (
        // Premium but not yet consented: the plan sends skill/role text to the third-party AI, so
        // require explicit consent first (Apple 5.1.2(i)) rather than dead-ending on a 403.
        <AiConsentCard />
      ) : (
        <>
          <Button onClick={onGenerate} disabled={planLoading}>
            {planLoading ? 'Generating…' : plan ? 'Regenerate plan' : 'Generate learning plan'}
          </Button>
          {planMsg && <ErrorText>{planMsg}</ErrorText>}
          {planLoading && (
            <div className="space-y-2">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-11/12" />
              <Skeleton className="h-4 w-4/5" />
            </div>
          )}
          {plan && !planLoading && (
            <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
              <Markdown content={plan.content} />
              <ArtifactActions text={plan.content} filename="learning-plan" />
            </div>
          )}
        </>
      )}
    </Card>
  );
}
