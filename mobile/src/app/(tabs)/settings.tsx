import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Alert, Pressable, ScrollView, Share, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card } from '@/components/ui';
import { AiConsentSetting } from '@/components/ai-consent';
import { useAuth } from '@/contexts/auth';
import { api } from '@/services/api';
import { colors, spacing } from '@/theme';
import type { ReferralStats } from '@/types';

// Mobile parity with the web "Refer a friend" card: shows the user's invite stats and opens
// the native share sheet. The reward (a bonus prep pack for both sides) is granted
// server-side from a verified signup — this is just the share surface.
function ReferAFriendCard() {
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    api
      .referralStats()
      .then((s) => active && setStats(s))
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
    };
  }, []);

  async function share() {
    if (!stats) return;
    // The /register page lives on the WEB frontend, which is a different origin from the
    // API in a split deploy. Prefer an explicit web URL; fall back to the API origin (correct
    // for the unified Vercel deploy where web + /api share one origin).
    const webBase = process.env.EXPO_PUBLIC_WEB_URL ?? api.apiUrl;
    const link = `${webBase}/register?ref=${stats.code}`;
    try {
      await Share.share({
        message: `Join me on Career Operator — we both get a bonus interview prep pack: ${link}`,
      });
    } catch {
      // User dismissed the share sheet, or it's unavailable — nothing to surface.
    }
  }

  if (failed) return null;

  return (
    <Card>
      <Text style={styles.referTitle}>Refer a friend</Text>
      <Text style={styles.referBody}>
        Share your link. When a friend signs up, you both get a free interview prep pack.
      </Text>
      {stats ? (
        <>
          <Button label="Share invite link" variant="secondary" onPress={share} />
          <Text style={styles.referStats}>
            {stats.total_referred} {stats.total_referred === 1 ? 'friend has' : 'friends have'}{' '}
            joined · {stats.bonus_prep_packs} bonus prep{' '}
            {stats.bonus_prep_packs === 1 ? 'pack' : 'packs'} earned
          </Text>
        </>
      ) : (
        <Text style={styles.referStats}>Loading your invite link…</Text>
      )}
    </Card>
  );
}

export default function SettingsScreen() {
  const { user, signOut } = useAuth();

  function confirmSignOut() {
    Alert.alert('Log out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log out', style: 'destructive', onPress: () => signOut() },
    ]);
  }

  async function deleteAccount() {
    // Required by Apple (5.1.1v) & Google. A REAL deletion: the server removes the user
    // and all their data, then we clear the local session (signOut sets user -> null, so
    // the root layout routes back to the auth screen).
    try {
      await api.deleteAccount();
    } catch (e) {
      // Only the deletion request itself failing should surface as a failure.
      Alert.alert(
        'Could not delete account',
        e instanceof Error ? e.message : 'Something went wrong. Please try again.',
      );
      return;
    }
    // Account is gone server-side. Clear the session; if signOut hiccups, force the user
    // back to auth rather than wrongly reporting a delete failure.
    try {
      await signOut();
    } catch {
      router.replace('/(auth)/login');
    }
  }

  function confirmDelete() {
    Alert.alert(
      'Delete account',
      'This permanently deletes your account and all your data. This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: deleteAccount },
      ],
    );
  }

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.h1}>Settings</Text>
        <Card>
          <Text style={styles.name}>{user?.full_name ?? 'Your account'}</Text>
          <Text style={styles.email}>{user?.email}</Text>
          <View style={styles.tierRow}>
            <Text style={styles.tierLabel}>Plan</Text>
            <Text style={[styles.tierValue, user?.tier === 'premium' && { color: colors.success }]}>
              {user?.tier === 'premium' ? 'Premium' : 'Free'}
            </Text>
          </View>
          <Text style={styles.usage}>
            Jobs remaining: {String(user?.jobs_remaining ?? '—')} · Prep packs:{' '}
            {String(user?.prep_packs_remaining ?? '—')}
          </Text>
        </Card>

        {user?.tier !== 'premium' ? (
          <Button label="Upgrade to Premium" onPress={() => router.push('/paywall')} />
        ) : null}

        <AiConsentSetting />

        <ReferAFriendCard />

        <View style={styles.meta}>
          <Text style={styles.metaText}>API: {api.apiUrl}</Text>
        </View>

        <Button label="Log out" variant="secondary" onPress={confirmSignOut} />
        {/* Destructive action set apart from preferences and visually marked as danger,
            so deleting an account never reads like just another button. */}
        <Pressable accessibilityRole="button" onPress={confirmDelete} style={styles.deleteBtn}>
          <Text style={styles.deleteText}>Delete account</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.md, gap: spacing.md },
  h1: { color: colors.text, fontSize: 26, fontWeight: '800' },
  name: { color: colors.text, fontSize: 18, fontWeight: '700' },
  email: { color: colors.textMuted, marginTop: 2 },
  tierRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.md },
  tierLabel: { color: colors.textMuted },
  tierValue: { color: colors.text, fontWeight: '700' },
  usage: { color: colors.textMuted, marginTop: spacing.sm, fontSize: 13 },
  referTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
  referBody: { color: colors.textMuted, marginTop: spacing.xs, marginBottom: spacing.md, fontSize: 13 },
  referStats: { color: colors.textMuted, marginTop: spacing.sm, fontSize: 13 },
  meta: { alignItems: 'center' },
  metaText: { color: colors.textMuted, fontSize: 12 },
  deleteBtn: { paddingVertical: 14, alignItems: 'center', marginTop: spacing.sm },
  deleteText: { color: colors.danger, fontWeight: '600', fontSize: 15 },
});
