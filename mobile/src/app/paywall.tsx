import { router } from 'expo-router';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Button, Card } from '@/components/ui';
import { colors, radius, spacing } from '@/theme';

const FEATURES = [
  'Unlimited tracked jobs',
  'AI interview prep packs',
  'AI Career Coach',
  'Salary negotiation scripts',
  'Priority fit scoring',
];

// Real paywall UI. The actual purchase flow (StoreKit / Play Billing via RevenueCat)
// is Track C and requires the owner's store accounts + product IDs (Human-Core).
export default function PaywallScreen() {
  function purchase() {
    Alert.alert(
      'Checkout not yet connected',
      'In-app purchase (RevenueCat / StoreKit / Play Billing) ships in Track C and needs the store accounts + product IDs configured by the owner.',
    );
  }

  return (
    <ScrollView style={styles.flex} contentContainerStyle={styles.container}>
      <Text style={styles.title}>Career Operator Premium</Text>
      <Text style={styles.subtitle}>Everything you need to land the offer, faster.</Text>

      <Card>
        {FEATURES.map((f) => (
          <View key={f} style={styles.featureRow}>
            <Text style={styles.check}>✓</Text>
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
  title: { color: colors.text, fontSize: 26, fontWeight: '800', textAlign: 'center' },
  subtitle: { color: colors.textMuted, textAlign: 'center', marginBottom: spacing.sm },
  featureRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: 6 },
  check: { color: colors.success, fontWeight: '800', fontSize: 16 },
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
