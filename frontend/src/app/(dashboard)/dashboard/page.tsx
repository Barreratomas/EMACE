'use client';

import { useEffect, useState, useSyncExternalStore } from 'react';

import { 
  Users, 
  Activity, 
  Zap, 
  Shield, 
  MessageSquare,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Bell
} from 'lucide-react';
import { requestPermission, getPermission, sendNotification } from '@/lib/notifications';
import { cn } from '@/lib/utils';
import { IndustrialProgress, CircularScanner } from '@/components/ui/IndustrialProgress';
import api from '@/lib/api';

const subscribe = () => () => {};
const getSnapshot = () => true;
const getServerSnapshot = () => false;

type ApiDashboardStat = {
  key: string;
  label: string;
  value: string;
  trend?: string | null;
  trend_direction?: 'up' | 'down' | 'stable' | null;
};

type ApiDashboardAgent = {
  name: string;
  status: string;
  load: number;
  activity?: string | null;
  type?: string | null;
};

type ApiDashboardChartPoint = {
  timestamp: string;
  total_events: number;
};

type ApiRecentActivityLog = {
  type: string;
  msg: string;
  time: string;
  icon: string;
  color: string;
  bg: string;
};

type DashboardOverviewResponse = {
  stats: ApiDashboardStat[];
  agents: ApiDashboardAgent[];
  chart_24h: ApiDashboardChartPoint[];
};

export default function DashboardPage() {
  const mounted = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const [overview, setOverview] = useState<DashboardOverviewResponse | null>(null);
  const [overviewError, setOverviewError] = useState<string | null>(null);
  const [recentActivity, setRecentActivity] = useState<ApiRecentActivityLog[] | null>(null);
  const [recentActivityError, setRecentActivityError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const fetchOverview = async () => {
      try {
        const response = await api.get<DashboardOverviewResponse>('/vendors/me/dashboard/overview');
        if (!cancelled) {
          setOverview(response.data);
          setOverviewError(null);
        }
      } catch (error) {
        if (!cancelled) {
          setOverviewError('No se pudieron cargar las métricas del panel');
        }
      }
    };
    fetchOverview();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const fetchRecentActivity = async () => {
      try {
        const response = await api.get<ApiRecentActivityLog[]>('/vendors/me/dashboard/recent-activity');
        if (!cancelled) {
          setRecentActivity(response.data);
          setRecentActivityError(null);
        }
      } catch {
        if (!cancelled) {
          setRecentActivity([]);
          setRecentActivityError('No se pudieron cargar los registros de actividad');
        }
      }
    };
    fetchRecentActivity();
    return () => {
      cancelled = true;
    };
  }, []);

  const getActivityIcon = (icon: string) => {
    const normalized = icon.toLowerCase();
    switch (normalized) {
      case 'messagesquare':
      case 'message_square':
        return MessageSquare;
      case 'alerttriangle':
      case 'alert_triangle':
        return AlertTriangle;
      case 'checkcircle2':
      case 'check_circle_2':
        return CheckCircle2;
      case 'users':
        return Users;
      case 'activity':
        return Activity;
      default:
        return MessageSquare;
    }
  };


  const handleEnablePush = async () => {
    const result = await requestPermission();
    if (result === 'granted') {
      sendNotification('EMACE // Notificaciones activadas', {
        body: 'Recibirás alertas críticas del ecosistema.',
      });
    }
  };
  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 relative">
        <div className="relative group">
          <div className="absolute -left-4 top-0 bottom-0 w-0.5 bg-primary/20 group-hover:bg-primary transition-colors" />
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] font-bold text-primary terminal-text tracking-[0.3em] uppercase opacity-60">System_Control_Panel</span>
            <div className="h-px w-8 bg-primary/20" />
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display uppercase">
            Panel de Control
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-[11px] mt-2 font-bold uppercase tracking-widest terminal-text opacity-70">
            Supervisión global del ecosistema // rendimiento_agentes_v2.4
          </p>
        </div>
        <div className="flex gap-3 items-center">
            <CircularScanner size={32} className="opacity-60" />
            <div className="bg-black/40 border border-white/5 p-2.5 px-5 rounded-none flex items-center gap-3 shadow-sm relative overflow-hidden group">
            <div className="absolute inset-0 bg-linear-to-r from-transparent via-primary/5 to-transparent -translate-x-full group-hover:animate-scan-horizontal pointer-events-none" />
            <div className="w-2 h-2 rounded-none bg-cyber-lime shadow-[0_0_8px_rgba(50,255,126,0.5)] animate-pulse" />
            <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest terminal-text">ESTADO: OPERATIVO</span>
          </div>
          <button
            onClick={handleEnablePush}
            className="bg-black/40 border border-white/5 p-2.5 px-5 rounded-none flex items-center gap-2 text-[10px] font-bold text-slate-500 hover:text-primary hover:border-primary/30 uppercase tracking-widest transition-all shadow-sm group terminal-text relative overflow-hidden"
            title={`Estado: ${mounted ? getPermission().toUpperCase() : 'DENIED'}`}
          >
            <div className="absolute inset-0 bg-linear-to-b from-transparent via-primary/5 to-transparent -translate-y-full group-hover:animate-scan pointer-events-none" />
            <Bell size={14} className={cn("transition-colors", mounted && getPermission() === 'granted' ? 'text-primary' : 'text-slate-500 group-hover:text-primary')} />
            {mounted && getPermission() === 'granted' ? 'ALERTAS_ON' : 'ACTIVAR_ALERTAS'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { key: 'agents_active', label: 'Agentes Activos', value: '--', icon: Users, color: 'text-primary', bg: 'bg-primary/10', glow: 'shadow-primary/5', trend: 'N/A', trendColor: 'text-slate-500' },
          { key: 'operations_24h', label: 'Operaciones 24h', value: '--', icon: Activity, color: 'text-primary', bg: 'bg-primary/10', glow: 'shadow-primary/5', trend: 'N/A', trendColor: 'text-slate-500' },
          { key: 'latency_avg', label: 'Latencia Media', value: '--', icon: Zap, color: 'text-safety-orange', bg: 'bg-safety-orange/10', glow: 'shadow-safety-orange/5', trend: 'N/A', trendColor: 'text-slate-500' },
          { key: 'integrity', label: 'Integridad', value: '--', icon: Shield, color: 'text-cyber-lime', bg: 'bg-cyber-lime/10', glow: 'shadow-cyber-lime/5', trend: 'N/A', trendColor: 'text-slate-500' },
        ].map((baseStat, i) => {
          const apiStat = overview?.stats?.find((s) => s.key === baseStat.key);
          const trendDirection = apiStat?.trend_direction;
          const trendColor =
            trendDirection === 'up'
              ? 'text-cyber-lime'
              : trendDirection === 'down'
              ? 'text-rose-500'
              : baseStat.trendColor;
          const value = apiStat?.value ?? baseStat.value;
          const label = apiStat?.label ?? baseStat.label;
          const trend = apiStat?.trend ?? baseStat.trend;
          const mergedStat = { ...baseStat, value, label, trend, trendColor };
          return (
          <div key={i} className={cn("panel-industrial p-5 group relative overflow-hidden hover:border-primary/30 transition-all duration-300 rounded-none border-white/5", mergedStat.glow)}>
            <div className="absolute inset-0 bg-linear-to-b from-transparent via-primary/5 to-transparent -translate-y-full group-hover:animate-scan pointer-events-none" />
            
            <div className="flex justify-between items-start mb-6 relative z-10">
              <div className={cn("p-2.5 border border-white/10 bg-black/40", mergedStat.color)}>
                <mergedStat.icon size={18} />
              </div>
              <span className={cn("text-[9px] font-bold uppercase tracking-[0.2em] px-2 py-0.5 border border-white/5 bg-black/20 terminal-text", mergedStat.trendColor)}>{mergedStat.trend}</span>
            </div>
            
            <div className="relative z-10">
              <div className="text-2xl font-black tracking-tighter mb-1 terminal-text">{mergedStat.value}</div>
              <div className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.25em] terminal-text">{mergedStat.label}</div>
            </div>

            <div className="absolute bottom-0 right-0 w-8 h-8 opacity-[0.03] group-hover:opacity-[0.1] transition-opacity">
              <mergedStat.icon size={32} />
            </div>
          </div>
        );})}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Agent Status & Analytics */}
        <div className="lg:col-span-2 space-y-6">
          {/* Agent Status */}
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
              {overview?.agents && overview.agents.length > 0 ? (
                overview.agents.map((agent, i) => (
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
                      <div className={cn("text-[9px] font-bold uppercase tracking-[0.2em] terminal-text", 
                        agent.status === 'Online' ? 'text-cyber-lime' : 
                        agent.status === 'Busy' ? 'text-safety-orange' : 'text-slate-500'
                      )}>
                        {agent.status}
                      </div>
                      <div className="text-[8px] font-bold text-slate-600 mt-1 uppercase terminal-text tracking-widest">UPTIME: --</div>
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
                    <div className="text-[8px] font-bold text-slate-600 mt-1 uppercase terminal-text tracking-widest">UPTIME: --</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Analytics Chart Mockup */}
          <div className="space-y-4">
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-3">
                <div className="w-1 h-4 bg-primary" />
                <h2 className="text-sm font-bold uppercase tracking-[0.2em] terminal-text">Rendimiento (24h)</h2>
              </div>
              <div className="flex gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-primary" />
                  <span className="text-[8px] font-bold text-slate-500 uppercase tracking-widest terminal-text">REQUESTS</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-cyber-lime" />
                  <span className="text-[8px] font-bold text-slate-500 uppercase tracking-widest terminal-text">SUCCESS</span>
                </div>
              </div>
            </div>
            
              <div className="panel-industrial p-6 h-72 relative flex flex-col justify-between rounded-none border-white/5 overflow-hidden group">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,rgba(0,255,255,0.05),transparent_70%)]" />
              
              <div className="absolute inset-0 p-6 flex flex-col justify-between pointer-events-none opacity-20">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="w-full h-px bg-primary/20" />
                ))}
              </div>
              
              <div className="relative flex-1 mt-4">
                <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 500 200">
                  <defs>
                    <linearGradient id="gradient-primary" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.2" />
                      <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  {(() => {
                    const fallback = [150, 120, 130, 80, 100, 40, 60, 20, 50, 30, 40];
                    const apiPoints = overview?.chart_24h || [];
                    const values = apiPoints.length ? apiPoints.map((p) => p.total_events) : fallback.map((_, i) => fallback[i]);
                    const length = values.length || fallback.length;
                    const maxValue = values.reduce((max, v) => (v > max ? v : max), 0) || 1;
                    const coords = Array.from({ length }, (_, i) => {
                      const x = (i / Math.max(length - 1, 1)) * 500;
                      const baseY = apiPoints.length ? values[i] : fallback[i] || fallback[fallback.length - 1];
                      const normalized = baseY / maxValue;
                      const y = 180 - normalized * 140;
                      return { x, y };
                    });
                    const areaPath = coords
                      .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
                      .join(' ');
                    const linePath = areaPath;
                    return (
                      <>
                        <path
                          d={`${areaPath} L 500 200 L 0 200 Z`}
                          fill="url(#gradient-primary)"
                          className="transition-all duration-1000"
                        />
                        <path
                          d={linePath}
                          fill="none"
                          stroke="var(--primary)"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          className="opacity-80"
                        />
                        {coords.map((point, index) => (
                          <circle
                            key={index}
                            cx={point.x}
                            cy={point.y}
                            r="2"
                            fill="var(--primary)"
                            className="animate-pulse"
                            style={{ animationDelay: `${index * 100}ms` }}
                          />
                        ))}
                      </>
                    );
                  })()}
                </svg>
              </div>

              <div className="flex justify-between items-center mt-4 border-t border-white/5 pt-4">
                <div className="flex gap-4">
                  <div className="text-[8px] font-bold text-slate-500 terminal-text">00:00</div>
                  <div className="text-[8px] font-bold text-slate-500 terminal-text">06:00</div>
                  <div className="text-[8px] font-bold text-slate-500 terminal-text">12:00</div>
                  <div className="text-[8px] font-bold text-slate-500 terminal-text">18:00</div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-[8px] font-bold text-slate-500 terminal-text">
                    {overview?.chart_24h
                      ? `EVENTOS_24H: ${overview.chart_24h.reduce((acc, p) => acc + p.total_events, 0)}`
                      : 'EVENTOS_24H: 0'}
                  </div>
                  <div className="text-[8px] font-bold text-primary terminal-text animate-pulse">
                    {overviewError ? 'STREAM_OFFLINE' : 'LIVE_STREAM_ACTIVE'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar activity feed */}
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-3">
              <div className="w-1 h-4 bg-primary" />
              <h2 className="text-sm font-bold uppercase tracking-[0.2em] terminal-text">Actividad Reciente</h2>
            </div>
            <div className="p-2 border border-white/5 bg-black/40 text-primary animate-pulse">
              <Activity size={14} />
            </div>
          </div>

          <div className="panel-industrial p-0 overflow-hidden rounded-none border-white/5 group/feed relative">
            <div className="absolute inset-0 bg-linear-to-b from-primary/2 to-transparent pointer-events-none" />
            <div className="max-h-620px overflow-y-auto custom-scrollbar">
              <div className="divide-y divide-white/5">
                {recentActivityError ? (
                  <div className="p-4 text-center">
                    <span className="text-[10px] font-bold text-rose-500 terminal-text uppercase tracking-wider">
                      {recentActivityError}
                    </span>
                  </div>
                ) : !recentActivity ? (
                  <div className="p-4 flex items-center justify-center">
                    <CircularScanner size={24} className="opacity-60" />
                  </div>
                ) : recentActivity.length === 0 ? (
                  <div className="p-4 text-center">
                    <span className="text-[10px] font-bold text-slate-500 terminal-text uppercase tracking-wider">
                      SIN_REGISTROS_DE_ACTIVIDAD
                    </span>
                  </div>
                ) : (
                  recentActivity.map((log, i) => {
                    const Icon = getActivityIcon(log.icon);
                    return (
                      <div key={i} className="p-4 hover:bg-white/5 transition-all flex gap-4 group relative overflow-hidden">
                        <div className="absolute inset-y-0 left-0 w-0.5 bg-transparent group-hover:bg-primary transition-colors" />
                        <div
                          className={cn(
                            "mt-1 p-2 border border-white/10 bg-black/40 transition-all duration-300 group-hover:border-primary/30",
                            log.color,
                            log.bg
                          )}
                        >
                          <Icon size={14} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-start mb-1">
                            <span className={cn("text-[10px] font-bold terminal-text truncate uppercase tracking-wider", log.color)}>
                              {log.msg}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[8px] font-bold text-slate-500 terminal-text tracking-widest">{log.time}</span>
                            <span className="text-[8px] text-slate-700 font-bold terminal-text tracking-widest">{"//"}</span>
                            <span className="text-[8px] font-bold text-slate-600 terminal-text tracking-widest">LOG_ID_{8291 + i}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
            <div className="p-3 bg-black/60 border-t border-white/5 flex justify-center">
              <button className="text-[9px] font-bold text-slate-500 hover:text-primary uppercase tracking-[0.3em] terminal-text transition-colors">
                VIEW_ALL_SYSTEM_LOGS
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
