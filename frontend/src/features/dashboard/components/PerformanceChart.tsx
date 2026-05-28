'use client';

import React from 'react';
import { DashboardViewResponse } from '../types';

interface PerformanceChartProps {
  chartData: DashboardViewResponse['chart_24h'];
  isOffline?: boolean;
}

export function PerformanceChart({ chartData, isOffline }: PerformanceChartProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-3">
          <div className="w-1 h-4 bg-primary" />
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] terminal-text">Rendimiento (24h)</h2>
        </div>
        <div className="flex gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-primary" />
            <span className="text-[8px] font-bold text-slate-500 uppercase tracking-widest terminal-text">REQUESTS</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-cyber-lime" />
            <span className="text-[8px] font-bold text-slate-500 uppercase tracking-widest terminal-text">SUCCESS</span>
          </div>
        </div>
      </div>
      
      <div className="panel-industrial p-6 h-72 relative flex flex-col justify-between rounded-none border-white/5 overflow-hidden group">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,rgba(0,255,255,0.05),transparent_70%)]" />
        
        <div className="absolute inset-0 p-6 flex flex-col justify-between pointer-events-none opacity-20">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="w-full h-px bg-primary/20" />
          ))}
        </div>
        
        <div className="relative flex-1 mt-4">
          <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 500 200">
            <defs>
              <linearGradient id="gradient-primary" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.2" />
                <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
              </linearGradient>
            </defs>
            {(() => {
              const apiPoints = chartData || [];
              if (apiPoints.length === 0) {
                return (
                  <text
                    x="250"
                    y="100"
                    textAnchor="middle"
                    className="fill-slate-500 text-[10px] font-bold uppercase tracking-widest terminal-text opacity-40"
                  >
                    SIN_DATOS_DE_RENDIMIENTO
                  </text>
                );
              }

              const values = apiPoints.map((p) => p.total_events);
              const length = values.length;
              const maxValue = Math.max(...values, 1);
              const coords = Array.from({ length }, (_, i) => {
                const x = (i / Math.max(length - 1, 1)) * 500;
                const baseY = values[i];
                const normalized = baseY / maxValue;
                const y = 180 - normalized * 140;
                return { x, y };
              });
              const areaPath = coords
                .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
                .join(' ');
              const linePath = areaPath;
              return (
                <>
                  <path
                    d={`${areaPath} L 500 200 L 0 200 Z`}
                    fill="url(#gradient-primary)"
                    className="transition-all duration-1000"
                  />
                  <path
                    d={linePath}
                    fill="none"
                    stroke="var(--primary)"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="opacity-80"
                  />
                  {coords.map((point, index) => (
                    <circle
                      key={index}
                      cx={point.x}
                      cy={point.y}
                      r="2"
                      fill="var(--primary)"
                      className="animate-pulse"
                      style={{ animationDelay: `${index * 100}ms` }}
                    />
                  ))}
                </>
              );
            })()}
          </svg>
        </div>

        <div className="flex justify-between items-center mt-4 border-t border-white/5 pt-4">
          <div className="flex gap-4">
            {chartData && chartData.length > 0 ? (
              <>
                <div className="text-[8px] font-bold text-slate-500 terminal-text">
                  {new Date(chartData[0].timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}
                </div>
                <div className="text-[8px] font-bold text-slate-500 terminal-text">
                  {new Date(chartData[Math.floor(chartData.length / 2)].timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}
                </div>
                <div className="text-[8px] font-bold text-slate-500 terminal-text">
                  {new Date(chartData[chartData.length - 1].timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}
                </div>
              </>
            ) : (
              <div className="text-[8px] font-bold text-slate-500 terminal-text">NO_TIME_DATA</div>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-[8px] font-bold text-slate-500 terminal-text">
              {chartData
                ? `EVENTOS_24H: ${chartData.reduce((acc, p) => acc + p.total_events, 0)}`
                : 'EVENTOS_24H: 0'}
            </div>
            <div className="text-[8px] font-bold text-primary terminal-text animate-pulse">
              {isOffline ? 'STREAM_OFFLINE' : 'LIVE_STREAM_ACTIVE'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
