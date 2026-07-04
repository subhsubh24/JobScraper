/// <reference types="jest" />
// Copy/share affordance for a generated prep artifact. Asserts the real side-effect: pressing
// the control opens the OS share sheet (RN's built-in Share) with the artifact's actual text —
// the way the user gets a generated résumé/cover letter/study plan OUT of the app. No fake
// success: the component never claims a copy/share happened.

import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { Share } from 'react-native';

import { ArtifactActions } from '@/components/artifact-actions';

afterEach(() => jest.restoreAllMocks());

describe('ArtifactActions', () => {
  it('opens the OS share sheet with the artifact text when pressed', async () => {
    const spy = jest.spyOn(Share, 'share').mockResolvedValue(undefined as never);

    render(<ArtifactActions text={'# Tailored résumé\n\nReal experience, reworded.'} title="Tailored résumé" />);
    fireEvent.press(screen.getByLabelText('Copy or share Tailored résumé'));

    await waitFor(() =>
      expect(spy).toHaveBeenCalledWith(
        expect.objectContaining({
          message: '# Tailored résumé\n\nReal experience, reworded.',
          title: 'Tailored résumé',
        }),
      ),
    );
  });

  it('swallows a dismissed/failed share without crashing (no fake success)', async () => {
    const spy = jest.spyOn(Share, 'share').mockRejectedValue(new Error('dismissed'));

    render(<ArtifactActions text="content" title="Cover letter" />);
    fireEvent.press(screen.getByLabelText('Copy or share Cover letter'));

    await waitFor(() => expect(spy).toHaveBeenCalled());
    // The control is still present; nothing claims success.
    expect(screen.getByText('Copy or share')).toBeTruthy();
  });
});
