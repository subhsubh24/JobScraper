// Typed client for the Career Operator FastAPI backend.
// Base URL: NEXT_PUBLIC_API_URL (set in Vercel) -> the live API default.
import type { Job, PipelineStats, User } from '@/lib/types';

// Single Vercel deployment (Vercel Services): the FastAPI backend is mounted at /api on
// the SAME origin as this web app, so the default base URL is empty (relative). Each
// api path below already starts with /api. Override with NEXT_PUBLIC_API_URL for a
// separate API origin (e.g. local dev against http://localhost:8000).
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

const TOKEN_KEY = 'career_operator_token';

// Hard timeout on every request. `fetch` has NO default timeout, so without this a slow or
// unreachable API hangs the call forever — on app launch that strands the user on a stuck
// "Loading…" screen with no error and no way forward (session restore awaits `api.me()`).
// An AbortController bounds every request; a timeout surfaces as an honest, retryable error.
// Set to the serverless function budget (vercel.json maxDuration=60s) so it NEVER aborts a
// legitimately slow response — incl. AI prep/coach calls (server LLM timeout 45s) — and only
// trips on a true hang (connection open, no response).
const REQUEST_TIMEOUT_MS = 60_000;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

function setToken(token: string | null): void {
  if (typeof window === 'undefined') return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

interface ReqOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  auth?: boolean;
}

async function request<T>(path: string, opts: ReqOptions = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (opts.auth !== false) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method: opts.method ?? 'GET',
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new ApiError(0, 'Request timed out — please try again.');
    }
    throw new ApiError(0, 'Network error — check your connection.');
  } finally {
    clearTimeout(timer);
  }
  const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : 'Request failed';
    throw new ApiError(res.status, detail);
  }
  return data as T;
}

interface AuthResponse {
  success: boolean;
  token: string;
  user: User;
}

export interface ReferralStats {
  code: string;
  total_referred: number;
  bonus_prep_packs: number;
}

export const api = {
  apiUrl: API_URL,

  async register(input: {
    email: string;
    password: string;
    full_name?: string;
    resume_text?: string;
    referral_code?: string;
  }): Promise<User> {
    const r = await request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: input,
      auth: false,
    });
    setToken(r.token);
    return r.user;
  },

  async login(email: string, password: string): Promise<User> {
    const r = await request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
      auth: false,
    });
    setToken(r.token);
    return r.user;
  },

  async me(): Promise<User> {
    return (await request<{ user: User }>('/api/auth/me')).user;
  },

  async referralStats(): Promise<ReferralStats> {
    return (await request<{ referral: ReferralStats }>('/api/referrals/me')).referral;
  },

  logout(): void {
    setToken(null);
  },

  // Permanently delete the signed-in account and ALL its data (store + GDPR requirement).
  // Awaits the real DELETE /api/auth/me and only clears the local token after the server
  // confirms the deletion — never an optimistic success. Throws ApiError on failure so the
  // caller can surface it honestly instead of pretending the account is gone.
  async deleteAccount(): Promise<void> {
    await request<{ success: boolean; deleted: boolean }>('/api/auth/me', { method: 'DELETE' });
    setToken(null);
  },

  async listJobs(): Promise<Job[]> {
    return (await request<{ jobs: Job[] }>('/api/jobs')).jobs;
  },

  async getJob(id: string): Promise<Job> {
    return (await request<{ job: Job }>(`/api/jobs/${id}`)).job;
  },

  async createJob(input: {
    title: string;
    company_name: string;
    location?: string;
    description?: string;
  }): Promise<Job> {
    return (await request<{ job: Job }>('/api/jobs', { method: 'POST', body: input })).job;
  },

  async updateJobStatus(id: string, status: string): Promise<Job> {
    return (
      await request<{ job: Job }>(`/api/jobs/${id}`, { method: 'PATCH', body: { status } })
    ).job;
  },

  async pipeline(): Promise<PipelineStats> {
    return (await request<{ stats: PipelineStats }>('/api/analytics/pipeline')).stats;
  },

  async coachSuggestions(): Promise<string[]> {
    return (await request<{ suggestions: string[] }>('/api/coach/suggestions')).suggestions;
  },

  // ``sessionId`` groups a multi-turn conversation server-side; the backend builds the
  // reply from prior messages sharing that id. Omitting it (the old behaviour) made every
  // message a fresh session, so the coach never remembered anything within a chat.
  async coachChat(message: string, sessionId?: string): Promise<string> {
    return (
      await request<{ message: string }>('/api/coach/chat', {
        method: 'POST',
        body: { message, session_id: sessionId },
      })
    ).message;
  },

  async generatePrepPack(jobId: string): Promise<{ title: string; content: string }> {
    return (
      await request<{ prep_pack: { title: string; content: string } }>('/api/prep-packs/generate', {
        method: 'POST',
        body: { job_id: jobId },
      })
    ).prep_pack;
  },

  // Report/flag an AI-generated response (coach reply or prep pack) for moderator review.
  // Awaits the REAL POST /api/report and throws ApiError on failure so the caller can
  // surface it honestly — the success state is only shown once the server records the row.
  async reportContent(input: {
    content_type: 'coach' | 'prep_pack';
    reason: 'harmful' | 'inaccurate' | 'offensive' | 'other';
    content_ref?: string;
    content_excerpt?: string;
    detail?: string;
  }): Promise<void> {
    await request<{ success: boolean; message: string }>('/api/report', {
      method: 'POST',
      body: input,
    });
  },

  // Join the pre-launch waitlist. Public (no auth). The backend never reveals whether the
  // email is already on the list, so the caller always treats a resolved promise as success.
  async joinWaitlist(email: string, source?: string): Promise<void> {
    await request<{ success: boolean; message: string }>('/api/waitlist/join', {
      method: 'POST',
      body: { email, source },
      auth: false,
    });
  },

  // Start a Stripe Checkout session for a subscription plan and return its hosted URL.
  // Throws ApiError(503) when billing isn't configured yet — the caller surfaces it
  // honestly rather than pretending a charge happened.
  async startCheckout(plan: string): Promise<string> {
    return (await request<{ url: string }>('/api/billing/checkout', { method: 'POST', body: { plan } }))
      .url;
  },
};
