'use client';

import React from 'react';
import { Activity, Search, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ApiAuditEvent } from '../types';

interface EventStreamProps {
  logs: ApiAuditEvent[];
  logFilter: string;
  setLogFilter: (filter: string) => void;
  logsError: string | null;
}

export function EventStream({ logs, logFilter, setLogFilter, logsError }: EventStreamProps) {
  const filteredLogs = logsFilterFunc(logs, logFilter);

  function logsFilterFunc(events: ApiAuditEvent[], term: string) {
    if (!events || !Array.isArray(events)) {
      console.error('[EventStream] events is not an array:', events);
      return [];
    }
    if (!term.trim()) return events;
    const lower = term.toLowerCase();
    return events.filter(event => {
      return (
        event.action.toLowerCase().includes(lower) ||
        event.agent_name.toLowerCase().includes(lower) ||
        event.level.toLowerCase().includes(lower) ||
        event.details.toLowerCase().includes(lower)
      );
    });
  }

  return (
    <div className="panel-industrial h-full flex flex-col">
      <div className="p-6 border-b border-white/5 bg-white/2">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold uppercase tracking-[0.2em] flex items-center gap-2">
            <Activity size={14} className="text-primary" /> Event_Stream
          </h3>
          <div className="flex gap-1">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-[9px] font-bold text-emerald-500 font-mono">LIVE</span>
          </div>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" size={12} />
          <input 
            type="text" 
            placeholder="FILTER_LOGS..." 
            className="w-full bg-black/40 border border-white/10 rounded-md py-1.5 pl-8 pr-3 text-[10px] font-mono focus:outline-none focus:border-primary/50 transition-colors"
            value={logFilter}
            onChange={(e) => setLogFilter(e.target.value)}
          />
        </div>
      </div>
      
      <div className="flex-1 p-6 space-y-4 font-mono text-[10px] overflow-y-auto max-h-[600px] scrollbar-thin scrollbar-thumb-white/10">
        {logsError && filteredLogs.length === 0 && (
          <div className="text-rose-500 text-[10px] font-bold uppercase tracking-widest">
            {logsError}
          </div>
        )}
        {!logsError && filteredLogs.length === 0 && (
          <div className="text-slate-500 text-[10px] font-bold uppercase tracking-widest">
            SIN_EVENTOS
          </div>
        )}
        {!logsError &&
          filteredLogs.map((log, i) => {
            const ts = new Date(log.timestamp);
            const hh = String(ts.getHours()).padStart(2, '0');
            const mm = String(ts.getMinutes()).padStart(2, '0');
            const ss = String(ts.getSeconds()).padStart(2, '0');
            const time = `${hh}:${mm}:${ss}`;
            return (
              <div
                key={`${log.timestamp}-${i}`}
                className="group flex flex-col gap-1 border-b border-white/5 pb-3 last:border-0 hover:bg-white/2 transition-colors rounded p-1"
              >
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">[{time}]</span>
                  <div className="flex gap-1">
                    <span className="text-[8px] px-1.5 py-0.5 rounded bg-white/5 text-slate-500 font-mono uppercase">
                      {log.agent_name}
                    </span>
                    <span className="text-[8px] px-1.5 py-0.5 rounded bg-primary/10 text-primary font-bold uppercase">
                      {log.action}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <span
                    className={cn(
                      'font-bold',
                      log.level === 'ERROR'
                        ? 'text-rose-500'
                        : log.level === 'SUCCESS'
                        ? 'text-emerald-500'
                        : log.level === 'WARN'
                        ? 'text-amber-500'
                        : 'text-blue-400'
                    )}
                  >
                    {log.level}:
                  </span>
                  <span className="text-slate-300 group-hover:text-white transition-colors">
                    {log.details}
                  </span>
                </div>
              </div>
            );
          })}
      </div>
      
      <div className="p-4 bg-black/40 border-t border-white/5 space-y-3">
        <div className="flex items-center justify-between text-[10px] font-bold">
          <div className="flex items-center gap-2 text-primary">
            <TrendingUp size={12} />
            <span className="uppercase tracking-widest">Health_Score</span>
          </div>
          <span className="text-emerald-500 font-mono">98.4 / 100</span>
        </div>
        <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
          <div className="h-full bg-primary animate-pulse" style={{ width: '98.4%' }} />
        </div>
      </div>
    </div>
  );
}
