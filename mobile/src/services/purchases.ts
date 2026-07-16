// RevenueCat in-app-purchase client (StoreKit on iOS / Play Billing on Android).
//
// HONESTY CONTRACT (mirrors the server rule in src/mobile_billing.py — "no client-trusted
// unlocks"): this screen NEVER grants entitlement. A completed native purchase resolves here,
// but the paid tier only ever flips SERVER-SIDE when RevenueCat POSTs its signature-verified
// webhook to /api/billing/revenuecat-webhook and the server calls recompute_user_tier. The UI
// then reflects the new tier by refetching /me — it is never assumed from this file.
//
// OWNER-GATED + INERT WHEN UNSET: the public RevenueCat SDK key lives in
// EXPO_PUBLIC_REVENUECAT_SDK_KEY (public by design — safe in the app bundle — but owner-set at
// build time, see PENDING_OPS `mobile-iap`). Until it is connected, purchasesConfigured() is
// false and every call throws PurchasesUnavailable, so the paywall degrades HONESTLY ("upgrade
// on the web", no charge) instead of faking a purchase. The native SDK is loaded via a LAZY
// dynamic import that only runs once a key is present, so an unconfigured build (and the jest
// suite) never touches the native module at all.
import Constants from 'expo-constants';

function sdkKey(): string | undefined {
  const fromExtra = (Constants.expoConfig?.extra as { revenuecatSdkKey?: string } | undefined)
    ?.revenuecatSdkKey;
  const key = fromExtra ?? process.env.EXPO_PUBLIC_REVENUECAT_SDK_KEY;
  return key && key.trim() ? key.trim() : undefined;
}

/** True only when the owner has connected a RevenueCat SDK key (else IAP is inert). */
export function purchasesConfigured(): boolean {
  return sdkKey() !== undefined;
}

/** Thrown when the RevenueCat SDK is not configured — the paywall surfaces this honestly. */
export class PurchasesUnavailable extends Error {
  constructor() {
    super('In-app purchases are not available yet.');
    this.name = 'PurchasesUnavailable';
  }
}

/** Thrown when the user dismisses the native purchase sheet — a no-op, not an error. */
export class PurchaseCancelled extends Error {
  constructor() {
    super('Purchase cancelled.');
    this.name = 'PurchaseCancelled';
  }
}

export type PlanId = 'annual' | 'monthly';

let configured = false;

// Load + configure the native SDK exactly once, only when a key exists. The dynamic import
// keeps react-native-purchases out of the JS bundle path (and the jest runtime) until it is
// genuinely needed and the module can actually run on a device.
async function sdk() {
  const key = sdkKey();
  if (!key) throw new PurchasesUnavailable();
  const Purchases = (await import('react-native-purchases')).default;
  if (!configured) {
    Purchases.configure({ apiKey: key });
    configured = true;
  }
  return Purchases;
}

// Associate the RevenueCat identity with our backend user id so the entitlement webhook's
// app_user_id matches User.id server-side. Best-effort + a silent no-op when unconfigured, so
// it can never break sign-in/sign-up.
export async function identifyUser(appUserId: string): Promise<void> {
  if (!purchasesConfigured()) return;
  try {
    const Purchases = await sdk();
    await Purchases.logIn(appUserId);
  } catch {
    // Identity linking is best-effort; the app still works without it.
  }
}

// Start the native purchase flow for the chosen plan. Resolves ONLY after StoreKit/Play reports
// a completed purchase. Entitlement is then granted server-side by the verified webhook — the
// caller must refetch /me and never assume the tier flipped here. Throws PurchasesUnavailable
// when unconfigured and PurchaseCancelled when the user dismisses the sheet.
export async function purchasePlan(plan: PlanId): Promise<void> {
  const Purchases = await sdk();
  const offerings = await Purchases.getOfferings();
  const offering = offerings.current;
  const pkg =
    (plan === 'annual' ? offering?.annual : offering?.monthly) ?? offering?.availablePackages?.[0];
  if (!pkg) throw new PurchasesUnavailable();
  try {
    await Purchases.purchasePackage(pkg);
  } catch (e) {
    if (e && typeof e === 'object' && (e as { userCancelled?: boolean }).userCancelled) {
      throw new PurchaseCancelled();
    }
    throw e;
  }
}

// Restore previously-purchased subscriptions (an App Store review requirement). Resolves after
// RevenueCat re-syncs entitlements; the caller then refetches /me to reflect them.
export async function restorePurchases(): Promise<void> {
  const Purchases = await sdk();
  await Purchases.restorePurchases();
}
