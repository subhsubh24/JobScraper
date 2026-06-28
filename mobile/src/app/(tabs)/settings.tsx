import { router } from 'expo-router';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card } from '@/components/ui';
import { useAuth } from '@/contexts/auth';
import { api } from '@/services/api';
import { colors, spacing } from '@/theme';

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
      await signOut();
    } catch (e) {
      Alert.alert(
        'Could not delete account',
        e instanceof Error ? e.message : 'Something went wrong. Please try again.',
      );
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

        <View style={styles.meta}>
          <Text style={styles.metaText}>API: {api.apiUrl}</Text>
        </View>

        <Button label="Log out" variant="secondary" onPress={confirmSignOut} />
        <Button label="Delete account" variant="secondary" onPress={confirmDelete} />
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
  meta: { alignItems: 'center' },
  metaText: { color: colors.textMuted, fontSize: 12 },
});
