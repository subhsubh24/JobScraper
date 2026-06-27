import type { ConfigContext, ExpoConfig } from 'expo/config';

// Dynamic config overlay: keeps app.json as the static source of truth and injects
// environment-driven values at build time so secrets/ids aren't committed:
//   - EAS_PROJECT_ID    -> extra.eas.projectId (written by `eas init`, or via CI env)
//   - EXPO_PUBLIC_API_URL -> extra.apiUrl (the deployed backend URL for the build)
export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: config.name ?? 'Career Operator',
  slug: config.slug ?? 'career-operator',
  extra: {
    ...config.extra,
    apiUrl: process.env.EXPO_PUBLIC_API_URL ?? config.extra?.apiUrl,
    eas: {
      projectId: process.env.EAS_PROJECT_ID ?? config.extra?.eas?.projectId,
    },
  },
});
