/// <reference types="jest" />
// BUILDS != WORKS for the auth screens (Track B "navigation + auth wired to the API"):
// the Login + Register screens must render their fields, validate input before calling the
// API, call signIn/signUp with the typed values, navigate into the app on success, and
// surface an ApiError honestly (no dead-end, no silent failure). Auth + router + the API
// client are mocked so the screens render headlessly; the real signIn/signUp -> api wiring
// is covered separately in api.test.ts.

import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

const mockReplace = jest.fn();
// Arrow wrappers (not `replace: mockReplace`): ES `import` hoists the screen's require above
// these `const` declarations, so a direct reference would capture the jest.fn while still
// undefined. The wrapper resolves the mock lazily at call time. (Same foot-gun as
// job-detail-screen.test.tsx.)
jest.mock('expo-router', () => {
  const { Text } = require('react-native');
  return {
    router: { replace: (...a: unknown[]) => mockReplace(...a) },
    Link: ({ children }: { children: React.ReactNode }) => <Text>{children}</Text>,
  };
});

const mockSignIn = jest.fn();
const mockSignUp = jest.fn();
jest.mock('@/contexts/auth', () => ({
  useAuth: () => ({ signIn: mockSignIn, signUp: mockSignUp }),
}));

jest.mock('@/services/api', () => {
  class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  }
  return { ApiError };
});

import LoginScreen from '@/app/(auth)/login';
import RegisterScreen from '@/app/(auth)/register';

beforeEach(() => {
  mockSignIn.mockResolvedValue(undefined);
  mockSignUp.mockResolvedValue(undefined);
});
afterEach(() => jest.clearAllMocks());

describe('LoginScreen', () => {
  it('renders the email + password fields and the register link', () => {
    render(<LoginScreen />);
    expect(screen.getByPlaceholderText('you@example.com')).toBeTruthy();
    expect(screen.getByPlaceholderText('••••••••')).toBeTruthy();
    expect(screen.getByText('Create an account')).toBeTruthy();
  });

  it('blocks submit and shows an error when fields are blank (no API call)', async () => {
    render(<LoginScreen />);
    fireEvent.press(screen.getByText('Log in'));
    expect(await screen.findByText('Enter your email and password.')).toBeTruthy();
    expect(mockSignIn).not.toHaveBeenCalled();
    expect(mockReplace).not.toHaveBeenCalled();
  });

  it('calls signIn with the typed values and navigates into the app on success', async () => {
    render(<LoginScreen />);
    fireEvent.changeText(screen.getByPlaceholderText('you@example.com'), '  jane@example.com  ');
    fireEvent.changeText(screen.getByPlaceholderText('••••••••'), 'hunter2pw');
    fireEvent.press(screen.getByText('Log in'));
    await waitFor(() => expect(mockSignIn).toHaveBeenCalledWith('jane@example.com', 'hunter2pw'));
    await waitFor(() => expect(mockReplace).toHaveBeenCalledWith('/(tabs)'));
  });

  it('surfaces an ApiError message and does NOT navigate (no dead-end)', async () => {
    const { ApiError } = require('@/services/api');
    mockSignIn.mockRejectedValue(new ApiError(401, 'Invalid email or password'));
    render(<LoginScreen />);
    fireEvent.changeText(screen.getByPlaceholderText('you@example.com'), 'jane@example.com');
    fireEvent.changeText(screen.getByPlaceholderText('••••••••'), 'wrongpass1');
    fireEvent.press(screen.getByText('Log in'));
    expect(await screen.findByText('Invalid email or password')).toBeTruthy();
    expect(mockReplace).not.toHaveBeenCalled();
  });
});

describe('RegisterScreen', () => {
  it('renders the account fields and the login link', () => {
    render(<RegisterScreen />);
    expect(screen.getByPlaceholderText('Jane Seeker')).toBeTruthy();
    expect(screen.getByPlaceholderText('you@example.com')).toBeTruthy();
    expect(screen.getByPlaceholderText('At least 8 characters')).toBeTruthy();
    expect(screen.getByText('Log in')).toBeTruthy();
  });

  it('blocks submit on a too-short password (no API call)', async () => {
    render(<RegisterScreen />);
    fireEvent.changeText(screen.getByPlaceholderText('you@example.com'), 'jane@example.com');
    fireEvent.changeText(screen.getByPlaceholderText('At least 8 characters'), 'short');
    fireEvent.press(screen.getByText('Create account'));
    expect(
      await screen.findByText('Use a valid email and a password of at least 8 characters.'),
    ).toBeTruthy();
    expect(mockSignUp).not.toHaveBeenCalled();
    expect(mockReplace).not.toHaveBeenCalled();
  });

  it('calls signUp with the typed profile and navigates into the app on success', async () => {
    render(<RegisterScreen />);
    fireEvent.changeText(screen.getByPlaceholderText('Jane Seeker'), 'Jane Seeker');
    fireEvent.changeText(screen.getByPlaceholderText('you@example.com'), 'jane@example.com');
    fireEvent.changeText(screen.getByPlaceholderText('At least 8 characters'), 'hunter2pw');
    fireEvent.press(screen.getByText('Create account'));
    await waitFor(() =>
      expect(mockSignUp).toHaveBeenCalledWith(
        expect.objectContaining({ email: 'jane@example.com', password: 'hunter2pw', full_name: 'Jane Seeker' }),
      ),
    );
    await waitFor(() => expect(mockReplace).toHaveBeenCalledWith('/(tabs)'));
  });

  it('surfaces an ApiError message and does NOT navigate (no dead-end)', async () => {
    const { ApiError } = require('@/services/api');
    mockSignUp.mockRejectedValue(new ApiError(400, 'Could not register with those details'));
    render(<RegisterScreen />);
    fireEvent.changeText(screen.getByPlaceholderText('you@example.com'), 'taken@example.com');
    fireEvent.changeText(screen.getByPlaceholderText('At least 8 characters'), 'hunter2pw');
    fireEvent.press(screen.getByText('Create account'));
    expect(await screen.findByText('Could not register with those details')).toBeTruthy();
    expect(mockReplace).not.toHaveBeenCalled();
  });
});
