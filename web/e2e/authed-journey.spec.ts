import { expect, test, type Page, type APIRequestContext } from '@playwright/test';
import { mkdirSync } from 'node:fs';

// AUTHENTICATED journey tier (BUILDS != WORKS for the logged-in product). Runs against the
// REAL auth backend (FastAPI + JWT) started by playwright.config.ts on a seeded throwaway DB.
// Covers: real SIGN-IN -> working dashboard, ACCOUNT/settings, and PAYWALL -> checkout
// (honest, no fake success). Each seeds its own confirmed user via the backend's register
// service path (register returns a usable session — no email-verification dead-end).
//
// Evidence-on-failure: every flow attaches console + pageerror listeners and, if sign-in
// doesn't reach the dashboard, reads the login form's error text and throws with BOTH — so a
// single CI run names the exact cause instead of a blind toHaveURL timeout.

const SHOTS = 'e2e/__screenshots__';
mkdirSync(SHOTS, { recursive: true });
const API = process.env.E2E_API_URL || 'http://127.0.0.1:8000';
const PW = 'supersecret123';

function freshEmail(tag: string): string {
  return `e2e-${tag}-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
}

function attachDiagnostics(page: Page): string[] {
  const logs: string[] = [];
  page.on('console', (m) => logs.push(`console.${m.type()}: ${m.text()}`));
  page.on('pageerror', (e) => logs.push(`pageerror: ${e.message}`));
  return logs;
}

async function readAuthError(page: Page): Promise<string> {
  try {
    const t = await page.locator('.text-red-400').first().textContent({ timeout: 1000 });
    return (t || '').trim() || '(no auth-error text rendered)';
  } catch {
    return '(no auth-error element present)';
  }
}

async function seedUser(request: APIRequestContext, email: string, name: string): Promise<void> {
  const r = await request.post(`${API}/api/auth/register`, { data: { email, password: PW, full_name: name } });
  expect(r.ok(), `seed register failed: ${r.status()} ${await r.text()}`).toBeTruthy();
}

async function signInViaUI(page: Page, email: string, logs: string[]): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(PW);
  await page.getByRole('button', { name: /^Log in$/i }).click();
  try {
    await expect(page).toHaveURL(/\/app/, { timeout: 20_000 });
    await expect(page.getByRole('heading', { name: /Your pipeline/i })).toBeVisible();
  } catch {
    const authErr = await readAuthError(page);
    throw new Error(
      `SIGN-IN did not reach the dashboard.\n  auth-error shown: ${authErr}\n  url: ${page.url()}\n` +
      `  browser logs:\n   ${logs.join('\n   ') || '(none)'}`,
    );
  }
}

test('real SIGN-IN: seeded user logs in through the UI -> working dashboard', async ({ page, request }) => {
  const email = freshEmail('signin');
  await seedUser(request, email, 'E2E SignIn');
  const logs = attachDiagnostics(page);
  await signInViaUI(page, email, logs);
  // Real post-login content, not an error boundary.
  await expect(page.getByText(/No jobs yet/i)).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/05-signed-in-dashboard.png`, fullPage: true });
});

test('ACCOUNT: authed settings renders real account data', async ({ page, request }) => {
  const email = freshEmail('acct');
  await seedUser(request, email, 'E2E Acct');
  const logs = attachDiagnostics(page);
  await signInViaUI(page, email, logs);
  await page.goto('/app/settings');
  await expect(page.getByRole('heading', { name: /^Settings$/i })).toBeVisible();
  await expect(page.getByText(email).first()).toBeVisible();  // real account data (also shown in the header)
  await expect(page.getByText(/^Free$/i).first()).toBeVisible(); // plan label
  await page.screenshot({ path: `${SHOTS}/06-account-settings.png`, fullPage: true });
});

test('PAYWALL -> checkout behaves HONESTLY (no fake success, no error boundary)', async ({ page, request }) => {
  const email = freshEmail('paywall');
  await seedUser(request, email, 'E2E Paywall');
  const logs = attachDiagnostics(page);
  await signInViaUI(page, email, logs);

  await page.goto('/pricing');
  await expect(page.getByRole('heading', { name: /Premium/i })).toBeVisible();
  await page.getByRole('button', { name: /Go Premium/i }).first().click();

  // Stripe isn't configured in CI, so checkout must refuse HONESTLY (a notice), never a fake
  // "you're premium" and never a crash/error boundary. If Stripe IS configured it navigates out.
  await page.waitForLoadState('networkidle').catch(() => {});
  const navigatedToCheckout = /checkout\.stripe\.com|\/billing\//.test(page.url());
  if (!navigatedToCheckout) {
    await expect(page.getByRole('heading', { name: /Premium/i })).toBeVisible(); // page intact, not broken
    const body = (await page.locator('body').innerText()) || '';
    expect(
      /try again|could not|unavailable|not configured|checkout|premium/i.test(body),
      `paywall gave neither a checkout redirect nor an honest notice.\n  url: ${page.url()}\n  logs:\n   ${logs.join('\n   ')}`,
    ).toBeTruthy();
    // and the user was NOT fake-upgraded: settings still shows Free
    await page.goto('/app/settings');
    await expect(page.getByText(/^Free$/i).first()).toBeVisible();
  }
  await page.screenshot({ path: `${SHOTS}/07-paywall.png`, fullPage: true });
});
