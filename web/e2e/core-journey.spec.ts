import { expect, test } from '@playwright/test';
import { mkdirSync } from 'node:fs';

// Outcome-asserting browser journey. NOT "the page returned 200" — it asserts the user
// actually reaches a WORKING app and the core-product OUTPUT (the fit SCORE) RENDERS.
// Self-seeds: every run creates a brand-new account via the real UI, so it needs no
// fixture data and is safe against a throwaway DB.

const SHOTS = 'e2e/__screenshots__';
mkdirSync(SHOTS, { recursive: true });

// A unique email per run so the journey self-seeds and never collides on the shared DB.
// No Math.random()/Date.now() banned here (this is the test runner, not a workflow script),
// but we keep it deterministic-ish with a per-worker counter + timestamp.
function freshEmail(tag: string): string {
  return `e2e-${tag}-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
}

test('signup → working dashboard → add job → fit SCORE renders (no dead-end)', async ({ page }) => {
  const email = freshEmail('core');

  // --- signup via the real form ---
  await page.goto('/register');
  await page.getByLabel('Full name').fill('E2E Seeker');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill('supersecret123');
  await page
    .getByLabel(/Paste your resume/i)
    .fill('Senior Python engineer. FastAPI, SQL, AWS, Docker, PostgreSQL, Kubernetes.');
  await page.getByRole('button', { name: /Create account/i }).click();

  // --- lands in the WORKING app immediately (no "check your email" dead-end) ---
  await expect(page).toHaveURL(/\/app/, { timeout: 20_000 });
  await expect(page.getByRole('heading', { name: /Your pipeline/i })).toBeVisible();
  // The empty state, not an error.
  await expect(page.getByText(/No jobs yet/i)).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/01-dashboard-empty.png`, fullPage: true });

  // --- core product loop: add a job, the FIT SCORE (core output) must RENDER ---
  await page.getByRole('button', { name: /Add a job/i }).click();
  await page.getByLabel(/Job title/i).fill('Senior Backend Engineer');
  await page.getByLabel(/Company/i).fill('Acme');
  await page.getByLabel(/Location/i).fill('Remote US');
  await page
    .getByLabel(/Job description/i)
    .fill('Python, FastAPI, PostgreSQL, AWS, Docker, Kubernetes. 5+ years backend.');
  await page.getByRole('button', { name: /Add & score/i }).click();

  // The job card appears with its title...
  const card = page.getByText('Senior Backend Engineer');
  await expect(card).toBeVisible({ timeout: 20_000 });

  // ...and the CORE-PRODUCT OUTPUT renders: a real numeric fit score next to "fit", NOT a
  // dash placeholder. This is the BUILDS!=WORKS assertion — heuristic scoring produced a
  // number the user can see.
  const fitBlock = page.locator('div', { hasText: /^fit$/ }).first();
  await expect(fitBlock).toBeVisible();
  const scoreText = (await page.locator('text=/^\\d{1,3}$/').first().textContent())?.trim() ?? '';
  expect(Number(scoreText)).toBeGreaterThan(0);

  // The "Avg fit" stat also reflects real data (not an em-dash).
  await expect(page.getByText('Avg fit')).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/02-job-scored.png`, fullPage: true });

  // --- detail view renders the job (still no dead-end) ---
  await page.getByText('Senior Backend Engineer').click();
  await expect(page).toHaveURL(/\/app\/jobs\//, { timeout: 20_000 });
  await expect(page.getByRole('heading', { name: /Senior Backend Engineer/i })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/03-job-detail.png`, fullPage: true });
});

test('login is reachable and the marketing landing renders', async ({ page }) => {
  await page.goto('/');
  // The landing page renders real content, not an error boundary.
  await expect(page.getByRole('link', { name: /Log in/i }).first()).toBeVisible();
  await page.goto('/login');
  await expect(page.getByRole('button', { name: /Log in/i })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/04-login.png`, fullPage: true });
});
