import api from './api';

export interface ChatMessage {
  role: 'user' | 'agent';
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  response: string;
  history: string[];
}

export const chatService = {
  sendMessage: async (message: string, threadId: string = 'default_thread'): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat/chat', {
      message,
      thread_id: threadId,
    });
    return response.data;
  },
};
