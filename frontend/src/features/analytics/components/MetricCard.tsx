import React from 'react';
import { LucideIcon, ArrowUpRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ApiMetricItem } from '../types';

interface MetricCardProps {
  metric: ApiMetricItem;
  icon: LucideIcon;
  colorClass: string;
}

export function MetricCard({ metric, icon: IconComponent, colorClass }: MetricCardProps) {
  return (
    <div className="panel-industrial p-6 group hover:border-primary/30 transition-all duration-500 relative overflow-hidden">
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
}
