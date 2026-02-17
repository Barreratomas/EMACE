'use client';

import { useMemo } from 'react';
import { Bot, Cpu, Shield, Activity, Network, Database } from 'lucide-react';
import { IndustrialProgress } from '@/components/ui/IndustrialProgress';
import { cn } from '@/lib/utils';

const AGENTS = [
  {
    id: 'general',
    name: 'EMACE_CORE',
    role: 'Orquestador General',
    status: 'online',
    load: 42,
    latency: '1.2s',
    domain: 'Core Routing',
  },
  {
    id: 'inventory',
    name: 'AGENTE_INVENTARIO',
    role: 'Stock y Catálogo',
    status: 'online',
    load: 68,
    latency: '1.5s',
    domain: 'Inventory',
  },
  {
    id: 'sales',
    name: 'AGENTE_VENTAS',
    role: 'Pedidos y Clientes',
    status: 'busy',
    load: 83,
    latency: '2.1s',
    domain: 'Sales',
  },
  {
    id: 'logistics',
    name: 'AGENTE_LOGISTICA',
    role: 'Rutas y Entregas',
    status: 'online',
    load: 37,
    latency: '1.0s',
    domain: 'Logistics',
  },
];

const TOOLS = [
  { icon: Database, label: 'Inventario', key: 'inventory', agents: ['AGENTE_INVENTARIO'] },
  { icon: Network, label: 'Ventas', key: 'sales', agents: ['AGENTE_VENTAS'] },
  { icon: Cpu, label: 'Logística', key: 'logistics', agents: ['AGENTE_LOGISTICA'] },
];

export default function AgentsPanel() {
  const overview = useMemo(() => {
    const total = AGENTS.length;
    const online = AGENTS.filter(a => a.status === 'online').length;
    const busy = AGENTS.filter(a => a.status === 'busy').length;
    const offline = total - online - busy;
    return { total, online, busy, offline };
  }, []);

  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] font-bold text-primary terminal-text tracking-[0.3em] uppercase opacity-60">
              Multi_Agent_Control
            </span>
            <div className="h-px w-8 bg-primary/20" />
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display uppercase">
            Panel de Agentes
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-[11px] mt-2 font-bold uppercase tracking-widest terminal-text opacity-70">
            Supervisión operativa de los agentes EMACE y sus dominios de responsabilidad.
          </p>
        </div>
        <div className="panel-industrial px-5 py-3 flex items-center gap-4 border-primary/30 bg-black/40">
          <div className="p-2 rounded-full bg-primary/10 border border-primary/30">
            <Shield size={18} className="text-primary" />
          </div>
          <div className="text-[10px] font-mono text-slate-400">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
              <span className="font-bold uppercase tracking-[0.2em]">AGENT_MESH_STATUS</span>
            </div>
            <div className="mt-1 text-[9px] opacity-70">
              {overview.online} online · {overview.busy} busy · {overview.offline} offline
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {AGENTS.map(agent => (
            <div
              key={agent.id}
              className="panel-industrial p-4 flex items-center gap-5 group hover:bg-white/5 transition-all rounded-none border-white/5 relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-linear-to-r from-transparent via-primary/5 to-transparent -translate-x-full group-hover:animate-scan-horizontal pointer-events-none" />
              <div
                className={cn(
                  'w-1 h-10',
                  agent.status === 'online'
                    ? 'bg-cyber-lime shadow-[0_0_8px_rgba(50,255,126,0.3)]'
                    : agent.status === 'busy'
                    ? 'bg-safety-orange shadow-[0_0_8px_rgba(255,153,0,0.3)]'
                    : 'bg-slate-700'
                )}
              />
              <div className="flex items-center justify-center w-10 h-10 rounded-md bg-black/40 border border-white/10">
                <Bot size={20} className="text-primary" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] font-black terminal-text tracking-wider">{agent.name}</span>
                  <span className="text-[8px] px-1.5 py-0.5 bg-black/40 border border-white/10 text-slate-500 font-bold uppercase tracking-widest terminal-text">
                    {agent.domain}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest terminal-text">
                  {agent.role}
                </div>
                <div className="mt-2 flex items-center gap-4">
                  <div className="flex items-center gap-2 text-[9px] font-mono text-slate-400">
                    <Cpu size={10} className="text-cyber-lime" />
                    <span>LOAD {agent.load}%</span>
                  </div>
                  <div className="flex items-center gap-2 text-[9px] font-mono text-slate-400">
                    <Activity size={10} className="text-primary" />
                    <span>LAT {agent.latency}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[9px] font-mono text-slate-400">
                    <span
                      className={cn(
                        'w-1.5 h-1.5 rounded-full',
                        agent.status === 'online'
                          ? 'bg-cyber-lime'
                          : agent.status === 'busy'
                          ? 'bg-safety-orange'
                          : 'bg-slate-500'
                      )}
                    />
                    <span>STATUS_{agent.status.toUpperCase()}</span>
                  </div>
                </div>
              </div>
              <div className="w-40 hidden md:block px-4">
                <div className="flex justify-between text-[8px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 terminal-text">
                  <span>UTILIZATION</span>
                  <span className="text-slate-300">{agent.load}%</span>
                </div>
                <IndustrialProgress
                  value={agent.load}
                  segments={12}
                  variant={agent.load > 80 ? 'safety' : agent.load > 0 ? 'cyber' : 'slate'}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-4">
          <div className="panel-industrial p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Network size={16} className="text-primary" />
                <h3 className="text-[11px] font-bold uppercase tracking-[0.2em] terminal-text">
                  Dominios y Herramientas
                </h3>
              </div>
              <span className="text-[9px] font-mono text-slate-500">SYNC_OK</span>
            </div>
            <div className="space-y-3">
              {TOOLS.map(tool => (
                <div
                  key={tool.key}
                  className="flex items-center justify-between p-3 bg-black/40 border border-white/5"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-md bg-white/5 border border-white/10">
                      <tool.icon size={14} className="text-slate-200" />
                    </div>
                    <div>
                      <div className="text-[11px] font-bold text-slate-100 tracking-tight">{tool.label}</div>
                      <div className="text-[9px] text-slate-500 font-mono">
                        {tool.agents.join(' · ')}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end text-[9px] font-mono text-slate-500">
                    <span className="uppercase">Toolset</span>
                    <span className="text-cyber-lime">OK</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel-industrial p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Database size={16} className="text-cyber-lime" />
                <h3 className="text-[11px] font-bold uppercase tracking-[0.2em] terminal-text">
                  Últimos eventos
                </h3>
              </div>
            </div>
            <div className="space-y-2 text-[9px] font-mono text-slate-400 max-h-60 overflow-y-auto custom-scrollbar">
              <div>[21:30:42] INFO  Supervisor enruta consulta a AGENTE_INVENTARIO</div>
              <div>[21:30:45] OK    AGENTE_VENTAS ejecuta create_order</div>
              <div>[21:31:10] WARN  Latencia elevada en herramienta inventory_search</div>
              <div>[21:31:22] INFO  AGENTE_LOGISTICA genera plan de rutas</div>
              <div>[21:31:58] OK    Sincronización de memoria vectorial completada</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

