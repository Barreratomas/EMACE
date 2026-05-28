'use client';


import { 
  MetricItem,
  AuditStreamItem,
  DashboardStats,
  AgentStatusList,
  PerformanceChart,
  RecentActivityFeed,
  ApiDashboardAgent,
  ApiDashboardChartPoint,
  DashboardViewResponse
} from '../index';

export function DashboardManager({ 
  dashboardView
}: { dashboardView: DashboardViewResponse }) {

  const { highlights, agents, chart_24h, activity } = dashboardView;

  // Mapear activity a ApiRecentActivityLog de forma pro
  const activityLogs = activity.map((item: AuditStreamItem) => ({
    type: item.level,
    msg: item.agent_name ? `${item.agent_name.toUpperCase()} > ${item.action}` : item.action,
    time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    icon: item.level === 'ERROR' ? 'AlertTriangle' : (item.level === 'OK' ? 'CheckCircle2' : 'Activity'),
    color: item.level === 'ERROR' ? 'text-rose-500' : (item.level === 'OK' ? 'text-cyber-lime' : 'text-primary'),
    bg: item.level === 'ERROR' ? 'bg-rose-500/10' : (item.level === 'OK' ? 'bg-cyber-lime/10' : 'bg-primary/10'),
  }));


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
            Supervisión global del ecosistema
          </p>
        </div>
    
      </div>

      <DashboardStats highlights={highlights} />

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Agent Status & Analytics */}
        <div className="lg:col-span-2 space-y-6">
          <AgentStatusList agents={agents} />
          <PerformanceChart 
            chartData={chart_24h} 
            isOffline={chart_24h.length === 0} 
          />
        </div>

        {/* Sidebar activity feed */}
        <RecentActivityFeed 
          activities={activityLogs} 
          error={null} 
        />
      </div>
    </div>
  );
}
