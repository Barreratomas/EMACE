import React from 'react';
import { Cpu } from 'lucide-react';
import { SectionHeader } from '@/components/ui/SectionHeader';

export function SystemTab() {
  return (
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
  );
}
