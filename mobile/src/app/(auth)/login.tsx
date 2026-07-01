import { Link, router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Button, Field } from '@/components/ui';
import { useAuth } from '@/contexts/auth';
import { ApiError } from '@/services/api';
import { colors, spacing } from '@/theme';

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    setError(null);
    if (!email.trim() || !password) {
      setError('Enter your email and password.');
      return;
    }
    setLoading(true);
    try {
      await signIn(email.trim(), password);
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
        <View style={styles.header}>
          <Text style={styles.brand}>Career Operator</Text>
          <Text style={styles.tagline}>Run your job search like an operator.</Text>
        </View>
        <Field
          label="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          placeholder="you@example.com"
        />
        <Field
          label="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          placeholder="••••••••"
        />
        {error ? (
          <Text style={styles.error} accessibilityRole="alert" accessibilityLiveRegion="polite">
            {error}
          </Text>
        ) : null}
        <Button label="Log in" onPress={onSubmit} loading={loading} />
        <View style={styles.footer}>
          <Text style={styles.muted}>New here? </Text>
          <Link
            href="/(auth)/register"
            style={styles.link}
            accessibilityRole="link"
            accessibilityLabel="Create an account"
          >
            Create an account
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingTop: spacing.xl * 2, gap: spacing.sm },
  header: { marginBottom: spacing.lg },
  brand: { color: colors.text, fontSize: 30, fontWeight: '800' },
  tagline: { color: colors.textMuted, fontSize: 15, marginTop: spacing.xs },
  error: { color: colors.danger, marginBottom: spacing.sm },
  footer: { flexDirection: 'row', justifyContent: 'center', marginTop: spacing.lg },
  muted: { color: colors.textMuted },
  link: { color: colors.primary, fontWeight: '700' },
});
