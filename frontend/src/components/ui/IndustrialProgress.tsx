import React, { useSyncExternalStore } from 'react';
import { cn } from '@/lib/utils';

// Custom hook for safe mounting check without useEffect setState
function useHasMounted() {
  return useSyncExternalStore(
    () => () => {}, // subscribe function (no-op)
    () => true,     // getSnapshot on client
    () => false     // getServerSnapshot on server
  );
}

interface IndustrialProgressProps {
  value: number;
  max?: number;
  segments?: number;
  className?: string;
  variant?: 'primary' | 'cyber' | 'safety' | 'slate';
}

export function IndustrialProgress({ 
  value, 
  max = 100, 
  segments = 10, 
  className,
  variant = 'primary'
}: IndustrialProgressProps) {
  const hasMounted = useHasMounted();

  const percentage = (value / max) * 100;
  const activeSegments = Math.floor((percentage / 100) * segments);

  const variantStyles = {
    primary: 'bg-primary shadow-[0_0_8px_rgba(255,95,31,0.3)]',
    cyber: 'bg-cyber-lime shadow-[0_0_8px_rgba(204,255,0,0.3)]',
    safety: 'bg-safety-orange shadow-[0_0_8px_rgba(255,95,31,0.3)]',
    slate: 'bg-slate-700 shadow-none'
  };

  return (
    <div className={cn("flex gap-0.5 h-1.5 w-full", className)}>
      {[...Array(segments)].map((_, i) => (
        <div
          key={i}
          className={cn(
            "flex-1 transition-all duration-300 relative overflow-hidden",
            hasMounted && i < activeSegments 
              ? variantStyles[variant] 
              : "bg-white/5"
          )}
        >
          {hasMounted && i < activeSegments && (
            <div className="absolute inset-0 bg-white/20 animate-pulse" />
          )}
        </div>
      ))}
    </div>
  );
}

export function CircularScanner({ size = 40, className }: { size?: number, className?: string }) {
  return (
    <div 
      className={cn("relative flex items-center justify-center", className)}
      style={{ width: size, height: size }}
    >
      {/* Outer ring */}
      <div className="absolute inset-0 border-2 border-white/5 rounded-full" />
      
      {/* Rotating segments */}
      <svg className="absolute inset-0 w-full h-full -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={(size / 2) - 4}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeDasharray="4, 8"
          className="text-primary animate-spin"
          style={{ animationDuration: '3s' }}
        />
      </svg>
      
      {/* Inner pulsing core */}
      <div className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse-fast shadow-[0_0_8px_rgba(255,95,31,0.8)]" />
      
      {/* Scanning line */}
      <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s' }}>
        <div className="absolute top-1/2 left-1/2 w-1/2 h-px bg-linear-to-r from-primary to-transparent origin-left" />
      </div>
    </div>
  );
}

export function ScanningLoader({ className }: { className?: string }) {
  return (
    <div className={cn("relative w-4 h-4 overflow-hidden border border-white/20", className)}>
      <div className="absolute inset-0 bg-primary/10" />
      <div className="absolute top-0 left-0 w-full h-2px bg-primary shadow-[0_0_8px_rgba(255,95,31,0.8)] animate-scan" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w1px h-full bg-white/5" />
        <div className="w-full h-1px bg-white/5 absolute" />
      </div>
    </div>
  );
}