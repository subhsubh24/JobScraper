// Typed client for the Career Operator Python API.
// Base URL comes from app.json -> expo.extra.apiUrl (owner sets the live Railway URL).
import Constants from 'expo-constants';

import * as storage from '@/services/storage';
import type {
  Competency,
  EnrichResult,
  Job,
  PipelineStats,
  ReferralStats,
  User,
} from '@/types';

const TOKEN_KEY = 'career_operator_token';

// Hard timeout on every request. `fetch` has NO default timeout, so without this a slow or
// unreachable API hangs the call forever — on app launch that strands the user on a stuck
// loading spinner with no error and no way forward (session restore awaits `api.me()`).
// An AbortController bounds every request; a timeout surfaces as an honest, retryable error.
// Set to the serverless function budget (vercel.json maxDuration=60s) so it NEVER aborts a
// legitimately slow response — incl. AI prep/coach calls (server LLM timeout 45s) — and only
// trips on a true hang (connection open, no response).
const REQUEST_TIMEOUT_MS = 60_000;

// Resolution order: build-time env (EXPO_PUBLIC_API_URL) -> app.json extra.apiUrl ->
// localhost. Set EXPO_PUBLIC_API_URL in the Vercel web project to your live API.
const API_URL: string =
  process.env.EXPO_PUBLIC_API_URL ??
  (Constants.expoConfig?.extra as { apiUrl?: string } | undefined)?.apiUrl ??
  'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  // Machine-readable error code when the API sends a structured `detail`
  // (e.g. `ai_consent_required`) so callers can branch without matching on message text.
  code?: string;
  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
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
    // `detail` is usually a string, but some gates send a structured `{ code, message }`
    // (e.g. ai_consent_required) so the client can branch on the code.
    const d = data.detail;
    let message = 'Request failed';
    let code: string | undefined;
    if (typeof d === 'string') {
      message = d;
    } else if (d && typeof d === 'object') {
      const obj = d as { code?: string; message?: string };
      code = obj.code;
      if (typeof obj.message === 'string') message = obj.message;
    }
    throw new ApiError(res.status, message, code);
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

  // Track A profile enrichment: read the user's current link-discovered competencies.
  async getEnrichment(): Promise<Competency[]> {
    const r = await request<{ competencies: Competency[] }>('/api/profile/enrichment');
    return r.competencies;
  },

  // Import competencies from the user's public GitHub profile (Pro+). Returns the honest result.
  async enrichGithub(github: string): Promise<EnrichResult> {
    return request<EnrichResult>('/api/profile/enrich/github', {
      method: 'POST',
      body: { github },
    });
  },

  // Remove ALL of the user's imported competencies (data control; web parity).
  async clearEnrichment(): Promise<void> {
    await request('/api/profile/enrichment', { method: 'DELETE' });
  },

  // Grant explicit, revocable third-party-AI consent (Apple 5.1.2(i)). Returns the updated
  // user (ai_consent=true) so the caller can sync auth state without a second /me round-trip.
  async grantAiConsent(): Promise<User> {
    const r = await request<{ user: User }>('/api/ai-consent', { method: 'POST' });
    return r.user;
  },

  // Revoke third-party-AI consent — generative AI is blocked again and scoring drops to the
  // local heuristic (no further data sent to the AI provider).
  async revokeAiConsent(): Promise<User> {
    const r = await request<{ user: User }>('/api/ai-consent', { method: 'DELETE' });
    return r.user;
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

  async generatePrepPack(jobId: string): Promise<{ id: string; title: string; content: string }> {
    const r = await request<{ prep_pack: { id: string; title: string; content: string } }>(
      '/api/prep-packs/generate',
      { method: 'POST', body: { job_id: jobId } },
    );
    return r.prep_pack;
  },

  // Generate salary-negotiation coaching for a job — a Career+ EXCLUSIVE. Throws
  // ApiError(403) if the user isn't Career+ (server is the source of truth; the client only
  // uses `career_plus` to decide whether to OFFER the action) and ApiError(503) when the
  // server has no LLM key — the caller surfaces either honestly, never a fake result.
  async generateSalaryNegotiation(
    jobId: string,
    targetSalary: number,
  ): Promise<{ id: string; title: string; content: string }> {
    const r = await request<{ artifact: { id: string; title: string; content: string } }>(
      '/api/prep/salary-negotiation',
      { method: 'POST', body: { job_id: jobId, target_salary: targetSalary } },
    );
    return r.artifact;
  },

  // Generate a tailored cover letter for a job — a Pro+ feature (Pro AND Career+). Throws
  // ApiError(403) if the user isn't paid (server is the source of truth; the client uses the
  // `premium` tier only to decide whether to OFFER it) and ApiError(503) when the server has no
  // LLM key — the caller surfaces either honestly, never a fake result.
  async generateCoverLetter(jobId: string): Promise<{ id: string; title: string; content: string }> {
    const r = await request<{ artifact: { id: string; title: string; content: string } }>(
      '/api/prep/cover-letter',
      { method: 'POST', body: { job_id: jobId } },
    );
    return r.artifact;
  },

  // Generate a day-by-day study plan for a job — a Pro+ feature. `days` is bounded 1–30
  // server-side (a 422 outside that range); same honest 403/503 contract as generateCoverLetter.
  async generateStudyPlan(jobId: string, days: number): Promise<{ id: string; title: string; content: string }> {
    const r = await request<{ artifact: { id: string; title: string; content: string } }>(
      '/api/prep/study-plan',
      { method: 'POST', body: { job_id: jobId, days } },
    );
    return r.artifact;
  },

  // Rewrite the user's saved résumé tailored to a job — a Pro+ feature. Same honest 403/503
  // contract as generateCoverLetter, plus ApiError(400) when the user has no saved résumé to
  // tailor (the server refuses rather than fabricate one) — the caller surfaces each honestly.
  async generateTailoredResume(jobId: string): Promise<{ id: string; title: string; content: string }> {
    const r = await request<{ artifact: { id: string; title: string; content: string } }>(
      '/api/prep/tailored-resume',
      { method: 'POST', body: { job_id: jobId } },
    );
    return r.artifact;
  },

  // Report/flag an AI-generated response for moderator review (store GenAI/UGC requirement).
  // Awaits the REAL POST /api/report and throws ApiError on failure so the caller can surface
  // it honestly — the success state is only shown once the server records the row.
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

  // Cross-pipeline skill-gap heatmap — FREE, computed locally on the server (no LLM). Ranked
  // gaps + strengths across ALL the user's tracked jobs vs their résumé.
  async skillGaps(): Promise<SkillGapAnalysis> {
    const r = await request<{ analysis: SkillGapAnalysis }>('/api/insights/skill-gaps');
    return r.analysis;
  },

  // Generate an AI learning plan for the user's top cross-pipeline skill gaps — a Pro+ feature.
  // Throws ApiError(403) for free tier / missing consent, ApiError(400) for no jobs / no résumé /
  // no gaps, ApiError(503) with no server key — the caller surfaces each honestly, never a fake
  // plan. Gaps are recomputed server-side; the client sends no skill list.
  async generateLearningPlan(): Promise<{ title: string; content: string; skills: string[] }> {
    const r = await request<{ artifact: { title: string; content: string; skills: string[] } }>(
      '/api/insights/learning-plan',
      { method: 'POST' },
    );
    return r.artifact;
  },
};

// One skill and how it relates to the pipeline + résumé (the heatmap unit).
export interface SkillStat {
  skill: string;
  job_count: number;
  total_jobs: number;
  coverage: number; // job_count / total_jobs, 0..1 — drives the heatmap bar
  in_resume: boolean;
}

export interface SkillGapAnalysis {
  total_jobs: number;
  has_resume: boolean;
  gaps: SkillStat[];
  strengths: SkillStat[];
}
