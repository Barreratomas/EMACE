import React from 'react';
import { Package } from 'lucide-react';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { Button } from '@/components/ui/Button';

export function InventoryTab() {
  return (
    <div className="panel-industrial p-8">
      <SectionHeader
        className="sm:flex-row sm:items-center sm:justify-between mb-8 pb-4 border-b border-white/5"
        rightClassName="w-full sm:w-auto justify-start sm:justify-end"
        left={
          <div className="flex items-center gap-3">
            <Package className="text-amber-500" size={20} />
            <h3 className="text-lg font-bold tracking-tight uppercase">
              Stock_Levels_By_Category
            </h3>
          </div>
        }
        right={
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-[9px] border-white/10"
          >
            VIEW_FULL_REPORT
          </Button>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-12 pt-4">
        <div className="space-y-6">
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">
            Categoría_Ranking
          </h4>
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            SIN_DATOS_DE_CATEGORIAS
          </div>
        </div>

        <div className="flex flex-col items-center justify-center border-l border-white/5 pl-8">
          <div className="relative w-40 h-40">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="15" fill="transparent" className="text-white/5" />
              <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="15" fill="transparent" strokeDasharray="439.8" strokeDashoffset="110" className="text-primary" />
              <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="15" fill="transparent" strokeDasharray="439.8" strokeDashoffset="300" className="text-cyber-lime" />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold">--</span>
              <span className="text-[8px] font-bold text-slate-500 uppercase">Items_Total</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 mt-6 w-full text-[9px] font-bold uppercase tracking-tighter">
            <div className="flex items-center gap-2"><div className="w-2 h-2 bg-primary rounded-full" /> In Stock</div>
            <div className="flex items-center gap-2"><div className="w-2 h-2 bg-cyber-lime rounded-full" /> Allocated</div>
            <div className="flex items-center gap-2"><div className="w-2 h-2 bg-white/10 rounded-full" /> Out of Stock</div>
            <div className="flex items-center gap-2"><div className="w-2 h-2 bg-blue-500 rounded-full" /> Transit</div>
          </div>
        </div>
      </div>
    </div>
  );
}
