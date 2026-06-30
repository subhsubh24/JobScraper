import { router, Stack, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Button, Card, ErrorBanner } from '@/components/ui';
import { Markdown } from '@/components/markdown';
import { useAuth } from '@/contexts/auth';
import { api, ApiError } from '@/services/api';
import { colors, radius, scoreColor, spacing } from '@/theme';
import { STATUS_LABELS, type ApplicationStatus, type Job } from '@/types';

const STATUS_ORDER: ApplicationStatus[] = [
  'saved',
  'applied',
  'phone_screen',
  'interview',
  'offer',
  'rejected',
  'withdrawn',
];

export default function JobDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user } = useAuth();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prepLoading, setPrepLoading] = useState(false);
  const [prep, setPrep] = useState<{ title: string; content: string } | null>(null);
  const [prepMsg, setPrepMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      setJob(await api.getJob(id));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load this job.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    // load() sets state asynchronously after the fetch resolves, not synchronously.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  async function setStatus(status: ApplicationStatus) {
    if (!id) return;
    try {
      setJob(await api.updateJobStatus(id, status));
    } catch (e) {
      Alert.alert('Update failed', e instanceof ApiError ? e.message : 'Try again.');
    }
  }

  async function generatePrep() {
    if (!id) return;
    setPrepLoading(true);
    setPrepMsg(null);
    try {
      // Render the full pack inline (scrollable) instead of a truncated, ephemeral alert —
      // the prep pack is the value, the user needs to read all of it and come back to it.
      setPrep(await api.generatePrepPack(id));
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        router.push('/paywall');
      } else if (e instanceof ApiError) {
        setPrepMsg(e.message); // 503 (AI not configured) and other API errors, honestly inline
      } else {
        setPrepMsg('Could not generate a prep pack. Please try again.');
      }
    } finally {
      setPrepLoading(false);
    }
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} size="large" />
      </View>
    );
  }

  if (error || !job) {
    return (
      <View style={styles.center}>
        <View style={styles.errorWrap}>
          <ErrorBanner
            message={error ?? 'Job not found.'}
            onRetry={() => {
              setError(null);
              setLoading(true);
              load();
            }}
          />
        </View>
        <Button label="Go back" variant="secondary" onPress={() => router.back()} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.flex} contentContainerStyle={styles.container}>
      <Stack.Screen options={{ title: job.company ?? 'Job' }} />
      <Text style={styles.title}>{job.title}</Text>
      <Text style={styles.company}>
        {job.company}
        {job.location ? ` · ${job.location}` : ''}
      </Text>

      <Card style={styles.scoreCard}>
        <Text style={[styles.scoreNum, { color: scoreColor(job.score) }]}>
          {job.score == null ? '—' : Math.round(job.score)}
          <Text style={styles.scoreOutOf}> / 100</Text>
        </Text>
        <Text style={styles.scoreLabel}>Fit score</Text>
        {job.score_explanation ? <Text style={styles.explain}>{job.score_explanation}</Text> : null}
      </Card>

      <Text style={styles.section}>Pipeline status</Text>
      <View style={styles.statusGrid} accessibilityRole="radiogroup" accessibilityLabel="Pipeline status">
        {STATUS_ORDER.map((s) => {
          const active = job.status === s;
          return (
            <Pressable
              key={s}
              onPress={() => setStatus(s)}
              // A screen reader otherwise just announces "Saved" with no hint that it's a
              // selectable status or which one is current. Expose it as a radio option so the
              // pipeline tracker — the core loop — is operable with VoiceOver/TalkBack.
              accessibilityRole="radio"
              accessibilityState={{ selected: active }}
              accessibilityLabel={`Set status to ${STATUS_LABELS[s]}`}
              style={[styles.statusChip, active && styles.statusChipActive]}
            >
              <Text style={[styles.statusChipText, active && styles.statusChipTextActive]}>
                {STATUS_LABELS[s]}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <Text style={styles.section}>Interview prep</Text>
      <Button
        label={
          prep
            ? 'Regenerate prep pack'
            : user?.tier === 'premium'
              ? 'Generate prep pack'
              : 'Generate prep pack (1 free)'
        }
        onPress={generatePrep}
        loading={prepLoading}
      />
      {prepMsg ? <Text style={styles.prepMsg}>{prepMsg}</Text> : null}
      {prep ? (
        <Card style={styles.prepCard}>
          <Text style={styles.prepTitle}>{prep.title}</Text>
          <Markdown content={prep.content} />
        </Card>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center', gap: spacing.md, padding: spacing.lg },
  container: { padding: spacing.md, gap: spacing.sm },
  title: { color: colors.text, fontSize: 24, fontWeight: '800' },
  company: { color: colors.textMuted, marginBottom: spacing.md },
  scoreCard: { alignItems: 'center', marginBottom: spacing.md },
  scoreNum: { fontSize: 44, fontWeight: '800' },
  scoreOutOf: { fontSize: 18, color: colors.textMuted, fontWeight: '600' },
  scoreLabel: { color: colors.textMuted, marginTop: spacing.xs },
  explain: { color: colors.text, marginTop: spacing.sm, textAlign: 'center', lineHeight: 20 },
  section: { color: colors.text, fontSize: 16, fontWeight: '700', marginTop: spacing.md, marginBottom: spacing.sm },
  statusGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  statusChip: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  statusChipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  statusChipText: { color: colors.textMuted, fontWeight: '600' },
  statusChipTextActive: { color: colors.primaryText },
  errorWrap: { alignSelf: 'stretch' },
  prepMsg: { color: colors.danger, fontSize: 13, marginTop: spacing.sm },
  prepCard: { marginTop: spacing.md, gap: spacing.sm },
  prepTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
});
