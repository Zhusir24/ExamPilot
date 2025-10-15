/**
 * 类型定义
 */

export interface Question {
  id: string;
  type: string;
  content: string;
  options?: string[];
  order: number;
  required: boolean;
}

export interface Questionnaire {
  id: number;
  url: string;
  platform: string;
  template_type: string;
  title: string;
  description?: string;
  total_questions: number;
  questions?: Question[];
  created_at?: string;
}

export interface Answer {
  question_id: string;
  content: any;
  status: string;
  confidence?: number;
  reasoning?: string;
  knowledge_references?: any[];
}

export interface LLMConfig {
  id?: number;
  name: string;
  provider: string;
  api_key?: string;
  base_url: string;
  model: string;
  temperature: number;
  max_tokens?: number;
  config_type: string;
  is_active: boolean;
  extra_params?: Record<string, any>;
}

export interface SystemSetting {
  id?: number;
  key: string;
  value: any;
  value_type: string;
  description?: string;
  category?: string;
}

export interface KnowledgeDocument {
  id: number;
  title: string;
  filename?: string;
  file_type?: string;
  file_size?: number;
  total_chunks: number;
  created_at: string;
}

export interface KnowledgeConfig {
  enabled: boolean;              // 是否启用知识库
  document_ids: number[];        // 选中的文档ID列表
  top_k: number;                 // 使用前几个分块
  score_threshold: number;       // 相似度阈值
}

export interface KnowledgeChunk {
  id: number;
  chunk_index: number;
  content: string;
  start_pos: number;
  end_pos: number;
}

export interface SearchResult {
  content: string;
  document_title: string;
  chunk_index: number;
  similarity: number;
  document_id: number;
}

export type AnsweringMode = 'FULL_AUTO' | 'USER_SELECT' | 'PRESET_ANSWERS';

export interface AnsweringProgress {
  current: number;
  total: number;
  question_id: string;
  answer: Answer;
}

export interface AnsweringSession {
  id: number;
  questionnaire?: {
    id: number;
    title: string;
    url: string;
  };
  mode: string;
  mode_display: string;
  status: string;
  total_questions: number;
  answered_questions: number;
  correct_answers?: number;
  avg_confidence?: number;
  duration?: number;
  submitted: boolean;
  submission_result?: string;
  start_time?: string;
  end_time?: string;
  created_at?: string;
}

export interface SessionDetail {
  session: {
    id: number;
    mode: string;
    mode_display: string;
    status: string;
    total_questions: number;
    answered_questions: number;
    correct_answers?: number;
    avg_confidence?: number;
    duration?: number;
    submitted: boolean;
    submission_result?: string;
    start_time?: string;
    end_time?: string;
  };
  questionnaire?: {
    id: number;
    title: string;
    url: string;
    description?: string;
  };
  answers: Array<{
    question_id: string;
    question: {
      order: number;
      type: string;
      content: string;
      options?: string[];
      required: boolean;
    };
    answer?: string;
    answer_display?: string;
    confidence?: number;
    reasoning?: string;
    status?: string;
    knowledge_references?: Array<{
      document_id: number;
      document_title: string;
      chunk_index: number;
      content: string;
      similarity: number;
    }>;
  }>;
}

export interface HistoryStats {
  total_sessions: number;
  total_questions_answered: number;
  avg_confidence: number;
  mode_distribution: Record<string, number>;
  recent_sessions: Array<{
    id: number;
    questionnaire_title: string;
    mode_display: string;
    status: string;
    answered_questions: number;
    avg_confidence?: number;
    created_at?: string;
  }>;
}

