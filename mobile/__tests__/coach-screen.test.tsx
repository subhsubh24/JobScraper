/// <reference types="jest" />
// Track B: the AI Coach is Premium-gated. A FREE user must hit an honest lock (not a dead
// end) that routes to the paywall; a PREMIUM user gets the real chat — suggestions load, a
// sent message gets a reply, and a provider failure surfaces honestly (no fake reply).
// expo-router + the auth context + the api client are mocked so the screen renders headlessly.

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';

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
let mockConsent = true;
jest.mock('@/contexts/auth', () => ({
  useAuth: () => ({ user: { id: 'u1', tier: mockTier, ai_consent: mockConsent }, setUser: jest.fn() }),
}));

jest.mock('@/services/api', () => ({
  api: {
    coachSuggestions: jest.fn(async () => ['How do I negotiate salary?']),
    coachChat: jest.fn(async () => 'Lead with your strongest signal.'),
    grantAiConsent: jest.fn(async () => ({ id: 'u1', tier: 'premium', ai_consent: true })),
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
import { api, ApiError } from '@/services/api';

afterEach(() => {
  jest.clearAllMocks();
  mockTier = 'premium';
  mockConsent = true;
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

  it('gates a premium user who has NOT consented to third-party AI (no coach call, prompts consent)', async () => {
    mockTier = 'premium';
    mockConsent = false;
    render(<CoachScreen />);
    // The chat surface must NOT render; the consent prompt does (Apple 5.1.2(i)).
    expect(screen.getByText('Enable AI features')).toBeTruthy();
    expect(screen.queryByText('Send')).toBeNull();
    fireEvent.press(screen.getByText('Turn on AI features'));
    await waitFor(() => expect(api.grantAiConsent).toHaveBeenCalled());
    // No message is sent to the AI until consent is granted.
    expect(api.coachChat).not.toHaveBeenCalled();
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

  it('a same-tick double-tap on Send fires coachChat only ONCE (no duplicate threaded turn)', async () => {
    // Two rapid taps on Send (or a suggestion chip) close over the pre-render sending=false and
    // the disabled prop lands late on RN — without the synchronous latch this fires coachChat
    // twice on the SAME session id, doubling the turn in the server-threaded context, appending a
    // duplicate user bubble + two replies, and burning two LLM ceiling slots. Revert-proof:
    // removing the `useLatch` guard (leaving only the `sending` state check) reddens this.
    mockTier = 'premium';
    (api.coachChat as jest.Mock).mockReturnValue(new Promise(() => {})); // never resolves: stays in-flight
    render(<CoachScreen />);
    await waitFor(() => expect(api.coachSuggestions).toHaveBeenCalled());
    fireEvent.changeText(screen.getByPlaceholderText('Type a message…'), 'help me negotiate');

    const btn = screen.getByText('Send');
    await act(async () => {
      fireEvent.press(btn);
      fireEvent.press(btn);
    });

    expect(api.coachChat).toHaveBeenCalledTimes(1);
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

  it('routes a mid-session 403 (lapsed Pro) to the paywall, not a dead-end inline error', async () => {
    // The screen's initial isPremium gate can let a user in, then the Pro entitlement lapses
    // (e.g. cancelled on another device) so the NEXT send 403s. Parity with the job generators /
    // mock interview / insights: a mid-call 403 must route to the paywall (a real recovery path),
    // never strand the user on the inline "unavailable" error — a dead end on a lapsed tier that
    // no retry can clear. Removing the `status === 403` branch reddens this (mockPush not called).
    mockTier = 'premium';
    (api.coachChat as jest.Mock).mockRejectedValueOnce(new ApiError(403, 'Upgrade to Pro'));
    render(<CoachScreen />);
    await waitFor(() => expect(api.coachSuggestions).toHaveBeenCalled());
    fireEvent.changeText(screen.getByPlaceholderText('Type a message…'), 'help me negotiate');
    fireEvent.press(screen.getByText('Send'));
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/paywall'));
    // No dead-end inline error is shown for the tier gate (the paywall IS the surfaced recovery).
    expect(screen.queryByText(/unavailable right now/i)).toBeNull();
  });

  it('rolls the failed turn back out of the transcript and restores the input for retry', async () => {
    // LOAD-BEARING: a send whose server call fails never reached the coach's threaded session,
    // so the optimistic user bubble must be rolled back (else the visible transcript desyncs from
    // what the coach knows and the next reply looks like it ignored the message) AND the typed
    // text must return to the input so the user can resend without retyping it. Removing the
    // `filter` rollback reddens the "no orphaned bubble" assertion; removing the `setInput`
    // restore reddens the "input restored" assertion.
    mockTier = 'premium';
    (api.coachChat as jest.Mock).mockRejectedValueOnce(new Error('boom'));
    render(<CoachScreen />);
    await waitFor(() => expect(api.coachSuggestions).toHaveBeenCalled()); // settle the load first
    const input = screen.getByPlaceholderText('Type a message…');
    fireEvent.changeText(input, 'help me negotiate');
    fireEvent.press(screen.getByText('Send'));
    await waitFor(() => expect(screen.getByText(/unavailable right now/i)).toBeTruthy());
    // No orphaned user bubble lingers in the transcript (the send never reached the server).
    expect(screen.queryByText('help me negotiate')).toBeNull();
    // The text is back in the input, ready to resend without retyping.
    expect(screen.getByDisplayValue('help me negotiate')).toBeTruthy();
  });

  it('rolls back ONLY the failed turn, leaving an earlier successful turn intact', async () => {
    // The rollback filters by the failed turn's own message id, so a later failure must never
    // remove an earlier turn's user bubble OR its assistant reply. Turn 1 succeeds; turn 2 fails.
    mockTier = 'premium';
    (api.coachChat as jest.Mock)
      .mockResolvedValueOnce('Lead with your strongest signal.') // turn 1 succeeds
      .mockRejectedValueOnce(new Error('boom')); // turn 2 fails
    render(<CoachScreen />);
    await waitFor(() => expect(api.coachSuggestions).toHaveBeenCalled());
    const input = screen.getByPlaceholderText('Type a message…');

    fireEvent.changeText(input, 'first question');
    fireEvent.press(screen.getByText('Send'));
    await waitFor(() => expect(screen.getByText('Lead with your strongest signal.')).toBeTruthy());

    fireEvent.changeText(input, 'second question');
    fireEvent.press(screen.getByText('Send'));
    await waitFor(() => expect(screen.getByText(/unavailable right now/i)).toBeTruthy());

    // Turn 1's user message AND assistant reply survive the turn-2 rollback…
    expect(screen.getByText('first question')).toBeTruthy();
    expect(screen.getByText('Lead with your strongest signal.')).toBeTruthy();
    // …and only turn 2's failed bubble is gone, its text returned to the input for retry.
    expect(screen.queryByText('second question')).toBeNull();
    expect(screen.getByDisplayValue('second question')).toBeTruthy();
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
