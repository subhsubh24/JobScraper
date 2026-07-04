import { Ionicons } from '@expo/vector-icons';
import { Pressable, Share, StyleSheet, Text, View } from 'react-native';

import { colors, spacing } from '@/theme';

/**
 * Copy / share affordance for a generated prep artifact (tailored résumé, cover letter, study
 * plan, interview-prep pack, negotiation guide). A generated document is only useful once the
 * user can get it OUT of the app — so this opens the OS share sheet (React Native's built-in
 * Share — no native dependency), which offers Copy, Save to Files, Mail, Messages, etc. on
 * both iOS and Android. Low-emphasis by default to match the sibling ReportButton.
 *
 * No fake success (SIDE-EFFECT INTEGRITY): the OS owns the outcome UI; a dismissed/failed
 * share simply does nothing here — we never claim the artifact was copied or shared.
 */
export function ArtifactActions({ text, title }: { text: string; title: string }) {
  async function share() {
    try {
      await Share.share({ message: text, title });
    } catch {
      // The OS surfaces its own error UI; there is nothing truthful for us to claim.
    }
  }

  return (
    <Pressable
      onPress={share}
      accessibilityRole="button"
      accessibilityLabel={`Copy or share ${title}`}
      style={styles.trigger}
    >
      <View style={styles.row}>
        {/* Real icon, not an emoji (VISION: no emoji-as-iconography). Decorative — the
            Pressable's accessibilityLabel already names the control for screen readers. */}
        <Ionicons name="share-outline" size={14} color={colors.textMuted} />
        <Text style={styles.text}>Copy or share</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  trigger: { marginTop: spacing.xs, alignSelf: 'flex-start' },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  text: { color: colors.textMuted, fontSize: 12 },
});
