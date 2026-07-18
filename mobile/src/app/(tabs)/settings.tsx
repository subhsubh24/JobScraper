import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Alert, Pressable, ScrollView, Share, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, Field } from '@/components/ui';
import { AiConsentSetting } from '@/components/ai-consent';
import { useAuth } from '@/contexts/auth';
import { api, ApiError } from '@/services/api';
import { colors, spacing } from '@/theme';
import type { Competency, ReferralStats } from '@/types';

// Mobile parity with the web "Résumé" card. The résumé powers fit scoring, tailored résumés,
// cover letters, and the skill-gap heatmap — several of those tell the user to add it "in
// Settings", so this is the reachable place to do so. Available to every tier (core input).
function ResumeCard() {
  const [resume, setResume] = useState<string | null>(null); // null = still loading
  const [saved, setSaved] = useState('');
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .getResume()
      .then((text) => {
        if (!active) return;
        setResume(text);
        setSaved(text);
      })
      .catch(() => active && setError('Could not load your résumé. Reopen Settings to try again.'));
    return () => {
      active = false;
    };
  }, []);

  const dirty = resume !== null && resume !== saved;

  async function save() {
    if (resume === null || saving || !dirty) return;
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      // Await the real PATCH; only reflect "saved" once the server confirms it.
      const hasResume = await api.saveResume(resume);
      setSaved(resume);
      setNotice(hasResume ? 'Résumé saved.' : 'Résumé cleared.');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not save your résumé. Try again.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <Text style={styles.referTitle}>Résumé</Text>
      <Text style={styles.referBody}>
        Paste your résumé as text. It powers your fit scores, tailored résumés, cover letters, and
        skill-gap heatmap — the more complete it is, the sharper they get.
      </Text>
      {resume === null ? (
        // Before the résumé loads, `resume` is null. If the initial GET fails we must surface
        // the error HERE — otherwise the card stays stuck on "Loading…" forever and the error
        // text below (only rendered once `resume` is non-null) is unreachable: a dead end on the
        // core résumé input. On failure we keep the editor hidden (don't present an empty field
        // that could overwrite a résumé that merely failed to load) and show the retry message.
        error ? (
          <Text style={styles.errorText}>{error}</Text>
        ) : (
          <Text style={styles.referStats}>Loading your résumé…</Text>
        )
      ) : (
        <>
          <Field
            label="Your résumé text"
            value={resume}
            onChangeText={(t) => {
              setResume(t);
              setNotice(null);
            }}
            placeholder="Paste your résumé here — experience, skills, achievements…"
            multiline
            numberOfLines={8}
            maxLength={50000}
            style={styles.resumeInput}
          />
          <Button
            label={saving ? 'Saving…' : 'Save résumé'}
            onPress={save}
            loading={saving}
            disabled={!dirty}
          />
          {notice ? <Text style={styles.savedText}>{notice}</Text> : null}
          {error ? <Text style={styles.errorText}>{error}</Text> : null}
        </>
      )}
    </Card>
  );
}

// Mobile parity with the web "Profile enrichment" card: import skills from the user's public
// GitHub (Pro+). Structured, factual data (repo languages/topics) that sharpens fit scores +
// cover letters — nothing invented. Honest states: reports the real found count / message.
function GithubEnrichmentCard() {
  const { user } = useAuth();
  const isPro = user?.tier === 'premium';
  const [competencies, setCompetencies] = useState<Competency[] | null>(null);
  const [handle, setHandle] = useState('');
  const [importing, setImporting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isPro) return;
    let active = true;
    api
      .getEnrichment()
      // Honest degrade: a FAILED load must not masquerade as "no skills imported". Setting
      // competencies to [] on error erases the user's imported skills from view — a user who
      // had skills opens Settings, the fetch fails, and they silently vanish with no error.
      // Keep competencies null (unknown) and surface the failure, mirroring the résumé card.
      .then((c) => active && setCompetencies(c))
      .catch(
        () => active && setError('Could not load your imported skills. Reopen Settings to try again.'),
      );
    return () => {
      active = false;
    };
  }, [isPro]);

  async function importGithub() {
    const value = handle.trim();
    if (!value || importing) return;
    setImporting(true);
    setNotice(null);
    setError(null);
    try {
      const result = await api.enrichGithub(value);
      setCompetencies(result.competencies);
      setNotice(result.message);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not import from GitHub. Try again.');
    } finally {
      setImporting(false);
    }
  }

  async function clearAll() {
    try {
      await api.clearEnrichment();
      setCompetencies([]);
      setNotice(null);
      setError(null);
    } catch {
      setError('Could not clear your imported skills. Try again.');
    }
  }

  return (
    <Card>
      <Text style={styles.referTitle}>Profile enrichment</Text>
      <Text style={styles.referBody}>
        Import skills from your public GitHub — repo languages and topics sharpen your fit scores
        and cover letters. Nothing is invented; we only read your public repos.
      </Text>
      {/* Gate like the Insights learning-plan card: SHOW the feature to free users with an
          upgrade CTA (discoverability/conversion), never hide it. */}
      {!isPro ? (
        <>
          <Text style={styles.proNote}>A Pro feature.</Text>
          <Button label="Upgrade to Pro" onPress={() => router.push('/paywall')} />
        </>
      ) : (
        <>
          <Field
            label="GitHub username or profile URL"
            value={handle}
            onChangeText={setHandle}
            placeholder="github.com/yourname"
            autoCapitalize="none"
            autoCorrect={false}
          />
          <Button
            label={importing ? 'Importing…' : 'Import'}
            onPress={importGithub}
            loading={importing}
            disabled={!handle.trim()}
          />
          {notice ? <Text style={styles.referStats}>{notice}</Text> : null}
          {error ? <Text style={styles.errorText}>{error}</Text> : null}
          {competencies && competencies.length > 0 ? (
            <>
              <View style={styles.chipWrap}>
                {competencies.map((c) => (
                  <View key={`${c.source_type}:${c.skill}`} style={styles.chip}>
                    <Text style={styles.chipText}>{c.skill}</Text>
                  </View>
                ))}
              </View>
              <Pressable accessibilityRole="button" onPress={clearAll} style={styles.clearBtn}>
                <Text style={styles.clearText}>Clear imported skills</Text>
              </Pressable>
            </>
          ) : null}
        </>
      )}
    </Card>
  );
}

// Mobile parity with the web "Refer a friend" card: shows the user's invite stats and opens
// the native share sheet. The reward (a bonus prep pack for both sides) is granted
// server-side from a verified signup — this is just the share surface.
function ReferAFriendCard() {
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    api
      .referralStats()
      .then((s) => active && setStats(s))
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
    };
  }, []);

  async function share() {
    if (!stats) return;
    // The /register page lives on the WEB frontend, which is a different origin from the
    // API in a split deploy. Prefer an explicit web URL; fall back to the API origin (correct
    // for the unified Vercel deploy where web + /api share one origin).
    const webBase = process.env.EXPO_PUBLIC_WEB_URL ?? api.apiUrl;
    const link = `${webBase}/register?ref=${stats.code}`;
    try {
      await Share.share({
        message: `Join me on Career Operator — we both get a bonus interview prep pack: ${link}`,
      });
    } catch {
      // User dismissed the share sheet, or it's unavailable — nothing to surface.
    }
  }

  if (failed) return null;

  return (
    <Card>
      <Text style={styles.referTitle}>Refer a friend</Text>
      <Text style={styles.referBody}>
        Share your link. When a friend signs up, you both get a free interview prep pack.
      </Text>
      {stats ? (
        <>
          <Button label="Share invite link" variant="secondary" onPress={share} />
          <Text style={styles.referStats}>
            {stats.total_referred} {stats.total_referred === 1 ? 'friend has' : 'friends have'}{' '}
            joined · {stats.bonus_prep_packs} bonus prep{' '}
            {stats.bonus_prep_packs === 1 ? 'pack' : 'packs'} earned
          </Text>
        </>
      ) : (
        <Text style={styles.referStats}>Loading your invite link…</Text>
      )}
    </Card>
  );
}

// Entry point to the team / seat-tier management surface (web parity with the /app/team nav
// link). Shown to every user; the Team screen itself honestly handles the "not on a team" case.
function TeamCard() {
  return (
    <Card>
      <Text style={styles.referTitle}>Team</Text>
      <Text style={styles.referBody}>
        On a team plan? Manage your teammates&apos; Pro seats — assign or free a seat, and see
        who&apos;s using them.
      </Text>
      <Button label="Manage team" variant="secondary" onPress={() => router.push('/team')} />
    </Card>
  );
}

export default function SettingsScreen() {
  const { user, signOut } = useAuth();

  function confirmSignOut() {
    Alert.alert('Log out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log out', style: 'destructive', onPress: () => signOut() },
    ]);
  }

  async function deleteAccount() {
    // Required by Apple (5.1.1v) & Google. A REAL deletion: the server removes the user
    // and all their data, then we clear the local session (signOut sets user -> null, so
    // the root layout routes back to the auth screen).
    try {
      await api.deleteAccount();
    } catch (e) {
      // Only the deletion request itself failing should surface as a failure.
      Alert.alert(
        'Could not delete account',
        e instanceof ApiError ? e.message : 'Something went wrong. Please try again.',
      );
      return;
    }
    // Account is gone server-side. Clear the session; if signOut hiccups, force the user
    // back to auth rather than wrongly reporting a delete failure.
    try {
      await signOut();
    } catch {
      router.replace('/(auth)/login');
    }
  }

  function confirmDelete() {
    Alert.alert(
      'Delete account',
      'This permanently deletes your account and all your data. This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: deleteAccount },
      ],
    );
  }

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.h1}>Settings</Text>
        <Card>
          <Text style={styles.name}>{user?.full_name ?? 'Your account'}</Text>
          <Text style={styles.email}>{user?.email}</Text>
          <View style={styles.tierRow}>
            <Text style={styles.tierLabel}>Plan</Text>
            <Text style={[styles.tierValue, user?.tier === 'premium' && { color: colors.success }]}>
              {user?.tier === 'premium' ? (user?.career_plus ? 'Career+' : 'Pro') : 'Free'}
            </Text>
          </View>
          <Text style={styles.usage}>
            Jobs remaining: {String(user?.jobs_remaining ?? '—')} · Prep packs:{' '}
            {String(user?.prep_packs_remaining ?? '—')}
          </Text>
        </Card>

        {user?.tier !== 'premium' ? (
          <Button label="Upgrade to Pro" onPress={() => router.push('/paywall')} />
        ) : null}

        <ResumeCard />

        <AiConsentSetting />

        <GithubEnrichmentCard />

        <TeamCard />

        <ReferAFriendCard />

        <View style={styles.meta}>
          <Text style={styles.metaText}>API: {api.apiUrl}</Text>
        </View>

        <Button label="Log out" variant="secondary" onPress={confirmSignOut} />
        {/* Destructive action set apart from preferences and visually marked as danger,
            so deleting an account never reads like just another button. */}
        <Pressable accessibilityRole="button" onPress={confirmDelete} style={styles.deleteBtn}>
          <Text style={styles.deleteText}>Delete account</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.md, gap: spacing.md },
  h1: { color: colors.text, fontSize: 26, fontWeight: '800' },
  name: { color: colors.text, fontSize: 18, fontWeight: '700' },
  email: { color: colors.textMuted, marginTop: 2 },
  tierRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.md },
  tierLabel: { color: colors.textMuted },
  tierValue: { color: colors.text, fontWeight: '700' },
  usage: { color: colors.textMuted, marginTop: spacing.sm, fontSize: 13 },
  referTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
  referBody: { color: colors.textMuted, marginTop: spacing.xs, marginBottom: spacing.md, fontSize: 13 },
  referStats: { color: colors.textMuted, marginTop: spacing.sm, fontSize: 13 },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.md },
  chip: {
    borderWidth: 1,
    borderColor: colors.primary,
    backgroundColor: 'rgba(99,102,241,0.12)',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  chipText: { color: colors.text, fontSize: 12, fontWeight: '600' },
  proNote: { color: colors.textMuted, marginBottom: spacing.sm, fontSize: 13 },
  resumeInput: { minHeight: 160, paddingTop: spacing.sm, textAlignVertical: 'top' },
  savedText: { color: colors.success, marginTop: spacing.sm, fontSize: 13 },
  errorText: { color: colors.danger, marginTop: spacing.sm, fontSize: 13 },
  clearBtn: { paddingVertical: 8, marginTop: spacing.xs },
  clearText: { color: colors.textMuted, fontSize: 12 },
  meta: { alignItems: 'center' },
  metaText: { color: colors.textMuted, fontSize: 12 },
  deleteBtn: { paddingVertical: 14, alignItems: 'center', marginTop: spacing.sm },
  deleteText: { color: colors.danger, fontWeight: '600', fontSize: 15 },
});
