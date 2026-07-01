/// <reference types="jest" />
// Track D: the user-facing "report this AI response" control (Apple/Google 2026 GenAI/UGC).
// Asserts the real side-effect wiring: expanding the control, submitting fires the REAL
// api.reportContent with the right payload, and the honest success state only shows AFTER it
// resolves — a provider failure surfaces an error and does NOT show "flagged for review".

import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';

jest.mock('@/services/api', () => ({
  api: { reportContent: jest.fn(async () => undefined) },
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

import { ReportButton } from '@/components/report-button';
import { api, ApiError } from '@/services/api';

afterEach(() => jest.clearAllMocks());

describe('ReportButton', () => {
  it('submits a report with the selected reason + excerpt and shows the honest done state', async () => {
    render(<ReportButton contentType="coach" contentRef="sess-1" contentExcerpt="bad advice" />);

    // Low-emphasis trigger, then the form opens.
    fireEvent.press(screen.getByLabelText('Report this response'));
    fireEvent.press(screen.getByLabelText('Harmful or dangerous advice'));
    fireEvent.press(screen.getByText('Submit report'));

    await waitFor(() =>
      expect(api.reportContent).toHaveBeenCalledWith({
        content_type: 'coach',
        reason: 'harmful',
        content_ref: 'sess-1',
        content_excerpt: 'bad advice',
        detail: undefined,
      }),
    );
    // Success state is downstream of the resolved call — never optimistic.
    await waitFor(() => expect(screen.getByText(/flagged for review/i)).toBeTruthy());
  });

  it('surfaces an error and does NOT show success when the report fails', async () => {
    (api.reportContent as jest.Mock).mockRejectedValueOnce(new ApiError(500, 'Server error'));
    render(<ReportButton contentType="prep_pack" contentExcerpt="x" />);

    fireEvent.press(screen.getByLabelText('Report this response'));
    fireEvent.press(screen.getByText('Submit report'));

    await waitFor(() => expect(screen.getByText('Server error')).toBeTruthy());
    expect(screen.queryByText(/flagged for review/i)).toBeNull();
  });
});
