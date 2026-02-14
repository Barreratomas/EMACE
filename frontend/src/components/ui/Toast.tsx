'use client';

// import { useToastStore, Toast as ToastType } from '@/hooks/use-toast';
import { useToastStore } from '@/hooks/use-toast';

import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, CheckCircle2, Info, X, ShieldAlert } from 'lucide-react';

const icons = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  error: ShieldAlert,
};

const colors = {
  info: 'border-border-ui/50 bg-background/80 text-slate-900 dark:text-slate-100',
  success: 'border-emerald-500/20 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400',
  warning: 'border-amber-500/20 bg-amber-500/5 text-amber-600 dark:text-amber-400',
  error: 'border-rose-500/20 bg-rose-500/5 text-rose-600 dark:text-rose-400',
};

const barColors = {
  info: 'bg-primary',
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  error: 'bg-rose-500',
};

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="fixed bottom-8 right-8 z-100 flex flex-col gap-4 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => {
          const Icon = icons[toast.type];
          return (
            <motion.div
              key={toast.id}
              layout
              initial={{ opacity: 0, x: 20, scale: 0.98 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ 
                type: "spring", 
                stiffness: 500, 
                damping: 35,
                mass: 0.8
              }}
              className={`pointer-events-auto w-80 backdrop-blur-xl border rounded-none shadow-2xl overflow-hidden relative ${colors[toast.type]}`}
            >
              {/* Decorative Scanning line */}
              <div className="absolute inset-0 bg-linear-to-b from-transparent via-white/5 to-transparent h-1/2 -translate-y-full animate-scan pointer-events-none" />
              
              {/* Progress Bar Animation */}
              <motion.div 
                initial={{ width: '100%' }}
                animate={{ width: '0%' }}
                transition={{ duration: 5, ease: "linear" }}
                className={`absolute top-0 left-0 h-0.5 ${barColors[toast.type]} opacity-50`} 
              />
              
              <div className="p-4 flex gap-4">
                <div className={`p-2 border border-white/10 bg-black/20 h-fit ${toast.type === 'info' ? 'text-primary' : 'text-current'}`}>
                  <Icon size={18} />
                </div>
                <div className="flex-1">
                  {toast.title && (
                    <div className="text-[10px] font-bold uppercase tracking-widest mb-1 opacity-60 terminal-text">
                      {toast.title}
                    </div>
                  )}
                  <div className="text-[12px] font-bold leading-relaxed terminal-text">
                    {toast.message}
                  </div>
                </div>
                <button 
                  onClick={() => removeToast(toast.id)}
                  className="h-fit p-1 hover:bg-black/5 dark:hover:bg-white/5 transition-colors opacity-40 hover:opacity-100"
                >
                  <X size={14} />
                </button>
              </div>

              {/* Status Bar */}
              <div className="flex justify-between px-4 py-2 border-t border-black/5 dark:border-white/5 bg-black/20">
                <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest terminal-text">
                  SYSTEM_ALERT
                </div>
                <div className="text-[9px] font-mono text-slate-500 uppercase tracking-tight opacity-40 terminal-text">
                  REF_{toast.id.slice(0, 8)}
                </div>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
