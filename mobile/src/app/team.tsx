import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, EmptyState, ErrorBanner, Field } from '@/components/ui';
import { api, ApiError } from '@/services/api';
import { colors, radius, spacing } from '@/theme';
import type { Organization } from '@/types';

// Team / seat-tier MANAGEMENT surface on mobile — the companion to the web /app/team page,
// making the B2B2C seat tier reachable end-to-end on the phone. The server is the source of
// truth: every mutation awaits the real API and re-renders from the returned org payload — no
// optimistic success. Seats are granted to members solely by the signed Stripe webhook.
//
// SCOPE (App Store 3.1.1): creating a team and buying seats are EXTERNAL-PAYMENT flows and live
// on the web dashboard only — this app never opens or steers to a purchase. An owner manages an
// already-active team (assign/free seats, roster, usage); a member sees their team status.

function SeatUsage({ org }: { org: Organization }) {
  return (
    <Text style={styles.usage} accessibilityRole="text">
      <Text style={styles.usageStrong}>{org.seats_used}</Text> of{' '}
      <Text style={styles.usageStrong}>{org.seats_purchased}</Text> seats used
    </Text>
  );
}

// Owner-only roster + seat assignment. Shown once the team is active (has purchased seats).
function MembersManager({
  org,
  onUpdated,
}: {
  org: Organization;
  onUpdated: (org: Organization) => void;
}) {
  const [email, setEmail] = useState('');
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  const members = org.members ?? [];
  const seatsFree = Math.max(0, (org.seats_purchased || 0) - (org.seats_used || 0));
  const canAdd = email.trim().length >= 3 && seatsFree > 0 && !adding;

  async function add() {
    if (!canAdd) return;
    setAdding(true);
    setError(null);
    try {
      // Await the real assign; re-render from the returned org, then clear the input.
      onUpdated(await api.addOrgMember(email.trim()));
      setEmail('');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not add that member. Try again.');
    } finally {
      setAdding(false);
    }
  }

  async function remove(userId: string) {
    if (removingId) return;
    setRemovingId(userId);
    setError(null);
    try {
      onUpdated(await api.removeOrgMember(userId));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not remove that member. Try again.');
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <Card>
      <Text style={styles.cardTitle}>Members</Text>
      <Text style={styles.cardBody}>
        Assign a seat by email — that teammate gets full Pro access. Free a seat to reassign it.
      </Text>

      <Field
        label="Teammate email"
        value={email}
        onChangeText={(t) => {
          setEmail(t);
          setError(null);
        }}
        placeholder="teammate@company.com"
        keyboardType="email-address"
        autoCapitalize="none"
        autoCorrect={false}
        spellCheck={false}
        maxLength={255}
      />
      <Button
        label={adding ? 'Adding…' : 'Add member'}
        onPress={add}
        loading={adding}
        disabled={!canAdd}
      />
      {seatsFree === 0 ? (
        <Text style={styles.note}>
          All seats are assigned. Free a seat below, or buy more from the web dashboard.
        </Text>
      ) : null}
      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      {members.length > 0 ? (
        <View style={styles.roster}>
          {members.map((m) => {
            const busy = removingId === m.user_id;
            return (
              <View key={m.user_id} style={styles.memberRow}>
                <Text style={styles.memberEmail} numberOfLines={1}>
                  {m.email ?? '(unknown account)'}
                </Text>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={`Remove ${m.email ?? 'member'}`}
                  accessibilityState={{ disabled: removingId !== null, busy }}
                  onPress={() => remove(m.user_id)}
                  disabled={removingId !== null}
                  style={({ pressed }) => [
                    styles.removeBtn,
                    removingId !== null && styles.removeBtnDisabled,
                    pressed && { opacity: 0.7 },
                  ]}
                >
                  <Text style={styles.removeText}>{busy ? 'Removing…' : 'Remove'}</Text>
                </Pressable>
              </View>
            );
          })}
        </View>
      ) : (
        <Text style={styles.note}>No members yet — assign a seat by email above.</Text>
      )}
    </Card>
  );
}

function OwnerView({
  org,
  onUpdated,
}: {
  org: Organization;
  onUpdated: (org: Organization) => void;
}) {
  const active = org.active && (org.seats_purchased || 0) > 0;
  return (
    <>
      <Card>
        <View style={styles.headerRow}>
          <View style={styles.headerText}>
            <Text style={styles.cardTitle}>{org.name}</Text>
            <SeatUsage org={org} />
          </View>
          <View style={[styles.badge, active ? styles.badgeActive : styles.badgeIdle]}>
            <Text style={active ? styles.badgeActiveText : styles.badgeIdleText}>
              {active ? 'Active' : 'No seats'}
            </Text>
          </View>
        </View>
      </Card>

      {active ? (
        <MembersManager org={org} onUpdated={onUpdated} />
      ) : (
        <Card>
          <Text style={styles.cardTitle}>No seats yet</Text>
          <Text style={styles.cardBody}>
            Purchase Pro seats for your team from the Career Operator dashboard on the web. Once
            seats are active they show up here and you can assign them to teammates.
          </Text>
        </Card>
      )}
    </>
  );
}

function MemberView({ org }: { org: Organization }) {
  return (
    <Card>
      <Text style={styles.cardTitle}>{org.name}</Text>
      <Text style={styles.cardBody}>
        You hold a Pro seat on this team — every Pro feature is unlocked on your account. Your
        team&apos;s owner manages seats and billing. To leave the team, contact your owner.
      </Text>
    </Card>
  );
}

export default function TeamScreen() {
  // undefined = loading; null = loaded, no team; Organization = loaded team.
  const [org, setOrg] = useState<Organization | null | undefined>(undefined);
  const [loadError, setLoadError] = useState(false);
  const mounted = useRef(true);

  // Fire the fetch; state is only ever set from the async callbacks (guarded by `mounted`), so
  // it never sets state synchronously inside the mount effect.
  const fetchOrg = useCallback(() => {
    api
      .getOrg()
      .then((o) => mounted.current && setOrg(o))
      .catch(() => mounted.current && setLoadError(true));
  }, []);

  useEffect(() => {
    mounted.current = true;
    fetchOrg();
    return () => {
      mounted.current = false;
    };
  }, [fetchOrg]);

  // Retry runs from a press handler (not an effect), so resetting to the loading state here is
  // fine — then re-fetch.
  const reload = () => {
    setLoadError(false);
    setOrg(undefined);
    fetchOrg();
  };

  return (
    <SafeAreaView style={styles.flex} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.container}>
        <View>
          <Text style={styles.h1}>Team</Text>
          <Text style={styles.sub}>Manage your team&apos;s Pro seats.</Text>
        </View>

        {loadError ? (
          <ErrorBanner message="Could not load your team." onRetry={reload} />
        ) : org === undefined ? (
          <View style={styles.loading} accessibilityRole="progressbar" accessibilityLabel="Loading your team">
            <ActivityIndicator color={colors.primary} />
          </View>
        ) : org === null ? (
          <Card>
            <EmptyState
              title="You're not on a team"
              subtitle="Team plans let an admin buy Pro seats in bulk for a group. Set one up and manage billing from your Career Operator account on the web."
            />
          </Card>
        ) : org.is_owner ? (
          <OwnerView org={org} onUpdated={setOrg} />
        ) : (
          <MemberView org={org} />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.md, gap: spacing.md },
  h1: { color: colors.text, fontSize: 26, fontWeight: '800' },
  sub: { color: colors.textMuted, marginTop: 2, fontSize: 13 },
  loading: { paddingVertical: spacing.xl, alignItems: 'center' },
  headerRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: spacing.md },
  headerText: { flex: 1, minWidth: 0 },
  cardTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
  cardBody: { color: colors.textMuted, marginTop: spacing.xs, fontSize: 13, lineHeight: 18 },
  usage: { color: colors.textMuted, marginTop: spacing.xs, fontSize: 13 },
  usageStrong: { color: colors.text, fontWeight: '700' },
  badge: { borderRadius: 999, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 4 },
  badgeActive: { borderColor: 'rgba(52,211,153,0.4)', backgroundColor: 'rgba(52,211,153,0.12)' },
  badgeActiveText: { color: colors.success, fontSize: 12, fontWeight: '700' },
  badgeIdle: { borderColor: colors.border, backgroundColor: colors.surfaceAlt },
  badgeIdleText: { color: colors.textMuted, fontSize: 12, fontWeight: '700' },
  note: { color: colors.textMuted, marginTop: spacing.sm, fontSize: 12, lineHeight: 17 },
  errorText: { color: colors.danger, marginTop: spacing.sm, fontSize: 13 },
  roster: { marginTop: spacing.md, borderTopWidth: 1, borderTopColor: colors.border },
  memberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  memberEmail: { color: colors.text, fontSize: 14, flex: 1 },
  removeBtn: {
    borderWidth: 1,
    borderColor: colors.danger,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  removeBtnDisabled: { opacity: 0.5 },
  removeText: { color: colors.danger, fontWeight: '700', fontSize: 13 },
});
