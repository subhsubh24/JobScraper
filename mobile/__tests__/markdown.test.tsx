/// <reference types="jest" />
import { render, screen } from '@testing-library/react-native';

import { Markdown } from '@/components/markdown';

// The Markdown renderer turns the backend's LLM prep-pack text into native hierarchy.
// These assert the INTENDED OUTCOME: headings, bold spans, and list items actually render
// as readable text — not a flat wall, not raw markup, not a blank screen.
describe('Markdown', () => {
  it('renders heading text without the leading hashes', () => {
    render(<Markdown content={'## Company Research\nAcme builds rockets.'} />);
    expect(screen.getByText('Company Research')).toBeTruthy();
    expect(screen.getByText('Acme builds rockets.')).toBeTruthy();
    // The raw markdown marker must not leak into the rendered output.
    expect(screen.queryByText('## Company Research')).toBeNull();
  });

  it('renders bold spans as their inner text (markers stripped)', () => {
    render(<Markdown content={'Highlight **your strongest** achievement.'} />);
    expect(screen.getByText('your strongest')).toBeTruthy();
    expect(screen.queryByText('**your strongest**')).toBeNull();
  });

  it('renders bullet and numbered list items', () => {
    render(<Markdown content={'- First point\n- Second point\n1. Step one'} />);
    expect(screen.getByText('First point')).toBeTruthy();
    expect(screen.getByText('Second point')).toBeTruthy();
    expect(screen.getByText('Step one')).toBeTruthy();
  });

  it('renders nothing for empty content without crashing', () => {
    const { toJSON } = render(<Markdown content={''} />);
    // An empty pack must degrade to an empty render, never throw.
    expect(toJSON()).toBeDefined();
  });
});
