'use server'

import { apiRequest } from '@/lib/server-api';
import { 
  MetricItem, 
  AuditStreamItem,
  ApiDashboardAgent,
  ApiDashboardChartPoint,
  ApiRecentActivityLog,
  DashboardViewResponse
} from '../types';

export async function getDashboardView(): Promise<DashboardViewResponse | null> {
  try {
    return await apiRequest<DashboardViewResponse>('/vendors/me/dashboard/view', { cache: 'no-store' });
  } catch (error) {
    console.error('Error fetching dashboard view:', error);
    return null;
  }
}

// Estos se mantienen por si se necesitan métricas individuales en otros lugares
export async function getSystemMetrics(): Promise<MetricItem[]> {
  try {
    return await apiRequest<MetricItem[]>('/vendors/me/metrics/system', { cache: 'no-store' });
  } catch (error) {
    console.error('Error fetching system metrics:', error);
    return [];
  }
}

export async function getInventoryMetrics(): Promise<MetricItem[]> {
  try {
    return await apiRequest<MetricItem[]>('/vendors/me/metrics/inventory', { cache: 'no-store' });
  } catch (error) {
    console.error('Error fetching inventory metrics:', error);
    return [];
  }
}

export async function getBusinessMetrics(): Promise<MetricItem[]> {
  try {
    return await apiRequest<MetricItem[]>('/vendors/me/metrics/business', { cache: 'no-store' });
  } catch (error) {
    console.error('Error fetching business metrics:', error);
    return [];
  }
}

