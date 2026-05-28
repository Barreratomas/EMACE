export interface MetricItem {
  key: string;
  value: string;
  trend?: string | null;
}

export interface AuditStreamItem {
  timestamp: string;
  level: 'ERROR' | 'WARN' | 'OK' | 'INFO';
  agent_name: string;
  action: string;
  details: any;
}

// Mantener los tipos anteriores por compatibilidad si es necesario, 
// o refactorizar para usar los nuevos de Analytics.
export type ApiDashboardStat = {
  key: string;
  label: string;
  value: string;
  trend?: string | null;
  trend_direction?: 'up' | 'down' | 'stable' | null;
};

export type ApiDashboardAgent = {
  name: string;
  status: string;
  load: number;
  activity?: string | null;
  type?: string | null;
};

export type ApiDashboardChartPoint = {
  timestamp: string;
  total_events: number;
};

export type ApiRecentActivityLog = {
  type: string;
  msg: string;
  time: string;
  icon: string;
  color: string;
  bg: string;
};

export interface DashboardViewResponse {
  highlights: MetricItem[];
  agents: ApiDashboardAgent[];
  chart_24h: ApiDashboardChartPoint[];
  activity: AuditStreamItem[];
}
