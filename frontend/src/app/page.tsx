'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ArrowRight, Box, Shield, Zap, Activity } from 'lucide-react';
import api from '@/lib/api';

type PlatformFeature = {
  key: string;
  name: string;
  enabled: boolean;
  status: string;
  reason?: string | null;
};

type PlatformFeaturesResponse = {
  features: PlatformFeature[];
};

export default function Home() {
  const [features, setFeatures] = useState<PlatformFeature[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const fetchFeatures = async () => {
      try {
        const res = await api.get<PlatformFeaturesResponse>('/platform/features');
        if (cancelled) return;
        setFeatures(res.data?.features ?? []);
        setError(null);
      } catch {
        if (cancelled) return;
        setFeatures([]);
        setError('No se pudo obtener el estado de la plataforma');
      }
    };
    fetchFeatures();
    return () => {
      cancelled = true;
    };
  }, []);

  const billingFeature = features?.find((f) => f.key === 'billing');
  const billingEnabled = !!billingFeature?.enabled;

  const encryptionFeature = features?.find((f) => f.key === 'encryption');
  const encryptionLabel = encryptionFeature?.enabled ? 'SECURE_ENCRYPTION_AES256' : 'SECURITY_BASELINE_ENABLED';

  const latencyFeature = features?.find((f) => f.key === 'low_latency_api');
  const latencyLabel = latencyFeature?.enabled ? 'LOW_LATENCY_API_CONNECTED' : 'API_STATUS_MONITORED';

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 gap-12 sm:p-20 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 left-0 w-full h-1 bg-linear-to-r from-transparent via-primary to-transparent opacity-50" />
      <div className="absolute -top-24 -left-24 w-96 h-96 bg-primary/10 blur-3xl rounded-full" />
      <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-secondary/10 blur-3xl rounded-full" />

      <main id="main-content" className="flex flex-col gap-10 items-center text-center max-w-4xl z-10">
        <div className="flex flex-col gap-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 border border-primary/30 bg-primary/5 text-primary text-xs font-bold uppercase tracking-widest self-center">
            <Activity size={14} /> System Online // v1.0.4
          </div>
          <h1 className="text-6xl md:text-8xl font-extrabold tracking-tighter leading-none glitch-text" data-text="EMACE">
            EMACE
          </h1>
          <p className="text-lg md:text-xl text-zinc-400 max-w-2xl font-mono uppercase tracking-tight">
            Ecosistema <span className="text-primary">Multi-Agente</span> Cognitivo Enterprise
          </p>
         
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full mt-4">
          <Link 
            href="/dashboard"
            className="group panel-industrial p-10 hover:border-primary/50 transition-all duration-300 flex flex-col items-start text-left gap-4"
          >
            <div className="p-3 bg-primary/10 text-primary border border-primary/20 group-hover:bg-primary group-hover:text-white transition-colors">
              <Box size={32} />
            </div>
            <div>
              <h2 className="text-2xl font-bold mb-2 group-hover:text-primary transition-colors italic uppercase font-display">Terminal_Dashboard</h2>
              <p className="text-sm text-zinc-500 font-mono leading-relaxed uppercase">
                Acceso al centro de comando multi-agente. Visualización de métricas y gestión de activos.
              </p>
            </div>
            <div className="mt-4 flex items-center text-primary font-bold uppercase tracking-tighter text-sm group-hover:gap-2 transition-all">
              INICIAR_PROTOCOLO_DE_ACCESO <ArrowRight size={16} className="ml-1" />
            </div>
          </Link>
          {billingEnabled ? (
            <Link
              href="/dashboard/settings/billing"
              className="group panel-industrial p-10 hover:border-secondary/50 transition-all duration-300 flex flex-col items-start text-left gap-4"
            >
              <div className="p-3 bg-secondary/10 text-secondary border border-secondary/20 group-hover:bg-secondary group-hover:text-white transition-colors">
                <Zap size={32} />
              </div>
              <div>
                <h2 className="text-2xl font-bold mb-2 italic uppercase font-display">Facturación</h2>
                <p className="text-sm text-zinc-500 font-mono leading-relaxed uppercase">
                  Módulo de transacciones enterprise. Integración de pagos habilitada.
                </p>
              </div>
              <div className="mt-4 flex items-center text-secondary font-bold uppercase tracking-tighter text-sm group-hover:gap-2 transition-all">
                ABRIR_PANEL_DE_FACTURACION <ArrowRight size={16} className="ml-1" />
              </div>
            </Link>
          ) : (
            <div className="panel-industrial p-10 opacity-40 grayscale flex flex-col items-start text-left gap-4 cursor-not-allowed">
              <div className="p-3 bg-zinc-800 text-zinc-500 border border-zinc-700">
                <Zap size={32} />
              </div>
              <div>
                <h2 className="text-2xl font-bold mb-2">Facturación</h2>
                <p className="text-sm text-zinc-600 font-mono leading-relaxed">
                  Módulo de transacciones enterprise. Pendiente de sincronización de protocolo.
                </p>
              </div>
              <div className="mt-4 flex items-center text-zinc-600 font-bold uppercase tracking-tighter text-sm">
                Bloqueado // Protocolo 403
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-wrap justify-center gap-8 mt-12 pt-12 border-t border-border-ui w-full">
          {error && (
            <div className="w-full text-center text-[10px] font-mono text-red-500 uppercase tracking-widest">
              {error}
            </div>
          )}
          <div className="flex items-center gap-2 text-zinc-500 text-xs font-mono">
            <Shield size={14} className="text-primary" /> {encryptionLabel}
          </div>
          <div className="flex items-center gap-2 text-zinc-500 text-xs font-mono">
            <Activity size={14} className="text-secondary" /> {latencyLabel}
          </div>
        </div>
      </main>
    </div>
  );
}
