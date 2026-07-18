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
  useAuth: () => ({
    user: mockUser,
    signOut: (...a: unknown[]) => mockSignOut(...a),
    setUser: jest.fn(),
  }),
}));

jest.mock('@/services/api', () => {
  // Mirror the real ApiError (extends Error) so the screen's `e instanceof ApiError`
  // guards resolve to a real class under the module mock — matching the sibling test
  // files (job-detail/insights/coach). Without this the mocked module would leave
  // ApiError undefined and `e instanceof ApiError` would throw at runtime.
  class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  }
  return {
  api: {
    apiUrl: 'https://api.example.com',
    referralStats: jest.fn(async () => ({ code: 'ABC123', total_referred: 2, bonus_prep_packs: 1 })),
    deleteAccount: jest.fn(async () => {}),
    grantAiConsent: jest.fn(async () => ({ ...mockUser, ai_consent: true })),
    revokeAiConsent: jest.fn(async () => ({ ...mockUser, ai_consent: false })),
    // The Résumé card loads the saved résumé on mount (every tier) and PATCHes on save.
    // Mocked so the screen render doesn't call undefined methods.
    getResume: jest.fn(async () => 'Existing résumé text.'),
    saveResume: jest.fn(async () => true),
    // Profile enrichment (Track A): the Pro-gated GitHub card loads current competencies on
    // mount for Pro users. Mocked so a premium render doesn't call an undefined method.
    getEnrichment: jest.fn(async () => []),
    enrichGithub: jest.fn(async () => ({
      success: true,
      found: 0,
      username: 'octocat',
      competencies: [],
      message: 'No public repositories with detectable skills found for github.com/octocat.',
    })),
    clearEnrichment: jest.fn(async () => {}),
  },
  ApiError,
  };
});

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
    // A free user gets at least one "Upgrade to Pro" CTA (the top-level Plan button AND the
    // Pro-gated enrichment card's contextual upsell both render), so match all of them.
    expect(screen.getAllByText('Upgrade to Pro').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Jobs remaining: 3/)).toBeTruthy();
    // The enrichment card is SHOWN to free users with a Pro upsell (not hidden).
    expect(screen.getByText('Profile enrichment')).toBeTruthy();
    expect(screen.getByText('A Pro feature.')).toBeTruthy();
    // Let the referral card's async load settle so its state update is wrapped in act().
    await screen.findByText('Share invite link');
  });

  it('a premium (Pro) user shows Pro and the enrichment import flow, no upgrade CTA', async () => {
    mockUser = { ...mockUser, tier: 'premium' };
    render(<SettingsScreen />);
    expect(screen.getByText('Pro')).toBeTruthy();
    // No "Upgrade to Pro" anywhere for a Pro user (top-level hidden; enrichment card shows the
    // import flow, not the upsell).
    expect(screen.queryByText('Upgrade to Pro')).toBeNull();
    // The Pro user sees the enrichment import affordance.
    expect(screen.getByText('Import')).toBeTruthy();
    await screen.findByText('Share invite link');
  });

  it('renders the referral share card with real invite stats once loaded', async () => {
    render(<SettingsScreen />);
    await waitFor(() =>
      expect(screen.getByText(/2 friends have joined · 1 bonus prep pack earned/)).toBeTruthy(),
    );
    expect(screen.getByText('Share invite link')).toBeTruthy();
  });

  it('résumé card loads the saved résumé and saves edits honestly (awaits the real PATCH)', async () => {
    render(<SettingsScreen />);
    // The card loads the current résumé on mount.
    const field = await screen.findByDisplayValue('Existing résumé text.');
    expect(screen.getByText('Résumé')).toBeTruthy();

    // Save is disabled until the text is dirty; editing enables it.
    fireEvent.changeText(field, 'Updated résumé — Python, FastAPI.');
    fireEvent.press(screen.getByText('Save résumé'));

    // The real PATCH is awaited with the edited text, and only then does the confirmation show
    // (no optimistic success).
    await waitFor(() =>
      expect(api.saveResume).toHaveBeenCalledWith('Updated résumé — Python, FastAPI.'),
    );
    await screen.findByText('Résumé saved.');
  });

  it('a failed résumé save surfaces the error and shows no success confirmation', async () => {
    // The card surfaces an honest error on failure (a real ApiError carries the server's
    // 'detail'; an unexpected non-ApiError throw like this one falls through to the friendly
    // fallback). The key guarantee under test: an error IS shown and the "saved" confirmation
    // is NOT (no optimistic/fake success).
    (api.saveResume as jest.Mock).mockRejectedValueOnce(new Error('Could not save your résumé.'));
    render(<SettingsScreen />);
    const field = await screen.findByDisplayValue('Existing résumé text.');
    fireEvent.changeText(field, 'Broken save attempt.');
    fireEvent.press(screen.getByText('Save résumé'));
    await screen.findByText(/could not save your résumé/i);
    expect(screen.queryByText('Résumé saved.')).toBeNull();
  });

  it('a failed résumé LOAD surfaces the retry error instead of hanging on "Loading…" forever', async () => {
    // Regression: before the load resolves `resume` is null (= "Loading your résumé…"). If the
    // initial GET fails, the error must be reachable — otherwise the card is stuck on the loading
    // placeholder forever and the retry message never renders (a dead end on the core input).
    (api.getResume as jest.Mock).mockRejectedValueOnce(new Error('network'));
    render(<SettingsScreen />);
    await screen.findByText(/could not load your résumé/i);
    expect(screen.queryByText('Loading your résumé…')).toBeNull();
    await screen.findByText('Share invite link'); // settle the referral card's async load
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
