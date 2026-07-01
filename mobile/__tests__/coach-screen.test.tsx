/// <reference types="jest" />
// Track B: the AI Coach is Premium-gated. A FREE user must hit an honest lock (not a dead
// end) that routes to the paywall; a PREMIUM user gets the real chat — suggestions load, a
// sent message gets a reply, and a provider failure surfaces honestly (no fake reply).
// expo-router + the auth context + the api client are mocked so the screen renders headlessly.

import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';

const mockPush = jest.fn();
jest.mock('expo-router', () => ({
  // Arrow wrapper: the screen import hoists above these consts, so resolve lazily at call time.
  router: { push: (...a: unknown[]) => mockPush(...a) },
}));

// jest-expo stubs the NATIVE bridge but not the JS layer of safe-area-context; mock it to a
// plain View (mirrors pipeline-screen.test.tsx) so the screen renders deterministically.
jest.mock('react-native-safe-area-context', () => {
  const { View } = require('react-native');
  return { SafeAreaView: View, useSafeAreaInsets: () => ({ top: 0, right: 0, bottom: 0, left: 0 }) };
});

let mockTier: 'free' | 'premium' = 'premium';
jest.mock('@/contexts/auth', () => ({
  useAuth: () => ({ user: { id: 'u1', tier: mockTier } }),
}));

jest.mock('@/services/api', () => ({
  api: {
    coachSuggestions: jest.fn(async () => ['How do I negotiate salary?']),
    coachChat: jest.fn(async () => 'Lead with your strongest signal.'),
  },
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

import CoachScreen from '@/app/(tabs)/coach';
import { api } from '@/services/api';

afterEach(() => {
  jest.clearAllMocks();
  mockTier = 'premium';
});

describe('CoachScreen', () => {
  it('shows a free user an honest Premium lock that routes to the paywall (no dead end)', async () => {
    mockTier = 'free';
    render(<CoachScreen />);
    expect(screen.getByText('Your AI Career Coach')).toBeTruthy();
    fireEvent.press(screen.getByText('Upgrade to unlock'));
    expect(mockPush).toHaveBeenCalledWith('/paywall');
    // The screen loads suggestions on mount unconditionally; settle that async state inside
    // act() so it can't leak a post-test update.
    await waitFor(() => expect(api.coachSuggestions).toHaveBeenCalled());
  });

  it('lets a premium user pick a suggestion and renders the real coach reply', async () => {
    mockTier = 'premium';
    render(<CoachScreen />);
    await waitFor(() => expect(screen.getByText('How do I negotiate salary?')).toBeTruthy());
    fireEvent.press(screen.getByText('How do I negotiate salary?'));
    // A non-empty session id is threaded so the backend can keep multi-turn context.
    expect(api.coachChat).toHaveBeenCalledWith(
      'How do I negotiate salary?',
      expect.stringMatching(/.+/),
    );
    await waitFor(() => expect(screen.getByText('Lead with your strongest signal.')).toBeTruthy());
  });

  it('reuses ONE session id across turns so the coach keeps conversation context', async () => {
    mockTier = 'premium';
    render(<CoachScreen />);
    await waitFor(() => expect(api.coachSuggestions).toHaveBeenCalled());
    const input = screen.getByPlaceholderText('Type a message…');

    fireEvent.changeText(input, 'first');
    fireEvent.press(screen.getByText('Send'));
    await waitFor(() => expect(api.coachChat).toHaveBeenCalledTimes(1));

    fireEvent.changeText(input, 'second');
    fireEvent.press(screen.getByText('Send'));
    await waitFor(() => expect(api.coachChat).toHaveBeenCalledTimes(2));

    const mock = api.coachChat as jest.Mock;
    const firstSession = mock.mock.calls[0][1];
    const secondSession = mock.mock.calls[1][1];
    expect(firstSession).toEqual(expect.stringMatching(/.+/));
    // Same conversation → identical session id (the whole point of the fix: without it the
    // server started a fresh, context-free session on every message).
    expect(secondSession).toBe(firstSession);
  });

  it('surfaces a coach provider failure honestly (no fabricated reply)', async () => {
    mockTier = 'premium';
    (api.coachChat as jest.Mock).mockRejectedValueOnce(new Error('boom'));
    render(<CoachScreen />);
    await waitFor(() => expect(api.coachSuggestions).toHaveBeenCalled()); // settle the load first
    fireEvent.changeText(screen.getByPlaceholderText('Type a message…'), 'hello');
    fireEvent.press(screen.getByText('Send'));
    await waitFor(() => expect(screen.getByText(/unavailable right now/i)).toBeTruthy());
    // The failed turn must NOT leave a fake assistant message claiming success.
    expect(screen.queryByText('Lead with your strongest signal.')).toBeNull();
  });

  it('exposes accessible names so a screen reader can operate the chat', async () => {
    mockTier = 'premium';
    render(<CoachScreen />);
    await waitFor(() => expect(api.coachSuggestions).toHaveBeenCalled());
    // The message input is labeled (was placeholder-only before) and the send control is a
    // named button — both required for VoiceOver/TalkBack users to use the core coach loop.
    expect(screen.getByLabelText('Message to your AI career coach')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Send message' })).toBeTruthy();
  });
});
