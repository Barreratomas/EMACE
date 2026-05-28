'use client';

import React from 'react';
import { Activity, MessageSquare, AlertTriangle, CheckCircle2, Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import { CircularScanner } from '@/components/ui/IndustrialProgress';
import { ApiRecentActivityLog } from '../types';

interface RecentActivityFeedProps {
  activities: ApiRecentActivityLog[] | null;
  error?: string | null;
}

const getActivityIcon = (icon: string) => {
  const normalized = icon.toLowerCase();
  switch (normalized) {
    case 'messagesquare':
    case 'message_square':
      return MessageSquare;
    case 'alerttriangle':
    case 'alert_triangle':
      return AlertTriangle;
    case 'checkcircle2':
    case 'check_circle_2':
      return CheckCircle2;
    case 'users':
      return Users;
    case 'activity':
      return Activity;
    default:
      return MessageSquare;
  }
};

export function RecentActivityFeed({ activities, error }: RecentActivityFeedProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-3">
          <div className="w-1 h-4 bg-primary" />
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] terminal-text">Actividad Reciente</h2>
        </div>
        <div className="p-2 border border-white/5 bg-black/40 text-primary animate-pulse">
          <Activity size={14} />
        </div>
      </div>

      <div className="panel-industrial p-0 overflow-hidden rounded-none border-white/5 group/feed relative">
        <div className="absolute inset-0 bg-linear-to-b from-primary/2 to-transparent pointer-events-none" />
        <div className="max-h-[620px] overflow-y-auto custom-scrollbar">
          <div className="divide-y divide-white/5">
            {error ? (
              <div className="p-4 text-center">
                <span className="text-[10px] font-bold text-rose-500 terminal-text uppercase tracking-wider">
                  {error}
                </span>
              </div>
            ) : !activities ? (
              <div className="p-4 flex items-center justify-center">
                <CircularScanner size={24} className="opacity-60" />
              </div>
            ) : activities.length === 0 ? (
              <div className="p-4 text-center">
                <span className="text-[10px] font-bold text-slate-500 terminal-text uppercase tracking-wider">
                  SIN_REGISTROS_DE_ACTIVIDAD
                </span>
              </div>
            ) : (
              activities.map((log, i) => {
                const Icon = getActivityIcon(log.icon);
                return (
                  <div key={i} className="p-4 hover:bg-white/5 transition-all flex gap-4 group relative overflow-hidden">
                    <div className="absolute inset-y-0 left-0 w-0.5 bg-transparent group-hover:bg-primary transition-colors" />
                    <div
                      className={cn(
                        "mt-1 p-2 border border-white/10 bg-black/40 transition-all duration-300 group-hover:border-primary/30",
                        log.color,
                        log.bg
                      )}
                    >
                      <Icon size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start mb-1">
                        <span className={cn("text-[10px] font-bold terminal-text truncate uppercase tracking-wider", log.color)}>
                          {log.msg}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                            <span className="text-[8px] font-bold text-slate-500 terminal-text tracking-widest">{log.time}</span>
                            <span className="text-[8px] text-slate-700 font-bold terminal-text tracking-widest">{"//"}</span>
                            <span className="text-[8px] font-bold text-slate-600 terminal-text tracking-widest uppercase">{log.type}</span>
                          </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
        <div className="p-3 bg-black/60 border-t border-white/5 flex justify-center">
          <button className="text-[9px] font-bold text-slate-500 hover:text-primary uppercase tracking-[0.3em] terminal-text transition-colors">
            VIEW_ALL_SYSTEM_LOGS
          </button>
        </div>
      </div>
    </div>
  );
}
