import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, EmptyState, ErrorBanner } from '@/components/ui';
import { Markdown } from '@/components/markdown';
import { ArtifactActions } from '@/components/artifact-actions';
import { AiConsentCard, hasAiConsent } from '@/components/ai-consent';
import { useAuth } from '@/contexts/auth';
import { api, ApiError, type SkillGapAnalysis, type SkillStat } from '@/services/api';
import { colors, radius, spacing } from '@/theme';

// Cross-pipeline skill-gap heatmap (free, computed locally on the server) + an AI learning plan
// (Pro). Looks across the user's WHOLE pipeline: which recurring skills their tracked jobs demand
// that their résumé is missing — the retention/planning surface a single fit score can't give.
export default function InsightsScreen() {
  const { user } = useAuth();
  const isPremium = user?.tier === 'premium';

  const [analysis, setAnalysis] = useState<SkillGapAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [plan, setPlan] = useState<{ title: string; content: string } | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [planMsg, setPlanMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setAnalysis(await api.skillGaps());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load your skill gaps.');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  async function generatePlan() {
    setPlanLoading(true);
    setPlanMsg(null);
    // Do NOT clear the existing plan up front: a transient failure (5xx / rate limit) would
    // otherwise silently DESTROY the user's already-generated plan, which is session-only
    // (never persisted server-side). The render already hides it while `planLoading` is true,
    // so keeping it means a failed REGENERATE leaves the prior plan intact — matching the
    // house pattern in job/[id].tsx generateStudyPlan (which never pre-clears its result).
    try {
      setPlan(await api.generateLearningPlan());
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        // 403 here is the tier gate (consent is obtained before this button renders).
        router.push('/paywall');
        return;
      }
      setPlanMsg(e instanceof ApiError ? e.message : 'Could not generate a learning plan — try again.');
    } finally {
      setPlanLoading(false);
    }
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.center} edges={['top']}>
        <ActivityIndicator color={colors.primary} />
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.flex} edges={['top']}>
        <ErrorBanner message={error} onRetry={() => { setLoading(true); void load(); }} />
      </SafeAreaView>
    );
  }

  if (analysis && analysis.total_jobs === 0) {
    return (
      <SafeAreaView style={styles.flex} edges={['top']}>
        <EmptyState
          title="Track a few jobs first"
          subtitle="Your skill gaps are computed from the skills your saved jobs ask for."
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Skill gaps</Text>
        <Text style={styles.subtitle}>
          Across every job you&rsquo;re tracking — the skills they demand most that your résumé is
          missing, ranked by how often they come up.
        </Text>

        {analysis && !analysis.has_resume ? (
          <Card style={styles.notice}>
            <Text style={styles.noticeText}>
              Add your résumé in Settings to see which of these skills you already cover — right
              now every demanded skill shows as a gap.
            </Text>
          </Card>
        ) : null}

        {analysis && analysis.gaps.length > 0 ? (
          <Card style={styles.section}>
            <Text style={styles.sectionTitle}>YOUR TOP GAPS</Text>
            {analysis.gaps.map((g) => (
              <GapRow key={g.skill} stat={g} />
            ))}
          </Card>
        ) : (
          <Card style={styles.section}>
            <Text style={styles.bodyText}>
              No skill gaps — your résumé already covers the skills your tracked jobs demand. Nice.
            </Text>
          </Card>
        )}

        {analysis && analysis.strengths.length > 0 ? (
          <Card style={styles.section}>
            <Text style={styles.sectionTitle}>SKILLS YOU ALREADY HAVE</Text>
            <View style={styles.chipWrap}>
              {analysis.strengths.map((s) => (
                <View key={s.skill} style={styles.chip}>
                  <Text style={styles.chipText}>
                    {s.skill} <Text style={styles.chipCount}>×{s.job_count}</Text>
                  </Text>
                </View>
              ))}
            </View>
          </Card>
        ) : null}

        {analysis && analysis.gaps.length > 0 ? (
          <Card style={styles.section}>
            <Text style={styles.planTitle}>Turn your gaps into a plan</Text>
            <Text style={styles.bodyText}>
              A prioritised learning plan for your top gaps — what to learn, in what order, with
              realistic time estimates.
            </Text>
            <PlanArea
              isPremium={isPremium}
              hasConsent={hasAiConsent(user)}
              plan={plan}
              planLoading={planLoading}
              planMsg={planMsg}
              onGenerate={generatePlan}
            />
          </Card>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

// One skill row: the name over a bar whose width encodes how much of the pipeline demands it.
function GapRow({ stat }: { stat: SkillStat }) {
  const pct = Math.max(Math.round(stat.coverage * 100), 6);
  return (
    <View style={styles.gapRow}>
      <View style={styles.gapHeader}>
        <Text style={styles.gapSkill}>{stat.skill}</Text>
        <Text style={styles.gapCount}>
          {stat.job_count} of {stat.total_jobs} {stat.total_jobs === 1 ? 'job' : 'jobs'}
        </Text>
      </View>
      <View
        style={styles.track}
        accessibilityRole="image"
        accessibilityLabel={`${stat.skill}: demanded by ${stat.job_count} of ${stat.total_jobs} tracked jobs`}
      >
        <View style={[styles.bar, { width: `${pct}%` }]} />
      </View>
    </View>
  );
}

function PlanArea({
  isPremium,
  hasConsent,
  plan,
  planLoading,
  planMsg,
  onGenerate,
}: {
  isPremium: boolean;
  hasConsent: boolean;
  plan: { title: string; content: string } | null;
  planLoading: boolean;
  planMsg: string | null;
  onGenerate: () => void;
}) {
  if (!isPremium) {
    return (
      <View style={styles.upsell}>
        <Text style={styles.bodyText}>AI learning plans are a Pro feature.</Text>
        <Button label="Upgrade to Pro" onPress={() => router.push('/paywall')} />
      </View>
    );
  }
  if (!hasConsent) {
    // Premium but not yet consented: the plan sends skill/role text to the third-party AI, so
    // require explicit consent first (Apple 5.1.2(i)) rather than dead-ending on a 403.
    return <AiConsentCard />;
  }
  return (
    <View style={styles.planArea}>
      <Button
        label={planLoading ? 'Generating…' : plan ? 'Regenerate plan' : 'Generate learning plan'}
        onPress={onGenerate}
        disabled={planLoading}
      />
      {planMsg ? (
        <Text style={styles.error} accessibilityRole="alert" accessibilityLiveRegion="polite">
          {planMsg}
        </Text>
      ) : null}
      {planLoading ? <ActivityIndicator color={colors.primary} style={styles.spinner} /> : null}
      {plan && !planLoading ? (
        <View style={styles.planContent}>
          <Markdown content={plan.content} />
          <ArtifactActions text={plan.content} title="Learning plan" />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center' },
  content: { padding: spacing.md, gap: spacing.md },
  title: { color: colors.text, fontSize: 24, fontWeight: '800' },
  subtitle: { color: colors.textMuted, lineHeight: 20 },
  notice: { borderColor: colors.warning, backgroundColor: 'rgba(251,191,36,0.08)' },
  noticeText: { color: colors.warning, lineHeight: 20 },
  section: { gap: spacing.sm },
  sectionTitle: { color: colors.textMuted, fontSize: 12, fontWeight: '700', letterSpacing: 0.5 },
  bodyText: { color: colors.text, lineHeight: 20 },
  gapRow: { gap: spacing.xs },
  gapHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  gapSkill: { color: colors.text, fontWeight: '600', textTransform: 'capitalize' },
  gapCount: { color: colors.textMuted, fontSize: 12 },
  track: { height: 8, borderRadius: radius.sm, backgroundColor: colors.surfaceAlt, overflow: 'hidden' },
  bar: { height: '100%', borderRadius: radius.sm, backgroundColor: colors.primary },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    borderWidth: 1,
    borderColor: 'rgba(52,211,153,0.3)',
    backgroundColor: 'rgba(52,211,153,0.1)',
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  chipText: { color: colors.success, textTransform: 'capitalize' },
  chipCount: { color: colors.success, fontSize: 12, opacity: 0.7 },
  planTitle: { color: colors.text, fontSize: 18, fontWeight: '700' },
  upsell: { gap: spacing.sm, marginTop: spacing.sm },
  planArea: { gap: spacing.sm, marginTop: spacing.sm },
  spinner: { marginVertical: spacing.sm },
  planContent: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surfaceAlt,
  },
  error: { color: colors.danger },
});
