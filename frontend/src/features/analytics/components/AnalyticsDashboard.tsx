'use client';

import React, { useState, useSyncExternalStore } from 'react';
import {
  Activity,
  Zap,
  BarChart3,
  Clock,
  ShieldCheck,
  AlertCircle,
  Cpu,
  Network,
  Database,
  Package,
  DollarSign,
  ShoppingCart,
  Users,
  TrendingUp,
  Download,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { ApiMetricItem, ApiAuditEvent } from '../types';
import { MetricCard } from './MetricCard';
import { EventStream } from './EventStream';
import { SystemTab } from './SystemTab';
import { InventoryTab } from './InventoryTab';
import { BusinessTab } from './BusinessTab';

// Custom hook for safe mounting check without useEffect setState
function useHasMounted() {
  return useSyncExternalStore(
    () => () => {}, // subscribe function (no-op)
    () => true,     // getSnapshot on client
    () => false     // getServerSnapshot on server
  );
}

interface AnalyticsDashboardProps {
  initialData: {
    systemMetrics: ApiMetricItem[];
    inventoryMetrics: ApiMetricItem[];
    businessMetrics: ApiMetricItem[];
    auditLogs: ApiAuditEvent[];
  };
}

export default function AnalyticsDashboard({
  initialData,
}: AnalyticsDashboardProps) {
  const { 
    systemMetrics: initialSystemMetrics, 
    inventoryMetrics: initialInventoryMetrics, 
    businessMetrics: initialBusinessMetrics, 
    auditLogs: initialLogs 
  } = initialData;

  const hasMounted = useHasMounted();
  const [activeTab, setActiveTab] = useState<'system' | 'inventory' | 'business'>('system');
  const [logFilter, setLogFilter] = useState('');

  if (!hasMounted) return null;

  const metricsForActiveTab =
    activeTab === 'system'
      ? initialSystemMetrics
      : activeTab === 'inventory'
      ? initialInventoryMetrics
      : initialBusinessMetrics;

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

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-12">
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
        {metricsForActiveTab.map((metric, index) => (
          <MetricCard
            key={metric.key}
            metric={metric}
            icon={metricIconsForTab[index % metricIconsForTab.length]}
            colorClass={metricColorsForTab[index % metricColorsForTab.length]}
          />
        ))}
        {metricsForActiveTab.length === 0 && (
          <div className="panel-industrial p-4 text-[10px] font-bold text-rose-500 terminal-text uppercase tracking-widest">
            No se pudieron cargar las métricas
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {activeTab === 'system' && <SystemTab />}
          {activeTab === 'inventory' && <InventoryTab />}
          {activeTab === 'business' && <BusinessTab />}

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

        <div className="lg:col-span-1">
          <EventStream
            logs={initialLogs}
            logFilter={logFilter}
            setLogFilter={setLogFilter}
            logsError={null}
          />
        </div>
      </div>
    </div>
  );
}
