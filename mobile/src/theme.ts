// Career Operator design tokens. One source of truth for color/spacing so the app
// reads like an intentional product, not a generated starter.
export const colors = {
  bg: '#0B1020',
  surface: '#151B2E',
  surfaceAlt: '#1E2740',
  border: '#2A3554',
  text: '#F4F6FB',
  textMuted: '#9AA6C2',
  primary: '#5B8CFF',
  primaryText: '#FFFFFF',
  success: '#34D399',
  warning: '#FBBF24',
  danger: '#F87171',
};

export const spacing = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 };
export const radius = { sm: 8, md: 12, lg: 20 };

/** Color a 0-100 fit score: green good, amber moderate, red weak. */
export function scoreColor(score: number | null | undefined): string {
  if (score == null) return colors.textMuted;
  if (score >= 75) return colors.success;
  if (score >= 50) return colors.warning;
  return colors.danger;
}
