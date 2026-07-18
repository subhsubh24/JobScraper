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

export interface ReferralStats {
  code: string;
  total_referred: number;
  bonus_prep_packs: number;
}

// A teammate holding a seat on the org (present only in the OWNER's org payload).
export interface OrgMember {
  user_id: string;
  email: string | null;
  role: string; // "owner" | "member"
}

// Team / organization (seat tier — B2B2C). Mirrors the API's `_org_payload` (asgi.py). The
// `members` roster is present ONLY in the owner's view; a member sees summary state without it.
export interface Organization {
  id: string;
  name: string;
  plan: string;
  active: boolean;
  seats_purchased: number;
  seats_used: number;
  is_owner: boolean;
  role: string; // "owner" | "member"
  members?: OrgMember[];
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
