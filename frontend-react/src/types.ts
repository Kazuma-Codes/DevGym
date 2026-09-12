export type InterviewMode =
  | "SUBJECT"
  | "RESUME"
  | "PROJECT_GRILL"
  | "RAPID_FIRE"
  | "BEHAVIORAL"
  | "SYSTEM_DESIGN"
  | "JD_MATCH";

export interface SetupPayload {
  mode: InterviewMode;
  subject: string;
  difficulty: string;
  resumeText: string;
  jobDescription: string;
  projectText: string;
  focusAreas: string;
  resumeFile: File | null;
}

export interface StartResponse {
  session_id: string;
  mode: InterviewMode;
  subject: string;
  difficulty: string;
  question: string;
  expected_concepts: string[];
  time_limit_seconds: number;
  max_questions: number;
  question_number?: number;
}

export interface VoiceAnalytics {
  wpm: number;
  word_count: number;
  filler_count: number;
  long_pauses: number;
  max_pause_seconds: number;
  speech_duration_seconds: number;
  total_duration_seconds: number;
  feedback: string;
}

export interface EvaluationAnalytics {
  communication_clarity?: number;
  structured_thinking?: number;
  depth_score?: number;
  tradeoffs_mentioned?: string[];
  edge_cases_caught?: string[];
}

export interface AnswerResponse {
  transcript: string;
  feedback: string;
  score: number;
  missing_concepts: string[];
  next_question: string;
  finished: boolean;
  voice: VoiceAnalytics;
  analytics: EvaluationAnalytics;
  knowledge_gaps: string[];
  graceful_exit_feedback: string;
  star_score: number | null;
  question_number: number;
  max_questions: number;
  overtime?: boolean;
  response_seconds?: number;
}

export interface SummaryTimelineItem {
  index: number;
  question: string;
  score: number;
  wpm: number;
  filler_count: number;
  max_pause_seconds: number;
  overtime?: boolean;
  created_at: string;
}

export interface SummaryRadar {
  communication_clarity: number;
  structured_thinking: number;
  depth_score: number;
}

export interface SummaryResponse {
  session_id: string;
  mode: InterviewMode;
  subject: string;
  difficulty: string;
  status: string;
  question_number: number;
  max_questions: number;
  average_score: number;
  average_wpm: number;
  average_filler_count: number;
  average_max_pause_seconds: number;
  radar: SummaryRadar;
  timeline: SummaryTimelineItem[];
  knowledge_gaps: string[];
  recommendations: string[];
  created_at: string;
  completed_at: string | null;
}

export interface ConfigResponse {
  single_user_mode: boolean;
  llm_configured: boolean;
}

export interface MeResponse {
  authenticated: boolean;
  username?: string;
}

export interface SessionListItem {
  session_id: string;
  mode: InterviewMode;
  subject: string;
  difficulty: string;
  status: string;
  question_number: number;
  max_questions: number;
  average_score: number;
  has_overtime: boolean;
  created_at: string | null;
  completed_at: string | null;
}

export interface ProgressPoint {
  session_id: string;
  date: string | null;
  mode: string;
  subject: string;
  average_score: number;
  average_wpm: number;
  average_filler_count: number;
}

export interface WeakTopic {
  topic: string;
  times_missed: number;
  weight: number;
}

export interface SubjectStat {
  subject: string;
  sessions: number;
  average_score: number;
}

export interface ProgressResponse {
  trend: ProgressPoint[];
  sessions: SessionListItem[];
  weak_topics: WeakTopic[];
  subjects: SubjectStat[];
  overall: {
    total_sessions: number;
    sessions_with_answers: number;
    average_wpm: number;
    average_filler_count: number;
  };
}

export interface ShareResponse {
  share_token: string;
  share_url: string;
}
