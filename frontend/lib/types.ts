// LEARNOVA — Type Definitions matching API Specification

export type DocumentStatus = 'PROCESSING' | 'READY' | 'FAILED' | 'ANALYZED';

export interface Topic {
  id: string;
  name: string;
  difficulty_level: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
  chunk_count?: number;
  mastery_score?: number;
  description?: string;
  prerequisites?: string[];
}

export interface DocumentItem {
  id: string;
  title: string;
  filename: string;
  file_size: number;
  mime_type: string;
  status: DocumentStatus;
  total_pages: number;
  total_chunks: number;
  word_count?: number;
  topic_count?: number;
  summary?: string;
  topics?: Topic[];
  created_at: string;
  updated_at?: string;
}

export interface DocumentAnalysis {
  document_id: string;
  status: string;
  executive_summary: string;
  topics_extracted: number;
  key_formulas_extracted: number;
  prerequisites_mapped: number;
  topics?: Topic[];
  key_formulas?: Array<{ name: string; formula: string; description?: string }>;
  key_definitions?: Array<{ term: string; definition: string }>;
}

export interface Citation {
  citation_id: string;
  document_id: string;
  page_number: number;
  chunk_id: string;
  snippet: string;
  relevance_score?: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: string;
  grounded?: boolean;
}

export interface ChatRequest {
  document_id: string;
  query: string;
  conversation_id?: string;
  stream?: boolean;
  top_k?: number;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  response: string;
  citations: Citation[];
  grounded: boolean;
}

export type PedagogicalMode =
  | 'socratic'
  | 'first_principles'
  | 'analogy'
  | 'feynman'
  | 'simpler'
  | 'example'
  | 'mathematical'
  | 'step_by_step';

export interface DiagnosticQuestion {
  question_id: string;
  question_type: 'open_ended' | 'mcq';
  prompt: string;
  hints?: string[];
  options?: Array<{ key: string; text: string }>;
}

export interface TeachRequest {
  document_id: string;
  topic_id?: string;
  session_id?: string;
  pedagogical_mode?: PedagogicalMode;
  preferred_difficulty?: 'beginner' | 'intermediate' | 'advanced';
}

export interface TeachResponse {
  session_id: string;
  step_index: number;
  topic_name: string;
  pedagogical_mode: PedagogicalMode;
  scaffold_explanation: string;
  diagnostic_question?: DiagnosticQuestion;
  citations?: Citation[];
}

export interface ExplainAgainRequest {
  session_id: string;
  target_concept: string;
  desired_modality: 'analogy' | 'simpler' | 'example' | 'mathematical' | 'step_by_step';
  current_obstacle?: string;
}

export interface ExplainAgainResponse {
  session_id: string;
  modality_used: string;
  revised_explanation: string;
  follow_up_check?: {
    prompt: string;
  };
}

export interface EvaluateAnswerRequest {
  session_id: string;
  question_id: string;
  student_answer: string;
}

export interface MisconceptionDiagnostic {
  detected: boolean;
  category: string;
  summary: string;
  explanation: string;
}

export interface EvaluateAnswerResponse {
  is_correct: boolean;
  understanding_level: 'COMPLETE' | 'PARTIAL' | 'MINIMAL' | 'MISCONCEPTION';
  misconception?: MisconceptionDiagnostic;
  scaffolded_hint?: string;
  mastery_delta: number;
  next_action: string;
}

export type QuestionType = 'mcq' | 'short_answer' | 'conceptual';

export interface QuizOption {
  key: string;
  text: string;
}

export interface QuizQuestion {
  id: string;
  type: QuestionType;
  topic_id?: string;
  prompt: string;
  options?: QuizOption[];
  model_answer?: string;
  explanation?: string;
}

export interface Quiz {
  quiz_id: string;
  document_id: string;
  total_questions: number;
  questions: QuizQuestion[];
  created_at?: string;
}

export interface QuizGenerateRequest {
  document_id: string;
  topic_ids?: string[];
  question_count?: number;
  question_types?: QuestionType[];
  difficulty?: 'beginner' | 'intermediate' | 'advanced' | 'adaptive';
}

export interface QuestionEvaluationResponse {
  question_id: string;
  is_correct: boolean;
  correct_answer: string;
  explanation: string;
  citation?: {
    document_id: string;
    page_number: number;
    chunk_id: string;
  };
}

export interface QuizSubmissionItem {
  question_id: string;
  submitted_answer: string;
}

export interface QuizSubmissionRequest {
  quiz_id: string;
  time_spent_seconds: number;
  submissions: QuizSubmissionItem[];
}

export interface TopicBreakdown {
  topic_id: string;
  topic_name: string;
  score: number;
  new_mastery_level: number;
}

export interface QuizResult {
  attempt_id: string;
  quiz_id: string;
  score_percentage: number;
  total_questions: number;
  correct_count: number;
  time_spent_seconds: number;
  topic_breakdown: TopicBreakdown[];
  identified_misconceptions: string[];
  recommended_review_date?: string;
}

export interface StudyPackFormula {
  name: string;
  formula: string;
  variables: string;
}

export interface StudyPackFlashcard {
  id: string;
  front: string;
  back: string;
  topic?: string;
}

export interface StudyPack {
  id: string;
  document_id: string;
  title: string;
  status: 'GENERATING' | 'READY' | 'FAILED';
  summary?: string;
  pack_type?: 'complete' | 'quick_revision' | 'formula_sheet' | 'exam_prep';
  formula_sheet?: StudyPackFormula[];
  flashcards?: StudyPackFlashcard[];
  key_takeaways?: string[];
  sample_questions?: Array<{ question: string; answer: string }>;
  pdf_available: boolean;
  pdf_url?: string;
  pdf_size_bytes?: number;
  generated_at?: string;
}

export interface StudyPackGenerateRequest {
  document_id: string;
  title?: string;
  pack_type?: 'complete' | 'quick_revision' | 'formula_sheet' | 'exam_prep';
  include_flashcards?: boolean;
  include_cheat_sheet?: boolean;
  include_practice_exam?: boolean;
}

export interface MasteryDistribution {
  novice: number;
  learning: number;
  proficient: number;
  mastered: number;
}

export interface StudentProgress {
  student_id: string;
  total_documents_studied: number;
  total_learning_time_minutes: number;
  current_streak_days: number;
  total_quizzes_completed: number;
  average_quiz_score: number;
  mastery_distribution: MasteryDistribution;
  upcoming_reviews_count: number;
}

export interface TopicMastery {
  topic_id: string;
  topic_name: string;
  document_id: string;
  mastery_score: number;
  confidence_level: 'LOW' | 'MODERATE' | 'HIGH';
  last_practiced_at?: string;
  spaced_repetition_interval_days?: number;
  next_review_at?: string;
  status: 'NOVICE' | 'LEARNING' | 'PRACTICING' | 'MASTERED';
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta?: {
    timestamp: string;
    request_id?: string;
  };
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
