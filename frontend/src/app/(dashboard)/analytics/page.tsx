'use client';

import React, { useEffect, useState, useSyncExternalStore } from 'react';
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
  Search,
} from 'lucide-react';
import { IndustrialProgress } from '@/components/ui/IndustrialProgress';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { SectionHeader } from '@/components/ui/SectionHeader';
import api from '@/lib/api';

// Custom hook for safe mounting check without useEffect setState
function useHasMounted() {
  return useSyncExternalStore(
    () => () => {}, // subscribe function (no-op)
    () => true,     // getSnapshot on client
    () => false     // getServerSnapshot on server
  );
}

type ApiMetricItem = {
  key: string;
  label: string;
  value: string;
  trend?: string | null;
};

type ApiAuditEvent = {
  timestamp: string;
  level: string;
  category: string;
  message: string;
};

export default function AnalyticsPage() {
  const hasMounted = useHasMounted();
  const [activeTab, setActiveTab] = useState<'system' | 'inventory' | 'business'>('system');
  const [systemMetrics, setSystemMetrics] = useState<ApiMetricItem[]>([]);
  const [inventoryMetrics, setInventoryMetrics] = useState<ApiMetricItem[]>([]);
  const [businessMetrics, setBusinessMetrics] = useState<ApiMetricItem[]>([]);
  const [logs, setLogs] = useState<ApiAuditEvent[]>([]);
  const [logFilter, setLogFilter] = useState('');
  const [metricsError, setMetricsError] = useState<string | null>(null);
  const [logsError, setLogsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const fetchMetricsAndLogs = async () => {
      try {
        const [
          systemRes,
          inventoryRes,
          businessRes,
          logsRes,
        ] = await Promise.all([
          api.get<ApiMetricItem[]>('/vendors/me/metrics/system'),
          api.get<ApiMetricItem[]>('/vendors/me/metrics/inventory'),
          api.get<ApiMetricItem[]>('/vendors/me/metrics/business'),
          api.get<ApiAuditEvent[]>('/vendors/me/audit/stream', { params: { limit: 100 } }),
        ]);
        if (cancelled) return;
        setSystemMetrics(systemRes.data || []);
        setInventoryMetrics(inventoryRes.data || []);
        setBusinessMetrics(businessRes.data || []);
        setLogs(logsRes.data || []);
        setMetricsError(null);
        setLogsError(null);
      } catch {
        if (cancelled) return;
        setMetricsError('No se pudieron cargar las métricas');
        setLogsError('No se pudo cargar el stream de eventos');
        setSystemMetrics([]);
        setInventoryMetrics([]);
        setBusinessMetrics([]);
        setLogs([]);
      }
    };
    fetchMetricsAndLogs();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!hasMounted) return null;

  const metricsForActiveTab =
    activeTab === 'system'
      ? systemMetrics
      : activeTab === 'inventory'
      ? inventoryMetrics
      : businessMetrics;

  const metricIconsForTab =
    activeTab === 'system'
      ? [Clock, ShieldCheck, Zap, Activity]
      : activeTab === 'inventory'
      ? [Package, DollarSign, AlertCircle, RefreshCw]
      : [DollarSign, ShoppingCart, Users, TrendingUp];

  const metricColorsForTab =
    activeTab === 'system'
      ? ['text-cyber-lime', 'text-emerald-500', 'text-primary', 'text-blue-500']
      : activeTab === 'inventory'
      ? ['text-amber-500', 'text-emerald-500', 'text-rose-500', 'text-blue-400']
      : ['text-emerald-500', 'text-primary', 'text-blue-500', 'text-cyber-lime'];

  const filteredLogs = logsFilter(logs, logFilter);

  function logsFilter(events: ApiAuditEvent[], term: string) {
    if (!term.trim()) return events;
    const lower = term.toLowerCase();
    return events.filter(event => {
      return (
        event.category.toLowerCase().includes(lower) ||
        event.level.toLowerCase().includes(lower) ||
        event.message.toLowerCase().includes(lower)
      );
    });
  }

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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricsError && metricsForActiveTab.length === 0 && (
          <div className="panel-industrial p-4 text-[10px] font-bold text-rose-500 terminal-text uppercase tracking-widest">
            {metricsError}
          </div>
        )}
        {!metricsError &&
          metricsForActiveTab.map((metric, index) => {
            const IconComponent = metricIconsForTab[index % metricIconsForTab.length];
            const colorClass = metricColorsForTab[index % metricColorsForTab.length];
            return (
              <div
                key={metric.key}
                className="panel-industrial p-6 group hover:border-primary/30 transition-all duration-500 relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-1 opacity-10">
                  <IconComponent size={60} />
                </div>
                <div className="flex justify-between items-start mb-4 relative z-10">
                  <div className={cn('p-2 bg-white/5 rounded-lg', colorClass)}>
                    <IconComponent size={20} />
                  </div>
                  <div className="flex items-center gap-1 text-[10px] font-mono text-emerald-500">
                    <ArrowUpRight size={10} /> {metric.trend || 'N/A'}
                  </div>
                </div>
                <div className="space-y-1 relative z-10">
                  <div className="text-3xl font-bold font-display tracking-tight leading-none mb-1">
                    {metric.value}
                  </div>
                  <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-800" />
                    {metric.label}
                  </div>
                </div>
              </div>
            );
          })}
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

              <div className="space-y-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                SIN_DATOS_DE_DISTRIBUCION_HISTORICA
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
                  <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">
                    Categoría_Ranking
                  </h4>
                  <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    SIN_DATOS_DE_CATEGORIAS
                  </div>
                </div>

                <div className="flex flex-col items-center justify-center border-l border-white/5 pl-8">
                  <div className="relative w-40 h-40">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="15" fill="transparent" className="text-white/5" />
                      <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="15" fill="transparent" strokeDasharray="439.8" strokeDashoffset="110" className="text-primary" />
                      <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="15" fill="transparent" strokeDasharray="439.8" strokeDashoffset="300" className="text-cyber-lime" />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-2xl font-bold">--</span>
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

              <div className="h-64 flex items-center justify-center px-4 relative">
                {/* Grid Lines */}
                <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-5 px-4">
                  {[1,2,3,4,5].map(i => <div key={i} className="w-full h-px bg-white" />)}
                </div>
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                  SIN_SERIE_DE_REVENUE_REAL
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="panel-industrial p-6 space-y-4">
              <div className="flex items-center gap-2 mb-2">
                <Network className="text-blue-500" size={16} />
                <h4 className="text-xs font-bold uppercase tracking-widest">Latencia de Red</h4>
              </div>
              <div className="h-24 flex items-center justify-center px-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                SIN_DATOS_DE_LATENCIA
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
                    <circle
                      cx="40"
                      cy="40"
                      r="36"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="transparent"
                      className="text-white/5"
                    />
                    <circle
                      cx="40"
                      cy="40"
                      r="36"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="transparent"
                      strokeDasharray="226.2"
                      strokeDashoffset="226.2"
                      className="text-cyber-lime"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center text-xs font-bold">--%</div>
                </div>
              </div>
              <div className="text-center text-[9px] font-mono text-slate-500 uppercase tracking-tighter">
                USO_NO_DISPONIBLE
              </div>
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
                  value={logFilter}
                  onChange={(e) => setLogFilter(e.target.value)}
                />
              </div>
            </div>
            
            <div className="flex-1 p-6 space-y-4 font-mono text-[10px] overflow-y-auto max-h-150 scrollbar-thin scrollbar-thumb-white/10">
              {logsError && filteredLogs.length === 0 && (
                <div className="text-rose-500 text-[10px] font-bold uppercase tracking-widest">
                  {logsError}
                </div>
              )}
              {!logsError && filteredLogs.length === 0 && (
                <div className="text-slate-500 text-[10px] font-bold uppercase tracking-widest">
                  SIN_EVENTOS
                </div>
              )}
              {!logsError &&
                filteredLogs.map((log, i) => {
                  const ts = new Date(log.timestamp);
                  const hh = String(ts.getHours()).padStart(2, '0');
                  const mm = String(ts.getMinutes()).padStart(2, '0');
                  const ss = String(ts.getSeconds()).padStart(2, '0');
                  const time = `${hh}:${mm}:${ss}`;
                  return (
                    <div
                      key={`${log.timestamp}-${i}`}
                      className="group flex flex-col gap-1 border-b border-white/5 pb-3 last:border-0 hover:bg-white/2 transition-colors rounded p-1"
                    >
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">[{time}]</span>
                        <span className="text-[8px] px-1.5 py-0.5 rounded bg-white/5 text-slate-400 font-bold uppercase">
                          {log.category}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <span
                          className={cn(
                            'font-bold',
                            log.level === 'ERROR'
                              ? 'text-rose-500'
                              : log.level === 'SUCCESS'
                              ? 'text-emerald-500'
                              : log.level === 'WARN'
                              ? 'text-amber-500'
                              : 'text-blue-400'
                          )}
                        >
                          {log.level}:
                        </span>
                        <span className="text-slate-300 group-hover:text-white transition-colors">
                          {log.message}
                        </span>
                      </div>
                    </div>
                  );
                })}
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
