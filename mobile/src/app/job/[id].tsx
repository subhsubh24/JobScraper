import { router, Stack, useLocalSearchParams, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, type DimensionValue, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Button, Card, ErrorBanner, Field } from '@/components/ui';
import { Markdown } from '@/components/markdown';
import { ReportButton } from '@/components/report-button';
import { ArtifactActions } from '@/components/artifact-actions';
import { useAiConsent } from '@/components/ai-consent';
import { useAuth } from '@/contexts/auth';
import { api, ApiError } from '@/services/api';
import { colors, radius, scoreColor, spacing } from '@/theme';
import { STATUS_LABELS, type ApplicationStatus, type Job, type Readiness } from '@/types';

const STATUS_ORDER: ApplicationStatus[] = [
  'saved',
  'applied',
  'phone_screen',
  'interview',
  'offer',
  'rejected',
  'withdrawn',
];

export default function JobDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user } = useAuth();
  const [job, setJob] = useState<Job | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // The status the user is committing right now, or null when idle. A single in-flight update at a
  // time serializes the PATCHes so a slow earlier response can't land AFTER a faster later one and
  // silently revert the user's most recent choice, and it disables the row so a slow network can't
  // read as a dead tap → double-submit.
  const [statusUpdating, setStatusUpdating] = useState<ApplicationStatus | null>(null);
  const [prepLoading, setPrepLoading] = useState(false);
  const [prep, setPrep] = useState<{ id: string; title: string; content: string } | null>(null);
  const [prepMsg, setPrepMsg] = useState<string | null>(null);
  const [targetSalary, setTargetSalary] = useState('');
  const [negLoading, setNegLoading] = useState(false);
  const [neg, setNeg] = useState<{ id: string; title: string; content: string } | null>(null);
  const [negMsg, setNegMsg] = useState<string | null>(null);
  const [letterLoading, setLetterLoading] = useState(false);
  const [letter, setLetter] = useState<{ id: string; title: string; content: string } | null>(null);
  const [letterMsg, setLetterMsg] = useState<string | null>(null);
  const [studyLoading, setStudyLoading] = useState(false);
  const [studyPlan, setStudyPlan] = useState<{ id: string; title: string; content: string } | null>(null);
  const [studyMsg, setStudyMsg] = useState<string | null>(null);
  const [studyDays, setStudyDays] = useState('7');
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resume, setResume] = useState<{ id: string; title: string; content: string } | null>(null);
  const [resumeMsg, setResumeMsg] = useState<string | null>(null);
  const isCareerPlus = user?.career_plus === true;
  // Pro (paid) tier: Pro AND Career+ are both PREMIUM. Gates the cover-letter + study-plan tools.
  const isPaid = user?.tier === 'premium';
  // Third-party-AI consent gate (Apple 5.1.2(i)) — prep + salary send resume/JD to Gemini.
  const { ensureConsent, dialog: consentDialog } = useAiConsent();

  const load = useCallback(async () => {
    if (!id) return;
    try {
      // Readiness is a FREE, independent read — never let it break the job screen: on any error
      // the card simply doesn't render (graceful degrade), the job still loads.
      const [j, r] = await Promise.all([api.getJob(id), api.getReadiness(id).catch(() => null)]);
      setJob(j);
      setReadiness(r);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load this job.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  // Re-read readiness after a signal changes on THIS screen (a prep artifact generated) so the
  // score reflects real, just-completed work. Best-effort — a failure never disturbs the screen.
  const refreshReadiness = useCallback(async () => {
    if (!id) return;
    setReadiness(await api.getReadiness(id).catch(() => null));
  }, [id]);

  useEffect(() => {
    // load() sets state asynchronously after the fetch resolves, not synchronously.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  async function setStatus(status: ApplicationStatus) {
    if (!id) return;
    // Serialize: ignore a new tap while one update is in flight (prevents the out-of-order race
    // where a slower earlier response overwrites a faster later one, reverting the user's choice).
    if (statusUpdating !== null) return;
    setStatusUpdating(status);
    try {
      setJob(await api.updateJobStatus(id, status));
    } catch (e) {
      Alert.alert('Update failed', e instanceof ApiError ? e.message : 'Try again.');
    } finally {
      setStatusUpdating(null);
    }
  }

  async function generatePrep() {
    if (!id) return;
    setPrepMsg(null);
    // Get explicit AI consent before sending resume/job text to the AI provider.
    if (!(await ensureConsent())) return;
    setPrepLoading(true);
    try {
      // Render the full pack inline (scrollable) instead of a truncated, ephemeral alert —
      // the prep pack is the value, the user needs to read all of it and come back to it.
      setPrep(await api.generatePrepPack(id));
      refreshReadiness();
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        router.push('/paywall');
      } else if (e instanceof ApiError) {
        setPrepMsg(e.message); // 503 (AI not configured) and other API errors, honestly inline
      } else {
        setPrepMsg('Could not generate a prep pack. Please try again.');
      }
    } finally {
      setPrepLoading(false);
    }
  }

  async function generateCoverLetter() {
    if (!id) return;
    setLetterMsg(null);
    if (!(await ensureConsent())) return;
    setLetterLoading(true);
    try {
      setLetter(await api.generateCoverLetter(id));
      refreshReadiness();
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        router.push('/paywall');
      } else if (e instanceof ApiError) {
        setLetterMsg(e.message); // 503 (AI not configured) and other API errors, honestly inline
      } else {
        setLetterMsg('Could not generate a cover letter. Please try again.');
      }
    } finally {
      setLetterLoading(false);
    }
  }

  async function generateStudyPlan() {
    if (!id) return;
    // Bound days client-side to match the server (1–30) so a bad value never burns an LLM call.
    const days = Math.round(Number(studyDays));
    if (!Number.isFinite(days) || days < 1 || days > 30) {
      setStudyMsg('Enter how many days you have to prep (1–30).');
      return;
    }
    setStudyMsg(null);
    if (!(await ensureConsent())) return;
    setStudyLoading(true);
    try {
      setStudyPlan(await api.generateStudyPlan(id, days));
      refreshReadiness();
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        router.push('/paywall');
      } else if (e instanceof ApiError) {
        setStudyMsg(e.message);
      } else {
        setStudyMsg('Could not generate a study plan. Please try again.');
      }
    } finally {
      setStudyLoading(false);
    }
  }

  async function generateTailoredResume() {
    if (!id) return;
    setResumeMsg(null);
    if (!(await ensureConsent())) return;
    setResumeLoading(true);
    try {
      setResume(await api.generateTailoredResume(id));
      refreshReadiness();
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        router.push('/paywall');
      } else if (e instanceof ApiError) {
        setResumeMsg(e.message); // 400 (no saved résumé), 503 (no key), other errors — honestly inline
      } else {
        setResumeMsg('Could not generate a tailored résumé. Please try again.');
      }
    } finally {
      setResumeLoading(false);
    }
  }

  async function generateNegotiation() {
    if (!id) return;
    // Round BEFORE validating: "0.4" is > 0 but rounds to 0, which we must reject client-side
    // to match the backend (target_salary is gt=0) and avoid a pointless round-trip. Validate
    // the value we actually send.
    const parsed = Math.round(Number(targetSalary));
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setNegMsg('Enter your target salary (a positive number).');
      return;
    }
    if (parsed > 10_000_000) {
      setNegMsg('Enter a realistic target salary.');
      return;
    }
    setNegMsg(null);
    if (!(await ensureConsent())) return;
    setNegLoading(true);
    try {
      setNeg(await api.generateSalaryNegotiation(id, parsed));
    } catch (e) {
      // The UI already gates this to Career+, but the server is the source of truth — if it
      // says 403, route to the paywall rather than dead-end.
      if (e instanceof ApiError && e.status === 403) {
        router.push('/paywall');
      } else if (e instanceof ApiError) {
        setNegMsg(e.message); // 503 (AI not configured) and other API errors, honestly inline
      } else {
        setNegMsg('Could not generate a negotiation guide. Please try again.');
      }
    } finally {
      setNegLoading(false);
    }
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} size="large" />
      </View>
    );
  }

  if (error || !job) {
    return (
      <View style={styles.center}>
        <View style={styles.errorWrap}>
          <ErrorBanner
            message={error ?? 'Job not found.'}
            onRetry={() => {
              setError(null);
              setLoading(true);
              load();
            }}
          />
        </View>
        <Button label="Go back" variant="secondary" onPress={() => router.back()} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.flex} contentContainerStyle={styles.container}>
      {consentDialog}
      <Stack.Screen options={{ title: job.company ?? 'Job' }} />
      <Text style={styles.title}>{job.title}</Text>
      <Text style={styles.company}>
        {job.company}
        {job.location ? ` · ${job.location}` : ''}
      </Text>

      <Card style={styles.scoreCard}>
        <Text style={[styles.scoreNum, { color: scoreColor(job.score == null ? job.score : Math.round(job.score)) }]}>
          {job.score == null ? '—' : Math.round(job.score)}
          <Text style={styles.scoreOutOf}> / 100</Text>
        </Text>
        <Text style={styles.scoreLabel}>Fit score</Text>
        {job.score_explanation ? <Text style={styles.explain}>{job.score_explanation}</Text> : null}
      </Card>

      {readiness && id ? <ReadinessCard readiness={readiness} jobId={id} /> : null}

      <Text style={styles.section}>Pipeline status</Text>
      <View style={styles.statusGrid} accessibilityRole="radiogroup" accessibilityLabel="Pipeline status">
        {STATUS_ORDER.map((s) => {
          const active = job.status === s;
          const busy = statusUpdating !== null;
          const pending = statusUpdating === s;
          return (
            <Pressable
              key={s}
              onPress={() => setStatus(s)}
              disabled={busy}
              // A screen reader otherwise just announces "Saved" with no hint that it's a
              // selectable status or which one is current. Expose it as a radio option so the
              // pipeline tracker — the core loop — is operable with VoiceOver/TalkBack.
              accessibilityRole="radio"
              accessibilityState={{ selected: active, busy: pending, disabled: busy }}
              accessibilityLabel={`Set status to ${STATUS_LABELS[s]}`}
              // Dim only the OTHER (locked) chips; the one being committed keeps full opacity and
              // shows a spinner so the user can see WHICH status is saving, not just that the whole
              // row went inert (matches the interview past-sessions "tapped row shows a spinner" idiom).
              style={[styles.statusChip, active && styles.statusChipActive, busy && !pending && styles.statusChipBusy]}
            >
              <View style={styles.statusChipInner}>
                {pending ? (
                  <ActivityIndicator size="small" color={active ? colors.primaryText : colors.textMuted} />
                ) : null}
                <Text style={[styles.statusChipText, active && styles.statusChipTextActive]}>
                  {STATUS_LABELS[s]}
                </Text>
              </View>
            </Pressable>
          );
        })}
      </View>

      <Text style={styles.section}>Interview prep</Text>
      <Button
        label={
          prep
            ? 'Regenerate prep pack'
            : user?.tier === 'premium'
              ? 'Generate prep pack'
              : 'Generate prep pack (1 free)'
        }
        onPress={generatePrep}
        loading={prepLoading}
      />
      {prepMsg ? (
        <Text style={styles.prepMsg} accessibilityRole="alert" accessibilityLiveRegion="polite">
          {prepMsg}
        </Text>
      ) : null}
      {prep ? (
        <Card style={styles.prepCard}>
          <Text style={styles.prepTitle}>{prep.title}</Text>
          <Markdown content={prep.content} />
          <ArtifactActions text={prep.content} title={prep.title} />
          <ReportButton contentType="prep_pack" contentRef={prep.id} contentExcerpt={prep.content} />
        </Card>
      ) : null}

      <Text style={styles.section}>Practice interview</Text>
      <Card style={styles.prepCard}>
        <Text style={styles.toolHint}>
          Run a role-specific mock interview — the coach asks questions from this job, scores each
          answer, and shows a model answer.
        </Text>
        <Button label="Start mock interview →" onPress={() => router.push(`/interview/${id}`)} />
      </Card>

      <Text style={styles.section}>Application tools</Text>
      {isPaid ? (
        <>
          <Text style={styles.toolHint}>
            Your résumé rewritten for this role — your real experience reordered and reworded to match the
            posting. Never invents anything you didn&apos;t do.
          </Text>
          <Button
            label={resume ? 'Regenerate tailored résumé' : 'Generate tailored résumé'}
            onPress={generateTailoredResume}
            loading={resumeLoading}
          />
          {resumeMsg ? (
            <Text style={styles.prepMsg} accessibilityRole="alert" accessibilityLiveRegion="polite">
              {resumeMsg}
            </Text>
          ) : null}
          {resume ? (
            <Card style={styles.prepCard}>
              <Text style={styles.prepTitle}>{resume.title}</Text>
              <Markdown content={resume.content} />
              <ArtifactActions text={resume.content} title={resume.title} />
              <ReportButton contentType="prep_pack" contentRef={resume.id} contentExcerpt={resume.content} />
            </Card>
          ) : null}

          <Text style={styles.toolHint}>A tailored cover letter for this role, drawn from your resume.</Text>
          <Button
            label={letter ? 'Regenerate cover letter' : 'Generate cover letter'}
            onPress={generateCoverLetter}
            loading={letterLoading}
          />
          {letterMsg ? (
            <Text style={styles.prepMsg} accessibilityRole="alert" accessibilityLiveRegion="polite">
              {letterMsg}
            </Text>
          ) : null}
          {letter ? (
            <Card style={styles.prepCard}>
              <Text style={styles.prepTitle}>{letter.title}</Text>
              <Markdown content={letter.content} />
              <ArtifactActions text={letter.content} title={letter.title} />
              <ReportButton contentType="prep_pack" contentRef={letter.id} contentExcerpt={letter.content} />
            </Card>
          ) : null}

          <Text style={styles.toolHint}>A day-by-day study plan paced to the time before your interview.</Text>
          <Field
            label="Days to prep (1–30)"
            keyboardType="numeric"
            value={studyDays}
            onChangeText={setStudyDays}
            placeholder="7"
          />
          <Button
            label={studyPlan ? 'Regenerate study plan' : 'Generate study plan'}
            onPress={generateStudyPlan}
            loading={studyLoading}
          />
          {studyMsg ? (
            <Text style={styles.prepMsg} accessibilityRole="alert" accessibilityLiveRegion="polite">
              {studyMsg}
            </Text>
          ) : null}
          {studyPlan ? (
            <Card style={styles.prepCard}>
              <Text style={styles.prepTitle}>{studyPlan.title}</Text>
              <Markdown content={studyPlan.content} />
              <ArtifactActions text={studyPlan.content} title={studyPlan.title} />
              <ReportButton contentType="prep_pack" contentRef={studyPlan.id} contentExcerpt={studyPlan.content} />
            </Card>
          ) : null}
        </>
      ) : (
        <Card style={styles.upsellCard}>
          <Text style={styles.upsellText}>
            Tailored résumés, cover letters, and study plans are a Pro feature.
          </Text>
          <Button label="Upgrade to Pro" onPress={() => router.push('/paywall')} />
        </Card>
      )}

      <Text style={styles.section}>Salary negotiation</Text>
      {isCareerPlus ? (
        <>
          <Field
            label="Your target salary (USD)"
            keyboardType="numeric"
            value={targetSalary}
            onChangeText={setTargetSalary}
            placeholder="180000"
          />
          <Button label="Generate negotiation guide" onPress={generateNegotiation} loading={negLoading} />
          {negMsg ? (
            <Text style={styles.prepMsg} accessibilityRole="alert" accessibilityLiveRegion="polite">
              {negMsg}
            </Text>
          ) : null}
          {neg ? (
            <Card style={styles.prepCard}>
              <Text style={styles.prepTitle}>{neg.title}</Text>
              <Markdown content={neg.content} />
              <ArtifactActions text={neg.content} title={neg.title} />
              <ReportButton contentType="prep_pack" contentRef={neg.id} contentExcerpt={neg.content} />
            </Card>
          ) : null}
        </>
      ) : (
        <Card style={styles.upsellCard}>
          <Text style={styles.upsellText}>
            AI salary-negotiation coaching is a Career+ feature — scripts and strategies tailored to this offer.
          </Text>
          <Button label="Upgrade to Career+" onPress={() => router.push('/paywall')} />
        </Card>
      )}
    </ScrollView>
  );
}

// Where the single next-best-action sends the user. `generate_artifact` has no target — the prep
// tools are already on THIS screen just below — and `ready` is a positive terminal state, so both
// render guidance without a CTA button (never a dead button).
const READINESS_ACTION_TARGET: Record<string, (jobId: string) => Href | null> = {
  add_resume: () => '/(tabs)/settings',
  start_mock_interview: (jobId) => `/interview/${jobId}`,
  answer_question: (jobId) => `/interview/${jobId}`,
  redo_answer: (jobId) => `/interview/${jobId}`,
  generate_artifact: () => null,
  study_skill: () => '/(tabs)/insights',
  ready: () => null,
};

function ReadinessMeter({ label, value }: { label: string; value: number | null }) {
  // value is 0..1 or null (unmeasurable — e.g. no extractable skills in the JD). Honest "n/a".
  const pct = value == null ? null : Math.round(value * 100);
  // Keep a visible sliver at a genuine 0% so an empty component reads as "0%", not a render glitch
  // (matches the interview ProgressBar's Math.max(pct, 4)); n/a stays truly empty.
  const fillPct = pct == null ? 0 : Math.max(pct, 4);
  return (
    <View style={styles.meterRow}>
      <View style={styles.meterHead}>
        <Text style={styles.meterLabel}>{label}</Text>
        <Text style={styles.meterPct}>{pct == null ? 'n/a' : `${pct}%`}</Text>
      </View>
      <View
        style={styles.meterTrack}
        accessibilityRole="progressbar"
        accessibilityLabel={`${label}: ${pct == null ? 'not measured' : `${pct}%`}`}
        accessibilityValue={pct == null ? undefined : { min: 0, max: 100, now: pct }}
      >
        <View style={[styles.meterFill, { width: `${fillPct}%` as DimensionValue }]} />
      </View>
    </View>
  );
}

function ReadinessCard({ readiness, jobId }: { readiness: Readiness; jobId: string }) {
  const { score, components, next_action: next } = readiness;
  const target = (READINESS_ACTION_TARGET[next.action] ?? (() => null))(jobId);
  return (
    <Card style={styles.readinessCard}>
      <View style={styles.readinessHead}>
        <View style={styles.readinessHeadText}>
          <Text style={styles.readinessTitle}>Interview readiness</Text>
          <Text style={styles.readinessSub}>
            How ready you are for this role — it climbs only as you practice, cover its skills, and prep.
          </Text>
        </View>
        <Text style={[styles.readinessScore, { color: scoreColor(score) }]}>
          {score}
          <Text style={styles.readinessScoreOut}> / 100</Text>
        </Text>
      </View>

      <View style={styles.meters}>
        <ReadinessMeter label="Practice" value={components.interview_practice} />
        <ReadinessMeter label="Skill coverage" value={components.skill_coverage} />
        <ReadinessMeter label="Materials" value={components.artifacts} />
      </View>

      <View style={styles.readinessNext}>
        <Text style={styles.readinessEyebrow}>NEXT STEP</Text>
        <Text style={styles.readinessActionLabel}>{next.label}</Text>
        <Text style={styles.readinessActionDetail}>{next.detail}</Text>
        {target ? (
          <View style={styles.readinessCta}>
            <Button label={`${next.label} →`} onPress={() => router.push(target)} />
          </View>
        ) : null}
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center', gap: spacing.md, padding: spacing.lg },
  container: { padding: spacing.md, gap: spacing.sm },
  title: { color: colors.text, fontSize: 24, fontWeight: '800' },
  company: { color: colors.textMuted, marginBottom: spacing.md },
  scoreCard: { alignItems: 'center', marginBottom: spacing.md },
  scoreNum: { fontSize: 44, fontWeight: '800' },
  scoreOutOf: { fontSize: 18, color: colors.textMuted, fontWeight: '600' },
  scoreLabel: { color: colors.textMuted, marginTop: spacing.xs },
  explain: { color: colors.text, marginTop: spacing.sm, textAlign: 'center', lineHeight: 20 },
  section: { color: colors.text, fontSize: 16, fontWeight: '700', marginTop: spacing.md, marginBottom: spacing.sm },
  statusGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  statusChip: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  statusChipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  statusChipBusy: { opacity: 0.5 },
  statusChipInner: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  statusChipText: { color: colors.textMuted, fontWeight: '600' },
  statusChipTextActive: { color: colors.primaryText },
  errorWrap: { alignSelf: 'stretch' },
  prepMsg: { color: colors.danger, fontSize: 13, marginTop: spacing.sm },
  toolHint: { color: colors.textMuted, fontSize: 13, marginBottom: spacing.sm, lineHeight: 18 },
  prepCard: { marginTop: spacing.md, gap: spacing.sm },
  prepTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
  upsellCard: { gap: spacing.md, alignItems: 'flex-start' },
  upsellText: { color: colors.text, lineHeight: 20 },
  readinessCard: { marginBottom: spacing.md, gap: spacing.md },
  readinessHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: spacing.md },
  readinessHeadText: { flex: 1 },
  readinessTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
  readinessSub: { color: colors.textMuted, fontSize: 13, marginTop: 2, lineHeight: 18 },
  readinessScore: { fontSize: 32, fontWeight: '800' },
  readinessScoreOut: { fontSize: 14, color: colors.textMuted, fontWeight: '600' },
  meters: { gap: spacing.sm },
  meterRow: { gap: 4 },
  meterHead: { flexDirection: 'row', justifyContent: 'space-between' },
  meterLabel: { color: colors.textMuted, fontSize: 12 },
  meterPct: { color: colors.textMuted, fontSize: 12 },
  meterTrack: { height: 6, borderRadius: 999, backgroundColor: colors.surfaceAlt, overflow: 'hidden' },
  meterFill: { height: '100%', borderRadius: 999, backgroundColor: colors.primary },
  readinessNext: { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: spacing.md },
  readinessEyebrow: { color: colors.primary, fontSize: 11, fontWeight: '700', letterSpacing: 0.5 },
  readinessActionLabel: { color: colors.text, fontSize: 15, fontWeight: '700', marginTop: 4 },
  readinessActionDetail: { color: colors.textMuted, fontSize: 13, marginTop: 2, lineHeight: 18 },
  readinessCta: { marginTop: spacing.md, alignItems: 'flex-start' },
});
