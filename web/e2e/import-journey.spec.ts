import { expect, test, type Page, type APIRequestContext } from '@playwright/test';

// ATS IMPORT journey (BUILDS != WORKS). Drives the careers-page import flow end-to-end against
// the REAL auth + job-create backend, mocking ONLY the external ATS preview call (a live
// Greenhouse/Lever board can't be reached deterministically in CI — §6: mock the un-reachable
// dependency, exercise everything real). Asserts: (1) the happy path preview -> pick -> pre-filled
// manual form -> a REAL job created on the backend appears in the pipeline; (2) each honest
// server state (unsupported board / unreachable / no open roles) is surfaced verbatim, no listings;
// (3) a preview API failure degrades to an honest error, never a dead-end or stuck spinner.

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8000';
const PW = 'supersecret123';

function freshEmail(tag: string): string {
  return `e2e-${tag}-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
}

async function seedUser(request: APIRequestContext, email: string): Promise<void> {
  const r = await request.post(`${API}/api/auth/register`, {
    data: { email, password: PW, full_name: 'E2E Import' },
  });
  expect(r.ok(), `seed register failed: ${r.status()} ${await r.text()}`).toBeTruthy();
}

async function signIn(page: Page, email: string): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(PW);
  await page.getByRole('button', { name: /^Log in$/i }).click();
  await expect(page).toHaveURL(/\/app/, { timeout: 20_000 });
  await expect(page.getByRole('heading', { name: /Your pipeline/i })).toBeVisible();
}

// Mock the import-preview endpoint (the external ATS call) with a given JSON body.
async function mockPreview(page: Page, body: unknown, status = 200): Promise<void> {
  await page.route('**/api/jobs/import-preview', (route) =>
    route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) }),
  );
}

const TWO_ROLES = {
  success: true,
  ats: 'greenhouse',
  supported: true,
  reachable: true,
  truncated: false,
  message: null,
  jobs: [
    {
      external_id: '123',
      title: 'Senior Backend Engineer',
      company_slug: 'acme',
      location: 'Remote',
      url: 'https://boards.greenhouse.io/acme/jobs/123',
      department: 'Engineering',
      remote_type: 'remote',
      posted_at: null,
    },
    {
      external_id: '124',
      title: 'Product Designer',
      company_slug: 'acme',
      location: 'New York',
      url: 'https://boards.greenhouse.io/acme/jobs/124',
      department: 'Design',
      remote_type: null,
      posted_at: null,
    },
  ],
};

async function openImportTab(page: Page): Promise<void> {
  await page.getByRole('button', { name: /\+ Add a job/i }).click();
  await page.getByRole('tab', { name: /Import from a careers page/i }).click();
}

test('import happy path: preview -> pick a role -> pre-filled form -> REAL job in pipeline', async ({
  page,
  request,
}) => {
  const email = freshEmail('import-ok');
  await seedUser(request, email);
  await mockPreview(page, TWO_ROLES);
  await signIn(page, email);

  await openImportTab(page);
  await page.getByLabel(/careers URL/i).fill('https://boards.greenhouse.io/acme');
  await page.getByRole('button', { name: /Preview roles/i }).click();

  // Both previewed roles render with their real title + location/department.
  await expect(page.getByText('Senior Backend Engineer')).toBeVisible();
  await expect(page.getByText('Product Designer')).toBeVisible();

  // Pick the first role -> the manual form opens PRE-FILLED (no unscoreable shell: the user
  // is asked to paste the JD before it is added).
  await page
    .getByRole('listitem')
    .filter({ hasText: 'Senior Backend Engineer' })
    .getByRole('button', { name: /Use this/i })
    .click();

  const title = page.getByLabel(/Job title/i);
  await expect(title).toHaveValue('Senior Backend Engineer');
  await expect(page.getByLabel(/Company/i)).toHaveValue('acme');
  await expect(page.getByText(/Imported from the careers page/i)).toBeVisible();

  // Paste the JD and add for real — this hits the REAL backend (no mock on POST /api/jobs).
  await page.getByLabel(/Job description/i).fill(
    'We need a backend engineer with Python, FastAPI and PostgreSQL experience to build APIs.',
  );
  await page.getByRole('button', { name: /Add & score/i }).click();

  // The real side-effect: the job now appears in the pipeline list (backend created + scored it).
  await expect(page.getByText('Senior Backend Engineer')).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/No jobs yet/i)).toHaveCount(0);
});

test('import honest state: an unsupported board shows the server message, no listings', async ({
  page,
  request,
}) => {
  const email = freshEmail('import-unsup');
  await seedUser(request, email);
  await mockPreview(page, {
    success: true,
    ats: 'workday',
    supported: false,
    jobs: [],
    truncated: false,
    message: 'We detected a Workday job board, but only Greenhouse and Lever are supported right now.',
  });
  await signIn(page, email);

  await openImportTab(page);
  await page.getByLabel(/careers URL/i).fill('https://acme.wd1.myworkdayjobs.com');
  await page.getByRole('button', { name: /Preview roles/i }).click();

  await expect(page.getByText(/only Greenhouse and Lever are supported/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /Use this/i })).toHaveCount(0);
});

test('import honest state: an unreachable board shows the retry message, no dead-end', async ({
  page,
  request,
}) => {
  const email = freshEmail('import-unreach');
  await seedUser(request, email);
  await mockPreview(page, {
    success: true,
    ats: 'greenhouse',
    supported: true,
    reachable: false,
    jobs: [],
    truncated: false,
    message: 'That job board was temporarily unreachable. Please try again shortly.',
  });
  await signIn(page, email);

  await openImportTab(page);
  await page.getByLabel(/careers URL/i).fill('https://boards.greenhouse.io/acme');
  await page.getByRole('button', { name: /Preview roles/i }).click();

  await expect(page.getByText(/temporarily unreachable/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /Use this/i })).toHaveCount(0);
});

test('import degrades honestly when the preview API fails (configured-but-failing path)', async ({
  page,
  request,
}) => {
  const email = freshEmail('import-500');
  await seedUser(request, email);
  await mockPreview(page, { detail: 'boom' }, 500);
  await signIn(page, email);

  await openImportTab(page);
  await page.getByLabel(/careers URL/i).fill('https://boards.greenhouse.io/acme');
  await page.getByRole('button', { name: /Preview roles/i }).click();

  // An honest, announced error — never a stuck "Previewing…" spinner or a blank panel.
  await expect(page.getByText('boom', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: /Preview roles/i })).toBeEnabled();
});
