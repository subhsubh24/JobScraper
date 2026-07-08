// Mirrors the FastAPI response shapes (see asgi.py serializers).
export type Tier = 'free' | 'premium';

// Entitlement LEVEL within the paid tier — derived server-side from the webhook-verified
// Subscription.plan (see src/billing.py). `career_plus` unlocks the Career+ exclusives.
export type PlanLevel = 'free' | 'pro' | 'career_plus';

export type ApplicationStatus =
  | 'saved'
  | 'applied'
  | 'phone_screen'
  | 'interview'
  | 'offer'
  | 'rejected'
  | 'withdrawn';

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  saved: 'Saved',
  applied: 'Applied',
  phone_screen: 'Phone Screen',
  interview: 'Interview',
  offer: 'Offer',
  rejected: 'Rejected',
  withdrawn: 'Withdrawn',
};

export const STATUS_ORDER: ApplicationStatus[] = [
  'saved',
  'applied',
  'phone_screen',
  'interview',
  'offer',
  'rejected',
  'withdrawn',
];

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  tier: Tier;
  // `plan_level` may be absent on an older API deploy; treat a missing value as not-Career+.
  plan_level?: PlanLevel;
  career_plus?: boolean;
  jobs_remaining: number | string;
  prep_packs_remaining: number | string;
  ai_coach: boolean;
  // Third-party-AI consent (Apple 5.1.2(i)). `ai_consent` may be absent on an older API
  // deploy; treat a missing value as not-consented (the safe default — prompt before use).
  ai_consent?: boolean;
  ai_consent_at?: string | null;
}

export interface Job {
  id: string;
  title: string;
  company: string | null;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
  score: number | null;
  score_explanation: string | null;
  status: ApplicationStatus;
  url: string | null;
  created_at: string | null;
}

export interface PipelineStats {
  total_jobs: number;
  status_breakdown: Record<string, number>;
  average_score: number;
  top_jobs: Job[];
}

// Interview readiness (GET /api/jobs/{id}/readiness) — a FREE, fully-local read that composites
// the user's real signals for one job into a 0–100 score + the single next-best-action.
export interface ReadinessComponents {
  interview_practice: number | null;
  skill_coverage: number | null;
  artifacts: number | null;
}

export interface ReadinessAction {
  // add_resume | start_mock_interview | answer_question | redo_answer | generate_artifact |
  // study_skill | ready
  action: string;
  label: string;
  detail: string;
}

export interface Readiness {
  score: number;
  components: ReadinessComponents;
  next_action: ReadinessAction;
  signals: {
    has_resume: boolean;
    answered_questions: number;
    missing_skill_count: number;
    artifacts_completed: string[];
    sessions: number;
  };
}

export function scoreColor(score: number | null | undefined): string {
  if (score == null) return 'text-slate-400';
  if (score >= 75) return 'text-emerald-400';
  if (score >= 50) return 'text-amber-400';
  return 'text-red-400';
}
