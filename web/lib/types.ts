// Mirrors the FastAPI response shapes (see asgi.py serializers).
export type Tier = 'free' | 'premium';

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
  jobs_remaining: number | string;
  prep_packs_remaining: number | string;
  ai_coach: boolean;
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

export function scoreColor(score: number | null | undefined): string {
  if (score == null) return 'text-slate-400';
  if (score >= 75) return 'text-emerald-400';
  if (score >= 50) return 'text-amber-400';
  return 'text-red-400';
}
