import { router } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui';
import { ReportButton } from '@/components/report-button';
import { AiConsentCard, hasAiConsent } from '@/components/ai-consent';
import { useAuth } from '@/contexts/auth';
import { api, ApiError } from '@/services/api';
import { colors, radius, spacing } from '@/theme';

interface Msg {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

// Stable per-conversation id used to thread multi-turn context server-side. React Native
// has no guaranteed crypto.randomUUID, so fall back to a time+random token; uniqueness per
// conversation is all that's required (the server groups history by this id).
function newSessionId(): string {
  const c = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
  if (c?.randomUUID) return c.randomUUID();
  return `s-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

// AI Career Coach. Premium-gated server-side; we reflect that honestly in the UI and
// route free users to the paywall instead of letting them hit a dead end.
export default function CoachScreen() {
  const { user } = useAuth();
  const isPremium = user?.tier === 'premium';
  const [messages, setMessages] = useState<Msg[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const counter = useRef(0);
  // One stable session id for this conversation so the coach threads multi-turn context.
  // Lazily initialised once (never regenerated on re-render) and safe to read during render
  // (unlike a ref) — the report control needs it as the reference for a flagged reply.
  const [sessionId] = useState<string>(newSessionId);

  useEffect(() => {
    api.coachSuggestions().then(setSuggestions).catch(() => setSuggestions([]));
  }, []);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || sending) return;
      setError(null);
      setInput('');
      const userMsg: Msg = { id: `u${counter.current++}`, role: 'user', content: trimmed };
      setMessages((m) => [...m, userMsg]);
      setSending(true);
      try {
        const reply = await api.coachChat(trimmed, sessionId);
        setMessages((m) => [...m, { id: `a${counter.current++}`, role: 'assistant', content: reply }]);
      } catch (e) {
        setError(e instanceof ApiError ? e.message : 'Coach is unavailable right now.');
      } finally {
        setSending(false);
      }
    },
    [sending, sessionId],
  );

  // Send is a no-op on empty/whitespace input, so reflect that in the control rather than
  // presenting an enabled button that silently does nothing — matching the other native surfaces
  // (team.tsx's Add member, settings.tsx) that disable their submit buttons until there is real input.
  const canSend = input.trim().length > 0 && !sending;

  if (!isPremium) {
    return (
      <SafeAreaView style={styles.center} edges={['top']}>
        <Text style={styles.lockTitle}>Your AI Career Coach</Text>
        <Text style={styles.lockBody}>
          Get role-specific advice, interview prep, and salary negotiation help on demand.
          The Coach is a Pro feature.
        </Text>
        <Button label="Upgrade to unlock" onPress={() => router.push('/paywall')} />
      </SafeAreaView>
    );
  }

  // Premium but not yet consented: the coach sends messages to the third-party AI, so require
  // explicit consent first (Apple 5.1.2(i)) rather than dead-ending on a 403.
  if (!hasAiConsent(user)) {
    return (
      <SafeAreaView style={styles.flex} edges={['top']}>
        <AiConsentCard />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <FlatList
          data={messages}
          keyExtractor={(m) => m.id}
          contentContainerStyle={styles.list}
          ListEmptyComponent={
            <View style={styles.suggestWrap}>
              <Text style={styles.suggestTitle}>Ask me anything about your search:</Text>
              {suggestions.map((s) => (
                <Pressable
                  key={s}
                  style={styles.suggest}
                  onPress={() => send(s)}
                  accessibilityRole="button"
                  accessibilityLabel={s}
                >
                  <Text style={styles.suggestText}>{s}</Text>
                </Pressable>
              ))}
            </View>
          }
          renderItem={({ item }) => (
            <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : styles.aiBubble]}>
              <Text style={styles.bubbleText}>{item.content}</Text>
              {item.role === 'assistant' ? (
                <ReportButton contentType="coach" contentRef={sessionId} contentExcerpt={item.content} />
              ) : null}
            </View>
          )}
        />
        {error ? (
          <Text
            style={styles.error}
            accessibilityRole="alert"
            accessibilityLiveRegion="polite"
          >
            {error}
          </Text>
        ) : null}
        {sending ? <ActivityIndicator color={colors.primary} style={{ marginBottom: spacing.sm }} /> : null}
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            accessibilityLabel="Message to your AI career coach"
            placeholder="Type a message…"
            placeholderTextColor={colors.textMuted}
            multiline
          />
          <Pressable
            style={[styles.sendBtn, !canSend && styles.sendBtnDisabled]}
            onPress={() => send(input)}
            disabled={!canSend}
            accessibilityRole="button"
            accessibilityLabel="Send message"
            accessibilityState={{ disabled: !canSend }}
          >
            <Text style={styles.sendText}>Send</Text>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center', padding: spacing.lg, gap: spacing.md },
  lockTitle: { color: colors.text, fontSize: 22, fontWeight: '800', textAlign: 'center' },
  lockBody: { color: colors.textMuted, textAlign: 'center', lineHeight: 21 },
  list: { padding: spacing.md, gap: spacing.sm },
  suggestWrap: { gap: spacing.sm, marginTop: spacing.md },
  suggestTitle: { color: colors.textMuted, marginBottom: spacing.xs },
  suggest: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  suggestText: { color: colors.text },
  bubble: { maxWidth: '85%', borderRadius: radius.lg, padding: spacing.md },
  userBubble: { alignSelf: 'flex-end', backgroundColor: colors.primary },
  aiBubble: { alignSelf: 'flex-start', backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  bubbleText: { color: colors.text, lineHeight: 20 },
  error: { color: colors.danger, paddingHorizontal: spacing.md, marginBottom: spacing.xs },
  inputRow: { flexDirection: 'row', padding: spacing.sm, gap: spacing.sm, borderTopWidth: 1, borderTopColor: colors.border },
  input: {
    flex: 1,
    backgroundColor: colors.surfaceAlt,
    borderRadius: radius.md,
    color: colors.text,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    maxHeight: 120,
  },
  sendBtn: { backgroundColor: colors.primary, borderRadius: radius.md, paddingHorizontal: spacing.md, justifyContent: 'center' },
  sendBtnDisabled: { opacity: 0.5 },
  sendText: { color: colors.primaryText, fontWeight: '700' },
});
