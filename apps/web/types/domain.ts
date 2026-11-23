export type Profile = {
  name: string;
  skills: string[];
  graduation_year: number | null;
  experience_years: number | null;
  experience?: string[];
  projects: string[];
  education: string[];
  languages: string[];
  evidence: Record<string, string>;
};
export type Job = {
  id: string;
  title: string;
  company: string;
  description: string;
  skills: string[];
  optional_skills: string[];
  location: string | null;
  mode: string | null;
  employment: string | null;
  salary: number | null;
  currency: string | null;
  period: string | null;
  url: string;
  synthetic: boolean;
  last_seen_at: string;
};
export type Result = {
  job: Job;
  eligibility: string;
  unknown: string[];
  explanation: {
    score: number | null;
    matched: string[];
    missing: string[];
    missing_optional: string[];
    features: Record<string, number>;
    score_label: string;
  };
};
export type Chat = {
  mode: string;
  message: string;
  results: Result[];
  tools: string[];
  constraints: Record<string, unknown>;
  evidence: { tool: string; result: unknown }[];
  pending_preference: string | null;
};
export type Evaluation = {
  id: string;
  created_at: string;
  metadata: Record<string, unknown>;
  metrics: Record<string, unknown>;
};
