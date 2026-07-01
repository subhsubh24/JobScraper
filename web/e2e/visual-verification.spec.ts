import { expect, test } from '@playwright/test';
import { mkdirSync } from 'node:fs';

// DUAL-AXIS visual verification capture (ROADMAP Track E). This suite REPLAYS the real
// end-to-end journeys against a running web build + running API + seeded throwaway DB and
// CAPTURES a committed, non-zero screenshot of every key route/state at BOTH mobile and
// desktop widths — including the core-product OUTPUT (the populated fit SCORE). The images
// are judged on the two axes (FUNCTIONAL reality + DESIGN) by the deep-audit lens and the
// readiness gate (a vision-capable model actually LOOKs at them). Capture lives here;
// the verdict is recorded in docs/loop-memory.md / the readiness evidence.
//
// These run AFTER core-journey.spec.ts proves functional correctness; here the assertions
// exist only to guarantee the page is actually rendered (not blank/erroring) before the shot.

const SHOTS = 'e2e/__screenshots__';
mkdirSync(SHOTS, { recursive: true });

const WIDTHS = [
  { label: 'desktop', size: { width: 1280, height: 800 } },
  { label: 'mobile', size: { width: 390, height: 844 } },
] as const;

function freshEmail(tag: string): string {
  return `e2e-vis-${tag}-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
}

for (const { label, size } of WIDTHS) {
  test(`public surfaces render and look right (${label})`, async ({ page }) => {
    await page.setViewportSize(size);

    await page.goto('/');
    await expect(page.getByRole('link', { name: /Log in/i }).first()).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/landing-${label}.png`, fullPage: true });

    await page.goto('/login');
    await expect(page.getByRole('button', { name: /Log in/i })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/login-${label}.png`, fullPage: true });

    await page.goto('/register');
    await expect(page.getByRole('button', { name: /Create account/i })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/register-${label}.png`, fullPage: true });

    await page.goto('/pricing');
    await expect(page.getByRole('heading', { name: /Pricing/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Career\+/i })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/pricing-${label}.png`, fullPage: true });

    await page.goto('/waitlist');
    await expect(page.getByRole('heading').first()).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/waitlist-${label}.png`, fullPage: true });
  });

  test(`authed core loop incl. fit-score output (${label})`, async ({ page }) => {
    await page.setViewportSize(size);
    const email = freshEmail(label);

    // signup -> working app (no dead-end)
    await page.goto('/register');
    await page.getByLabel('Full name').fill('E2E Seeker');
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password').fill('supersecret123');
    await page
      .getByLabel(/Paste your resume/i)
      .fill('Senior Python engineer. FastAPI, SQL, AWS, Docker, PostgreSQL, Kubernetes.');
    await page.getByRole('button', { name: /Create account/i }).click();
    await expect(page).toHaveURL(/\/app/, { timeout: 20_000 });
    await expect(page.getByText(/No jobs yet/i)).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/app-dashboard-empty-${label}.png`, fullPage: true });

    // add a job -> the CORE-PRODUCT OUTPUT (numeric fit score) must render
    await page.getByRole('button', { name: /Add a job/i }).click();
    await page.getByLabel(/Job title/i).fill('Senior Backend Engineer');
    await page.getByLabel(/Company/i).fill('Acme');
    await page.getByLabel(/Location/i).fill('Remote US');
    await page
      .getByLabel(/Job description/i)
      .fill('Python, FastAPI, PostgreSQL, AWS, Docker, Kubernetes. 5+ years backend.');
    await page.getByRole('button', { name: /Add & score/i }).click();
    await expect(page.getByText('Senior Backend Engineer')).toBeVisible({ timeout: 20_000 });
    const scoreText = (await page.locator('text=/^\\d{1,3}$/').first().textContent())?.trim() ?? '';
    expect(Number(scoreText)).toBeGreaterThan(0);
    await page.screenshot({ path: `${SHOTS}/app-job-scored-${label}.png`, fullPage: true });

    // job detail — assert the CONTENT painted (heading), not just the URL, before the shot
    await page.getByText('Senior Backend Engineer').click();
    await expect(page).toHaveURL(/\/app\/jobs\//, { timeout: 20_000 });
    await expect(
      page.getByRole('heading', { name: /Senior Backend Engineer/i }).first(),
    ).toBeVisible({ timeout: 20_000 });
    // Career+-gated salary-negotiation surface: a free user sees the honest locked CTA,
    // not the tool (BUILDS != WORKS for the entitlement gate).
    await expect(page.getByRole('button', { name: /Upgrade to Career\+/i })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/app-job-detail-${label}.png`, fullPage: true });

    // coach (free tier sees the honest upgrade-gated state — a real state worth judging)
    await page.goto('/app/coach');
    await expect(page.getByRole('heading', { name: /Career Coach/i }).first()).toBeVisible({
      timeout: 20_000,
    });
    await page.screenshot({ path: `${SHOTS}/app-coach-gated-${label}.png`, fullPage: true });

    // settings
    await page.goto('/app/settings');
    await expect(page.getByRole('heading', { name: /^Settings$/i })).toBeVisible({
      timeout: 20_000,
    });
    await page.screenshot({ path: `${SHOTS}/app-settings-${label}.png`, fullPage: true });
  });
}
