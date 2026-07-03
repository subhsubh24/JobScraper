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

let mockUser: { tier: string; career_plus?: boolean; ai_consent?: boolean } = {
  tier: 'free',
  ai_consent: true,
};
jest.mock('@/contexts/auth', () => ({ useAuth: () => ({ user: mockUser, setUser: jest.fn() }) }));

const mockGetJob = jest.fn();
const mockGeneratePrep = jest.fn();
const mockUpdateStatus = jest.fn();
const mockGenerateNeg = jest.fn();
const mockGenerateLetter = jest.fn();
const mockGenerateStudy = jest.fn();
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
      generateSalaryNegotiation: (id: string, target: number) => mockGenerateNeg(id, target),
      generateCoverLetter: (id: string) => mockGenerateLetter(id),
      generateStudyPlan: (id: string, days: number) => mockGenerateStudy(id, days),
      grantAiConsent: jest.fn(async () => ({ ...mockUser, ai_consent: true })),
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
  // Default: consented, so the AI-consent gate is a no-op and these tests exercise the
  // prep/salary flows directly. A dedicated test below covers the not-consented gate.
  mockUser = { tier: 'free', ai_consent: true };
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

  it('gates prep generation on third-party-AI consent — no LLM call until consented (Apple 5.1.2(i))', async () => {
    mockUser = { tier: 'free', ai_consent: false };
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');

    fireEvent.press(screen.getByText('Generate prep pack (1 free)'));
    // The consent prompt appears and NO prep request is made until the user consents.
    expect(await screen.findByText('Enable AI features')).toBeTruthy();
    expect(mockGeneratePrep).not.toHaveBeenCalled();
  });

  it('gates salary negotiation behind Career+ for a non-Career+ user (upsell, no input)', async () => {
    mockUser = { tier: 'premium' }; // Pro (premium, not career_plus) — must NOT see the tool
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');
    expect(screen.getByText('Upgrade to Career+')).toBeTruthy();
    expect(screen.queryByText('Generate negotiation guide')).toBeNull();

    fireEvent.press(screen.getByText('Upgrade to Career+'));
    expect(mockPush).toHaveBeenCalledWith('/paywall');
  });

  it('lets a Career+ user generate a negotiation guide and renders it inline', async () => {
    mockUser = { tier: 'premium', career_plus: true, ai_consent: true };
    mockGenerateNeg.mockResolvedValue({
      title: 'Salary Negotiation: Senior Backend Engineer',
      content: '## Talking points\nAnchor high, cite market data.',
    });
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');

    fireEvent.changeText(screen.getByPlaceholderText('180000'), '190000');
    fireEvent.press(screen.getByText('Generate negotiation guide'));

    expect(await screen.findByText('Salary Negotiation: Senior Backend Engineer')).toBeTruthy();
    // The real target salary reached the API (rounded int), and the artifact content rendered.
    expect(mockGenerateNeg).toHaveBeenCalledWith('job-1', 190000);
    expect(screen.getByTestId('prep-content').props.children).toContain('Anchor high');
  });

  it('rejects a sub-1 target salary that rounds to 0 (no wasted LLM call)', async () => {
    mockUser = { tier: 'premium', career_plus: true, ai_consent: true };
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');

    fireEvent.changeText(screen.getByPlaceholderText('180000'), '0.4');
    fireEvent.press(screen.getByText('Generate negotiation guide'));

    expect(await screen.findByText('Enter your target salary (a positive number).')).toBeTruthy();
    expect(mockGenerateNeg).not.toHaveBeenCalled();
  });

  it('gates cover letter + study plan behind Pro for a free user (upsell, no generate buttons)', async () => {
    mockUser = { tier: 'free', ai_consent: true };
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');
    expect(screen.getByText('Upgrade to Pro')).toBeTruthy();
    expect(screen.queryByText('Generate cover letter')).toBeNull();
    expect(screen.queryByText('Generate study plan')).toBeNull();

    fireEvent.press(screen.getByText('Upgrade to Pro'));
    expect(mockPush).toHaveBeenCalledWith('/paywall');
  });

  it('lets a Pro user generate a cover letter and renders it inline', async () => {
    mockUser = { tier: 'premium', ai_consent: true };
    mockGenerateLetter.mockResolvedValue({
      title: 'Cover Letter: Senior Backend Engineer at Acme',
      content: 'Dear Hiring Manager, I build reliable Python services.',
    });
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');

    fireEvent.press(screen.getByText('Generate cover letter'));

    expect(await screen.findByText('Cover Letter: Senior Backend Engineer at Acme')).toBeTruthy();
    expect(mockGenerateLetter).toHaveBeenCalledWith('job-1');
  });

  it('lets a Pro user generate a study plan, passing the bounded day count through', async () => {
    mockUser = { tier: 'premium', ai_consent: true };
    mockGenerateStudy.mockResolvedValue({
      title: '7-Day Study Plan: Senior Backend Engineer',
      content: '## Day 1\nData structures.',
    });
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');

    // Default days is 7 (the field's initial value) — pressing generate sends it as an int.
    fireEvent.press(screen.getByText('Generate study plan'));

    expect(await screen.findByText('7-Day Study Plan: Senior Backend Engineer')).toBeTruthy();
    expect(mockGenerateStudy).toHaveBeenCalledWith('job-1', 7);
  });

  it('rejects an out-of-range study-plan day count client-side (no wasted LLM call)', async () => {
    mockUser = { tier: 'premium', ai_consent: true };
    render(<JobDetailScreen />);
    await screen.findByText('Senior Backend Engineer');

    fireEvent.changeText(screen.getByPlaceholderText('7'), '40');
    fireEvent.press(screen.getByText('Generate study plan'));

    expect(await screen.findByText('Enter how many days you have to prep (1–30).')).toBeTruthy();
    expect(mockGenerateStudy).not.toHaveBeenCalled();
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
