/**
 * Valtio状态管理
 */
import { proxy } from 'valtio';
import type { Questionnaire, Question, Answer, LLMConfig, AnsweringMode, KnowledgeConfig } from '@/types';

interface AppState {
  // 问卷相关
  questionnaire: Questionnaire | null;
  questions: Question[];
  answers: Record<string, Answer>;
  
  // 答题模式
  mode: AnsweringMode;
  selectedQuestions: string[];
  presetAnswers: any[];
  
  // 知识库配置
  knowledgeConfig: KnowledgeConfig;
  
  // LLM配置
  llmConfigs: LLMConfig[];
  activeLLMConfig: LLMConfig | null;
  
  // 系统设置
  settings: Record<string, any>;
  
  // 答题进度
  isAnswering: boolean;
  answeringProgress: {
    current: number;
    total: number;
  };
  
  // UI状态
  loading: boolean;
  error: string | null;
}

export const appState = proxy<AppState>({
  questionnaire: null,
  questions: [],
  answers: {},
  
  mode: 'FULL_AUTO',
  selectedQuestions: [],
  presetAnswers: [],
  
  knowledgeConfig: {
    enabled: false,
    document_ids: [],
    top_k: 3,
    score_threshold: 0.5,
  },
  
  llmConfigs: [],
  activeLLMConfig: null,
  
  settings: {},
  
  isAnswering: false,
  answeringProgress: {
    current: 0,
    total: 0,
  },
  
  loading: false,
  error: null,
});

// 辅助函数
export const resetQuestionnaire = () => {
  appState.questionnaire = null;
  appState.questions = [];
  appState.answers = {};
  appState.selectedQuestions = [];
  appState.presetAnswers = [];
};

export const setLoading = (loading: boolean) => {
  appState.loading = loading;
};

export const setError = (error: string | null) => {
  appState.error = error;
};

export const setQuestionnaire = (questionnaire: Questionnaire, questions: Question[]) => {
  appState.questionnaire = questionnaire;
  appState.questions = questions;
  appState.answers = {};
};

export const setAnsweringMode = (mode: AnsweringMode) => {
  appState.mode = mode;
};

export const toggleQuestionSelection = (questionId: string) => {
  const index = appState.selectedQuestions.indexOf(questionId);
  if (index > -1) {
    appState.selectedQuestions.splice(index, 1);
  } else {
    appState.selectedQuestions.push(questionId);
  }
};

export const setPresetAnswers = (answers: any[]) => {
  appState.presetAnswers = answers;
};

export const updateAnswer = (questionId: string, answer: Answer) => {
  appState.answers[questionId] = answer;
};

export const updateAnsweringProgress = (current: number, total: number) => {
  appState.answeringProgress = { current, total };
};

export const setAnswering = (isAnswering: boolean) => {
  appState.isAnswering = isAnswering;
};

export const setSettings = (settings: Record<string, any>) => {
  appState.settings = settings;
};

export const updateSetting = (key: string, value: any) => {
  appState.settings[key] = value;
};

// 知识库配置
export const setKnowledgeConfig = (config: Partial<KnowledgeConfig>) => {
  Object.assign(appState.knowledgeConfig, config);
};

export const toggleKnowledgeEnabled = () => {
  appState.knowledgeConfig.enabled = !appState.knowledgeConfig.enabled;
};

export const toggleDocumentSelection = (documentId: number) => {
  const index = appState.knowledgeConfig.document_ids.indexOf(documentId);
  if (index > -1) {
    appState.knowledgeConfig.document_ids.splice(index, 1);
  } else {
    appState.knowledgeConfig.document_ids.push(documentId);
  }
};

