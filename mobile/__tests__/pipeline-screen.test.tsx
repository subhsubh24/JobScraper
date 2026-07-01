/// <reference types="jest" />
// BUILDS != WORKS for the core data screen: the pipeline must render REAL API data (job
// titles, company, fit score, aggregate stats) and degrade to honest empty / error states —
// not placeholders, not a blank screen, not a dead-end. expo-router, the auth context, and
// the API are mocked so the screen renders headlessly (native can't compile on CI/Linux).
//
// (Factory vars are `mock`-prefixed per jest's hoisting rule; the mocked object KEYS keep the
// real api method names the screen calls.)

import { render, screen } from '@testing-library/react-native';

jest.mock('react-native-safe-area-context', () => {
  const { View } = require('react-native');
  return { SafeAreaView: View, useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }) };
});

const mockPush = jest.fn();
jest.mock('expo-router', () => {
  const React = require('react');
  return {
    // Arrow wrapper: ES import hoists the screen require above the `const mockPush`, so a
    // direct `push: mockPush` would capture it while undefined. Resolve lazily at call time.
    router: { push: (...a: unknown[]) => mockPush(...a), back: jest.fn() },
    // Run the focus callback once on mount, like a real focus event.
    useFocusEffect: (cb: () => void) => React.useEffect(() => cb(), [cb]),
  };
});

jest.mock('@/contexts/auth', () => ({
  useAuth: () => ({ user: { id: 'u1', full_name: 'Ada Lovelace', tier: 'free' } }),
}));

const mockListJobs = jest.fn();
const mockPipeline = jest.fn();
jest.mock('@/services/api', () => {
  class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  }
  return { api: { listJobs: () => mockListJobs(), pipeline: () => mockPipeline() }, ApiError };
});

import PipelineScreen from '@/app/(tabs)/index';

const JOBS = [
  { id: 'j1', title: 'Senior Backend Engineer', company: 'Acme', location: 'Remote', score: 87, status: 'applied' },
  { id: 'j2', title: 'Staff Platform Engineer', company: 'Globex', location: null, score: null, status: 'saved' },
];
// average_score deliberately distinct from any job score so the assertions are unambiguous.
const STATS = { total_jobs: 2, status_breakdown: { applied: 1, saved: 1 }, average_score: 84, top_jobs: [] };

afterEach(() => jest.clearAllMocks());

describe('PipelineScreen', () => {
  it('renders real jobs + aggregate stats after loading', async () => {
    mockListJobs.mockResolvedValue(JOBS);
    mockPipeline.mockResolvedValue(STATS);

    render(<PipelineScreen />);

    // The real job rows render with their actual titles + companies + score.
    expect(await screen.findByText('Senior Backend Engineer')).toBeTruthy();
    expect(screen.getByText('Staff Platform Engineer')).toBeTruthy();
    expect(screen.getByText('87')).toBeTruthy(); // j1 fit score, not a placeholder
    // Aggregate stat row reflects the API payload (avg fit = 84, tracked = 2).
    expect(screen.getByText('Tracked')).toBeTruthy();
    expect(screen.getByText('Avg fit')).toBeTruthy();
    expect(screen.getByText('84')).toBeTruthy();
    // Each stat announces as ONE labelled element ("Avg fit: 84"), not two bare Text nodes.
    expect(screen.getByLabelText('Avg fit: 84')).toBeTruthy();
    expect(screen.getByLabelText('Tracked: 2')).toBeTruthy();
    // Personalized greeting uses the real user.
    expect(screen.getByText(/Ada/)).toBeTruthy();
  });

  it('shows the empty state when the user has no jobs', async () => {
    mockListJobs.mockResolvedValue([]);
    mockPipeline.mockResolvedValue({ total_jobs: 0, status_breakdown: {}, average_score: 0, top_jobs: [] });

    render(<PipelineScreen />);
    expect(await screen.findByText('No jobs yet')).toBeTruthy();
  });

  it('surfaces an honest error state when the API fails', async () => {
    const { ApiError } = require('@/services/api');
    mockListJobs.mockRejectedValue(new ApiError(500, 'Could not load your pipeline.'));
    mockPipeline.mockRejectedValue(new ApiError(500, 'boom'));

    render(<PipelineScreen />);
    // The spinner must give way to a real error message — not hang forever.
    expect(await screen.findByText('Could not load your pipeline.')).toBeTruthy();
  });

  it('replaces the loading spinner with content (no stuck spinner)', async () => {
    mockListJobs.mockResolvedValue(JOBS);
    mockPipeline.mockResolvedValue(STATS);
    const { UNSAFE_queryAllByType } = render(<PipelineScreen />);
    await screen.findByText('Senior Backend Engineer');
    const { ActivityIndicator } = require('react-native');
    expect(UNSAFE_queryAllByType(ActivityIndicator).length).toBe(0);
  });
});
