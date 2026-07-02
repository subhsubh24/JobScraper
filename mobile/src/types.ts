// Shared types — mirror the Python API response shapes (see api.py serializers).

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

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  tier: Tier;
  // Optional so an older API deploy (no plan_level) safely reads as not-Career+.
  plan_level?: PlanLevel;
  career_plus?: boolean;
  jobs_remaining: number | string;
  prep_packs_remaining: number | string;
  ai_coach: boolean;
  // Third-party-AI consent (Apple 5.1.2(i)). Absent on an older API deploy reads as
  // not-consented (the safe default — prompt before sending data to the AI provider).
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

export interface ReferralStats {
  code: string;
  total_referred: number;
  bonus_prep_packs: number;
}
