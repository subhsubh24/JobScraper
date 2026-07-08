// Typed client for the Career Operator FastAPI backend.
// Base URL: NEXT_PUBLIC_API_URL (set in Vercel) -> the live API default.
import type { Job, PipelineStats, Readiness, User } from '@/lib/types';

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
  // Machine-readable error code when the API sends a structured `detail` (e.g.
  // `ai_consent_required`) — lets callers branch without matching on message text.
  code?: string;
  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
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
    // `detail` is usually a string, but some gates send a structured
    // `{ code, message }` (e.g. ai_consent_required) so the client can branch on the code.
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

export interface ReferralStats {
  code: string;
  total_referred: number;
  bonus_prep_packs: number;
}

// One skill and how it relates to the pipeline + résumé (the heatmap unit).
export interface SkillStat {
  skill: string;
  job_count: number; // how many tracked jobs demand this skill
  total_jobs: number;
  coverage: number; // job_count / total_jobs, 0..1 — drives the heatmap intensity
  in_resume: boolean;
}

export interface SkillGapAnalysis {
  total_jobs: number;
  has_resume: boolean;
  gaps: SkillStat[]; // demanded skills missing from the résumé, most-demanded first
  strengths: SkillStat[]; // demanded skills the résumé already has
}

// A competency discovered from a linked public source (Track A profile enrichment).
export interface Competency {
  skill: string;
  source_type: string;
  evidence: string | null;
}

export interface EnrichResult {
  success: boolean;
  found: number;
  username: string;
  competencies: Competency[];
  message: string;
}

export interface MockInterviewQuestion {
  question: string;
  category: string; // "technical" | "behavioral"
}

export interface MockInterviewAnswer {
  question_index: number;
  answer: string;
  relevance: number;
  specificity: number;
  star: number;
  overall: number;
  feedback: string;
  model_answer: string;
}

export interface MockInterviewSession {
  id: string;
  job_id: string;
  status: string; // "in_progress" | "completed"
  questions: MockInterviewQuestion[];
  answers: MockInterviewAnswer[];
  answered_count: number;
  total: number;
  created_at: string | null;
}

export interface MockInterviewSummary {
  id: string;
  status: string;
  total: number;
  answered_count: number;
  created_at: string | null;
}

export const api = {
  apiUrl: API_URL,

  async register(input: {
    email: string;
    password: string;
    full_name?: string;
    resume_text?: string;
    referral_code?: string;
    captcha_token?: string;
  }): Promise<User> {
    const r = await request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: input,
      auth: false,
    });
    setToken(r.token);
    return r.user;
  },

  async login(email: string, password: string, captchaToken?: string): Promise<User> {
    const r = await request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: { email, password, captcha_token: captchaToken },
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

  // Read the signed-in user's saved résumé text (their own data) so Settings can edit it.
  // Returns '' when none is saved (the server sends an empty string, never null).
  async getResume(): Promise<string> {
    return (await request<{ resume_text: string }>('/api/profile/resume')).resume_text;
  },

  // Save (or clear, with an empty string) the user's résumé. Awaits the real PATCH and returns
  // the server-confirmed has_resume — never an optimistic success.
  async saveResume(resumeText: string): Promise<boolean> {
    return (
      await request<{ has_resume: boolean }>('/api/profile/resume', {
        method: 'PATCH',
        body: { resume_text: resumeText },
      })
    ).has_resume;
  },

  // Track A profile enrichment: read the user's current link-discovered competencies.
  async getEnrichment(): Promise<Competency[]> {
    return (await request<{ competencies: Competency[] }>('/api/profile/enrichment')).competencies;
  },

  // Import competencies from the user's public GitHub profile (Pro+). Returns the honest result
  // (found count + the persisted set + a message) — never a fake success.
  async enrichGithub(github: string): Promise<EnrichResult> {
    return request<EnrichResult>('/api/profile/enrich/github', {
      method: 'POST',
      body: { github },
    });
  },

  async clearEnrichment(): Promise<void> {
    await request('/api/profile/enrichment', { method: 'DELETE' });
  },

  // Grant explicit, revocable third-party-AI consent (Apple 5.1.2(i)). Returns the updated
  // user (ai_consent=true) so the caller can sync auth state without a second /me round-trip.
  async grantAiConsent(): Promise<User> {
    return (await request<{ user: User }>('/api/ai-consent', { method: 'POST' })).user;
  },

  // Revoke third-party-AI consent — after this, generative AI paths are blocked again and
  // scoring drops to the local heuristic (no further data sent to the AI provider).
  async revokeAiConsent(): Promise<User> {
    return (await request<{ user: User }>('/api/ai-consent', { method: 'DELETE' })).user;
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

  // FREE, fully-local read: the interview-readiness score + next-best-action for one job.
  async getReadiness(id: string): Promise<Readiness> {
    return (await request<{ readiness: Readiness }>(`/api/jobs/${id}/readiness`)).readiness;
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

  async generatePrepPack(jobId: string): Promise<{ id: string; title: string; content: string }> {
    return (
      await request<{ prep_pack: { id: string; title: string; content: string } }>('/api/prep-packs/generate', {
        method: 'POST',
        body: { job_id: jobId },
      })
    ).prep_pack;
  },

  // Generate salary-negotiation coaching for a job — a Career+ EXCLUSIVE. Throws
  // ApiError(403) if the user isn't Career+ (the server is the source of truth; the client
  // only uses `career_plus` to decide whether to OFFER the action) and ApiError(503) when the
  // server has no LLM key — the caller surfaces either honestly, never a fake result.
  async generateSalaryNegotiation(
    jobId: string,
    targetSalary: number,
  ): Promise<{ id: string; title: string; content: string }> {
    return (
      await request<{ artifact: { id: string; title: string; content: string } }>(
        '/api/prep/salary-negotiation',
        { method: 'POST', body: { job_id: jobId, target_salary: targetSalary } },
      )
    ).artifact;
  },

  // Generate a tailored cover letter for a job — a Pro+ feature (Pro AND Career+). Throws
  // ApiError(403) if the user isn't paid (the server is the source of truth; the client uses
  // the `premium` tier to decide whether to OFFER the action) and ApiError(503) when the server
  // has no LLM key — the caller surfaces either honestly, never a fake result.
  async generateCoverLetter(jobId: string): Promise<{ id: string; title: string; content: string }> {
    return (
      await request<{ artifact: { id: string; title: string; content: string } }>('/api/prep/cover-letter', {
        method: 'POST',
        body: { job_id: jobId },
      })
    ).artifact;
  },

  // Generate a day-by-day study plan for a job — a Pro+ feature. `days` is bounded 1–30
  // server-side (a 422 outside that range); same honest 403/503 contract as coverLetter.
  async generateStudyPlan(jobId: string, days: number): Promise<{ id: string; title: string; content: string }> {
    return (
      await request<{ artifact: { id: string; title: string; content: string } }>('/api/prep/study-plan', {
        method: 'POST',
        body: { job_id: jobId, days },
      })
    ).artifact;
  },

  // Rewrite the user's saved résumé tailored to a job — a Pro+ feature. Same honest 403/503
  // contract as coverLetter, plus ApiError(400) when the user has no saved résumé to tailor
  // (the server refuses rather than fabricate one) — the caller surfaces each honestly.
  async generateTailoredResume(jobId: string): Promise<{ id: string; title: string; content: string }> {
    return (
      await request<{ artifact: { id: string; title: string; content: string } }>('/api/prep/tailored-resume', {
        method: 'POST',
        body: { job_id: jobId },
      })
    ).artifact;
  },

  // Report/flag an AI-generated response (coach reply or prep pack) for moderator review.
  // Awaits the REAL POST /api/report and throws ApiError on failure so the caller can
  // surface it honestly — the success state is only shown once the server records the row.
  async reportContent(input: {
    content_type: 'coach' | 'prep_pack' | 'mock_interview';
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
  async joinWaitlist(email: string, source?: string, captchaToken?: string): Promise<void> {
    await request<{ success: boolean; message: string }>('/api/waitlist/join', {
      method: 'POST',
      body: { email, source, captcha_token: captchaToken },
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

  // Cross-pipeline skill-gap heatmap — FREE, computed locally on the server (no LLM). Returns the
  // ranked gaps + strengths across ALL the user's tracked jobs vs their résumé.
  async skillGaps(): Promise<SkillGapAnalysis> {
    return (await request<{ analysis: SkillGapAnalysis }>('/api/insights/skill-gaps')).analysis;
  },

  // Generate an AI learning plan for the user's top cross-pipeline skill gaps — a Pro+ feature.
  // Throws ApiError(403) for free tier / missing consent, ApiError(400) for no jobs / no résumé /
  // no gaps, and ApiError(503) with no server key — the caller surfaces each honestly, never a
  // fake plan. The gaps are recomputed server-side; the client sends no skill list.
  async generateLearningPlan(): Promise<{ title: string; content: string; skills: string[] }> {
    return (
      await request<{ artifact: { title: string; content: string; skills: string[] } }>(
        '/api/insights/learning-plan',
        { method: 'POST' },
      )
    ).artifact;
  },

  // Mock interview engine (Pro+). Start a session: the server generates JD-derived questions.
  // Throws ApiError(403) tier/consent, (404) job, (503) no key — the caller surfaces each honestly.
  async startMockInterview(jobId: string, numQuestions = 5): Promise<MockInterviewSession> {
    return (
      await request<{ interview: MockInterviewSession }>('/api/prep/mock-interview', {
        method: 'POST',
        body: { job_id: jobId, num_questions: numQuestions },
      })
    ).interview;
  },

  // Submit one answer and get it scored. Returns the scored result + the running session status.
  // Awaits the real POST — the score/feedback shown is only ever the server's, never optimistic.
  async answerMockInterview(
    interviewId: string,
    questionIndex: number,
    answer: string,
  ): Promise<{ result: MockInterviewAnswer; status: string; answered_count: number; total: number }> {
    return request<{
      result: MockInterviewAnswer;
      status: string;
      answered_count: number;
      total: number;
    }>(`/api/prep/mock-interview/${encodeURIComponent(interviewId)}/answer`, {
      method: 'POST',
      body: { question_index: questionIndex, answer },
    });
  },

  // Reload a full session (questions + scored answers) — the caller's own only.
  async getMockInterview(interviewId: string): Promise<MockInterviewSession> {
    return (
      await request<{ interview: MockInterviewSession }>(
        `/api/prep/mock-interview/${encodeURIComponent(interviewId)}`,
      )
    ).interview;
  },

  // List the caller's mock-interview sessions for one job (most recent first).
  async listMockInterviews(jobId: string): Promise<MockInterviewSummary[]> {
    return (
      await request<{ interviews: MockInterviewSummary[] }>(
        `/api/prep/mock-interviews?job_id=${encodeURIComponent(jobId)}`,
      )
    ).interviews;
  },
};
