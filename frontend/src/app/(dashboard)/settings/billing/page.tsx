'use client';

import { useEffect, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import { DateTime } from 'luxon';
import { RefreshCw, CalendarClock, ShieldCheck, AlertTriangle, CreditCard, CheckCircle2, Ban } from 'lucide-react';
import { Button } from '@/components/ui/Button';

type AccessState = {
  vendor_id: number;
  access_mode: 'subscription' | 'lifetime';
  source: 'trial' | 'paid_subscription' | 'lifetime_purchase';
  valid_until: string | null;
  subscription_id_mp?: string | null;
};

export default function BillingSettingsPage() {
  const queryClient = useQueryClient();
  const { data: state } = useQuery({
    queryKey: ['billing', 'access-state'],
    queryFn: async () => {
      const res = await api.get<AccessState>('/billing/access-state');
      return res.data;
    },
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const queryStatus = useMemo(() => {
    if (typeof window === 'undefined') return null;
    const sp = new URLSearchParams(window.location.search);
    return sp.get('status');
  }, []);

  useEffect(() => {
    if (queryStatus === 'success') {
      toast.success('Pago aprobado. Tu acceso fue extendido.');
    } else if (queryStatus === 'failure') {
      toast.warning('Pago no aprobado. Puedes reintentar el checkout.');
    }
  }, [queryStatus]);

  const refetchState = () => queryClient.invalidateQueries({ queryKey: ['billing', 'access-state'] });

  const daysLeft = useMemo(() => {
    if (!state?.valid_until) return null;
    const now = DateTime.now();
    const until = DateTime.fromISO(state.valid_until);
    const diff = until.diff(now, 'days').days;
    return Math.max(0, Math.ceil(diff));
  }, [state]);

  const onSubscribe = async () => {
    try {
      const res = await api.post<{ checkout_url: string }>('/billing/subscriptions', {});
      const url = res.data.checkout_url;
      if (url) {
        window.location.href = url;
      } else {
        toast.error('No se pudo obtener el enlace de checkout');
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo iniciar la suscripción');
    }
  };

  const onLifetime = async () => {
    try {
      await api.post('/billing/lifetime', {});
      toast.success('Plan lifetime activado correctamente');
      refetchState();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo activar el plan lifetime');
    }
  };

  const onCancel = async () => {
    try {
      await api.post('/billing/cancel-subscription', {});
      toast.info('Suscripción cancelada. Mantienes acceso hasta la fecha de vencimiento');
      refetchState();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo cancelar la suscripción');
    }
  };

  const onRefresh = async () => {
    try {
      await api.post('/billing/refresh', {});
      await refetchState();
      toast.info('Estado actualizado');
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo refrescar el estado');
    }
  };

  const statusBadge = () => {
    if (!state) return null;
    const base = 'text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-lg border';
    if (state.access_mode === 'lifetime') {
      return <span className={`${base} bg-emerald-500/10 text-emerald-600 border-emerald-500/20 flex items-center gap-1`}><ShieldCheck size={12}/> Lifetime</span>;
    }
    if (state.source === 'paid_subscription') {
      return <span className={`${base} bg-blue-500/10 text-blue-600 border-blue-500/20 flex items-center gap-1`}><CheckCircle2 size={12}/> Suscripción activa</span>;
    }
    if (state.source === 'trial') {
      return <span className={`${base} bg-amber-500/10 text-amber-600 border-amber-500/20 flex items-center gap-1`}><AlertTriangle size={12}/> Trial</span>;
    }
    return <span className={`${base} bg-slate-100 text-slate-500 border-slate-200`}>Sin Estado</span>;
  };

  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display">Billing y Acceso</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-2 font-medium">
            Gestiona tu plan, verifica tu estado y accede a opciones de suscripción o lifetime.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={onRefresh} variant="secondary" className="flex items-center gap-2">
            <RefreshCw size={14}/> Refrescar
          </Button>
        </div>
      </div>

      <div className="panel-industrial p-6 border-0 shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">Estado</span>
              {statusBadge()}
            </div>
            <div className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-400">
              <CalendarClock size={14}/>
              {state?.access_mode === 'lifetime' ? (
                <span>Acceso permanente</span>
              ) : state?.valid_until ? (
                <span>Vence el {DateTime.fromISO(state.valid_until).toLocaleString(DateTime.DATETIME_MED)} {daysLeft !== null && `(${daysLeft} días restantes)`}</span>
              ) : (
                <span>Sin fecha de vencimiento disponible</span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={onSubscribe} className="flex items-center gap-2">
              <CreditCard size={14}/> Suscribirme
            </Button>
            <Button onClick={onLifetime} variant="secondary" className="flex items-center gap-2">
              <ShieldCheck size={14}/> Comprar Lifetime
            </Button>
            {state?.access_mode === 'subscription' && (
              <Button onClick={onCancel} variant="ghost" className="flex items-center gap-2 text-rose-600 hover:text-rose-700">
                <Ban size={14}/> Cancelar Suscripción
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
