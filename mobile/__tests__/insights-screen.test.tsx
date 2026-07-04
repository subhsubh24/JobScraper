/// <reference types="jest" />
// BUILDS != WORKS for the cross-pipeline skill-gap screen: it must render REAL heatmap data (the
// gap skills + how many jobs demand them), degrade to honest empty / error states, and gate the
// AI learning plan behind Pro — not placeholders, not a blank screen, not a dead-end. expo-router,
// the auth context, and the API are mocked so the screen renders headlessly (native can't compile
// on CI/Linux). (Factory vars are `mock`-prefixed per jest's hoisting rule.)

import { render, screen } from '@testing-library/react-native';

jest.mock('react-native-safe-area-context', () => {
  const { View } = require('react-native');
  return { SafeAreaView: View, useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }) };
});

const mockPush = jest.fn();
jest.mock('expo-router', () => {
  const React = require('react');
  return {
    router: { push: (...a: unknown[]) => mockPush(...a), back: jest.fn() },
    useFocusEffect: (cb: () => void) => React.useEffect(() => cb(), [cb]),
  };
});

let mockUser: { id: string; tier: string; ai_consent?: boolean } = { id: 'u1', tier: 'free' };
jest.mock('@/contexts/auth', () => ({
  useAuth: () => ({ user: mockUser }),
}));

// Isolate the screen from the consent card's own deps; keep the real hasAiConsent logic.
jest.mock('@/components/ai-consent', () => {
  const { Text } = require('react-native');
  return {
    hasAiConsent: (u: { ai_consent?: boolean } | null) => u?.ai_consent === true,
    AiConsentCard: () => <Text>Enable AI features</Text>,
  };
});

const mockSkillGaps = jest.fn();
const mockGenerateLearningPlan = jest.fn();
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
      skillGaps: () => mockSkillGaps(),
      generateLearningPlan: () => mockGenerateLearningPlan(),
    },
    ApiError,
  };
});

import InsightsScreen from '@/app/(tabs)/insights';

const ANALYSIS = {
  total_jobs: 3,
  has_resume: true,
  gaps: [
    { skill: 'kubernetes', job_count: 2, total_jobs: 3, coverage: 0.667, in_resume: false },
    { skill: 'aws', job_count: 1, total_jobs: 3, coverage: 0.333, in_resume: false },
  ],
  strengths: [{ skill: 'python', job_count: 2, total_jobs: 3, coverage: 0.667, in_resume: true }],
};

afterEach(() => {
  jest.clearAllMocks();
  mockUser = { id: 'u1', tier: 'free' };
});

describe('InsightsScreen', () => {
  it('renders the real skill-gap heatmap for a free user, with a Pro upsell (not the generate button)', async () => {
    mockSkillGaps.mockResolvedValue(ANALYSIS);

    render(<InsightsScreen />);

    // The most-demanded missing skill + its real pipeline count render (not a placeholder).
    expect(await screen.findByText('kubernetes')).toBeTruthy();
    expect(screen.getByText('2 of 3 jobs')).toBeTruthy();
    expect(screen.getByText('aws')).toBeTruthy();
    // A résumé skill shows as a strength, never a gap.
    expect(screen.getByText(/python/)).toBeTruthy();
    // Free tier sees the upsell, NOT the generate button (server-side gate reflected honestly).
    expect(screen.getByText('Upgrade to Pro')).toBeTruthy();
    expect(screen.queryByText('Generate learning plan')).toBeNull();
  });

  it('shows the generate button for a consented Pro user', async () => {
    mockUser = { id: 'u1', tier: 'premium', ai_consent: true };
    mockSkillGaps.mockResolvedValue(ANALYSIS);

    render(<InsightsScreen />);

    expect(await screen.findByText('Generate learning plan')).toBeTruthy();
    expect(screen.queryByText('Upgrade to Pro')).toBeNull();
  });

  it('requires consent before a Pro user can generate a plan', async () => {
    mockUser = { id: 'u1', tier: 'premium', ai_consent: false };
    mockSkillGaps.mockResolvedValue(ANALYSIS);

    render(<InsightsScreen />);

    expect(await screen.findByText('Enable AI features')).toBeTruthy();
    expect(screen.queryByText('Generate learning plan')).toBeNull();
  });

  it('shows the empty state when the user has no jobs', async () => {
    mockSkillGaps.mockResolvedValue({ total_jobs: 0, has_resume: false, gaps: [], strengths: [] });

    render(<InsightsScreen />);
    expect(await screen.findByText('Track a few jobs first')).toBeTruthy();
  });

  it('surfaces an honest error state when the API fails (no stuck spinner)', async () => {
    const { ApiError } = require('@/services/api');
    mockSkillGaps.mockRejectedValue(new ApiError(500, 'Could not load your skill gaps.'));

    render(<InsightsScreen />);
    expect(await screen.findByText('Could not load your skill gaps.')).toBeTruthy();
  });
});
