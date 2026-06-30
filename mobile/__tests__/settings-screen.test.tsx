/// <reference types="jest" />
// Track B: Settings shows the real account (email + plan + usage), the referral share card,
// and the store-required account deletion. The delete flow must be HONEST — it calls the real
// DELETE endpoint and only then clears the session (no optimistic "deleted" without the server
// confirming). expo-router + auth context + api + native Alert/Share are mocked for headless run.

import { Alert } from 'react-native';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';

const mockReplace = jest.fn();
jest.mock('expo-router', () => ({
  router: { push: jest.fn(), replace: (...a: unknown[]) => mockReplace(...a) },
}));

// jest-expo stubs the NATIVE bridge but not the JS layer of safe-area-context; mock it to a
// plain View (mirrors pipeline-screen.test.tsx) so the screen renders deterministically.
jest.mock('react-native-safe-area-context', () => {
  const { View } = require('react-native');
  return { SafeAreaView: View, useSafeAreaInsets: () => ({ top: 0, right: 0, bottom: 0, left: 0 }) };
});

const mockSignOut = jest.fn(async (..._a: unknown[]) => {});
let mockUser: Record<string, unknown> = {
  id: 'u1',
  email: 'jane@example.com',
  full_name: 'Jane Seeker',
  tier: 'free',
  jobs_remaining: 3,
  prep_packs_remaining: 1,
};
jest.mock('@/contexts/auth', () => ({
  useAuth: () => ({ user: mockUser, signOut: (...a: unknown[]) => mockSignOut(...a) }),
}));

jest.mock('@/services/api', () => ({
  api: {
    apiUrl: 'https://api.example.com',
    referralStats: jest.fn(async () => ({ code: 'ABC123', total_referred: 2, bonus_prep_packs: 1 })),
    deleteAccount: jest.fn(async () => {}),
  },
}));

import SettingsScreen from '@/app/(tabs)/settings';
import { api } from '@/services/api';

afterEach(() => {
  jest.clearAllMocks();
  mockUser = {
    id: 'u1',
    email: 'jane@example.com',
    full_name: 'Jane Seeker',
    tier: 'free',
    jobs_remaining: 3,
    prep_packs_remaining: 1,
  };
});

describe('SettingsScreen', () => {
  it('renders the real account: name, email, Free plan + upgrade CTA, usage', async () => {
    render(<SettingsScreen />);
    expect(screen.getByText('Jane Seeker')).toBeTruthy();
    expect(screen.getByText('jane@example.com')).toBeTruthy();
    expect(screen.getByText('Free')).toBeTruthy();
    expect(screen.getByText('Upgrade to Premium')).toBeTruthy();
    expect(screen.getByText(/Jobs remaining: 3/)).toBeTruthy();
    // Let the referral card's async load settle so its state update is wrapped in act().
    await screen.findByText('Share invite link');
  });

  it('a premium user shows Premium and no upgrade CTA', async () => {
    mockUser = { ...mockUser, tier: 'premium' };
    render(<SettingsScreen />);
    expect(screen.getByText('Premium')).toBeTruthy();
    expect(screen.queryByText('Upgrade to Premium')).toBeNull();
    await screen.findByText('Share invite link');
  });

  it('renders the referral share card with real invite stats once loaded', async () => {
    render(<SettingsScreen />);
    await waitFor(() =>
      expect(screen.getByText(/2 friends have joined · 1 bonus prep pack earned/)).toBeTruthy(),
    );
    expect(screen.getByText('Share invite link')).toBeTruthy();
  });

  it('delete account is HONEST: calls the real DELETE then clears the session', async () => {
    const alertSpy = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
    render(<SettingsScreen />);
    await screen.findByText('Share invite link'); // settle the referral card first

    fireEvent.press(screen.getByText('Delete account'));
    // The confirm dialog fired; invoke its destructive "Delete" action the way a tap would.
    const buttons = alertSpy.mock.calls[0][2] as Array<{ text?: string; onPress?: () => void }>;
    const del = buttons.find((b) => b.text === 'Delete');
    expect(del).toBeTruthy();
    await del!.onPress!();

    expect(api.deleteAccount).toHaveBeenCalledTimes(1);
    expect(mockSignOut).toHaveBeenCalledTimes(1);
    // Pin the ORDER: the server delete must resolve BEFORE the session is cleared, so we never
    // sign out (and report success) on a delete that hasn't actually happened.
    const deleteOrder = (api.deleteAccount as jest.Mock).mock.invocationCallOrder[0];
    const signOutOrder = mockSignOut.mock.invocationCallOrder[0];
    expect(deleteOrder).toBeLessThan(signOutOrder);
    alertSpy.mockRestore();
  });

  it('a failed delete surfaces an error and does NOT clear the session (no fake success)', async () => {
    (api.deleteAccount as jest.Mock).mockRejectedValueOnce(new Error('server down'));
    const alertSpy = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
    render(<SettingsScreen />);
    await screen.findByText('Share invite link'); // settle the referral card first

    fireEvent.press(screen.getByText('Delete account'));
    const confirmButtons = alertSpy.mock.calls[0][2] as Array<{ text?: string; onPress?: () => void }>;
    await confirmButtons.find((b) => b.text === 'Delete')!.onPress!();

    expect(api.deleteAccount).toHaveBeenCalledTimes(1);
    // Deletion failed -> we must NOT sign the user out as if it worked; an error alert fires.
    expect(mockSignOut).not.toHaveBeenCalled();
    const lastAlert = alertSpy.mock.calls[alertSpy.mock.calls.length - 1];
    expect(String(lastAlert[0])).toMatch(/could not delete/i);
    alertSpy.mockRestore();
  });
});
