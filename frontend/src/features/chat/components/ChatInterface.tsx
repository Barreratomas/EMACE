'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity,
  X, 
  Send, 
  Terminal, 
  Bot, 
  User, 
  Maximize2, 
  Minimize2,
  Cpu,
  Shield,
} from 'lucide-react';
// import { Agent, Message, AgentType } from '../types';
import { Agent, Message } from '../types';
import { useMutation } from '@tanstack/react-query';
import { chatEndpointApiV1ChatPost } from '@/lib/api/generated/sdk.gen';
import { cn } from '@/lib/utils';
import { ScanningLoader } from '@/components/ui/IndustrialProgress';
import { TypewriterText } from '@/components/ui/TypewriterText';
import { useSystemSounds } from '@/hooks/use-system-sounds';

const AGENTS: Agent[] = [
  { id: 'general', name: 'EMACE_CORE', description: 'Asistente general del sistema', status: 'online' },
  { id: 'inventory', name: 'AGENTE_INVENTARIO', description: 'Especialista en stock y almacén', status: 'online' },
  { id: 'sales', name: 'AGENTE_VENTAS', description: 'Gestión de pedidos y clientes', status: 'busy' },
  { id: 'logistics', name: 'AGENTE_LOGISTICA', description: 'Rutas y distribución', status: 'online' },
];

export default function ChatInterface() {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent>(AGENTS[0]);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'agent',
      content: 'TERMINAL DE COMUNICACIÓN EMACE v2.0.4 INICIALIZADA. ESTADO: ÓPTIMO. ESPERANDO COMANDOS DEL OPERADOR...',
      timestamp: new Date(),
      agentId: 'general'
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [wsConnected, setWsConnected] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const { playSound } = useSystemSounds();

  // Handle open/close with sound
  const toggleChat = (state: boolean) => {
    setIsOpen(state);
    playSound('click');
  };

  // WebSocket initialization
  useEffect(() => {
    if (isOpen && !socketRef.current) {
      const token = document.cookie
        .split('; ')
        .find((row) => row.startsWith('access_token='))
        ?.split('=')[1];

      if (!token) return;

      const baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/api\/v1\/?$/, '');
      const wsUrl = baseUrl.replace('http', 'ws') + '/api/v1/chat/ws';
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('WS Connected');
        setWsConnected(true);
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WS Message:', data);
        const content = data.content || data.response;
        console.log('Content:', content);
        if (content) {
          playSound('scan');
          const agentResponse: Message = {
            id: Date.now().toString(),
            role: 'agent',
            content: content,
            timestamp: new Date(),
            agentId: selectedAgent.id
          };
          setMessages(prev => [...prev, agentResponse]);
        } else if (data.error) {
          console.error('WS Error message:', data.error);
        }
      };

      socket.onclose = () => {
        console.log('WS Disconnected');
        setWsConnected(false);
        socketRef.current = null;
      };

      socketRef.current = socket;
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [isOpen, selectedAgent.id, playSound]);

  const mutation = useMutation({
    mutationFn: async (text: string) => {
      const response = await chatEndpointApiV1ChatPost({
        body: {
          message: text,
          thread_id: 'default_thread'
        }
      });
      return response.data;
    },
    onSuccess: (data) => {
      if (!data) return;
      const agentResponse: Message = {
        id: Date.now().toString(),
        role: 'agent',
        content: data.response,
        timestamp: new Date(),
        agentId: selectedAgent.id
      };
      setMessages(prev => [...prev, agentResponse]);
    },
    onError: (error) => {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'agent',
        content: 'CRITICAL_ERROR: FALLO EN EL ENLACE DE DATOS. REINTENTANDO CONEXIÓN...',
        timestamp: new Date(),
        agentId: 'system'
      };
      setMessages(prev => [...prev, errorMessage]);
      console.error('Chat error:', error);
    }
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputValue.trim()) return;

    playSound('click');
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);

    // Intentar usar WebSocket si está conectado
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const token = document.cookie
        .split('; ')
        .find((row) => row.startsWith('access_token='))
        ?.split('=')[1];

      socketRef.current.send(JSON.stringify({
        token,
        message: inputValue,
        thread_id: `thread_${selectedAgent.id}`
      }));
    } else {
      // Fallback a HTTP
      mutation.mutate(inputValue);
    }

    setInputValue('');
  };

  return (
    <>
      {/* FAB - Technical Aesthetic */}
      <motion.button
        whileHover={{ scale: 1.05, boxShadow: '0 0 20px rgba(255,95,31,0.3)' }}
        whileTap={{ scale: 0.95 }}
        onClick={() => toggleChat(true)}
        className={cn(
          "fixed bottom-6 right-6 z-50 p-4 bg-primary text-white shadow-[0_0_15px_rgba(255,95,31,0.2)] transition-all duration-300 border border-primary/50",
          isOpen ? "opacity-0 pointer-events-none" : "opacity-100"
        )}
        style={{ clipPath: 'polygon(15% 0, 100% 0, 100% 85%, 85% 100%, 0 100%, 0 15%)' }}
      >
        <div className="relative">
          <Terminal size={24} />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-cyber-lime shadow-[0_0_5px_rgba(204,255,0,0.8)] animate-pulse" />
        </div>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ 
              type: "spring", 
              stiffness: 400, 
              damping: 30,
              mass: 0.8
            }}
            className={cn(
              "fixed z-60 panel-industrial flex flex-col overflow-hidden transition-all duration-300",
              isExpanded 
                ? "bottom-0 right-0 w-full h-full md:bottom-6 md:right-6 md:w-800px md:h-600px]" 
                : "bottom-6 right-6 w-420px h-540px"
            )}
            style={{ borderRadius: '4px' }}
          >
            {/* Header - Operator View */}
            <div className="p-4 bg-black/40 border-b border-white/5 flex justify-between items-center relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1px bg-linear-to-r from-transparent via-primary/40 to-transparent" />
              <div className="flex items-center gap-3 relative z-10">
                <div className="p-1.5 bg-primary/10 border border-primary/20 text-primary animate-pulse">
                  <Cpu size={16} />
                </div>
                <div>
                  <div className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em] terminal-text">COMMS_LINK_01</div>
                  <div className="text-[12px] font-bold terminal-text text-slate-200">OPERATOR_TERMINAL_v2.0</div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button 
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="p-2 text-slate-500 hover:text-primary transition-colors hidden md:block"
                >
                  {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                </button>
                <button 
                  onClick={() => toggleChat(false)}
                  className="p-2 text-slate-500 hover:text-rose-500 transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="absolute inset-0 bg-linear-to-r from-transparent via-primary/5 to-transparent -translate-x-full group-hover:animate-scan-horizontal pointer-events-none" />
            </div>

            <div className="flex-1 flex overflow-hidden">
              {/* Sidebar - Unit Selection */}
              <div className={cn(
                "w-14 md:w-44 bg-black/40 border-r border-white/5 flex flex-col py-3",
                !isExpanded && "w-14"
              )}>
                <div className="px-3 mb-3 hidden md:block">
                  <span className="text-[8px] font-bold text-slate-600 uppercase tracking-[0.2em] terminal-text">AVAILABLE_UNITS</span>
                </div>
                {AGENTS.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent)}
                    className={cn(
                      "w-full px-3 py-2.5 flex items-center gap-3 transition-all relative border-y border-transparent",
                      selectedAgent.id === agent.id 
                        ? "bg-primary/5 border-primary/10 text-primary" 
                        : "text-slate-500 hover:text-slate-300 hover:bg-white/5"
                    )}
                  >
                    {selectedAgent.id === agent.id && (
                      <div className="absolute left-0 top-0 bottom-0 w-2px bg-primary" />
                    )}
                    <div className="relative">
                      <div className={cn(
                        "p-1.5 border",
                        selectedAgent.id === agent.id ? "bg-primary/10 border-primary/30" : "bg-black/40 border-white/10"
                      )}>
                        <Bot size={14} />
                      </div>
                      <div className={cn(
                        "absolute -bottom-0.5 -right-0.5 w-1.5 h-1.5 border border-midnight shadow-[0_0_3px_rgba(0,0,0,0.5)]",
                        agent.status === 'online' ? "bg-cyber-lime" : agent.status === 'busy' ? "bg-primary" : "bg-slate-600"
                      )} />
                    </div>
                    {isExpanded && (
                      <div className="text-left hidden md:block overflow-hidden">
                        <div className="text-[10px] font-bold truncate terminal-text uppercase">{agent.name}</div>
                        <div className="text-[8px] font-bold opacity-40 terminal-text">STATUS_{agent.status.toUpperCase()}</div>
                      </div>
                    )}
                  </button>
                ))}
              </div>

              {/* Chat Area - Tactical Console */}
              <div className="flex-1 flex flex-col bg-midnight relative overflow-hidden">
                {/* Tactical grid decoration */}
                <div className="absolute inset-0 pointer-events-none opacity-[0.03]" 
                  style={{ backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)', backgroundSize: '24px 24px' }} 
                />

                {/* Messages List */}
                <div 
                  ref={scrollRef}
                  className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar"
                >
                  {messages.map((msg) => (
                    <div 
                      key={msg.id}
                      className={cn(
                        "flex flex-col max-w-[90%]",
                        msg.role === 'user' ? "ml-auto items-end" : "items-start"
                      )}
                    >
                      <div className="flex items-center gap-2 mb-1 opacity-40 terminal-text text-[9px]">
                        {msg.role === 'agent' ? (
                          <>
                            <Bot size={10} className="text-primary" />
                            <span className="font-bold text-primary">[{selectedAgent.name}]</span>
                          </>
                        ) : (
                          <>
                            <span className="font-bold">OPERATOR_LOG</span>
                            <User size={10} />
                          </>
                        )}
                        <span>{"//"}</span>
                        <span>{msg.timestamp.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                      </div>
                      <div className={cn(
                        "p-3 border terminal-text text-[11px] leading-relaxed",
                        msg.role === 'user' 
                          ? "bg-steel/40 border-white/10 text-slate-200" 
                          : "bg-primary/5 border-primary/20 text-slate-200"
                      )}
                      style={{ 
                        clipPath: msg.role === 'user' 
                          ? 'polygon(0 0, 100% 0, 100% 85%, 95% 100%, 0 100%)' 
                          : 'polygon(0 0, 100% 0, 100% 100%, 5% 100%, 0 85%)' 
                      }}
                      >
                        {msg.role === 'agent' && (
                          <span className="text-primary mr-2 opacity-50">&gt;</span>
                        )}
                        {msg.role === 'agent' ? (
                          <TypewriterText text={msg.content} speed={15} />
                        ) : (
                          msg.content
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Input Area - Command Entry */}
                <div className="p-4 border-t border-white/5 bg-black/40">
                  <form onSubmit={handleSendMessage} className="flex gap-2">
                    <div className="flex-1 relative group">
                      <div className="absolute inset-y-0 left-3 flex items-center text-primary/40 group-focus-within:text-primary transition-colors">
                        <Terminal size={12} />
                      </div>
                      <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="ENTER_COMMAND_OR_QUERY..."
                        className="w-full bg-midnight border border-white/10 p-2.5 pl-9 pr-10 text-[11px] terminal-text text-slate-200 focus:border-primary/40 focus:bg-black/60 outline-none transition-all placeholder:text-slate-700"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={!inputValue.trim() || mutation.isPending}
                      className="px-4 bg-primary text-white hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center justify-center border border-primary/20"
                      style={{ clipPath: 'polygon(15% 0, 100% 0, 100% 85%, 85% 100%, 0 100%, 0 15%)' }}
                    >
                      {mutation.isPending ? (
                        <ScanningLoader className="border-primary/40" />
                      ) : (
                        <Send size={14} />
                      )}
                    </button>
                  </form>
                  <div className="mt-3 flex justify-between items-center opacity-40">
                    <div className="flex gap-4">
                      <div className={cn(
                        "flex items-center gap-1.5 text-[8px] font-bold terminal-text uppercase",
                        wsConnected ? "text-cyber-lime" : "text-rose-500"
                      )}>
                        <Activity size={8} /> LINK: {wsConnected ? "ESTABLISHED" : "LOST"}
                      </div>
                      <div className="flex items-center gap-1.5 text-[8px] font-bold terminal-text text-slate-500 uppercase">
                        <Shield size={8} /> PROTOCOL: AES_256_SECURE
                      </div>
                    </div>
                    <div className="text-[8px] font-bold terminal-text text-slate-500 uppercase tracking-widest">
                      UNIT_01 {"//"} READY
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
