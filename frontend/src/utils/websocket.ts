/**
 * WebSocket工具类
 */
import type { AnsweringMode } from '@/types';

type MessageHandler = (data: any) => void;

export class AnsweringWebSocket {
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/answer`;
    
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => {
      console.log('WebSocket连接成功');
      this.reconnectAttempts = 0;
      this.emit('connected', {});
    };
    
    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const { type, data } = message;
        this.emit(type, data);
      } catch (error) {
        console.error('解析WebSocket消息失败:', error);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
      this.emit('error', { message: 'WebSocket连接错误' });
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket连接关闭');
      this.emit('disconnected', {});
      
      // 尝试重连
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        setTimeout(() => {
          console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          this.connect();
        }, 3000);
      }
    };
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  send(command: string, data: any = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ command, ...data }));
    } else {
      console.error('WebSocket未连接');
    }
  }
  
  startAnswering(
    questionnaireId: number,
    mode: AnsweringMode,
    selectedQuestions: string[] = [],
    presetAnswers: any[] = [],
    knowledgeConfig?: {
      enabled: boolean;
      document_ids: number[];
      top_k: number;
      score_threshold: number;
    }
  ) {
    this.send('start', {
      questionnaire_id: questionnaireId,
      mode,
      selected_questions: selectedQuestions,
      preset_answers: presetAnswers,
      knowledge_config: knowledgeConfig,
    });
  }
  
  confirmAnswer(questionId: string, answer: any) {
    this.send('confirm', {
      question_id: questionId,
      answer,
    });
  }
  
  submitAnswers() {
    this.send('submit');
  }
  
  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, []);
    }
    this.handlers.get(type)!.push(handler);
  }
  
  off(type: string, handler: MessageHandler) {
    const handlers = this.handlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }
  
  private emit(type: string, data: any) {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }
}

export const answeringWs = new AnsweringWebSocket();

