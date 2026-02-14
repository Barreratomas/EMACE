export type AgentType = 'inventory' | 'sales' | 'logistics' | 'analytics' | 'general' | 'system';

export interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
  agentId?: AgentType;
}

export interface Agent {
  id: AgentType;
  name: string;
  description: string;
  status: 'online' | 'busy' | 'offline';
  avatar?: string;
}
