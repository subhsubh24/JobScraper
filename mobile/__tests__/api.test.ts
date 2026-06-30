/// <reference types="jest" />
// Outcome-asserting tests for the API client — the data layer every screen depends on.
// Proves real behavior, not just that methods exist: the right path/method/body is sent,
// the auth token is attached, responses are unwrapped to the documented shape, and errors
// map to ApiError with the server's status + detail (so screens can branch on 403 -> paywall,
// 503 -> honest message, network -> retry). fetch + secure-store are mocked; no real I/O.

// In-memory secure-store stand-in (the device keystore isn't available under jest).
const store: Record<string, string> = {};
jest.mock('@/services/storage', () => ({
  getItem: jest.fn(async (k: string) => store[k] ?? null),
  setItem: jest.fn(async (k: string, v: string) => {
    store[k] = v;
  }),
  deleteItem: jest.fn(async (k: string) => {
    delete store[k];
  }),
}));

import { api, ApiError, getToken } from '@/services/api';

function mockFetch(status: number, body: unknown) {
  const fn = jest.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })) as unknown as typeof fetch;
  globalThis.fetch = fn;
  return fn as unknown as jest.Mock;
}

afterEach(async () => {
  await api.logout(); // clear the cached token between tests
  for (const k of Object.keys(store)) delete store[k];
  jest.clearAllMocks();
});

describe('api client', () => {
  it('login posts credentials, persists the token, and returns the user', async () => {
    const fetchMock = mockFetch(200, { success: true, token: 'tok_123', user: { id: 'u1', email: 'a@b.co' } });
    const user = await api.login('a@b.co', 'pw12345678');

    expect(user.id).toBe('u1');
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain('/api/auth/login');
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body)).toEqual({ email: 'a@b.co', password: 'pw12345678' });
    // Token is now persisted + cached for subsequent authed requests.
    expect(await getToken()).toBe('tok_123');
  });

  it('attaches the bearer token on authed requests after login', async () => {
    mockFetch(200, { success: true, token: 'tok_abc', user: { id: 'u1' } });
    await api.login('a@b.co', 'pw12345678');

    const fetchMock = mockFetch(200, { jobs: [] });
    await api.listJobs();
    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.Authorization).toBe('Bearer tok_abc');
  });

  it('listJobs unwraps the jobs array', async () => {
    const fetchMock = mockFetch(200, { jobs: [{ id: 'j1', title: 'Eng' }] });
    const jobs = await api.listJobs();
    expect(jobs).toEqual([{ id: 'j1', title: 'Eng' }]);
    expect(fetchMock.mock.calls[0][0]).toContain('/api/jobs');
  });

  it('updateJobStatus PATCHes the status body and unwraps the job', async () => {
    const fetchMock = mockFetch(200, { job: { id: 'j1', status: 'applied' } });
    const job = await api.updateJobStatus('j1', 'applied');
    expect(job.status).toBe('applied');
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain('/api/jobs/j1');
    expect(init.method).toBe('PATCH');
    expect(JSON.parse(init.body)).toEqual({ status: 'applied' });
  });

  it('maps a non-OK response to ApiError with the server status + detail', async () => {
    mockFetch(403, { detail: 'Upgrade to Premium' });
    await expect(api.generatePrepPack('j1')).rejects.toMatchObject({
      status: 403,
      message: 'Upgrade to Premium',
    });
  });

  it('falls back to a generic message when the error body has no detail', async () => {
    mockFetch(500, {});
    await expect(api.listJobs()).rejects.toMatchObject({ status: 500, message: 'Request failed' });
  });

  it('maps a thrown fetch (offline) to a network ApiError(0)', async () => {
    globalThis.fetch = jest.fn(async () => {
      throw new Error('Network request failed');
    }) as unknown as typeof fetch;
    const err = await api.listJobs().catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(0);
    // The message is what screens surface to the user on connection loss — pin it.
    expect(err.message).toMatch(/network/i);
  });

  it('bounds every request with a real AbortSignal', async () => {
    const fetchMock = mockFetch(200, { jobs: [] });
    await api.listJobs();
    const [, init] = fetchMock.mock.calls[0];
    // No signal == a request that can hang forever (stuck loading on launch). Pin that it's a
    // genuine AbortSignal (the one the timeout aborts), not just any truthy value.
    expect(init.signal).toBeInstanceOf(AbortSignal);
  });

  it('maps a hung request (timeout/abort) to a retryable ApiError(0)', async () => {
    jest.useFakeTimers();
    try {
      // A fetch that never resolves until its signal aborts — i.e. the timer kills it.
      globalThis.fetch = jest.fn(
        (_url: string, init: { signal: AbortSignal }) =>
          new Promise((_resolve, reject) => {
            init.signal.addEventListener('abort', () =>
              reject(Object.assign(new Error('Aborted'), { name: 'AbortError' })),
            );
          }),
      ) as unknown as typeof fetch;

      const pending = api.listJobs().catch((e) => e);
      await jest.advanceTimersByTimeAsync(60_000); // past REQUEST_TIMEOUT_MS
      const err = await pending;
      expect(err).toBeInstanceOf(ApiError);
      expect(err.status).toBe(0);
      // Distinct from the offline message so a screen says "try again", not "check connection".
      expect(err.message).toMatch(/timed out/i);
    } finally {
      // Restore real timers even if an assertion above throws — fake timers must never leak
      // into the rest of the suite.
      jest.useRealTimers();
    }
  });

  it('generatePrepPack posts the job_id and unwraps prep_pack (happy path)', async () => {
    const fetchMock = mockFetch(200, { prep_pack: { title: 'Interview Prep: Eng', content: '## X' } });
    const pack = await api.generatePrepPack('j1');
    expect(pack).toEqual({ title: 'Interview Prep: Eng', content: '## X' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain('/api/prep-packs/generate');
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body)).toEqual({ job_id: 'j1' });
  });
});
