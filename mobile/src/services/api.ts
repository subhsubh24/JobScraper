// Typed client for the Career Operator Python API.
// Base URL comes from app.json -> expo.extra.apiUrl (owner sets the live Railway URL).
import Constants from 'expo-constants';

import * as storage from '@/services/storage';
import type { Job, PipelineStats, ReferralStats, User } from '@/types';

const TOKEN_KEY = 'career_operator_token';

// Resolution order: build-time env (EXPO_PUBLIC_API_URL) -> app.json extra.apiUrl ->
// localhost. Set EXPO_PUBLIC_API_URL in the Vercel web project to your live API.
const API_URL: string =
  process.env.EXPO_PUBLIC_API_URL ??
  (Constants.expoConfig?.extra as { apiUrl?: string } | undefined)?.apiUrl ??
  'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

let cachedToken: string | null = null;

export async function getToken(): Promise<string | null> {
  if (cachedToken) return cachedToken;
  cachedToken = await storage.getItem(TOKEN_KEY);
  return cachedToken;
}

async function setToken(token: string | null): Promise<void> {
  cachedToken = token;
  if (token) await storage.setItem(TOKEN_KEY, token);
  else await storage.deleteItem(TOKEN_KEY);
}

interface ReqOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  auth?: boolean;
}

async function request<T>(path: string, opts: ReqOptions = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (opts.auth !== false) {
    const token = await getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method: opts.method ?? 'GET',
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
  } catch {
    throw new ApiError(0, 'Network error — check your connection.');
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

export const api = {
  apiUrl: API_URL,

  async register(input: {
    email: string;
    password: string;
    full_name?: string;
    resume_text?: string;
  }): Promise<User> {
    const r = await request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: input,
      auth: false,
    });
    await setToken(r.token);
    return r.user;
  },

  async login(email: string, password: string): Promise<User> {
    const r = await request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
      auth: false,
    });
    await setToken(r.token);
    return r.user;
  },

  async me(): Promise<User> {
    const r = await request<{ user: User }>('/api/auth/me');
    return r.user;
  },

  async referralStats(): Promise<ReferralStats> {
    const r = await request<{ referral: ReferralStats }>('/api/referrals/me');
    return r.referral;
  },

  async logout(): Promise<void> {
    await setToken(null);
  },

  async deleteAccount(): Promise<void> {
    // Real deletion server-side. Local session state is owned by the auth context
    // (the caller signs out on success), so we don't clear the token here.
    await request('/api/auth/me', { method: 'DELETE' });
  },

  async listJobs(): Promise<Job[]> {
    const r = await request<{ jobs: Job[] }>('/api/jobs');
    return r.jobs;
  },

  async getJob(id: string): Promise<Job> {
    const r = await request<{ job: Job }>(`/api/jobs/${id}`);
    return r.job;
  },

  async createJob(input: {
    title: string;
    company_name: string;
    location?: string;
    salary_min?: number;
    salary_max?: number;
    description?: string;
    requirements?: string;
    url?: string;
  }): Promise<Job> {
    const r = await request<{ job: Job }>('/api/jobs', { method: 'POST', body: input });
    return r.job;
  },

  async updateJobStatus(id: string, status: string): Promise<Job> {
    const r = await request<{ job: Job }>(`/api/jobs/${id}`, {
      method: 'PATCH',
      body: { status },
    });
    return r.job;
  },

  async pipeline(): Promise<PipelineStats> {
    const r = await request<{ stats: PipelineStats }>('/api/analytics/pipeline');
    return r.stats;
  },

  async coachSuggestions(): Promise<string[]> {
    const r = await request<{ suggestions: string[] }>('/api/coach/suggestions');
    return r.suggestions;
  },

  async coachChat(message: string, sessionId?: string): Promise<string> {
    const r = await request<{ message: string }>('/api/coach/chat', {
      method: 'POST',
      body: { message, session_id: sessionId },
    });
    return r.message;
  },

  async generatePrepPack(jobId: string): Promise<{ title: string; content: string }> {
    const r = await request<{ prep_pack: { title: string; content: string } }>(
      '/api/prep-packs/generate',
      { method: 'POST', body: { job_id: jobId } },
    );
    return r.prep_pack;
  },
};
