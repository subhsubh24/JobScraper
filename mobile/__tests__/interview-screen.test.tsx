/// <reference types="jest" />
// BUILDS != WORKS for the mock-interview screen: it must gate on Pro + consent, generate real
// questions, render the current question, score a real answer (the server's score, shown after the
// POST resolves — no optimistic fake), and degrade to honest error states. expo-router, auth, the
// consent card, the report button, and the API are mocked so the screen renders headlessly (native
// can't compile on CI/Linux). (Factory vars are `mock`-prefixed per jest's hoisting rule.)

import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';

jest.mock('react-native-safe-area-context', () => {
  const { View } = require('react-native');
  return { SafeAreaView: View, useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }) };
});

const mockPush = jest.fn();
jest.mock('expo-router', () => ({
  router: { push: (...a: unknown[]) => mockPush(...a), back: jest.fn() },
  Stack: { Screen: () => null },
  useLocalSearchParams: () => ({ jobId: 'job-1' }),
}));

let mockUser: { id: string; tier: string; ai_consent?: boolean } = { id: 'u1', tier: 'free' };
jest.mock('@/contexts/auth', () => ({
  useAuth: () => ({ user: mockUser }),
}));

jest.mock('@/components/ai-consent', () => {
  const { Text } = require('react-native');
  return {
    hasAiConsent: (u: { ai_consent?: boolean } | null) => u?.ai_consent === true,
    AiConsentCard: () => <Text>Enable AI features</Text>,
  };
});

jest.mock('@/components/report-button', () => {
  const { Text } = require('react-native');
  return { ReportButton: () => <Text>Report</Text> };
});

const mockList = jest.fn();
const mockStart = jest.fn();
const mockAnswer = jest.fn();
const mockGet = jest.fn();
jest.mock('@/services/api', () => {
  class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  }
  return {
    api: {
      listMockInterviews: (...a: unknown[]) => mockList(...a),
      startMockInterview: (...a: unknown[]) => mockStart(...a),
      answerMockInterview: (...a: unknown[]) => mockAnswer(...a),
      getMockInterview: (...a: unknown[]) => mockGet(...a),
    },
    ApiError,
  };
});

import MockInterviewScreen from '@/app/interview/[jobId]';

const SESSION = {
  id: 'iv-1',
  job_id: 'job-1',
  status: 'in_progress',
  questions: [
    { question: 'Describe a system you designed.', category: 'technical' },
    { question: 'Tell me about a conflict you resolved.', category: 'behavioral' },
  ],
  answers: [],
  answered_count: 0,
  total: 2,
  created_at: null,
};

afterEach(() => {
  jest.clearAllMocks();
  mockUser = { id: 'u1', tier: 'free' };
});

describe('MockInterviewScreen', () => {
  it('shows a Pro upsell for a free user (not the start control)', async () => {
    mockList.mockResolvedValue([]);
    render(<MockInterviewScreen />);
    expect(await screen.findByText('Upgrade to Pro')).toBeTruthy();
    expect(screen.queryByText('Start mock interview')).toBeNull();
  });

  it('requires consent before a Pro user can start', async () => {
    mockUser = { id: 'u1', tier: 'premium', ai_consent: false };
    mockList.mockResolvedValue([]);
    render(<MockInterviewScreen />);
    expect(await screen.findByText('Enable AI features')).toBeTruthy();
    expect(screen.queryByText('Start mock interview')).toBeNull();
  });

  it('starts a session and renders the first real question', async () => {
    mockUser = { id: 'u1', tier: 'premium', ai_consent: true };
    mockList.mockResolvedValue([]);
    mockStart.mockResolvedValue(SESSION);

    render(<MockInterviewScreen />);
    fireEvent.press(await screen.findByText('Start mock interview'));

    expect(await screen.findByText('Describe a system you designed.')).toBeTruthy();
    expect(mockStart).toHaveBeenCalledWith('job-1', 5);
  });

  it('scores a real answer and shows the SERVER score + feedback (no optimistic fake)', async () => {
    mockUser = { id: 'u1', tier: 'premium', ai_consent: true };
    mockList.mockResolvedValue([]);
    mockStart.mockResolvedValue(SESSION);
    mockAnswer.mockResolvedValue({
      result: {
        question_index: 0,
        answer: 'my answer',
        relevance: 4,
        specificity: 3,
        star: 5,
        overall: 80,
        feedback: 'Strong structure; add a concrete metric.',
        model_answer: 'A strong answer would open with the situation.',
      },
      status: 'in_progress',
      answered_count: 1,
      total: 2,
    });

    render(<MockInterviewScreen />);
    fireEvent.press(await screen.findByText('Start mock interview'));

    const input = await screen.findByLabelText('Your answer');
    fireEvent.changeText(input, 'I designed a distributed queue that cut latency 40%.');
    fireEvent.press(screen.getByText('Submit answer'));

    // The score shown is the server's — its feedback, model answer, and "scored" panel only
    // appear after the POST resolved (no optimistic fake before the real result arrives).
    expect(await screen.findByText('Strong structure; add a concrete metric.')).toBeTruthy();
    expect(screen.getByText('Your answer scored')).toBeTruthy();
    expect(screen.getByText('A strong answer would open with the situation.')).toBeTruthy();
    await waitFor(() => expect(mockAnswer).toHaveBeenCalledWith('iv-1', 0, 'I designed a distributed queue that cut latency 40%.'));
  });

  it('surfaces an honest error state when the session list fails (no stuck spinner)', async () => {
    const { ApiError } = require('@/services/api');
    mockList.mockRejectedValue(new ApiError(500, 'Could not load this interview.'));
    render(<MockInterviewScreen />);
    expect(await screen.findByText('Could not load this interview.')).toBeTruthy();
  });
});
