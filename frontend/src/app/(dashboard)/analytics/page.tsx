'use client';

import React, { useState, useSyncExternalStore } from 'react';
import { 
  Activity, 
  Zap, 
  BarChart3, 
  Clock, 
  ShieldCheck, 
  AlertCircle,
  TrendingUp,
  Cpu,
  Network,
  Database,
  Package,
  DollarSign,
  ShoppingCart,
  Users,
  ArrowUpRight,

  Download,
  RefreshCw,
  Search
} from 'lucide-react';
import { IndustrialProgress } from '@/components/ui/IndustrialProgress';
import { cn } from '@/lib/utils';
import { Button } from "@/components/ui/Button";
import { SectionHeader } from "@/components/ui/SectionHeader";

// Custom hook for safe mounting check without useEffect setState
function useHasMounted() {
  return useSyncExternalStore(
    () => () => {}, // subscribe function (no-op)
    () => true,     // getSnapshot on client
    () => false     // getServerSnapshot on server
  );
}

export default function AnalyticsPage() {
  const hasMounted = useHasMounted();
  const [activeTab, setActiveTab] = useState<'system' | 'inventory' | 'business'>('system');

  const systemMetrics = [
    { label: 'AGENT_UPTIME', value: '99.98%', icon: Clock, color: 'text-cyber-lime', trend: '+0.02%' },
    { label: 'TASK_SUCCESS', value: '94.2%', icon: ShieldCheck, color: 'text-emerald-500', trend: '+1.5%' },
    { label: 'AVG_LATENCY', value: '1.2s', icon: Zap, color: 'text-primary', trend: '-120ms' },
    { label: 'ACTIVE_THREADS', value: '24', icon: Activity, color: 'text-blue-500', trend: '+4' },
  ];

  const inventoryMetrics = [
    { label: 'TOTAL_ASSETS', value: '1,284', icon: Package, color: 'text-amber-500', trend: '+12' },
    { label: 'INVENTORY_VALUE', value: '$452.2k', icon: DollarSign, color: 'text-emerald-500', trend: '+$5.4k' },
    { label: 'LOW_STOCK_ITEMS', value: '18', icon: AlertCircle, color: 'text-rose-500', trend: '-3' },
    { label: 'STOCK_TURNOVER', value: '4.2x', icon: RefreshCw, color: 'text-blue-400', trend: '+0.5' },
  ];

  const businessMetrics = [
    { label: 'MONTHLY_REVENUE', value: '$84,200', icon: DollarSign, color: 'text-emerald-500', trend: '+12.4%' },
    { label: 'TOTAL_SALES', value: '412', icon: ShoppingCart, color: 'text-primary', trend: '+8.2%' },
    { label: 'ACTIVE_CLIENTS', value: '89', icon: Users, color: 'text-blue-500', trend: '+2' },
    { label: 'CONVERSION_RATE', value: '3.8%', icon: TrendingUp, color: 'text-cyber-lime', trend: '+0.4%' },
  ];

  if (!hasMounted) return null;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-12">
      {/* Header + Tabs using SectionHeader */}
      <SectionHeader
        className="md:flex-row md:items-center md:justify-between gap-6 pb-8 border-b border-border-ui/50"
        rightClassName="md:justify-end"
        left={
          <div>
            <div className="flex items-center gap-2 text-primary text-[11px] font-bold mb-3 uppercase tracking-[0.2em]">
              <Activity size={14} className="animate-pulse" /> Analytics & Intelligence Control
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight font-display uppercase">
              Centro de Control
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1 font-mono uppercase tracking-tighter">
              Monitoring critical infrastructure and business health metrics.
            </p>
          </div>
        }
        right={
          <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:flex-wrap sm:justify-end">
            <div className="flex flex-wrap p-1 bg-white/5 border border-white/10 rounded-xl">
              {[
                { id: 'system', label: 'Métricas Sistema', icon: Cpu },
                { id: 'inventory', label: 'Estado Inventario', icon: Package },
                { id: 'business', label: 'Dashboards Negocio', icon: BarChart3 },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg text-[11px] font-bold uppercase tracking-widest transition-all duration-200",
                    activeTab === tab.id
                      ? "bg-primary text-white shadow-lg shadow-primary/20"
                      : "text-slate-500 hover:text-slate-300 hover:bg-white/5"
                  )}
                >
                  <tab.icon size={14} />
                  {tab.label}
                </button>
              ))}
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                size="sm"
                className="gap-2 border-white/5 bg-white/5 hover:bg-white/10"
              >
                <Download size={14} /> EXPORT_DATA
              </Button>
              <Button variant="cyber" size="sm" className="gap-2">
                <RefreshCw size={14} /> SYNC_REALTIME
              </Button>
            </div>
          </div>
        }
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {(activeTab === 'system' ? systemMetrics : activeTab === 'inventory' ? inventoryMetrics : businessMetrics).map((metric) => (
          <div key={metric.label} className="panel-industrial p-6 group hover:border-primary/30 transition-all duration-500 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-1 opacity-10">
              <metric.icon size={60} />
            </div>
            <div className="flex justify-between items-start mb-4 relative z-10">
              <div className={cn("p-2 bg-white/5 rounded-lg", metric.color)}>
                <metric.icon size={20} />
              </div>
              <div className="flex items-center gap-1 text-[10px] font-mono text-emerald-500">
                <ArrowUpRight size={10} /> {metric.trend}
              </div>
            </div>
            <div className="space-y-1 relative z-10">
              <div className="text-3xl font-bold font-display tracking-tight leading-none mb-1">{metric.value}</div>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-800" />
                {metric.label}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Dynamic Content Based on Tab */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Main Chart Area */}
        <div className="lg:col-span-2 space-y-8">
          
          {activeTab === 'system' && (
            <div className="panel-industrial p-8">
              <SectionHeader
                className="sm:flex-row sm:items-center sm:justify-between mb-8 pb-4 border-b border-white/5"
                rightClassName="w-full sm:w-auto justify-start sm:justify-end"
                left={
                  <div className="flex items-center gap-3">
                    <Cpu className="text-primary" size={20} />
                    <h3 className="text-lg font-bold tracking-tight uppercase">
                      Agent_Workload_Distribution
                    </h3>
                  </div>
                }
                right={
                  <>
                    <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                    <span className="text-[10px] font-mono text-primary uppercase">
                      Active_Processing
                    </span>
                  </>
                }
              />

              <div className="space-y-10">
                {[
                  { name: 'Supervisor_Agent', val: 42, color: 'primary' },
                  { name: 'Inventory_Expert', val: 78, color: 'secondary' },
                  { name: 'QA_Validator', val: 15, color: 'primary' },
                  { name: 'Business_Analyst', val: 56, color: 'secondary' },
                ].map((agent) => (
                  <div key={agent.name} className="space-y-4">
                    <div className="flex justify-between text-[11px] font-bold uppercase tracking-widest">
                      <span className="text-slate-400">{agent.name}</span>
                      <span className={agent.color === 'primary' ? 'text-primary' : 'text-cyber-lime'}>{agent.val}%</span>
                    </div>
                      <IndustrialProgress value={agent.val} variant={agent.color as any} />
                   </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'inventory' && (
            <div className="panel-industrial p-8">
              <SectionHeader
                className="sm:flex-row sm:items-center sm:justify-between mb-8 pb-4 border-b border-white/5"
                rightClassName="w-full sm:w-auto justify-start sm:justify-end"
                left={
                  <div className="flex items-center gap-3">
                    <Package className="text-amber-500" size={20} />
                    <h3 className="text-lg font-bold tracking-tight uppercase">
                      Stock_Levels_By_Category
                    </h3>
                  </div>
                }
                right={
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-[9px] border-white/10"
                  >
                    VIEW_FULL_REPORT
                  </Button>
                }
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-12 pt-4">
                <div className="space-y-6">
                  <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Categoría_Ranking</h4>
                  {[
                    { cat: 'Electrónica', val: 85, color: 'bg-primary' },
                    { cat: 'Herramientas', val: 62, color: 'bg-blue-500' },
                    { cat: 'Componentes', val: 45, color: 'bg-cyber-lime' },
                    { cat: 'Consumibles', val: 30, color: 'bg-amber-500' },
                  ].map((item) => (
                    <div key={item.cat} className="space-y-2">
                      <div className="flex justify-between text-[10px] font-mono uppercase">
                        <span>{item.cat}</span>
                        <span>{item.val}%</span>
                      </div>
                      <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                        <div className={cn("h-full transition-all duration-1000", item.color)} style={{ width: `${item.val}%` }} />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex flex-col items-center justify-center border-l border-white/5 pl-8">
                  <div className="relative w-40 h-40">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="15" fill="transparent" className="text-white/5" />
                      <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="15" fill="transparent" strokeDasharray="439.8" strokeDashoffset="110" className="text-primary" />
                      <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="15" fill="transparent" strokeDasharray="439.8" strokeDashoffset="300" className="text-cyber-lime" />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-2xl font-bold">1.2k</span>
                      <span className="text-[8px] font-bold text-slate-500 uppercase">Items_Total</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 mt-6 w-full text-[9px] font-bold uppercase tracking-tighter">
                    <div className="flex items-center gap-2"><div className="w-2 h-2 bg-primary rounded-full" /> In Stock</div>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 bg-cyber-lime rounded-full" /> Allocated</div>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 bg-white/10 rounded-full" /> Out of Stock</div>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 bg-blue-500 rounded-full" /> Transit</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'business' && (
            <div className="panel-industrial p-8">
              <SectionHeader
                className="sm:flex-row sm:items-center sm:justify-between mb-8 pb-4 border-b border-white/5"
                rightClassName="w-full sm:w-auto justify-start sm:justify-end items-center gap-4"
                left={
                  <div className="flex items-center gap-3">
                    <TrendingUp className="text-cyber-lime" size={20} />
                    <h3 className="text-lg font-bold tracking-tight uppercase">
                      Revenue_Growth_Analysis
                    </h3>
                  </div>
                }
                right={
                  <>
                    <div className="flex items-center gap-2 text-[10px] font-bold">
                      <div className="w-2 h-2 bg-primary rounded-full" /> REVENUE
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-bold">
                      <div className="w-2 h-2 bg-blue-500 rounded-full" /> EXPENSES
                    </div>
                  </>
                }
              />

              <div className="h-64 flex items-end gap-3 px-4 relative">
                {/* Grid Lines */}
                <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-5 px-4">
                  {[1,2,3,4,5].map(i => <div key={i} className="w-full h-px bg-white" />)}
                </div>
                
                {[45, 62, 55, 80, 95, 75, 88, 100, 82, 90, 78, 85].map((h, i) => (
                  <div key={i} className="flex-1 flex flex-col justify-end gap-1 group relative">
                    <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-primary text-white text-[8px] px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity font-bold">
                      ${h}k
                    </div>
                    <div 
                      className="w-full bg-primary/20 border-t border-x border-primary/40 hover:bg-primary/40 transition-all duration-300"
                      style={{ height: `${h}%` }}
                    />
                    <div 
                      className="w-full bg-blue-500/20 border-t border-x border-blue-500/40 hover:bg-blue-500/40 transition-all duration-300"
                      style={{ height: `${h * 0.6}%` }}
                    />
                    <div className="mt-2 text-[8px] font-mono text-slate-500 text-center uppercase">
                      {['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'][i]}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="panel-industrial p-6 space-y-4">
              <div className="flex items-center gap-2 mb-2">
                <Network className="text-blue-500" size={16} />
                <h4 className="text-xs font-bold uppercase tracking-widest">Latencia de Red</h4>
              </div>
              <div className="h-24 flex items-end gap-1 px-2">
                {[40, 60, 45, 90, 65, 30, 50, 80, 45, 60, 75, 40].map((h, i) => (
                  <div 
                    key={i} 
                    className="flex-1 bg-blue-500/20 border-t border-blue-500/40 hover:bg-blue-500/60 transition-all duration-300"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
              <div className="flex justify-between text-[9px] font-mono text-slate-500">
                <span>T-30M</span>
                <span>NOW</span>
              </div>
            </div>

            <div className="panel-industrial p-6 space-y-4">
              <div className="flex items-center gap-2 mb-2">
                <Database className="text-cyber-lime" size={16} />
                <h4 className="text-xs font-bold uppercase tracking-widest">Uso de Memoria Vectorial</h4>
              </div>
              <div className="flex items-center justify-center h-24">
                <div className="relative w-20 h-20">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-white/5" />
                    <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="8" fill="transparent" strokeDasharray="226.2" strokeDashoffset="80" className="text-cyber-lime shadow-[0_0_10px_rgba(204,255,0,0.4)]" />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center text-xs font-bold">65%</div>
                </div>
              </div>
              <div className="text-center text-[9px] font-mono text-slate-500 uppercase tracking-tighter">2.4GB / 4.0GB ALLOCATED</div>
            </div>
          </div>
        </div>

        {/* System Logs / Side Panel */}
        <div className="lg:col-span-1">
          <div className="panel-industrial h-full flex flex-col">
            <div className="p-6 border-b border-white/5 bg-white/2">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold uppercase tracking-[0.2em] flex items-center gap-2">
                  <Activity size={14} className="text-primary" /> Event_Stream
                </h3>
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                  <span className="text-[9px] font-bold text-emerald-500 font-mono">LIVE</span>
                </div>
              </div>
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" size={12} />
                <input 
                  type="text" 
                  placeholder="FILTER_LOGS..." 
                  className="w-full bg-black/40 border border-white/10 rounded-md py-1.5 pl-8 pr-3 text-[10px] font-mono focus:outline-none focus:border-primary/50 transition-colors"
                />
              </div>
            </div>
            
            <div className="flex-1 p-6 space-y-4 font-mono text-[10px] overflow-y-auto max-h-150 scrollbar-thin scrollbar-thumb-white/10">
              {[
                { time: '21:30:42', type: 'INFO', msg: 'Supervisor routing to Inventory_Expert', category: 'AGENT' },
                { time: '21:30:45', type: 'SUCCESS', msg: 'Tool set_product_status executed', category: 'SYSTEM' },
                { time: '21:31:02', type: 'WARN', msg: 'High latency detected in OpenRouter', category: 'NETWORK' },
                { time: '21:31:15', type: 'INFO', msg: 'Vector memory synchronization complete', category: 'MEMORY' },
                { time: '21:32:01', type: 'INFO', msg: 'New user session: USER_042 (ADMIN)', category: 'AUTH' },
                { time: '21:32:45', type: 'ERROR', msg: 'Validation failed: STOCK_NEGATIVE', category: 'BUSINESS' },
                { time: '21:33:10', type: 'INFO', msg: 'System integrity check: 100% OK', category: 'SYSTEM' },
                { time: '21:34:22', type: 'SUCCESS', msg: 'Bulk inventory update complete', category: 'BUSINESS' },
                { time: '21:35:01', type: 'INFO', msg: 'Database backup initiated', category: 'SYSTEM' },
                { time: '21:35:55', type: 'WARN', msg: 'Agent "Business_Analyst" low response time', category: 'AGENT' },
                { time: '21:36:12', type: 'INFO', msg: 'New sale recorded: $1,240.00', category: 'BUSINESS' },
              ].map((log, i) => (
                <div key={i} className="group flex flex-col gap-1 border-b border-white/5 pb-3 last:border-0 hover:bg-white/2 transition-colors rounded p-1">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">[{log.time}]</span>
                    <span className="text-[8px] px-1.5 py-0.5 rounded bg-white/5 text-slate-400 font-bold uppercase">{log.category}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className={cn(
                      "font-bold",
                      log.type === 'ERROR' ? 'text-rose-500' : 
                      log.type === 'SUCCESS' ? 'text-emerald-500' : 
                      log.type === 'WARN' ? 'text-amber-500' : 
                      'text-blue-400'
                    )}>{log.type}:</span>
                    <span className="text-slate-300 group-hover:text-white transition-colors">{log.msg}</span>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="p-4 bg-black/40 border-t border-white/5 space-y-3">
              <div className="flex items-center justify-between text-[10px] font-bold">
                <div className="flex items-center gap-2 text-primary">
                  <TrendingUp size={12} />
                  <span className="uppercase tracking-widest">Health_Score</span>
                </div>
                <span className="text-emerald-500 font-mono">98.4 / 100</span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-primary animate-pulse" style={{ width: '98.4%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
