/**
 * API调用
 */
import axios from 'axios';
import type { Questionnaire, Question, LLMConfig, SystemSetting, KnowledgeDocument, KnowledgeChunk, SearchResult, AnsweringSession, SessionDetail, HistoryStats } from '@/types';

const api = axios.create({
  baseURL: '/api',
  timeout: 180000, // 3分钟超时，给Embedding足够时间
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败';
    return Promise.reject(new Error(message));
  }
);

// 问卷相关API
export const questionnaireApi = {
  parse: (url: string) => 
    api.post<any, any>('/questionnaire/parse', { url }),
  
  getById: (id: number) =>
    api.get<any, Questionnaire>(`/questionnaire/${id}`),
  
  getQuestions: (id: number) =>
    api.get<any, Question[]>(`/questionnaire/${id}/questions`),
};

// LLM配置API
export const llmApi = {
  getConfigs: (configType?: string) =>
    api.get<any, LLMConfig[]>('/llm/configs', { params: { config_type: configType } }),

  getConfig: (id: number) =>
    api.get<any, LLMConfig>(`/llm/configs/${id}`),

  createConfig: (config: Partial<LLMConfig>) =>
    api.post<any, LLMConfig>('/llm/configs', config),

  updateConfig: (id: number, config: Partial<LLMConfig>) =>
    api.put<any, LLMConfig>(`/llm/configs/${id}`, config),

  deleteConfig: (id: number) =>
    api.delete(`/llm/configs/${id}`),

  validateConfig: (config: Partial<LLMConfig>) =>
    api.post<any, { valid: boolean; message: string; details?: any }>('/llm/configs/validate', config),
};

// 知识库API
export const knowledgeApi = {
  getDocuments: (skip = 0, limit = 100) =>
    api.get<any, KnowledgeDocument[]>('/knowledge/documents', { params: { skip, limit } }),
  
  addDocument: (data: { title: string; content: string; chunk_size?: number; chunk_overlap?: number }) =>
    api.post<any, KnowledgeDocument>('/knowledge/documents', data),
  
  uploadDocument: (file: File, chunk_size = 500, chunk_overlap = 50) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<any, KnowledgeDocument>('/knowledge/documents/upload', formData, {
      params: { chunk_size, chunk_overlap },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  deleteDocument: (id: number) =>
    api.delete(`/knowledge/documents/${id}`),
  
  getDocumentChunks: (id: number) =>
    api.get<any, KnowledgeChunk[]>(`/knowledge/documents/${id}/chunks`),
  
  search: (query: string, top_k = 5, score_threshold = 0.0, use_rerank = true) =>
    api.post<any, SearchResult[]>('/knowledge/search', {
      query,
      top_k,
      score_threshold,
      use_rerank,
    }),
};

// 系统设置API
export const settingsApi = {
  getAll: (category?: string) =>
    api.get<any, SystemSetting[]>('/settings', { params: { category } }),
  
  get: (key: string) =>
    api.get<any, SystemSetting>(`/settings/${key}`),
  
  update: (key: string, data: Partial<SystemSetting>) =>
    api.put<any, SystemSetting>(`/settings/${key}`, data),
  
  create: (data: Partial<SystemSetting>) =>
    api.post<any, SystemSetting>('/settings', data),
  
  delete: (key: string) =>
    api.delete(`/settings/${key}`),
  
  initDefaults: () =>
    api.post('/settings/init-defaults'),
};

// 健康检查
export const healthApi = {
  check: () =>
    api.get('/health'),
  
  getInfo: () =>
    api.get('/info'),
};

// 历史记录API
export const historyApi = {
  getSessions: (params?: {
    page?: number;
    page_size?: number;
    questionnaire_id?: number;
    mode?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  }) => api.get<any, {
    total: number;
    page: number;
    page_size: number;
    items: AnsweringSession[];
  }>('/history/sessions', { params }),
  
  getSessionDetail: (sessionId: number) => 
    api.get<any, SessionDetail>(`/history/sessions/${sessionId}`),
  
  deleteSession: (sessionId: number) => 
    api.delete(`/history/sessions/${sessionId}`),
  
  getStats: () => 
    api.get<any, HistoryStats>('/history/stats'),
  
  exportSession: (sessionId: number, format: 'json' | 'csv' = 'json') =>
    api.post<any, SessionDetail>(`/history/sessions/${sessionId}/export`, null, { params: { format } }),

  submitSession: (sessionId: number, answers: Record<string, any>) =>
    api.post<any, { success: boolean; message: string; result: any }>(`/history/sessions/${sessionId}/submit`, answers),
};

export default api;

