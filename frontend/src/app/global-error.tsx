'use client';

import { AlertTriangle, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function GlobalError({
  // error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body className="bg-zinc-950 text-zinc-100 flex items-center justify-center min-h-screen p-4 font-sans antialiased">
        <div className="panel-industrial p-12 max-w-xl w-full space-y-8 text-center border-accent/30">
          <div className="flex justify-center">
            <div className="p-4 bg-accent/10 border border-accent/20 text-accent">
              <AlertTriangle size={48} />
            </div>
          </div>
          <h2 className="text-3xl font-bold font-display italic uppercase tracking-tighter">
            ERROR_GLOBAL_NÚCLEO
          </h2>
          <p className="text-zinc-500 font-mono text-xs uppercase">
            Se ha detectado una anomalía crítica que impide la carga del sistema base.
          </p>
          <Button
            variant="cyber"
            onClick={() => reset()}
            className="w-full py-4 group"
          >
            <RefreshCcw size={16} />
            <span className="text-[10px] font-mono uppercase">Reintentar_Carga_Sistema</span>
          </Button>
        </div>
      </body>
    </html>
  );
}
