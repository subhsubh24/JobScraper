import { Ionicons } from '@expo/vector-icons';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, EmptyState, ErrorBanner } from '@/components/ui';
import { useAuth } from '@/contexts/auth';
import { api, ApiError } from '@/services/api';
import { colors, radius, scoreColor, spacing } from '@/theme';
import { STATUS_LABELS, type Job, type PipelineStats } from '@/types';

// The first real, data-backed screen: the user's pipeline. Pulls live jobs +
// aggregate stats from the Python API, with real loading / empty / error states.
export default function PipelineScreen() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [j, s] = await Promise.all([api.listJobs(), api.pipeline()]);
      setJobs(j);
      setStats(s);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load your pipeline.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} size="large" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <FlatList
        data={jobs}
        keyExtractor={(j) => j.id}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              load();
            }}
            tintColor={colors.primary}
          />
        }
        ListHeaderComponent={
          <View>
            <Text style={styles.h1}>Hi{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}</Text>
            <Text style={styles.sub}>Your job search, scored and organized.</Text>
            {stats ? (
              <View style={styles.statsRow}>
                <Stat label="Tracked" value={String(stats.total_jobs)} />
                <Stat label="Avg fit" value={stats.average_score ? `${stats.average_score}` : '—'} />
                <Stat label="Active" value={String(activeCount(stats))} />
              </View>
            ) : null}
            {error ? (
              <View style={styles.errorWrap}>
                <ErrorBanner
                  message={error}
                  onRetry={() => {
                    setLoading(true);
                    load();
                  }}
                />
              </View>
            ) : null}
            <View style={styles.addBtn}>
              <Button label="+ Add a job" onPress={() => router.push('/job/new')} />
            </View>
          </View>
        }
        renderItem={({ item }) => <JobRow job={item} />}
        ListEmptyComponent={
          <EmptyState
            title="No jobs yet"
            subtitle="Add a role you're chasing and we'll score how well it fits you."
          />
        }
      />
    </SafeAreaView>
  );
}

function activeCount(stats: PipelineStats): number {
  const b = stats.status_breakdown;
  return (b.applied ?? 0) + (b.phone_screen ?? 0) + (b.interview ?? 0) + (b.offer ?? 0);
}

function Stat({ label, value }: { label: string; value: string }) {
  // Announce as ONE labelled element ("Tracked: 12") instead of two bare Text nodes a
  // screen reader would read as a contextless number followed by a word.
  return (
    <View
      style={styles.stat}
      accessible
      accessibilityRole="text"
      accessibilityLabel={`${label}: ${value}`}
    >
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function JobRow({ job }: { job: Job }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${job.title} at ${job.company ?? 'unknown company'}, fit score ${
        job.score == null ? 'not scored' : Math.round(job.score)
      }, status ${STATUS_LABELS[job.status]}`}
      style={({ pressed }) => [styles.row, pressed && { opacity: 0.85 }]}
      onPress={() => router.push(`/job/${job.id}`)}
    >
      <View style={styles.rowMain}>
        <Text style={styles.jobTitle} numberOfLines={1}>
          {job.title}
        </Text>
        <Text style={styles.jobCompany} numberOfLines={1}>
          {job.company ?? 'Unknown company'}
          {job.location ? ` · ${job.location}` : ''}
        </Text>
        <View style={styles.statusPill}>
          <Text style={styles.statusText}>{STATUS_LABELS[job.status]}</Text>
        </View>
      </View>
      <View style={styles.scoreWrap}>
        <Text style={[styles.scoreNum, { color: scoreColor(job.score == null ? job.score : Math.round(job.score)) }]}>
          {job.score == null ? '—' : Math.round(job.score)}
        </Text>
        <Text style={styles.scoreLabel}>fit</Text>
        <Ionicons name="chevron-forward" size={16} color={colors.textMuted} />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg },
  listContent: { padding: spacing.md, gap: spacing.sm },
  h1: { color: colors.text, fontSize: 26, fontWeight: '800' },
  sub: { color: colors.textMuted, marginTop: spacing.xs, marginBottom: spacing.md },
  statsRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  stat: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    alignItems: 'center',
  },
  statValue: { color: colors.text, fontSize: 22, fontWeight: '800' },
  statLabel: { color: colors.textMuted, fontSize: 12, marginTop: 2 },
  addBtn: { marginBottom: spacing.md },
  errorWrap: { marginBottom: spacing.sm },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  rowMain: { flex: 1, gap: 4 },
  jobTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
  jobCompany: { color: colors.textMuted, fontSize: 13 },
  statusPill: {
    alignSelf: 'flex-start',
    backgroundColor: colors.surfaceAlt,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    marginTop: 2,
  },
  statusText: { color: colors.textMuted, fontSize: 11, fontWeight: '600' },
  scoreWrap: { alignItems: 'center', marginLeft: spacing.sm, flexDirection: 'row', gap: 4 },
  scoreNum: { fontSize: 22, fontWeight: '800' },
  scoreLabel: { color: colors.textMuted, fontSize: 11 },
});
