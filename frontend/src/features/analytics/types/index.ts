export type ApiMetricItem = {
  key: string;
  label: string;
  value: string;
  trend?: string | null;
};

export type ApiAuditEvent = {
  timestamp: string;
  level: string;
  agent_name: string;
  action: string;
  details: string;
};
