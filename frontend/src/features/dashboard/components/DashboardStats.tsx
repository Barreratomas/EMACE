'use client';

import React from 'react';
import { 
  Users, 
  Package,
  DollarSign,
  Activity,
  Clock,
  LucideIcon
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { IndustrialProgress } from '@/components/ui/IndustrialProgress';
import { MetricItem, ApiDashboardAgent } from '../types';

interface DashboardStatsProps {
  highlights: MetricItem[];
}

const UI_CONFIG: Record<string, { label: string, icon: LucideIcon, color: string, bg: string, glow: string }> = {
  inventory_products_active: { label: 'Productos Activos', icon: Package, color: 'text-primary', bg: 'bg-primary/10', glow: 'shadow-primary/5' },
  business_customers_total: { label: 'Clientes Totales', icon: Users, color: 'text-cyber-lime', bg: 'bg-cyber-lime/10', glow: 'shadow-cyber-lime/5' },
  business_revenue_30d: { label: 'Ingresos (30d)', icon: DollarSign, color: 'text-safety-orange', bg: 'bg-safety-orange/10', glow: 'shadow-safety-orange/5' },
  system_operations_24h: { label: 'Eventos (24h)', icon: Activity, color: 'text-primary', bg: 'bg-primary/10', glow: 'shadow-primary/5' },
};

export function DashboardStats({ highlights }: DashboardStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {highlights.map((metric, i) => {
        const config = UI_CONFIG[metric.key] || { label: 'Métrica', icon: Activity, color: 'text-slate-500', bg: 'bg-slate-500/10', glow: '' };
        const Icon = config.icon;

        return (
          <div key={i} className={cn("panel-industrial p-5 group relative overflow-hidden hover:border-primary/30 transition-all duration-300 rounded-none border-white/5", config.glow)}>
            <div className="absolute inset-0 bg-linear-to-b from-transparent via-primary/5 to-transparent -translate-y-full group-hover:animate-scan pointer-events-none" />
            
            <div className="flex justify-between items-start mb-6 relative z-10">
              <div className={cn("p-2.5 border border-white/10 bg-black/40", config.color)}>
                <Icon size={18} />
              </div>
              <span className={cn("text-[9px] font-bold uppercase tracking-[0.2em] px-2 py-0.5 border border-white/5 bg-black/20 terminal-text text-slate-500")}>
                {metric.trend || 'STABLE'}
              </span>
            </div>
            
            <div className="relative z-10">
              <div className="text-2xl font-black tracking-tighter mb-1 terminal-text">
                {metric.key.includes('revenue') ? `$${metric.value}` : metric.value}
              </div>
              <div className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.25em] terminal-text">
                {config.label}
              </div>
            </div>

            <div className="absolute bottom-0 right-0 w-8 h-8 opacity-[0.03] group-hover:opacity-[0.1] transition-opacity">
              <Icon size={32} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface AgentStatusListProps {
  agents: ApiDashboardAgent[];
}

export function AgentStatusList({ agents }: AgentStatusListProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-3">
          <div className="w-1 h-4 bg-primary" />
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] terminal-text">Estado de Agentes</h2>
        </div>
        <button className="text-[10px] font-bold text-primary/60 hover:text-primary transition-colors flex items-center gap-2 uppercase tracking-widest terminal-text">
          FULL_LOG <Clock size={12} />
        </button>
      </div>
      
      <div className="space-y-3">
        {agents && agents.length > 0 ? (
          agents.map((agent: ApiDashboardAgent, i: number) => (
            <div key={i} className="panel-industrial p-4 flex items-center gap-5 group hover:bg-white/5 transition-all rounded-none border-white/5 relative overflow-hidden">
              <div className="absolute inset-0 bg-linear-to-r from-transparent via-primary/5 to-transparent -translate-x-full group-hover:animate-scan-horizontal pointer-events-none" />
              
              <div className={cn("w-1 h-10", 
                agent.status === 'Online' ? 'bg-cyber-lime shadow-[0_0_8px_rgba(50,255,126,0.3)]' : 
                agent.status === 'Busy' ? 'bg-safety-orange shadow-[0_0_8px_rgba(255,153,0,0.3)]' : 'bg-slate-700'
              )} />
              
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-[11px] font-black terminal-text tracking-wider">{agent.name}</span>
                  <span className="text-[8px] px-1.5 py-0.5 bg-black/40 border border-white/10 text-slate-500 font-bold uppercase tracking-widest terminal-text">
                    {agent.type || 'System'}
                  </span>
                </div>
                <div className="text-[9px] font-bold text-slate-500 terminal-text opacity-60 uppercase tracking-widest">[{agent.activity || 'SIN_DATOS'}]</div>
              </div>

              <div className="w-44 hidden md:block px-4">
                <div className="flex justify-between text-[8px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 terminal-text">
                  <span>LOAD_CAPACITY</span>
                  <span className="text-slate-300">{agent.load}%</span>
                </div>
                <IndustrialProgress 
                  value={agent.load} 
                  segments={12}
                  variant={agent.load > 80 ? 'safety' : agent.load > 0 ? 'cyber' : 'slate'}
                />
              </div>

              <div className="text-right min-w-24">
                <div className="text-[8px] font-bold text-slate-600 mt-1 uppercase terminal-text tracking-widest">ESTADO: {agent.status === 'Online' ? 'ACTIVO' : 'OCUPADO'}</div>
              </div>
            </div>
          ))
        ) : (
          <div className="panel-industrial p-4 flex items-center justify-between gap-5 rounded-none border-white/5">
            <div className="flex items-center gap-3">
              <div className="w-1 h-10 bg-slate-700" />
              <div>
                <div className="text-[11px] font-black terminal-text tracking-wider text-slate-400">
                  SIN_DATOS_DE_AGENTES
                </div>
                <div className="text-[9px] font-bold text-slate-500 terminal-text opacity-60 uppercase tracking-widest">
                  [Sin eventos de agentes en las últimas 24h]
                </div>
              </div>
            </div>
            <div className="text-right min-w-24">
              <div className="text-[9px] font-bold uppercase tracking-[0.2em] terminal-text text-slate-500">
                OFFLINE
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
