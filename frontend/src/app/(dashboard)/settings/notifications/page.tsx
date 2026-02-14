'use client';

import { useNotificationCenterStore } from '@/hooks/use-notifications';
import { AlertTriangle, CheckCircle2, Info, ShieldAlert, Check, Trash2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import { cn } from '@/lib/utils';

const iconByType = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  error: ShieldAlert,
};

export default function NotificationCenterPage() {
  const { events, markDone, clearAll } = useNotificationCenterStore();
  const [filter, setFilter] = useState<'all' | 'pending' | 'done'>('all');
  const filtered = useMemo(() => {
    if (filter === 'all') return events;
    return events.filter((e) => e.status === filter);
  }, [events, filter]);

  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display">
            Centro de Notificaciones
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-2 font-medium">
            Historial centralizado y gestión de alertas críticas del ecosistema.
          </p>
        </div>
        <div className="flex bg-background/40 backdrop-blur-md border border-border-ui/50 p-1.5 rounded-2xl shadow-sm gap-1">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-xl text-[11px] font-bold uppercase tracking-wider transition-all ${filter === 'all' ? 'bg-primary text-white shadow-md shadow-primary/20' : 'text-slate-500 hover:text-primary hover:bg-primary/5'}`}
          >
            Todos
          </button>
          <button
            onClick={() => setFilter('pending')}
            className={`px-4 py-2 rounded-xl text-[11px] font-bold uppercase tracking-wider transition-all ${filter === 'pending' ? 'bg-primary text-white shadow-md shadow-primary/20' : 'text-slate-500 hover:text-primary hover:bg-primary/5'}`}
          >
            Pendientes
          </button>
          <button
            onClick={() => setFilter('done')}
            className={`px-4 py-2 rounded-xl text-[11px] font-bold uppercase tracking-wider transition-all ${filter === 'done' ? 'bg-primary text-white shadow-md shadow-primary/20' : 'text-slate-500 hover:text-primary hover:bg-primary/5'}`}
          >
            Completadas
          </button>
          <div className="w-px h-6 bg-border-ui/50 my-auto mx-1" />
          <button
            onClick={clearAll}
            className="px-4 py-2 rounded-xl text-[11px] font-bold uppercase tracking-wider text-rose-500 hover:bg-rose-500/10 transition-all flex items-center gap-2"
          >
            <Trash2 size={14} /> Limpiar
          </button>
        </div>
      </div>

      <div className="panel-industrial p-0 overflow-hidden border-0 shadow-xl">
        <div className="grid grid-cols-4 gap-0 border-b border-border-ui/50 bg-background/50 backdrop-blur-md">
          <div className="p-5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Evento</div>
          <div className="p-5 text-[10px] font-bold text-slate-500 uppercase tracking-widest col-span-2">Detalles del Sistema</div>
          <div className="p-5 text-[10px] font-bold text-slate-500 uppercase tracking-widest text-right">Estado / Acción</div>
        </div>
        <div className="divide-y divide-border-ui/30">
          {filtered.length === 0 ? (
            <div className="p-20 text-center flex flex-col items-center gap-4">
              <div className="w-16 h-16 rounded-3xl bg-slate-100 dark:bg-slate-900 flex items-center justify-center text-slate-300">
                <CheckCircle2 size={32} />
              </div>
              <p className="text-sm font-bold text-slate-400 uppercase tracking-wider">Sin notificaciones relevantes</p>
            </div>
          ) : (
            filtered.map((e) => {
              const Icon = iconByType[e.type];
              return (
                <div key={e.id} className="grid grid-cols-4 gap-0 hover:bg-primary/2 transition-colors group">
                  <div className="p-5 flex items-center gap-4">
                    <div className={cn("p-2.5 rounded-xl backdrop-blur-md border shadow-sm transition-transform group-hover:scale-110", 
                      e.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500' :
                      e.type === 'warning' ? 'bg-amber-500/10 border-amber-500/20 text-amber-500' :
                      e.type === 'error' ? 'bg-rose-500/10 border-rose-500/20 text-rose-500' : 'bg-slate-500/10 border-slate-500/20 text-slate-500'
                    )}>
                      <Icon size={16} />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-tight leading-none mb-1.5">{e.title || 'Evento'}</div>
                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                        <span className="w-1 h-1 rounded-full bg-slate-300" />
                        {e.time}
                      </div>
                    </div>
                  </div>
                  <div className="p-5 col-span-2 flex items-center">
                    <div className="text-xs font-medium text-slate-600 dark:text-slate-400 leading-relaxed">{e.message}</div>
                  </div>
                  <div className="p-5 flex items-center justify-end gap-4">
                    <span className={cn("text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-lg border", 
                      e.status === 'pending' ? 'bg-primary/5 text-primary border-primary/20' : 'bg-slate-50 text-slate-400 border-slate-200 dark:bg-slate-800/50 dark:border-slate-700'
                    )}>
                      {e.status === 'pending' ? 'Pendiente' : 'Completada'}
                    </span>
                    {e.status === 'pending' && (
                      <button
                        onClick={() => markDone(e.id)}
                        className="p-2 rounded-xl bg-background/50 border border-border-ui/50 text-slate-400 hover:text-primary hover:border-primary/50 hover:shadow-lg transition-all"
                        title="Marcar como resuelto"
                      >
                        <Check size={18} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
