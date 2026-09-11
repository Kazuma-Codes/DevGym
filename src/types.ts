export type InterviewMode = 'SUBJECT' | 'RESUME' | 'PROJECT_GRILL' | 'BEHAVIORAL' | 'SYSTEM_DESIGN' | 'JD_MATCH';
export interface VoiceStats { wpm: number; filler_count: number; max_pause: number; feedback: string; }
export interface Turn { question: string; transcript: string; score: number; feedback: string; voice: VoiceStats; }