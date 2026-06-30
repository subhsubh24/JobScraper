/// <reference types="jest" />
// BUILDS != WORKS for the job-detail screen: it must render the REAL fetched job (title,
// fit score, explanation), gate prep generation by entitlement, route a 403 to the paywall
// (not a dead-end), and render a generated prep pack inline. Heavy deps mocked so it renders
// headlessly.

import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

const mockPush = jest.fn();
const mockBack = jest.fn();
// `push`/`back` are arrow wrappers (not `push: mockPush`) because ES `import` hoists the
// screen's require above the `const mock*` declarations — a direct reference would capture
// the jest.fn while still undefined. The wrappers resolve the mock lazily at call time.
jest.mock('expo-router', () => ({
  router: { push: (...a: unknown[]) => mockPush(...a), back: (...a: unknown[]) => mockBack(...a) },
  Stack: { Screen: () => null },
  useLocalSearchParams: () => ({ id: 'job-1' }),
}));

let mockUser: { tier: string } = { tier: 'free' };
jest.mock('@/contexts/auth', () => ({ useAuth: () => ({ user: mockUser }) }));

const mockGetJob = jest.fn();
const mockGeneratePrep = jest.fn();
const mockUpdateStatus = jest.fn();
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
      getJob: (id: string) => mockGetJob(id),
      generatePrepPack: (id: string) => mockGeneratePrep(id),
      updateJobStatus: (id: string, s: string) => mockUpdateStatus(id, s),
    },
    ApiError,
  };
});

// Markdown rendering correctness is owned by markdown.test.tsx — mock it to a passthrough
// here so this suite asserts the SCREEN's integration (it hands the real prep content to the
// renderer + shows the title), not the renderer's hash-stripping again.
jest.mock('@/components/markdown', () => {
  const { Text } = require('react-native');
  return { Markdown: ({ content }: { content: string }) => <Text testID="prep-content">{content}</Text> };
});

import JobDetailScreen from '@/app/job/[id]';

const JOB = {
  id: 'job-1',
  title: 'Senior Backend Engineer',
  company: 'Acme',
  location: 'Remote',
  score: 87,
  score_explanation: 'Strong Python + distributed systems match.',
  status: 'saved',
};

beforeEach(() => {
  mockUser = { tier: 'free' };
  mockGetJob.mockResolvedValue(JOB);
});
afterEach(() => jest.clearAllMocks());

describe('JobDetailScreen', () => {
  it('renders the real fetched job: title, fit score, explanation', async () => {
    render(<JobDetailScreen />);
    expect(await screen.findByText('Senior Backend Engineer')).toBeTruthy();
    expect(screen.getByText(/87/)).toBeTruthy();
    expect(screen.getByText('Strong Python + distributed systems match.')).toBeTruthy();
  });

  it('labels prep generation as "(1 free)" for a free-tier user', async () => {
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');
    expect(screen.getByText('Generate prep pack (1 free)')).toBeTruthy();
  });

  it('routes a 403 from prep generation to the paywall (no dead-end)', async () => {
    const { ApiError } = require('@/services/api');
    mockGeneratePrep.mockRejectedValue(new ApiError(403, 'Upgrade'));
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');

    fireEvent.press(screen.getByText('Generate prep pack (1 free)'));
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/paywall'));
  });

  it('renders a generated prep pack inline on success', async () => {
    mockGeneratePrep.mockResolvedValue({ title: 'Interview Prep: Senior Backend Engineer', content: '## Company Research\nAcme builds rockets.' });
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');

    fireEvent.press(screen.getByText('Generate prep pack (1 free)'));
    // Screen-level integration: the prep card renders with the title and hands the REAL
    // generated content to the (mocked) Markdown renderer. Rendering correctness of the
    // markdown itself is covered by markdown.test.tsx.
    expect(await screen.findByText('Interview Prep: Senior Backend Engineer')).toBeTruthy();
    expect(screen.getByTestId('prep-content').props.children).toContain('Acme builds rockets.');
  });

  it('shows an honest error state when the job fails to load', async () => {
    const { ApiError } = require('@/services/api');
    mockGetJob.mockRejectedValue(new ApiError(404, 'Could not load this job.'));
    render(<JobDetailScreen />);
    expect(await screen.findByText('Could not load this job.')).toBeTruthy();
  });

  it('exposes the pipeline status chips as a radio group with the current status selected', async () => {
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');

    // All 7 pipeline statuses are operable as radio options (VoiceOver/TalkBack), not just
    // unlabeled tappable text — the core job-tracking loop is accessible.
    const options = screen.getAllByRole('radio');
    expect(options).toHaveLength(7);

    // The current status ('saved') is announced as the selected option.
    const selected = screen.getByRole('radio', { name: 'Set status to Saved', selected: true });
    expect(selected).toBeTruthy();
    // A non-current status is NOT selected.
    expect(
      screen.getByRole('radio', { name: 'Set status to Applied', selected: false }),
    ).toBeTruthy();
  });
});
