import { router, Stack, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, ErrorBanner, Field } from '@/components/ui';
import { ReportButton } from '@/components/report-button';
import { AiConsentCard, hasAiConsent } from '@/components/ai-consent';
import { useAuth } from '@/contexts/auth';
import {
  api,
  ApiError,
  type MockInterviewAnswer,
  type MockInterviewSession,
  type MockInterviewSummary,
} from '@/services/api';
import { colors, radius, spacing } from '@/theme';

// The interview-coaching pillar (north-star surface 3): a realistic, role-specific mock interview.
// JD-derived questions one at a time; the user answers; each answer is scored (relevance /
// specificity / STAR) with concrete feedback + a model answer. Honest — a weak answer scores low;
// the score is the server's, shown only after the real POST resolves.
export default function MockInterviewScreen() {
  const { jobId } = useLocalSearchParams<{ jobId: string }>();
  const id = jobId ?? '';
  const { user } = useAuth();
  const isPaid = user?.tier === 'premium';
  const consented = hasAiConsent(user);

  const [sessions, setSessions] = useState<MockInterviewSummary[]>([]);
  const [interview, setInterview] = useState<MockInterviewSession | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [numQuestions, setNumQuestions] = useState(5);
  const [starting, setStarting] = useState(false);
  const [startMsg, setStartMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setSessions(await api.listMockInterviews(id));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load this interview.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    // load() setStates asynchronously after the fetch resolves, not synchronously.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  async function start() {
    setStartMsg(null);
    setStarting(true);
    try {
      const iv = await api.startMockInterview(id, numQuestions);
      setInterview(iv);
      setActiveIndex(0);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        router.push('/paywall');
        return;
      }
      setStartMsg(e instanceof ApiError ? e.message : 'Could not start the interview — try again.');
    } finally {
      setStarting(false);
    }
  }

  async function openSession(interviewId: string) {
    setStartMsg(null);
    try {
      const iv = await api.getMockInterview(interviewId);
      setInterview(iv);
      const answered = new Set(iv.answers.map((a) => a.question_index));
      const firstUnanswered = iv.questions.findIndex((_q, i) => !answered.has(i));
      setActiveIndex(firstUnanswered === -1 ? Math.max(iv.questions.length - 1, 0) : firstUnanswered);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        router.push('/paywall');
        return;
      }
      setStartMsg(e instanceof ApiError ? e.message : 'Could not open that session.');
    }
  }

  function exitSession() {
    setInterview(null);
    setLoading(true);
    void load();
  }

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <Stack.Screen options={{ title: 'Mock interview' }} />
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : error ? (
        <ErrorBanner message={error} onRetry={() => { setLoading(true); void load(); }} />
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.title}>Mock interview</Text>
          {interview ? (
            <InterviewRunner
              interview={interview}
              activeIndex={activeIndex}
              onSetActiveIndex={setActiveIndex}
              onUpdate={setInterview}
              onExit={exitSession}
            />
          ) : (
            <StartScreen
              isPaid={isPaid}
              consented={consented}
              sessions={sessions}
              numQuestions={numQuestions}
              starting={starting}
              startMsg={startMsg}
              onSetNumQuestions={setNumQuestions}
              onStart={start}
              onOpen={openSession}
            />
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

function StartScreen({
  isPaid,
  consented,
  sessions,
  numQuestions,
  starting,
  startMsg,
  onSetNumQuestions,
  onStart,
  onOpen,
}: {
  isPaid: boolean;
  consented: boolean;
  sessions: MockInterviewSummary[];
  numQuestions: number;
  starting: boolean;
  startMsg: string | null;
  onSetNumQuestions: (n: number) => void;
  onStart: () => void;
  onOpen: (id: string) => void;
}) {
  return (
    <View style={styles.stack}>
      <Card style={styles.section}>
        <Text style={styles.sectionHeading}>Practice for this role</Text>
        <Text style={styles.bodyText}>
          The coach asks questions drawn from this job, one at a time. Answer in your own words and
          get scored feedback — relevance, specificity, and structure — plus a model answer.
        </Text>

        {!isPaid ? (
          <View style={styles.upsell}>
            <Text style={styles.bodyText}>Mock interviews are a Pro feature.</Text>
            <Button label="Upgrade to Pro" onPress={() => router.push('/paywall')} />
          </View>
        ) : !consented ? (
          <AiConsentCard />
        ) : (
          <View style={styles.stack}>
            <Text style={styles.pickerLabel}>NUMBER OF QUESTIONS</Text>
            <View style={styles.pickerRow} accessibilityRole="radiogroup">
              {[3, 4, 5, 6, 7, 8].map((n) => {
                const selected = n === numQuestions;
                return (
                  <Pressable
                    key={n}
                    accessibilityRole="radio"
                    accessibilityState={{ selected }}
                    accessibilityLabel={`${n} questions`}
                    onPress={() => onSetNumQuestions(n)}
                    style={[styles.pickerChip, selected && styles.pickerChipSelected]}
                  >
                    <Text style={[styles.pickerChipText, selected && styles.pickerChipTextSelected]}>
                      {n}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
            <Button
              label={starting ? 'Preparing your questions…' : 'Start mock interview'}
              onPress={onStart}
              disabled={starting}
              loading={starting}
            />
            {startMsg ? (
              <Text style={styles.error} accessibilityRole="alert" accessibilityLiveRegion="polite">
                {startMsg}
              </Text>
            ) : null}
          </View>
        )}
      </Card>

      {sessions.length > 0 ? (
        <Card style={styles.section}>
          <Text style={styles.pickerLabel}>YOUR PAST SESSIONS</Text>
          {sessions.map((s) => (
            <Pressable
              key={s.id}
              accessibilityRole="button"
              // Explicit label so a screen reader announces ONE complete, meaningful row —
              // status + progress + the action — instead of a bare "button" or two fragmented
              // Text nodes (child-text aggregation on a Pressable is platform-dependent).
              accessibilityLabel={`${
                s.status === 'completed' ? 'Completed' : 'In progress'
              } interview, ${s.answered_count} of ${s.total} answered. ${
                s.status === 'completed' ? 'Review' : 'Resume'
              }.`}
              onPress={() => onOpen(s.id)}
              style={styles.sessionRow}
            >
              <Text style={styles.sessionText}>
                {s.status === 'completed' ? 'Completed' : 'In progress'} · {s.answered_count}/
                {s.total} answered
              </Text>
              <Text style={styles.sessionCta}>{s.status === 'completed' ? 'Review' : 'Resume'}</Text>
            </Pressable>
          ))}
        </Card>
      ) : null}
    </View>
  );
}

function InterviewRunner({
  interview,
  activeIndex,
  onSetActiveIndex,
  onUpdate,
  onExit,
}: {
  interview: MockInterviewSession;
  activeIndex: number;
  onSetActiveIndex: (i: number) => void;
  onUpdate: (iv: MockInterviewSession) => void;
  onExit: () => void;
}) {
  const [answer, setAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [reAnswer, setReAnswer] = useState(false);

  const total = interview.questions.length;
  const question = interview.questions[activeIndex];
  const scored = interview.answers.find((a) => a.question_index === activeIndex) ?? null;
  const answeredCount = interview.answers.length;
  const completed = interview.status === 'completed';

  useEffect(() => {
    // Reset the local draft when the active question changes (intentional derived reset).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAnswer('');
    setMsg(null);
    setReAnswer(false);
  }, [activeIndex]);

  async function submit() {
    if (!answer.trim()) {
      setMsg('Type your answer first.');
      return;
    }
    setMsg(null);
    setSubmitting(true);
    try {
      const submitted = answer.trim();
      const res = await api.answerMockInterview(interview.id, activeIndex, submitted);
      // The POST result echoes the scores but not the answer text; carry the answer we just
      // submitted so the in-memory entry is complete and type-accurate (GET returns it on reload).
      const scoredEntry: MockInterviewAnswer = { ...res.result, answer: submitted };
      const next: MockInterviewSession = {
        ...interview,
        status: res.status,
        answers: [
          ...interview.answers.filter((a) => a.question_index !== activeIndex),
          scoredEntry,
        ].sort((a, b) => a.question_index - b.question_index),
        answered_count: res.answered_count,
      };
      onUpdate(next);
      setReAnswer(false);
    } catch (e) {
      // The server is the source of truth: a 403 mid-session (Pro lapsed / consent revoked on
      // another device) must route to the paywall, not trap the user with an inline-only error —
      // same contract as every generator in job/[id].tsx.
      if (e instanceof ApiError && e.status === 403) {
        router.push('/paywall');
        return;
      }
      setMsg(e instanceof ApiError ? e.message : 'Could not score your answer — try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (!question) return null;

  const pct = total > 0 ? Math.round((answeredCount / total) * 100) : 0;

  return (
    <View style={styles.stack}>
      <View style={styles.progressWrap}>
        <View style={styles.progressHeader}>
          <Text style={styles.progressText}>
            {completed ? 'Interview complete' : `${answeredCount} of ${total} answered`}
          </Text>
          <Text style={styles.progressText}>{pct}%</Text>
        </View>
        <View
          style={styles.track}
          accessibilityRole="image"
          accessibilityLabel={`${pct}% complete`}
        >
          <View
            style={[styles.bar, { width: `${Math.max(pct, 4)}%` }, completed && styles.barDone]}
          />
        </View>
      </View>

      <Card style={styles.section}>
        <Text style={styles.questionMeta}>
          {question.category === 'technical' ? 'TECHNICAL' : 'BEHAVIORAL'} · QUESTION{' '}
          {activeIndex + 1} OF {total}
        </Text>
        <Text style={styles.question}>{question.question}</Text>

        {scored && !reAnswer ? (
          <ScoreResult
            scored={scored}
            contentRef={`${interview.id}:${activeIndex}`}
            onPracticeAgain={() => setReAnswer(true)}
          />
        ) : (
          <View style={styles.stack}>
            <Field
              label="Your answer"
              value={answer}
              onChangeText={setAnswer}
              multiline
              numberOfLines={6}
              maxLength={8000}
              placeholder="Answer in your own words — be specific, use a real example."
              style={styles.answerInput}
            />
            <Button
              label={submitting ? 'Scoring…' : scored ? 'Re-submit answer' : 'Submit answer'}
              onPress={submit}
              disabled={submitting}
              loading={submitting}
            />
            {scored ? (
              <Button label="Cancel" variant="secondary" onPress={() => setReAnswer(false)} />
            ) : null}
            {msg ? (
              <Text style={styles.error} accessibilityRole="alert" accessibilityLiveRegion="polite">
                {msg}
              </Text>
            ) : null}
          </View>
        )}
      </Card>

      <View style={styles.navRow}>
        <Button
          label="← Previous"
          variant="secondary"
          onPress={() => onSetActiveIndex(Math.max(activeIndex - 1, 0))}
          disabled={activeIndex === 0}
        />
        {activeIndex < total - 1 ? (
          <Button
            label="Next →"
            variant="secondary"
            onPress={() => onSetActiveIndex(activeIndex + 1)}
          />
        ) : (
          <Button label="Done" variant="secondary" onPress={onExit} />
        )}
      </View>
    </View>
  );
}

function ScoreResult({
  scored,
  contentRef,
  onPracticeAgain,
}: {
  scored: MockInterviewAnswer;
  contentRef: string;
  onPracticeAgain: () => void;
}) {
  return (
    <View style={styles.scoreCard}>
      <View style={styles.scoreHeader}>
        <Text style={styles.scoreLabel}>Your answer scored</Text>
        <Text style={styles.scoreValue}>
          {Math.round(scored.overall)}
          <Text style={styles.scoreOutOf}>/100</Text>
        </Text>
      </View>
      <View style={styles.scoreBars}>
        <ScoreBar label="Relevance" value={scored.relevance} />
        <ScoreBar label="Specificity" value={scored.specificity} />
        <ScoreBar label="Structure" value={scored.star} />
      </View>
      <Text style={styles.scoreSectionTitle}>Feedback</Text>
      <Text style={styles.bodyText}>{scored.feedback}</Text>
      {scored.model_answer ? (
        <>
          <Text style={styles.scoreSectionTitle}>A strong answer</Text>
          <Text style={styles.modelAnswer}>{scored.model_answer}</Text>
        </>
      ) : null}
      <Pressable accessibilityRole="button" onPress={onPracticeAgain}>
        <Text style={styles.practiceAgain}>Practice this answer again</Text>
      </Pressable>
      <ReportButton
        contentType="mock_interview"
        contentRef={contentRef}
        contentExcerpt={`${scored.feedback}\n\n${scored.model_answer}`}
      />
    </View>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round((Math.max(0, Math.min(value, 5)) / 5) * 100);
  return (
    <View style={styles.scoreBarRow}>
      <View style={styles.scoreBarHeader}>
        <Text style={styles.scoreBarLabel}>{label}</Text>
        <Text style={styles.scoreBarValue}>{value}/5</Text>
      </View>
      <View style={styles.scoreBarTrack}>
        <View style={[styles.scoreBarFill, { width: `${Math.max(pct, 4)}%` }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  content: { padding: spacing.md, gap: spacing.md },
  stack: { gap: spacing.md },
  title: { color: colors.text, fontSize: 24, fontWeight: '800' },
  section: { gap: spacing.sm },
  sectionHeading: { color: colors.text, fontSize: 18, fontWeight: '700' },
  bodyText: { color: colors.text, lineHeight: 20 },
  upsell: { gap: spacing.sm, marginTop: spacing.sm },
  pickerLabel: { color: colors.textMuted, fontSize: 12, fontWeight: '700', letterSpacing: 0.5 },
  pickerRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  pickerChip: {
    minWidth: 44,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  pickerChipSelected: { borderColor: colors.primary, backgroundColor: 'rgba(99,102,241,0.15)' },
  pickerChipText: { color: colors.textMuted, fontWeight: '600' },
  pickerChipTextSelected: { color: colors.text },
  sessionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surfaceAlt,
  },
  sessionText: { color: colors.text, flexShrink: 1 },
  sessionCta: { color: colors.primary, fontWeight: '600' },
  progressWrap: { gap: spacing.xs },
  progressHeader: { flexDirection: 'row', justifyContent: 'space-between' },
  progressText: { color: colors.textMuted, fontSize: 12 },
  track: { height: 8, borderRadius: radius.sm, backgroundColor: colors.surfaceAlt, overflow: 'hidden' },
  bar: { height: '100%', borderRadius: radius.sm, backgroundColor: colors.primary },
  barDone: { backgroundColor: colors.success },
  questionMeta: { color: colors.primary, fontSize: 12, fontWeight: '700', letterSpacing: 0.5 },
  question: { color: colors.text, fontSize: 17, fontWeight: '600', lineHeight: 24 },
  answerInput: { minHeight: 120, textAlignVertical: 'top' },
  navRow: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.md },
  error: { color: colors.danger },
  scoreCard: {
    gap: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surfaceAlt,
  },
  scoreHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  scoreLabel: { color: colors.textMuted, fontWeight: '600' },
  scoreValue: { color: colors.text, fontSize: 26, fontWeight: '800' },
  scoreOutOf: { color: colors.textMuted, fontSize: 14, fontWeight: '500' },
  scoreBars: { gap: spacing.sm },
  scoreBarRow: { gap: spacing.xs },
  scoreBarHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  scoreBarLabel: { color: colors.textMuted, fontSize: 12 },
  scoreBarValue: { color: colors.text, fontSize: 12, fontWeight: '600' },
  scoreBarTrack: { height: 6, borderRadius: radius.sm, backgroundColor: colors.surface, overflow: 'hidden' },
  scoreBarFill: { height: '100%', borderRadius: radius.sm, backgroundColor: colors.primary },
  scoreSectionTitle: { color: colors.text, fontSize: 14, fontWeight: '700', marginTop: spacing.xs },
  modelAnswer: { color: colors.textMuted, lineHeight: 20 },
  practiceAgain: { color: colors.primary, fontWeight: '600', marginTop: spacing.xs },
});
