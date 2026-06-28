import { defineConfig, devices } from '@playwright/test';

// Browser-level functional journey suite (BUILDS != WORKS). Replays the REAL end-to-end
// user journey against a RUNNING web app + a RUNNING FastAPI backend + a seeded throwaway
// SQLite DB, and asserts the user-visible OUTCOME renders (the fit SCORE — the core-product
// output — actually appears, signup never dead-ends). Each run starts both servers fresh.
//
// IMPORTANT (CI gotchas, carried forward so the owner's first run is green):
//  (a) NEXT_PUBLIC_API_URL is baked at BUILD time in Next.js — CI must `next build` with it
//      set to the API origin below, THEN start. (No next-auth here; auth is Bearer-JWT in
//      localStorage, so there is no trusted-host callback to configure — the equivalent knob
//      is simply pointing the web build at the local API.)
//  (b) one CI runner replays every journey from ONE IP and trips the per-IP rate limiter —
//      the API server below is started with E2E_DISABLE_RATE_LIMIT=1 (test-only; the app
//      refuses to boot with it set on Vercel).

const API_PORT = 8000;
const WEB_PORT = 3000;
const API_URL = `http://127.0.0.1:${API_PORT}`;
const WEB_URL = `http://127.0.0.1:${WEB_PORT}`;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['list']] : [['list']],
  use: {
    baseURL: WEB_URL,
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      // FastAPI backend against a throwaway sqlite DB, rate-limit bypassed for the single
      // E2E runner, NO Gemini key (graceful-degradation paths exercised deterministically).
      command:
        'python3 -m uvicorn asgi:app --host 127.0.0.1 --port ' + API_PORT,
      cwd: '..',
      url: `${API_URL}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        JWT_SECRET: 'e2e-secret-not-for-prod',
        DATABASE_URL: 'sqlite:///./e2e-throwaway.db',
        AUTO_CREATE_TABLES: '1',
        E2E_DISABLE_RATE_LIMIT: '1',
        GEMINI_API_KEY: '',
      },
    },
    {
      // Next.js production server. Must be BUILT with NEXT_PUBLIC_API_URL set (see gotcha a);
      // CI does that before invoking playwright. `npm run start` serves that build.
      command: 'npm run start',
      url: WEB_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
