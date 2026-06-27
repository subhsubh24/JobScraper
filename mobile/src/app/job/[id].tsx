import { router, Stack, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Button, Card } from '@/components/ui';
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
    try {
      const pack = await api.generatePrepPack(id);
      Alert.alert(pack.title, pack.content.slice(0, 600));
    } catch (e) {
      if (e instanceof ApiError && e.status === 503) {
        Alert.alert('AI not configured', e.message);
      } else if (e instanceof ApiError && e.status === 403) {
        router.push('/paywall');
      } else {
        Alert.alert('Could not generate', e instanceof ApiError ? e.message : 'Try again.');
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
        <Text style={styles.error}>{error ?? 'Job not found.'}</Text>
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
      <View style={styles.statusGrid}>
        {STATUS_ORDER.map((s) => {
          const active = job.status === s;
          return (
            <Pressable
              key={s}
              onPress={() => setStatus(s)}
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
        label={user?.tier === 'premium' ? 'Generate prep pack' : 'Generate prep pack (1 free)'}
        onPress={generatePrep}
        loading={prepLoading}
      />
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
  error: { color: colors.danger },
});
