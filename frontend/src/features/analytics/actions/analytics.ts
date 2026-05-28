'use server'

import { apiRequest } from '@/lib/server-api';
import { ApiMetricItem, ApiAuditEvent } from '../types';

export async function getSystemMetrics(): Promise<ApiMetricItem[]> {
  try {
    return await apiRequest<ApiMetricItem[]>('/vendors/me/metrics/system', {
      cache: 'no-store',
    });
  } catch (error) {
    console.error('getSystemMetrics error:', error);
    return [];
  }
}

export async function getInventoryMetrics(): Promise<ApiMetricItem[]> {
  try {
    return await apiRequest<ApiMetricItem[]>('/vendors/me/metrics/inventory', {
      cache: 'no-store',
    });
  } catch (error) {
    console.error('getInventoryMetrics error:', error);
    return [];
  }
}

export async function getBusinessMetrics(): Promise<ApiMetricItem[]> {
  try {
    return await apiRequest<ApiMetricItem[]>('/vendors/me/metrics/business', {
      cache: 'no-store',
    });
  } catch (error) {
    console.error('getBusinessMetrics error:', error);
    return [];
  }
}


export async function getAuditLogs(limit: number = 100): Promise<ApiAuditEvent[]> {
  try {
    return await apiRequest<ApiAuditEvent[]>(`/vendors/me/audit/stream?limit=${limit}`, {
      cache: 'no-store',
    });
  } catch (error) {
    console.error('getAuditLogs error:', error);
    return [];
  }
}

// Grouped data fetching for the analytics overview
export async function getAnalyticsOverview() {
  const [
    systemMetrics,
    inventoryMetrics,
    businessMetrics,
    auditLogs
  ] = await Promise.all([
    getSystemMetrics(),
    getInventoryMetrics(),
    getBusinessMetrics(),
    getAuditLogs(100)
  ]);

  return {
    systemMetrics,
    inventoryMetrics,
    businessMetrics,
    auditLogs
  };
}
