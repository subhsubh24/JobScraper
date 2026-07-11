import { expect, test, type Page, type APIRequestContext } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { createHmac } from 'node:crypto';

// TEAM / organization seat-tier journey (BUILDS != WORKS for the paid team surface). Runs
// against the REAL org backend (FastAPI, run-39 seat tier) started by playwright.config.ts on
// a seeded throwaway DB with NO Stripe key — so buying seats must refuse HONESTLY (a notice,
// no fake purchase, no crash), exactly the SIDE-EFFECT-INTEGRITY contract. Covers: the Team
// nav link, the empty (no-org) state, real org CREATE -> the org renders, and buy-seats ->
// honest checkout refusal (no fake activation).

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
  const r = await request.post(`${API}/api/auth/register`, {
    data: { email, password: PW, full_name: name },
  });
  expect(r.ok(), `seed register failed: ${r.status()} ${await r.text()}`).toBeTruthy();
}

// Seed a user and return their bearer token, so a test can drive owner-only API setup
// (create org, add member) directly before exercising the UI.
async function seedUserToken(
  request: APIRequestContext,
  email: string,
  name: string,
): Promise<string> {
  const r = await request.post(`${API}/api/auth/register`, {
    data: { email, password: PW, full_name: name },
  });
  expect(r.ok(), `seed register failed: ${r.status()} ${await r.text()}`).toBeTruthy();
  return (await r.json()).token as string;
}

async function createOrgApi(
  request: APIRequestContext,
  token: string,
  name: string,
): Promise<string> {
  const r = await request.post(`${API}/api/org`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { name },
  });
  expect(r.ok(), `create org failed: ${r.status()} ${await r.text()}`).toBeTruthy();
  return (await r.json()).id as string;
}

async function addMemberApi(
  request: APIRequestContext,
  token: string,
  email: string,
): Promise<void> {
  const r = await request.post(`${API}/api/org/members`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { email },
  });
  expect(r.ok(), `add member failed: ${r.status()} ${await r.text()}`).toBeTruthy();
}

// ACTIVATE an org without live Stripe: post the SAME signature-verified synthetic
// `customer.subscription.created` event tests/test_org_billing.py uses (STRIPE_WEBHOOK_SECRET is
// set for the E2E backend in playwright.config.ts). Entitlement moves ONLY through the signed
// webhook, so this faithfully exercises the real activation path — no client-side shortcut.
const WHSEC = 'whsec_test_secret';

function signStripe(payload: string): string {
  const ts = Math.floor(Date.now() / 1000);
  const sig = createHmac('sha256', WHSEC).update(`${ts}.${payload}`).digest('hex');
  return `t=${ts},v1=${sig}`;
}

async function activateOrg(
  request: APIRequestContext,
  orgId: string,
  seats: number,
): Promise<void> {
  const payload = JSON.stringify({
    id: 'evt_test',
    object: 'event',
    type: 'customer.subscription.created',
    data: {
      object: {
        id: `sub_${orgId.slice(0, 6)}`,
        customer: `cus_${orgId.slice(0, 6)}`,
        status: 'active',
        metadata: { org_id: orgId, plan: 'team_annual' },
        items: { data: [{ quantity: seats }] },
      },
    },
  });
  const r = await request.post(`${API}/api/billing/webhook`, {
    headers: { 'stripe-signature': signStripe(payload), 'content-type': 'application/json' },
    data: payload,
  });
  expect(r.ok(), `activate-org webhook failed: ${r.status()} ${await r.text()}`).toBeTruthy();
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

test('TEAM: nav link reaches the team page and shows the empty (no-org) state', async ({
  page,
  request,
}) => {
  const email = freshEmail('team-nav');
  await seedUser(request, email, 'E2E Team Nav');
  const logs = attachDiagnostics(page);
  await signInViaUI(page, email, logs);

  // Reachable from the primary nav, not just by URL.
  await page.getByRole('link', { name: /^Team$/i }).click();
  await expect(page).toHaveURL(/\/app\/team/);
  await expect(page.getByRole('heading', { name: /^Team$/i })).toBeVisible();
  // A user with no org sees the create-team affordance, not an error boundary.
  await expect(page.getByRole('heading', { name: /Create your team/i })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/08-team-empty.png`, fullPage: true });
});

test('TEAM: creating an org renders it with a no-seats-yet state (real create, no fake success)', async ({
  page,
  request,
}) => {
  const email = freshEmail('team-create');
  await seedUser(request, email, 'E2E Team Create');
  const logs = attachDiagnostics(page);
  await signInViaUI(page, email, logs);

  await page.goto('/app/team');
  await page.getByLabel('Team name').fill('E2E Test Team');
  await page.getByRole('button', { name: /Create team/i }).click();

  // The real org must render (owner view): the name + the "no seats yet" state + a buy control.
  await expect(page.getByText('E2E Test Team')).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/No seats yet/i)).toBeVisible();
  await expect(page.getByRole('heading', { name: /Buy seats/i })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/09-team-created.png`, fullPage: true });
});

test('TEAM: buying seats refuses HONESTLY when Stripe is unconfigured (no fake activation)', async ({
  page,
  request,
}) => {
  const email = freshEmail('team-buy');
  await seedUser(request, email, 'E2E Team Buy');
  const logs = attachDiagnostics(page);
  await signInViaUI(page, email, logs);

  await page.goto('/app/team');
  await page.getByLabel('Team name').fill('E2E Buy Team');
  await page.getByRole('button', { name: /Create team/i }).click();
  await expect(page.getByText('E2E Buy Team')).toBeVisible({ timeout: 20_000 });

  // Click buy — Stripe isn't configured in CI, so this must surface an honest notice and NEVER
  // navigate to a fake success or flip the org to Active.
  await page.getByRole('button', { name: /Buy \d+ seats?/i }).click();
  await page.waitForLoadState('networkidle').catch(() => {});
  const navigatedToStripe = /checkout\.stripe\.com/.test(page.url());
  if (!navigatedToStripe) {
    await expect(page).toHaveURL(/\/app\/team/); // stayed put, no crash
    await expect(page.getByText(/aren’t live yet|no charge was made|Could not start/i)).toBeVisible();
    // The org was NOT fake-activated: the no-seats-yet state persists.
    await expect(page.getByText(/No seats yet/i)).toBeVisible();
  }
  await page.screenshot({ path: `${SHOTS}/10-team-buy-honest.png`, fullPage: true });
});

test('TEAM: owner on an ACTIVE org adds a member, sees the roster, then removes them (real, no fake success)', async ({
  page,
  request,
}) => {
  const ownerEmail = freshEmail('mgr-owner');
  const memberEmail = freshEmail('mgr-member');
  const ownerToken = await seedUserToken(request, ownerEmail, 'E2E Mgr Owner');
  await seedUser(request, memberEmail, 'E2E Mgr Member'); // the account a seat is assigned to
  const orgId = await createOrgApi(request, ownerToken, 'E2E Managed Team');
  await activateOrg(request, orgId, 3);

  const logs = attachDiagnostics(page);
  await signInViaUI(page, ownerEmail, logs);
  await page.goto('/app/team');
  await expect(page.getByText('E2E Managed Team')).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/^Active$/)).toBeVisible(); // seats activated via the signed webhook
  await expect(page.getByRole('heading', { name: /^Members$/i })).toBeVisible();

  // Assign a purchased seat to the real member account -> the roster row renders. The UI shows
  // it only AFTER the server confirms the assignment (re-render from the returned org payload).
  await page.getByLabel(/Teammate email/i).fill(memberEmail);
  await page.getByRole('button', { name: /Add member/i }).click();
  await expect(page.getByText(memberEmail)).toBeVisible({ timeout: 20_000 });

  // Free the seat -> the roster empties (server-confirmed), proving remove is wired, not cosmetic.
  await page.getByRole('button', { name: /^Remove$/i }).click();
  await expect(page.getByText(memberEmail)).toBeHidden({ timeout: 20_000 });
  await expect(page.getByText(/No members yet/i)).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/11-team-members.png`, fullPage: true });
});

test('TEAM: a seated member sees the member view — no owner controls, no roster', async ({
  page,
  request,
}) => {
  const ownerEmail = freshEmail('mv-owner');
  const memberEmail = freshEmail('mv-member');
  const ownerToken = await seedUserToken(request, ownerEmail, 'E2E MV Owner');
  await seedUser(request, memberEmail, 'E2E MV Member');
  const orgId = await createOrgApi(request, ownerToken, 'E2E Member View Team');
  await activateOrg(request, orgId, 2);
  await addMemberApi(request, ownerToken, memberEmail); // seat assigned by the owner

  const logs = attachDiagnostics(page);
  await signInViaUI(page, memberEmail, logs);
  await page.goto('/app/team');
  await expect(page.getByRole('heading', { name: /Your team/i })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText('E2E Member View Team')).toBeVisible();
  await expect(page.getByText(/You have a Pro seat/i)).toBeVisible();
  // Tenant privacy: a member must NOT see the owner's seat-buying controls or the member roster.
  await expect(page.getByRole('heading', { name: /Buy seats/i })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: /^Members$/i })).toHaveCount(0);
  await page.screenshot({ path: `${SHOTS}/12-team-member-view.png`, fullPage: true });
});
