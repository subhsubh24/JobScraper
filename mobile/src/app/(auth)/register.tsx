import { Link, router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Button, Field } from '@/components/ui';
import { useAuth } from '@/contexts/auth';
import { ApiError } from '@/services/api';
import { colors, spacing } from '@/theme';

export default function RegisterScreen() {
  const { signUp } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [resume, setResume] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    setError(null);
    if (!email.trim() || password.length < 8) {
      setError('Use a valid email and a password of at least 8 characters.');
      return;
    }
    setLoading(true);
    try {
      await signUp({
        email: email.trim(),
        password,
        full_name: fullName.trim() || undefined,
        resume_text: resume.trim() || undefined,
      });
      router.replace('/(tabs)');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>Create your account</Text>
        <Text style={styles.subtitle}>Free to start — 5 tracked jobs and a prep pack on us.</Text>
        <Field label="Full name" value={fullName} onChangeText={setFullName} placeholder="Jane Seeker" />
        <Field
          label="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          placeholder="you@example.com"
        />
        <Field label="Password" value={password} onChangeText={setPassword} secureTextEntry placeholder="At least 8 characters" />
        <Field
          label="Paste your resume (optional — powers fit scoring)"
          value={resume}
          onChangeText={setResume}
          multiline
          numberOfLines={4}
          style={{ minHeight: 100, textAlignVertical: 'top' }}
          placeholder="Your experience, skills, achievements…"
        />
        {error ? (
          <Text style={styles.error} accessibilityRole="alert" accessibilityLiveRegion="polite">
            {error}
          </Text>
        ) : null}
        <Button label="Create account" onPress={onSubmit} loading={loading} />
        <View style={styles.footer}>
          <Text style={styles.muted}>Already have an account? </Text>
          <Link
            href="/(auth)/login"
            style={styles.link}
            accessibilityRole="link"
            accessibilityLabel="Log in"
          >
            Log in
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingTop: spacing.xl, gap: spacing.sm },
  title: { color: colors.text, fontSize: 26, fontWeight: '800' },
  subtitle: { color: colors.textMuted, marginBottom: spacing.md },
  error: { color: colors.danger, marginBottom: spacing.sm },
  footer: { flexDirection: 'row', justifyContent: 'center', marginTop: spacing.lg },
  muted: { color: colors.textMuted },
  link: { color: colors.primary, fontWeight: '700' },
});
