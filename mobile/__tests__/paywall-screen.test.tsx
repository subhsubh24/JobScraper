/// <reference types="jest" />
// Track B: the paywall must reflect REAL entitlement state, not a fixed upgrade pitch.
// - a FREE user sees the upgrade offer (plans + "Start Premium"), and the purchase button is
//   HONEST (no fake "purchase complete" — entitlement only flips server-side);
// - a PREMIUM user sees a confirmation state, NOT an upgrade CTA (the stale-prompt bug);
// - the screen refreshes entitlement on open so an upgrade made elsewhere is reflected.
// expo-router + the auth context are mocked so the screen renders headlessly.

import { Alert } from 'react-native';
import { fireEvent, render, screen } from '@testing-library/react-native';

const mockBack = jest.fn();
jest.mock('expo-router', () => ({
  // Arrow wrapper: ES import hoists the screen require above these consts, so a direct
  // `back: mockBack` would capture it while undefined. Resolve lazily at call time.
  router: { back: (...a: unknown[]) => mockBack(...a), push: jest.fn() },
}));

const mockRefresh = jest.fn((..._a: unknown[]) => Promise.resolve());
let mockTier: 'free' | 'premium' = 'free';
jest.mock('@/contexts/auth', () => ({
  useAuth: () => ({ user: { id: 'u1', tier: mockTier }, refresh: (...a: unknown[]) => mockRefresh(...a) }),
}));

import PaywallScreen from '@/app/paywall';

afterEach(() => {
  jest.clearAllMocks();
  mockTier = 'free';
});

describe('PaywallScreen', () => {
  it('shows the upgrade offer to a free user', () => {
    mockTier = 'free';
    render(<PaywallScreen />);
    expect(screen.getByText('Career Operator Premium')).toBeTruthy();
    expect(screen.getByText('Start Premium')).toBeTruthy();
    expect(screen.getByText('Annual')).toBeTruthy();
    expect(screen.getByText('Monthly')).toBeTruthy();
    // Must NOT tell a free user they already have Premium.
    expect(screen.queryByText("You're on Premium")).toBeNull();
  });

  it('shows a confirmation state (no buy CTA) to a premium user', () => {
    mockTier = 'premium';
    render(<PaywallScreen />);
    expect(screen.getByText("You're on Premium")).toBeTruthy();
    // The upgrade CTA + plan cards must NOT show to someone already entitled.
    expect(screen.queryByText('Start Premium')).toBeNull();
    expect(screen.queryByText('Monthly')).toBeNull();
  });

  it('refreshes entitlement when the paywall opens', () => {
    render(<PaywallScreen />);
    expect(mockRefresh).toHaveBeenCalledTimes(1);
  });

  it('plan cards expose a single descriptive accessibility label (price read as one unit)', () => {
    mockTier = 'free';
    render(<PaywallScreen />);
    // A screen reader otherwise reads "Annual" "$96" "/yr" "Save ~33%" as disjoint fragments.
    // Each plan card is one accessible element with the price + terms in its label.
    expect(
      screen.getByLabelText('Annual plan, $96 per year. Save about 33%, best value.'),
    ).toBeTruthy();
    expect(
      screen.getByLabelText('Monthly plan, $12 per month. Cancel anytime.'),
    ).toBeTruthy();
  });

  it('feature rows are accessible (one announced element) on the free-tier upgrade screen', () => {
    // The free-tier path is what most users hit; its feature rows must group the text into one
    // a11y element (the decorative checkmark is hidden), same as the premium-confirmation path.
    mockTier = 'free';
    render(<PaywallScreen />);
    expect(screen.getByLabelText('Unlimited tracked jobs')).toBeTruthy();
    expect(screen.getByLabelText('AI Career Coach')).toBeTruthy();
  });

  it('purchase is honest — no fake success, no navigation', () => {
    const alertSpy = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
    mockTier = 'free';
    render(<PaywallScreen />);
    // The screen wires "Start Premium" to an honest alert. Invoke the handler the same way a
    // press would, by finding the button and triggering its onPress via the alert side-effect.
    // fireEvent.press bubbles from the label Text to the Button's Pressable ancestor.
    fireEvent.press(screen.getByText('Start Premium'));
    expect(alertSpy).toHaveBeenCalledTimes(1);
    const [title, body] = alertSpy.mock.calls[0];
    expect(String(title)).toMatch(/coming soon/i);
    expect(String(body)).toMatch(/no charge was made/i);
    // Honest dead-stop, not a fake unlock — we never navigate as if purchased.
    expect(mockBack).not.toHaveBeenCalled();
    alertSpy.mockRestore();
  });
});
