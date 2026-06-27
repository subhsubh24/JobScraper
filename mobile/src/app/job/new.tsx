import { router, Stack } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text } from 'react-native';

import { Button, Field } from '@/components/ui';
import { api, ApiError } from '@/services/api';
import { colors, spacing } from '@/theme';

export default function NewJobScreen() {
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    setError(null);
    if (!title.trim() || !company.trim()) {
      setError('A title and company are required.');
      return;
    }
    setLoading(true);
    try {
      await api.createJob({
        title: title.trim(),
        company_name: company.trim(),
        location: location.trim() || undefined,
        description: description.trim() || undefined,
      });
      router.back();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not add this job.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Stack.Screen options={{ title: 'Add a job' }} />
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.hint}>Paste the role details and we will score how well it fits you.</Text>
        <Field label="Job title *" value={title} onChangeText={setTitle} placeholder="Senior Backend Engineer" />
        <Field label="Company *" value={company} onChangeText={setCompany} placeholder="Acme" />
        <Field label="Location" value={location} onChangeText={setLocation} placeholder="Remote US" />
        <Field
          label="Job description (powers the fit score)"
          value={description}
          onChangeText={setDescription}
          multiline
          numberOfLines={6}
          style={{ minHeight: 140, textAlignVertical: 'top' }}
          placeholder="Responsibilities, requirements, tech stack…"
        />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Button label="Add & score" onPress={onSubmit} loading={loading} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.md, gap: spacing.sm },
  hint: { color: colors.textMuted, marginBottom: spacing.sm },
  error: { color: colors.danger, marginBottom: spacing.sm },
});
