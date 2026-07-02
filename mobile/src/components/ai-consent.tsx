import { useRef, useState } from 'react';
import { Modal, StyleSheet, Text, View } from 'react-native';

import { Button, Card } from '@/components/ui';
import { useAuth } from '@/contexts/auth';
import { api, ApiError } from '@/services/api';
import { colors, spacing } from '@/theme';

// Single source of truth for the consent disclosure copy. Apple 5.1.2(i) requires the prompt
// to NAME the third-party AI + the data before the first transmission; consent must be
// explicit and revocable (see Settings).
export const AI_PROVIDER = 'Google Gemini';
const DISCLOSURE =
  `To generate fit scores, prep packs, salary coaching and AI-coach replies, we send the ` +
  `relevant text — your resume and the job details you enter — to our AI provider ` +
  `(${AI_PROVIDER}). Nothing is sent until you turn this on, and you can turn it off anytime ` +
  `in Settings.`;

export function hasAiConsent(user: { ai_consent?: boolean } | null): boolean {
  return user?.ai_consent === true;
}

// --------------------------------------------------------------------------- imperative flow
/**
 * Consent flow for actions embedded in a larger screen (job-detail prep / salary). Render
 * `dialog` in the tree; call `ensureConsent()` before the AI call — it resolves true if
 * consent is already granted or the user grants it in the modal, false if they dismiss it.
 */
export function useAiConsent() {
  const { user, setUser } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const resolverRef = useRef<((granted: boolean) => void) | null>(null);

  const consented = hasAiConsent(user);

  function ensureConsent(): Promise<boolean> {
    if (consented) return Promise.resolve(true);
    setError(null);
    setOpen(true);
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
    });
  }

  function settle(granted: boolean) {
    setOpen(false);
    const resolve = resolverRef.current;
    resolverRef.current = null;
    resolve?.(granted);
  }

  async function enable() {
    setBusy(true);
    setError(null);
    try {
      setUser(await api.grantAiConsent());
      settle(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not enable AI features. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  const dialog = (
    <Modal visible={open} transparent animationType="fade" onRequestClose={() => settle(false)}>
      <View style={styles.backdrop}>
        <Card style={styles.modalCard}>
          <Text style={styles.title} accessibilityRole="header">
            Enable AI features
          </Text>
          <Text style={styles.body}>{DISCLOSURE}</Text>
          {error ? (
            <Text style={styles.error} accessibilityRole="alert">
              {error}
            </Text>
          ) : null}
          <View style={styles.actions}>
            <Button label={busy ? 'Enabling…' : 'Turn on AI features'} onPress={enable} loading={busy} />
            <Button label="Not now" variant="secondary" onPress={() => settle(false)} disabled={busy} />
          </View>
        </Card>
      </View>
    </Modal>
  );

  return { consented, ensureConsent, dialog };
}

// --------------------------------------------------------------------------- inline gate (coach)
export function AiConsentCard({ onEnabled }: { onEnabled?: () => void }) {
  const { setUser } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function enable() {
    setBusy(true);
    setError(null);
    try {
      setUser(await api.grantAiConsent());
      onEnabled?.();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not enable AI features. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.center}>
      <Text style={styles.gateTitle} accessibilityRole="header">
        Enable AI features
      </Text>
      <Text style={styles.gateBody}>{DISCLOSURE}</Text>
      {error ? (
        <Text style={styles.error} accessibilityRole="alert">
          {error}
        </Text>
      ) : null}
      <Button label={busy ? 'Enabling…' : 'Turn on AI features'} onPress={enable} loading={busy} />
    </View>
  );
}

// --------------------------------------------------------------------------- settings control
export function AiConsentSetting() {
  const { user, setUser } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const consented = hasAiConsent(user);

  async function toggle() {
    setBusy(true);
    setError(null);
    try {
      setUser(consented ? await api.revokeAiConsent() : await api.grantAiConsent());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not update your preference. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <Text style={styles.settingTitle}>AI features</Text>
      <Text style={styles.settingBody}>{DISCLOSURE}</Text>
      <View style={styles.settingRow}>
        <Text style={[styles.state, consented ? styles.stateOn : styles.stateOff]}>
          {consented ? 'Enabled' : 'Off'}
        </Text>
      </View>
      <Button
        label={busy ? 'Saving…' : consented ? 'Turn off' : 'Turn on AI features'}
        variant={consented ? 'secondary' : 'primary'}
        onPress={toggle}
        loading={busy}
      />
      {error ? (
        <Text style={styles.error} accessibilityRole="alert">
          {error}
        </Text>
      ) : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  modalCard: { gap: spacing.sm },
  title: { color: colors.text, fontSize: 18, fontWeight: '800' },
  body: { color: colors.textMuted, lineHeight: 21 },
  actions: { gap: spacing.sm, marginTop: spacing.sm },
  center: {
    flex: 1,
    backgroundColor: colors.bg,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
    gap: spacing.md,
  },
  gateTitle: { color: colors.text, fontSize: 22, fontWeight: '800', textAlign: 'center' },
  gateBody: { color: colors.textMuted, textAlign: 'center', lineHeight: 21 },
  settingTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
  settingBody: { color: colors.textMuted, marginTop: spacing.xs, marginBottom: spacing.md, fontSize: 13, lineHeight: 19 },
  settingRow: { flexDirection: 'row', marginBottom: spacing.md },
  state: {
    fontSize: 12,
    fontWeight: '700',
    overflow: 'hidden',
    borderRadius: 999,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
  },
  stateOn: { color: colors.success, backgroundColor: 'rgba(16,185,129,0.12)' },
  stateOff: { color: colors.textMuted, backgroundColor: colors.surfaceAlt },
  error: { color: colors.danger, fontSize: 13 },
});
