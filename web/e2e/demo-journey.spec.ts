import { expect, test } from '@playwright/test';
import { mkdirSync } from 'node:fs';

// Outcome-asserting browser journey for the PUBLIC, no-account demo (FACTORY_STANDARD §34).
// NOT "the /demo page returned 200" — it drives the real end-to-end flow a visitor takes
// (paste a JD + résumé → click → the REAL skills match RENDERS) against the live backend
// endpoint, and asserts the produced artifact (matching skills, gap skills, coverage %) is
// actually on screen. No account, no auth — the whole point of the funnel driver.

const SHOTS = 'e2e/__screenshots__';
mkdirSync(SHOTS, { recursive: true });

const JD =
  'Senior Backend Engineer. Build services in Python with FastAPI and PostgreSQL, deploy on ' +
  'AWS using Docker and Kubernetes, own CI/CD. React knowledge is a plus.';
const RESUME =
  'Python engineer. I use FastAPI and PostgreSQL daily and deploy on AWS. Comfortable with Docker.';

test('public demo: paste JD + résumé → real skill match RENDERS (no account, no dead-end)', async ({
  page,
}) => {
  // --- reachable with NO auth ---
  await page.goto('/demo');
  await expect(page.getByRole('heading', { name: /See how you match a role/i })).toBeVisible();

  // --- drive the real flow: paste inputs and submit ---
  await page.getByPlaceholder(/Paste the role/i).fill(JD);
  await page.getByPlaceholder(/Paste your résumé/i).fill(RESUME);
  await page.getByRole('button', { name: /See your match/i }).click();

  // --- the CORE OUTPUT renders: a coverage % + real matching AND missing skills ---
  // Coverage badge (aria-labelled) proves the numeric read reached the DOM.
  await expect(page.getByLabel(/percent skill coverage/i)).toBeVisible({ timeout: 20_000 });

  // Matching skills the résumé shares with the role (python/fastapi/postgresql/aws/docker).
  await expect(page.getByRole('heading', { name: 'Skills you already have' })).toBeVisible();
  await expect(page.getByText('python', { exact: true })).toBeVisible();

  // Missing skills the role wants that the résumé lacks (kubernetes/react must appear).
  await expect(page.getByRole('heading', { name: /Skills to highlight or build/i })).toBeVisible();
  await expect(page.getByText('kubernetes', { exact: true })).toBeVisible();
  await expect(page.getByText('react', { exact: true })).toBeVisible();

  // The funnel CTA back to the waitlist is present (demo → waitlist).
  await expect(page.getByRole('link', { name: /Join the waitlist/i })).toBeVisible();

  await page.screenshot({ path: `${SHOTS}/40-demo-result.png`, fullPage: true });
});

test('public demo: empty submit is guarded, not a dead-end', async ({ page }) => {
  await page.goto('/demo');
  await page.getByRole('button', { name: /See your match/i }).click();
  // An inline validation message, not a crash or a silent no-op.
  await expect(page.getByText(/paste a job description to see your match/i)).toBeVisible();
});
