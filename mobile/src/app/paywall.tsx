import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect } from 'react';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Button, Card } from '@/components/ui';
import { useAuth } from '@/contexts/auth';
import { colors, radius, spacing } from '@/theme';

const FEATURES = [
  'Unlimited tracked jobs',
  'AI interview prep packs',
  'AI Career Coach',
  'Salary negotiation coaching',
  'Priority fit scoring',
];

// Paywall wired to REAL entitlement state (Track B). It reads the user's tier from the auth
// context and refreshes it on open, so a user who upgraded elsewhere (e.g. web Stripe
// checkout) sees their Premium status instead of a stale upgrade prompt. The actual in-app
// purchase (StoreKit / Play Billing via RevenueCat) is Track C and owner-gated; until it's
// live we are HONEST about it (no fake "purchase complete"), never granting access here —
// entitlement only ever flips server-side from a verified RevenueCat webhook.
export default function PaywallScreen() {
  const { user, refresh } = useAuth();
  const isPremium = user?.tier === 'premium';

  // Re-check entitlement when the paywall opens. A user may have subscribed on another
  // surface; this keeps the screen from showing an upgrade CTA to someone already Premium.
  useEffect(() => {
    refresh().catch(() => {
      // Offline / transient — keep showing whatever tier we already have, no crash.
    });
  }, [refresh]);

  if (isPremium) {
    return (
      <ScrollView style={styles.flex} contentContainerStyle={styles.container}>
        <View style={styles.badge}>
          <Ionicons name="checkmark-circle" size={48} color={colors.success} />
        </View>
        <Text style={styles.title}>You&apos;re on Premium</Text>
        <Text style={styles.subtitle}>
          Every Career Operator feature is unlocked on this account.
        </Text>

        <Card>
          {FEATURES.map((f) => (
            <View key={f} style={styles.featureRow}>
              <Ionicons name="checkmark-circle" size={18} color={colors.success} />
              <Text style={styles.feature}>{f}</Text>
            </View>
          ))}
        </Card>

        <Button label="Back to app" onPress={() => router.back()} />
        <Text style={styles.legal}>
          Manage or cancel your subscription anytime in your app store account.
        </Text>
      </ScrollView>
    );
  }

  function purchase() {
    // HONEST, not a fake success: no charge is made and the plan is unchanged. In-app
    // purchases unlock once the owner connects the store accounts (Track C); entitlement is
    // then granted server-side by a verified RevenueCat webhook, never from this screen.
    Alert.alert(
      'In-app purchase coming soon',
      'Subscriptions are being finalized for the App Store and Play Store. No charge was made '
        + 'and your plan is unchanged — check back shortly.',
    );
  }

  return (
    <ScrollView style={styles.flex} contentContainerStyle={styles.container}>
      <Text style={styles.title}>Career Operator Premium</Text>
      <Text style={styles.subtitle}>Everything you need to land the offer, faster.</Text>

      <Card>
        {FEATURES.map((f) => (
          <View key={f} style={styles.featureRow}>
            <Ionicons name="checkmark-circle" size={18} color={colors.success} />
            <Text style={styles.feature}>{f}</Text>
          </View>
        ))}
      </Card>

      <View style={styles.plans}>
        <View style={[styles.plan, styles.planHighlight]}>
          <Text style={styles.planName}>Annual</Text>
          <Text style={styles.planPrice}>$96<Text style={styles.per}>/yr</Text></Text>
          <Text style={styles.planNote}>Save ~33% · best value</Text>
        </View>
        <View style={styles.plan}>
          <Text style={styles.planName}>Monthly</Text>
          <Text style={styles.planPrice}>$12<Text style={styles.per}>/mo</Text></Text>
          <Text style={styles.planNote}>Cancel anytime</Text>
        </View>
      </View>

      <Button label="Start Premium" onPress={purchase} />
      <Button label="Maybe later" variant="secondary" onPress={() => router.back()} />
      <Text style={styles.legal}>
        Subscriptions renew automatically until cancelled. Manage in your app store account.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, gap: spacing.md },
  badge: { alignItems: 'center', marginTop: spacing.sm },
  title: { color: colors.text, fontSize: 26, fontWeight: '800', textAlign: 'center' },
  subtitle: { color: colors.textMuted, textAlign: 'center', marginBottom: spacing.sm },
  featureRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: 6 },
  feature: { color: colors.text, fontSize: 15 },
  plans: { flexDirection: 'row', gap: spacing.md },
  plan: {
    flex: 1,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    padding: spacing.md,
    alignItems: 'center',
  },
  planHighlight: { borderColor: colors.primary },
  planName: { color: colors.textMuted, fontWeight: '600' },
  planPrice: { color: colors.text, fontSize: 26, fontWeight: '800', marginVertical: 4 },
  per: { fontSize: 14, color: colors.textMuted, fontWeight: '600' },
  planNote: { color: colors.textMuted, fontSize: 12, textAlign: 'center' },
  legal: { color: colors.textMuted, fontSize: 11, textAlign: 'center', marginTop: spacing.sm },
});
