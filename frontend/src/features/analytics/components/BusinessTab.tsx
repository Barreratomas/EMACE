import React from 'react';
import { TrendingUp } from 'lucide-react';
import { SectionHeader } from '@/components/ui/SectionHeader';

export function BusinessTab() {
  return (
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
  );
}
