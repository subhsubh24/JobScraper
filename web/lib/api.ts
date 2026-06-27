// Typed client for the Career Operator FastAPI backend.
// Base URL: NEXT_PUBLIC_API_URL (set in Vercel) -> the live API default.
import type { Job, PipelineStats, User } from '@/lib/types';

// Single Vercel deployment (Vercel Services): the FastAPI backend is mounted at /api on
// the SAME origin as this web app, so the default base URL is empty (relative). Each
// api path below already starts with /api. Override with NEXT_PUBLIC_API_URL for a
// separate API origin (e.g. local dev against http://localhost:8000).
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

const TOKEN_KEY = 'career_operator_token';

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

  logout(): void {
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

  async coachChat(message: string): Promise<string> {
    return (await request<{ message: string }>('/api/coach/chat', { method: 'POST', body: { message } }))
      .message;
  },

  async generatePrepPack(jobId: string): Promise<{ title: string; content: string }> {
    return (
      await request<{ prep_pack: { title: string; content: string } }>('/api/prep-packs/generate', {
        method: 'POST',
        body: { job_id: jobId },
      })
    ).prep_pack;
  },
};
