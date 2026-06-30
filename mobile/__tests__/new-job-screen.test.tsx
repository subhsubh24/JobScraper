/// <reference types="jest" />
// Track B: the Add-a-job screen validates required fields locally, calls the real createJob
// API with the typed values, navigates back on success, and surfaces an API failure honestly
// (no fake "added" + no navigation). expo-router + the api client are mocked for a headless run.

import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';

const mockBack = jest.fn();
jest.mock('expo-router', () => ({
  // Arrow wrapper guards against ES-import hoisting capturing an undefined mock.
  router: { back: (...a: unknown[]) => mockBack(...a) },
  Stack: { Screen: () => null },
}));

jest.mock('@/services/api', () => ({
  api: { createJob: jest.fn(async () => ({ id: 'j1' })) },
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

import NewJobScreen from '@/app/job/new';
import { api, ApiError } from '@/services/api';

afterEach(() => jest.clearAllMocks());

describe('NewJobScreen', () => {
  it('blocks submit when title/company are empty and does NOT call the API', () => {
    render(<NewJobScreen />);
    fireEvent.press(screen.getByText('Add & score'));
    expect(screen.getByText('A title and company are required.')).toBeTruthy();
    expect(api.createJob).not.toHaveBeenCalled();
    expect(mockBack).not.toHaveBeenCalled();
  });

  it('creates the job with the typed values and navigates back on success', async () => {
    render(<NewJobScreen />);
    fireEvent.changeText(screen.getByPlaceholderText('Senior Backend Engineer'), 'Staff Engineer');
    fireEvent.changeText(screen.getByPlaceholderText('Acme'), 'Globex');
    fireEvent.changeText(screen.getByPlaceholderText('Remote US'), 'Remote');
    fireEvent.press(screen.getByText('Add & score'));

    await waitFor(() => expect(mockBack).toHaveBeenCalledTimes(1));
    expect(api.createJob).toHaveBeenCalledWith({
      title: 'Staff Engineer',
      company_name: 'Globex',
      location: 'Remote',
      description: undefined,
    });
  });

  it('surfaces an API failure honestly and does NOT navigate (no fake success)', async () => {
    (api.createJob as jest.Mock).mockRejectedValueOnce(new ApiError(500, 'Server exploded'));
    render(<NewJobScreen />);
    fireEvent.changeText(screen.getByPlaceholderText('Senior Backend Engineer'), 'Staff Engineer');
    fireEvent.changeText(screen.getByPlaceholderText('Acme'), 'Globex');
    fireEvent.press(screen.getByText('Add & score'));

    await waitFor(() => expect(screen.getByText('Server exploded')).toBeTruthy());
    expect(mockBack).not.toHaveBeenCalled();
  });
});
