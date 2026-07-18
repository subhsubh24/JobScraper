import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Alert, Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Button, Card } from '@/components/ui';
import { api } from '@/services/api';
import { useAuth } from '@/contexts/auth';
import {
  PlanId,
  PurchaseCancelled,
  PurchasesUnavailable,
  purchasePlan,
  restorePurchases,
} from '@/services/purchases';
import { colors, radius, spacing } from '@/theme';

// Features included at the Pro tier. Career+ is a strict superset: Pro + the exclusive below.
const PRO_FEATURES = [
  'Unlimited tracked jobs',
  'AI interview prep packs',
  'AI tailored résumés, cover letters & study plans',
  'AI Career Coach',
];
// The Career+-exclusive (a real, additive feature — no tier ever lost it).
const CAREERPLUS_FEATURE = 'AI salary-negotiation coaching';

// Subscription legal footer. App Store guideline 3.1.2 requires a subscription screen to carry
// FUNCTIONAL links to the Terms of Service and Privacy Policy — not just prose. These open the
// hosted /terms and /privacy pages (the same documents the web app links from its footer).
function LegalFooter({ text }: { text: string }) {
  const webBase = process.env.EXPO_PUBLIC_WEB_URL ?? api.apiUrl;
  const open = (path: string) => {
    // Fire-and-forget: a browser open can reject offline / with no handler — surface nothing
    // (the prose remains), never crash the paywall.
    Linking.openURL(`${webBase}${path}`).catch(() => {});
  };
  return (
    <View style={styles.legalWrap}>
      <Text style={styles.legal}>{text}</Text>
      <View style={styles.legalLinks}>
        <Pressable
          accessibilityRole="link"
          accessibilityLabel="Terms of Service"
          onPress={() => open('/terms')}
          hitSlop={8}
        >
          <Text style={styles.legalLink}>Terms of Service</Text>
        </Pressable>
        <Text style={styles.legalDot}>·</Text>
        <Pressable
          accessibilityRole="link"
          accessibilityLabel="Privacy Policy"
          onPress={() => open('/privacy')}
          hitSlop={8}
        >
          <Text style={styles.legalLink}>Privacy Policy</Text>
        </Pressable>
      </View>
    </View>
  );
}

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
// (salary-negotiation coaching) — that would be a false claim + a dead end.
//
// The in-app purchase runs the native StoreKit / Play Billing flow via RevenueCat
// (@/services/purchases). It is HONEST end-to-end: we never grant access here — a completed
// purchase is confirmed by RevenueCat's signature-verified webhook server-side, and the screen
// reflects it only by refetching /me. Until the owner connects the RevenueCat SDK key the
// client is inert and the button degrades to an honest "in-app purchase unavailable" (no charge,
// and no steering to the web to pay — App Store guideline 3.1.1).
export default function PaywallScreen() {
  const { user, refresh } = useAuth();
  const isPremium = user?.tier === 'premium';
  const isCareerPlus = user?.career_plus === true;
  const [plan, setPlan] = useState<PlanId>('annual');
  const [busy, setBusy] = useState(false);

  async function purchase() {
    if (busy) return;
    setBusy(true);
    try {
      await purchasePlan(plan);
      // StoreKit/Play reported a completed purchase. Entitlement is granted server-side by the
      // verified RevenueCat webhook — pull the REAL tier from the server, never assume it here.
      Alert.alert(
        'Thank you!',
        'Your purchase is being confirmed — your access will unlock shortly.',
      );
      await refresh();
    } catch (err) {
      if (err instanceof PurchaseCancelled) return; // user dismissed the sheet — no-op
      if (err instanceof PurchasesUnavailable) {
        Alert.alert(
          'In-app purchase unavailable',
          'In-app purchases aren’t available right now — no charge was made and your plan is '
            + 'unchanged. Please try again later.',
        );
      } else {
        Alert.alert('Purchase failed', 'Something went wrong and no charge was made. Please try again.');
      }
    } finally {
      setBusy(false);
    }
  }

  async function restore() {
    if (busy) return;
    setBusy(true);
    try {
      const found = await restorePurchases();
      await refresh();
      // When an entitlement was recovered, refresh() flips the tier and the screen re-renders to
      // the entitled state. When nothing was found, say so honestly instead of doing nothing.
      if (!found) {
        Alert.alert(
          'No purchases found',
          'We couldn’t find any active purchases to restore on this account.',
        );
      }
    } catch (err) {
      if (err instanceof PurchasesUnavailable) {
        Alert.alert('Nothing to restore yet', 'In-app purchases aren’t available yet.');
      } else {
        Alert.alert('Restore failed', 'We couldn’t restore your purchases. Please try again.');
      }
    } finally {
      setBusy(false);
    }
  }

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
        <LegalFooter text="Manage or cancel your subscription anytime in your app store account." />
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
            In-app upgrade to Career+ is coming soon. No charge is made here.
          </Text>
        </Card>

        <Button label="Back to app" onPress={() => router.back()} />
        <LegalFooter text="Manage or cancel your subscription anytime in your app store account." />
      </ScrollView>
    );
  }

  return (
    <ScrollView style={styles.flex} contentContainerStyle={styles.container}>
      <Text style={styles.title}>Career Operator Pro</Text>
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
        <Pressable
          style={[styles.plan, plan === 'annual' && styles.planSelected]}
          accessibilityRole="button"
          accessibilityState={{ selected: plan === 'annual' }}
          accessibilityLabel="Annual plan, $96 per year. Save about 33%, best value."
          onPress={() => setPlan('annual')}
        >
          <Text style={styles.planName}>Annual</Text>
          <Text style={styles.planPrice}>$96<Text style={styles.per}>/yr</Text></Text>
          <Text style={styles.planNote}>Save ~33% · best value</Text>
        </Pressable>
        <Pressable
          style={[styles.plan, plan === 'monthly' && styles.planSelected]}
          accessibilityRole="button"
          accessibilityState={{ selected: plan === 'monthly' }}
          accessibilityLabel="Monthly plan, $12 per month. Cancel anytime."
          onPress={() => setPlan('monthly')}
        >
          <Text style={styles.planName}>Monthly</Text>
          <Text style={styles.planPrice}>$12<Text style={styles.per}>/mo</Text></Text>
          <Text style={styles.planNote}>Cancel anytime</Text>
        </Pressable>
      </View>

      <Button label="Start Pro" onPress={purchase} loading={busy} />
      <Button label="Restore purchases" variant="secondary" onPress={restore} disabled={busy} />
      <Button label="Maybe later" variant="secondary" onPress={() => router.back()} disabled={busy} />
      <LegalFooter text="Subscriptions renew automatically until cancelled. Manage in your app store account." />
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
  planSelected: { borderColor: colors.primary, borderWidth: 2 },
  planName: { color: colors.textMuted, fontWeight: '600' },
  planPrice: { color: colors.text, fontSize: 26, fontWeight: '800', marginVertical: 4 },
  per: { fontSize: 14, color: colors.textMuted, fontWeight: '600' },
  planNote: { color: colors.textMuted, fontSize: 12, textAlign: 'center' },
  legalWrap: { alignItems: 'center', marginTop: spacing.sm, gap: 6 },
  legal: { color: colors.textMuted, fontSize: 11, textAlign: 'center' },
  legalLinks: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  legalLink: { color: colors.primary, fontSize: 12, fontWeight: '600' },
  legalDot: { color: colors.textMuted, fontSize: 12 },
});
