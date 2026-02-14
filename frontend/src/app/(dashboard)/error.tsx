'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCcw, Home } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('System Error:', error);
  }, [error]);

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center p-8 text-center">
      <div className="panel-industrial p-12 max-w-xl w-full space-y-8 relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-1 bg-accent/50" />
        <div className="absolute -top-12 -right-12 w-24 h-24 bg-accent/5 opacity-20 blur-2xl rounded-full" />
        
        <div className="flex justify-center">
          <div className="p-4 bg-accent/10 border border-accent/20 text-accent animate-pulse">
            <AlertTriangle size={48} />
          </div>
        </div>

        <div className="space-y-2">
          <h2 className="text-3xl font-bold font-display italic uppercase tracking-tighter">
            FALLO_CRÍTICO_SISTEMA
          </h2>
          <div className="flex items-center justify-center gap-2 text-[10px] font-mono text-zinc-500 uppercase">
            <span>ID_ERROR: {error.digest || 'UNKNOWN'}</span>
            <span className="w-1 h-1 bg-zinc-800 rounded-full" />
            <span>ESTADO: CRITICAL</span>
          </div>
        </div>

        <div className="bg-zinc-950/50 border border-zinc-900 p-4 font-mono text-[10px] text-zinc-400 text-left overflow-auto max-h-32">
          <p className="text-accent mb-2 uppercase tracking-widest font-bold">Trace_Log:</p>
          <code className="whitespace-pre-wrap">{error.message || 'Error no especificado durante la ejecución del protocolo.'}</code>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Button
            variant="cyber"
            onClick={() => reset()}
            className="py-3 group"
          >
            <RefreshCcw size={16} className="group-hover:rotate-180 transition-transform duration-500" />
            <span className="text-[10px] font-mono uppercase">Reiniciar_Protocolo</span>
          </Button>
          
          <Button
            variant="outline"
            asChild
            className="py-3 group border-zinc-800 bg-zinc-900"
          >
            <Link href="/">
              <Home size={16} className="text-zinc-500 group-hover:text-primary transition-colors" />
              <span className="text-[10px] font-mono uppercase text-zinc-500 group-hover:text-zinc-200">Volver_Home</span>
            </Link>
          </Button>
        </div>

        <div className="pt-4 border-t border-zinc-900">
          <p className="text-[8px] font-mono text-zinc-600 uppercase tracking-widest">
            Protocolo de recuperación automática EMACE v1.0.4
          </p>
        </div>
      </div>
    </div>
  );
}
