import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { Button } from '@/components/ui';
import { api, ApiError } from '@/services/api';
import { colors, radius, spacing } from '@/theme';

type Reason = 'harmful' | 'inaccurate' | 'offensive' | 'other';

const REASONS: { value: Reason; label: string }[] = [
  { value: 'inaccurate', label: 'Inaccurate or misleading' },
  { value: 'harmful', label: 'Harmful or dangerous advice' },
  { value: 'offensive', label: 'Offensive or inappropriate' },
  { value: 'other', label: 'Something else' },
];

/**
 * User-facing control to report an AI-generated response (coach reply or prep pack) for
 * moderator review — the store-required (Apple/Google 2026 GenAI/UGC) counterpart to the
 * server-side output moderation. Low-emphasis until tapped; the success state shows ONLY
 * after the real POST /api/report resolves (never an optimistic "reported" claim).
 */
export function ReportButton({
  contentType,
  contentRef,
  contentExcerpt,
}: {
  contentType: 'coach' | 'prep_pack';
  contentRef?: string;
  contentExcerpt?: string;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<Reason>('inaccurate');
  const [detail, setDetail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  if (done) {
    return (
      <Text style={styles.doneText} accessibilityRole="text">
        Flagged for review — thank you.
      </Text>
    );
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      await api.reportContent({
        content_type: contentType,
        reason,
        content_ref: contentRef,
        content_excerpt: contentExcerpt?.slice(0, 5000),
        detail: detail.trim() || undefined,
      });
      setDone(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not send the report — try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) {
    return (
      <Pressable
        onPress={() => setOpen(true)}
        accessibilityRole="button"
        accessibilityLabel="Report this response"
        style={styles.trigger}
      >
        <Text style={styles.triggerText}>⚑ Report this response</Text>
      </Pressable>
    );
  }

  return (
    <View style={styles.panel}>
      <Text style={styles.legend}>Report this AI response</Text>
      {REASONS.map((r) => {
        const selected = reason === r.value;
        return (
          <Pressable
            key={r.value}
            onPress={() => setReason(r.value)}
            accessibilityRole="radio"
            accessibilityState={{ selected }}
            accessibilityLabel={r.label}
            style={styles.reasonRow}
          >
            <View style={[styles.radio, selected && styles.radioSelected]}>
              {selected ? <View style={styles.radioDot} /> : null}
            </View>
            <Text style={styles.reasonText}>{r.label}</Text>
          </Pressable>
        );
      })}
      <TextInput
        value={detail}
        onChangeText={setDetail}
        maxLength={1000}
        multiline
        accessibilityLabel="Add a detail about this report (optional)"
        placeholder="What was wrong with this response? (optional)"
        placeholderTextColor={colors.textMuted}
        style={styles.detail}
      />
      {error ? (
        <Text style={styles.error} accessibilityRole="alert" accessibilityLiveRegion="polite">
          {error}
        </Text>
      ) : null}
      <View style={styles.actions}>
        <Button label={submitting ? 'Sending…' : 'Submit report'} onPress={submit} loading={submitting} />
        <Button label="Cancel" variant="secondary" onPress={() => setOpen(false)} disabled={submitting} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  trigger: { marginTop: spacing.xs, alignSelf: 'flex-start' },
  triggerText: { color: colors.textMuted, fontSize: 12 },
  doneText: { color: colors.textMuted, fontSize: 12, marginTop: spacing.xs },
  panel: {
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    backgroundColor: colors.surfaceAlt,
    padding: spacing.md,
    gap: spacing.xs,
  },
  legend: { color: colors.textMuted, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', marginBottom: spacing.xs },
  reasonRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.xs },
  radio: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioSelected: { borderColor: colors.primary },
  radioDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.primary },
  reasonText: { color: colors.text, fontSize: 14, flexShrink: 1 },
  detail: {
    marginTop: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    color: colors.text,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    minHeight: 56,
    textAlignVertical: 'top',
  },
  error: { color: colors.danger, fontSize: 13, marginTop: spacing.xs },
  actions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
});
