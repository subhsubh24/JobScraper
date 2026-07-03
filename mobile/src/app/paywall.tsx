import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect } from 'react';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Button, Card } from '@/components/ui';
import { useAuth } from '@/contexts/auth';
import { colors, radius, spacing } from '@/theme';

// Features included at the Pro tier. Career+ is a strict superset: Pro + the exclusive below.
const PRO_FEATURES = [
  'Unlimited tracked jobs',
  'AI interview prep packs',
  'AI cover letters & study plans',
  'AI Career Coach',
];
// The Career+-exclusive (a real, additive feature — no tier ever lost it).
const CAREERPLUS_FEATURE = 'AI salary-negotiation coaching';

function FeatureRow({ label }: { label: string }) {
  return (
    <View style={styles.featureRow} accessible accessibilityLabel={label}>
      <Ionicons
        name="checkmark-circle"
        size={18}
        color={colors.success}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
      <Text style={styles.feature}>{label}</Text>
    </View>
  );
}

// Paywall wired to REAL entitlement state (Track B/C). It reads the user's tier + plan LEVEL
// from the auth context and refreshes on open, so a user who upgraded elsewhere (e.g. web
// Stripe checkout) sees their real status instead of a stale prompt. CRITICAL honesty rule:
// a Pro (premium, not Career+) user must NOT be told they already have the Career+ exclusive
// (salary-negotiation coaching) — that would be a false claim + a dead end. The actual in-app
// purchase (StoreKit / Play Billing via RevenueCat) is Track C and owner-gated; until it's
// live we are HONEST (no fake "purchase complete"), never granting access here — entitlement
// only ever flips server-side from a verified webhook.
export default function PaywallScreen() {
  const { user, refresh } = useAuth();
  const isPremium = user?.tier === 'premium';
  const isCareerPlus = user?.career_plus === true;

  // Re-check entitlement when the paywall opens. A user may have subscribed on another
  // surface; this keeps the screen from showing an upgrade CTA to someone already entitled.
  useEffect(() => {
    refresh().catch(() => {
      // Offline / transient — keep showing whatever tier we already have, no crash.
    });
  }, [refresh]);

  if (isCareerPlus) {
    return (
      <ScrollView style={styles.flex} contentContainerStyle={styles.container}>
        <View style={styles.badge}>
          <Ionicons name="checkmark-circle" size={48} color={colors.success} />
        </View>
        <Text style={styles.title}>You&apos;re on Career+</Text>
        <Text style={styles.subtitle}>
          Every Career Operator feature, including salary-negotiation coaching, is unlocked.
        </Text>

        <Card>
          {[...PRO_FEATURES, CAREERPLUS_FEATURE].map((f) => (
            <FeatureRow key={f} label={f} />
          ))}
        </Card>

        <Button label="Back to app" onPress={() => router.back()} />
        <Text style={styles.legal}>
          Manage or cancel your subscription anytime in your app store account.
        </Text>
      </ScrollView>
    );
  }

  if (isPremium) {
    // Pro (premium, not Career+): confirm Pro honestly and present Career+ as an upgrade —
    // WITHOUT claiming they already have the Career+ exclusive, and WITHOUT a dead end.
    return (
      <ScrollView style={styles.flex} contentContainerStyle={styles.container}>
        <View style={styles.badge}>
          <Ionicons name="checkmark-circle" size={48} color={colors.success} />
        </View>
        <Text style={styles.title}>You&apos;re on Pro</Text>
        <Text style={styles.subtitle}>Your Pro features are unlocked.</Text>

        <Card>
          {PRO_FEATURES.map((f) => (
            <FeatureRow key={f} label={f} />
          ))}
        </Card>

        <Card>
          <Text style={styles.upsellTitle}>Career+ adds</Text>
          <Text style={styles.feature}>{CAREERPLUS_FEATURE}</Text>
          <Text style={styles.upsellNote}>
            In-app upgrade to Career+ is coming soon — you can switch plans on the web. No charge
            is made here.
          </Text>
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
        {PRO_FEATURES.map((f) => (
          <FeatureRow key={f} label={f} />
        ))}
        <Text style={styles.upsellNote}>
          Career+ ($24/mo) adds {CAREERPLUS_FEATURE}.
        </Text>
      </Card>

      <View style={styles.plans}>
        <View
          style={[styles.plan, styles.planHighlight]}
          accessible
          accessibilityLabel="Annual plan, $96 per year. Save about 33%, best value."
        >
          <Text style={styles.planName}>Annual</Text>
          <Text style={styles.planPrice}>$96<Text style={styles.per}>/yr</Text></Text>
          <Text style={styles.planNote}>Save ~33% · best value</Text>
        </View>
        <View
          style={styles.plan}
          accessible
          accessibilityLabel="Monthly plan, $12 per month. Cancel anytime."
        >
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
  upsellTitle: { color: colors.textMuted, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  upsellNote: { color: colors.textMuted, fontSize: 13, marginTop: spacing.xs, lineHeight: 18 },
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
