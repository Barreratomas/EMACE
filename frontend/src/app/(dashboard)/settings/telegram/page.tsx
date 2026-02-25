'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/Button';

type TelegramIntegrationState = {
  vendor_id: number;
  bot_username: string;
  webhook_url: string;
  state?: 'active' | 'paused' | 'deleted';
  is_active?: boolean;
  status?: 'healthy' | 'degraded' | 'inactive';
  last_error?: string | null;
  last_latency_ms?: number | null;
  last_metric_at?: string | null;
};

type MtprotoStatusState = {
  vendor_id: number;
  allowed: boolean;
  mtproto_enabled: boolean;
  mtproto_status: string;
  last_heartbeat_at: string | null;
  last_error?: string | null;
};

export default function TelegramSettingsPage() {
  const [loading, setLoading] = useState(false);
  const [integration, setIntegration] = useState<TelegramIntegrationState | null>(null);
  const [mtprotoAccepted, setMtprotoAccepted] = useState(false);
  const [mtprotoLoading, setMtprotoLoading] = useState(false);
  const [mtprotoStatus, setMtprotoStatus] = useState<MtprotoStatusState | null>(null);
  const [mtprotoStatusLoading, setMtprotoStatusLoading] = useState(false);
  const [mtprotoPhone, setMtprotoPhone] = useState('');
  const [mtprotoCode, setMtprotoCode] = useState('');
  const [mtprotoLoginStep, setMtprotoLoginStep] = useState<1 | 2 | 3>(1);
  const [mtprotoSessionLoading, setMtprotoSessionLoading] = useState(false);
  const [autoBotName, setAutoBotName] = useState('');
  const [autoBotUsername, setAutoBotUsername] = useState('');
  const [autoBotStatus, setAutoBotStatus] = useState<'none' | 'creating' | 'ready' | 'error'>('none');
  const [autoBotError, setAutoBotError] = useState<string | null>(null);
  const [discoveredBots, setDiscoveredBots] = useState<Array<{ username: string; display_name: string }>>([]);
  const [discoveringBots, setDiscoveringBots] = useState(false);
  const [manualToken, setManualToken] = useState('');
  const [importingToken, setImportingToken] = useState(false);

  const hasIntegration = !!integration && integration.state !== 'deleted';
  const canAutoCreate =
    !!mtprotoStatus && mtprotoStatus.allowed && mtprotoStatus.mtproto_enabled;

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await api.get('/vendors/me/integrations/telegram/status');
        if (res.data?.has_integration) {
          setIntegration({
            vendor_id: res.data.vendor_id,
            bot_username: res.data.bot_username,
            webhook_url: res.data.webhook_url,
            state: res.data.state || undefined,
            is_active: res.data.is_active,
            status: res.data.status,
            last_error: res.data.last_error ?? null,
            last_latency_ms: res.data.last_latency_ms ?? null,
            last_metric_at: res.data.last_metric_at ?? null,
          });
        } else {
          setIntegration(null);
        }
      } catch (e: any) {
        const detail = e?.response?.data?.detail;
        if (detail && detail !== 'integration_not_found') {
          toast.error(detail || 'No se pudo obtener el estado de Telegram.');
        }
      }
    };
    fetchStatus();
  }, []);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (cancelled) return;
      try {
        setMtprotoStatusLoading(true);
        const res = await api.get<MtprotoStatusState>(
          '/vendors/me/integrations/telegram/mtproto/status',
        );
        if (cancelled) return;
        const data = res.data;
        setMtprotoStatus(data);
        if (data.mtproto_status === 'ready' || data.mtproto_status === 'enabled') {
          setMtprotoLoginStep(3);
        } else if (
          data.mtproto_status === 'awaiting_code' ||
          data.mtproto_status === 'awaiting_session'
        ) {
          setMtprotoLoginStep(2);
        }
      } catch (e: any) {
        const detail = e?.response?.data?.detail;
        if (detail && detail !== 'mtproto_unavailable') {
          toast.error(detail || 'No se pudo obtener el estado de la integración MTProto.');
        }
      } finally {
        if (!cancelled) {
          setMtprotoStatusLoading(false);
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshIntegrationStatus = async () => {
    try {
      const res = await api.get('/vendors/me/integrations/telegram/status');
      if (res.data?.has_integration) {
        setIntegration({
          vendor_id: res.data.vendor_id,
          bot_username: res.data.bot_username,
          webhook_url: res.data.webhook_url,
          state: res.data.state || undefined,
          is_active: res.data.is_active,
          status: res.data.status,
          last_error: res.data.last_error ?? null,
          last_latency_ms: res.data.last_latency_ms ?? null,
          last_metric_at: res.data.last_metric_at ?? null,
        });
      } else {
        setIntegration(null);
      }
    } catch {
      /* noop */
    }
  };

  const handlePause = async () => {
    if (!integration) return;
    const ok = window.confirm('Pausar el bot cortará el webhook y no recibirá mensajes. ¿Continuar?');
    if (!ok) return;
    setLoading(true);
    try {
      await api.post('/vendors/me/integrations/telegram/bot/pause');
      toast.info('Bot pausado.');
      await refreshIntegrationStatus();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo pausar el bot.');
    } finally {
      setLoading(false);
    }
  };

  const handleResume = async () => {
    if (!integration) return;
    setLoading(true);
    try {
      await api.post('/vendors/me/integrations/telegram/bot/resume');
      toast.success('Bot reanudado.');
      await refreshIntegrationStatus();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo reanudar el bot.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateWebhookSecret = async () => {
    if (!integration) return;
    const ok = window.confirm('Se regenerará el secreto del webhook y se actualizará en Telegram. ¿Continuar?');
    if (!ok) return;
    setLoading(true);
    try {
      await api.patch('/vendors/me/integrations/telegram/bot', {
        regenerate_webhook_secret: true,
      });
      toast.success('Secreto del webhook regenerado.');
      await refreshIntegrationStatus();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo regenerar el secreto del webhook.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteIntegration = async () => {
    if (!integration) return;
    const ok = window.confirm(
      'Eliminar la integración es una acción lógica: se desactiva el webhook y el bot no recibirá mensajes. ¿Confirmás?',
    );
    if (!ok) return;
    setLoading(true);
    try {
      await api.delete('/vendors/me/integrations/telegram/bot');
      toast.info('Integración eliminada lógicamente.');
      await refreshIntegrationStatus();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo eliminar la integración.');
    } finally {
      setLoading(false);
    }
  };

  const handleHardDeleteBot = async () => {
    if (!integration) return;
    const ok = window.confirm(
      '¡ADVERTENCIA CRÍTICA! Esto eliminará el bot de tu sistema Y TAMBIÉN le ordenará a BotFather que lo elimine permanentemente de Telegram. Esta acción no se puede deshacer. ¿Estás TOTALMENTE seguro?',
    );
    if (!ok) return;
    
    setLoading(true);
    try {
      await api.delete('/vendors/me/integrations/telegram/bot/hard-delete');
      toast.warning('Solicitud de eliminación total enviada a BotFather.');
      await refreshIntegrationStatus();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo iniciar la eliminación total.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAutoCreateStatus = async () => {
    try {
      const res = await api.get('/vendors/me/integrations/telegram/bot/status');
      const st = res.data?.bot_status as 'none' | 'creating' | 'ready' | 'error';
      const err = res.data?.last_error ?? null;
      setAutoBotStatus(st || 'none');
      setAutoBotError(err);
      if (st === 'ready') {
        try {
          const sres = await api.get('/vendors/me/integrations/telegram/status');
          if (sres.data?.has_integration) {
            setIntegration({
              vendor_id: sres.data.vendor_id,
              bot_username: sres.data.bot_username,
              webhook_url: sres.data.webhook_url,
              is_active: sres.data.is_active,
              status: sres.data.status,
              last_error: sres.data.last_error ?? null,
              last_latency_ms: sres.data.last_latency_ms ?? null,
              last_metric_at: sres.data.last_metric_at ?? null,
            });
            toast.success('Bot creado y vinculado automáticamente.');
          }
        } catch {
          /* noop */
        }
      }
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (detail && detail !== 'mtproto_unavailable') {
        toast.error(detail || 'No se pudo obtener el estado de auto‑creación.');
      }
    }
  };

  useEffect(() => {
    let interval: any;
    if (autoBotStatus === 'creating') {
      interval = setInterval(() => {
        fetchAutoCreateStatus();
      }, 2500);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoBotStatus]);

  const handleAutoCreate = async () => {
    if (!autoBotName.trim()) {
      toast.error('Ingresá el nombre público del bot.');
      return;
    }
    if (!autoBotUsername.trim()) {
      toast.error('Ingresá un username para el bot.');
      return;
    }
    setAutoBotStatus('creating');
    setAutoBotError(null);
    try {
      await api.post('/vendors/me/integrations/telegram/bot/auto-create', {
        bot_name: autoBotName.trim(),
        username_hint: autoBotUsername.trim(),
      });
      toast.info('Creación iniciada. Vamos a avisarte cuando esté listo.');
      await fetchAutoCreateStatus();
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (detail === 'session_not_configured') {
        setAutoBotStatus('error');
        setAutoBotError(
          'Antes de crear el bot, completá el login y activá la sesión MTProto.',
        );
      } else if (detail === 'bot_already_exists') {
        setAutoBotStatus('ready');
        setAutoBotError(null);
        toast.info('Ya tenés un bot activo vinculado. No se creará uno nuevo.');
      } else if (detail === 'creation_rate_limited_vendor') {
        setAutoBotStatus('error');
        setAutoBotError('Alcanzaste el límite diario de creación. Intentalo mañana.');
      } else if (detail === 'creation_rate_limited_global') {
        setAutoBotStatus('error');
        setAutoBotError('Se alcanzó el límite global de creación por hoy. Intentalo más tarde.');
      } else if (detail === 'mtproto_unavailable') {
        setAutoBotStatus('error');
        setAutoBotError('La integración MTProto no está disponible para tu cuenta.');
      } else if (detail === 'creation_in_progress') {
        setAutoBotStatus('creating');
      } else if (detail === 'bot_name_and_username_required') {
        setAutoBotStatus('error');
        setAutoBotError('Faltan datos de nombre o username.');
      } else {
        setAutoBotStatus('error');
        setAutoBotError(detail || 'No se pudo iniciar la auto‑creación.');
      }
    }
  };

  /* Consentimiento se maneja en handleConsentAndEnable */

  const refreshMtprotoStatus = async () => {
    try {
      setMtprotoStatusLoading(true);
      const res = await api.get<MtprotoStatusState>(
        '/vendors/me/integrations/telegram/mtproto/status',
      );
      const data = res.data;
      setMtprotoStatus(data);
      if (data.mtproto_status === 'ready' || data.mtproto_status === 'enabled') {
        setMtprotoLoginStep(3);
      } else if (
        data.mtproto_status === 'awaiting_code' ||
        data.mtproto_status === 'awaiting_session'
      ) {
        setMtprotoLoginStep(2);
      }
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (detail && detail !== 'mtproto_unavailable') {
        toast.error(detail || 'No se pudo obtener el estado de la integración MTProto.');
      }
    } finally {
      setMtprotoStatusLoading(false);
    }
  };

  const handleMtprotoInit = async () => {
    if (!mtprotoPhone.trim()) {
      toast.error('Ingresá el número de teléfono con código de país.');
      return;
    }
    let pn = mtprotoPhone.trim().replace(/[()\s-]/g, '');
    if (pn.startsWith('00')) pn = `+${pn.slice(2)}`;
    if (!pn.startsWith('+')) {
      toast.error('Ingresá el número en formato internacional (+código de país). Ej: +54911...');
      return;
    }
    setMtprotoSessionLoading(true);
    try {
      await api.post('/vendors/me/integrations/telegram/mtproto/session/init', {
        phone_number: pn,
      });
      toast.success('Código enviado por Telegram. Revisá la app e ingresalo.');
      setMtprotoLoginStep(2);
      await refreshMtprotoStatus();
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
        if (detail === 'mtproto_unavailable') {
          toast.info('La integración MTProto aún no está disponible para tu cuenta.');
      } else if (detail === 'invalid_phone_number') {
        toast.error('El número no es válido. Usá formato E.164: +<país><número>.');
      } else if (detail === 'mtproto_login_error') {
        toast.error('No se pudo iniciar el login MTProto. Revisá el número.');
      } else {
        toast.error(detail || 'No se pudo iniciar el login MTProto.');
      }
    } finally {
      setMtprotoSessionLoading(false);
    }
  };

  const handleMtprotoConfirmCode = async () => {
    if (!mtprotoCode.trim()) {
      toast.error('Ingresá el código que recibiste por Telegram.');
      return;
    }
    setMtprotoSessionLoading(true);
    try {
      const payload: any = { code: mtprotoCode.trim() };
      if (mtprotoPhone.trim()) {
        payload.phone_number = mtprotoPhone.trim();
      }
      await api.post('/vendors/me/integrations/telegram/mtproto/session/confirm', payload);
      toast.success(
        'Sesión MTProto confirmada. Ahora podés habilitar la integración de userbot.',
      );
      setMtprotoLoginStep(3);
      await refreshMtprotoStatus();
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (detail === 'pending_session_required') {
        toast.error('Primero tenés que iniciar el login y enviar el código.');
      } else if (detail === 'mtproto_login_error') {
        toast.error('El código no es válido o expiró. Podés pedir uno nuevo.');
      } else if (detail === 'phone_required') {
        toast.error('Falta el número de teléfono para completar el login.');
      } else if (detail === 'mtproto_unavailable') {
        toast.info('La integración MTProto aún no está disponible para tu cuenta.');
      } else {
        toast.error(detail || 'No se pudo confirmar el código MTProto.');
      }
    } finally {
      setMtprotoSessionLoading(false);
    }
  };

  const handleMtprotoResendCode = async () => {
    if (!mtprotoPhone.trim()) {
      toast.error('Ingresá el número de teléfono con código de país.');
      setMtprotoLoginStep(1);
      return;
    }
    await handleMtprotoInit();
  };

  const handleMtprotoResetPhone = () => {
    setMtprotoCode('');
    setMtprotoPhone('');
    setMtprotoLoginStep(1);
    toast.info('Podés ingresar un número nuevo para solicitar un código.');
  };

  /* Habilitación se maneja en handleConsentAndEnable */

  const handleConsentAndEnable = async () => {
    if (!mtprotoAccepted) {
      toast.error(
        'Tenés que aceptar los términos para habilitar la integración de userbot.',
      );
      return;
    }
    setMtprotoLoading(true);
    try {
      await api.post('/vendors/me/integrations/telegram/mtproto/consent', {
        accepted: true,
        terms_version: 'v1',
      });
      await api.post('/vendors/me/integrations/telegram/mtproto/enable');
      toast.success('Consentimiento guardado e integración de userbot habilitada.');
      await refreshMtprotoStatus();
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (detail === 'session_not_configured') {
        toast.error('Primero tenés que completar el login MTProto.');
      } else if (detail === 'mtproto_unavailable') {
        toast.info('La integración MTProto aún no está disponible para tu cuenta.');
      } else if (detail === 'consent_not_accepted') {
        toast.error('Debés aceptar los términos antes de continuar.');
      } else {
        toast.error(
          detail || 'No se pudo completar la habilitación de la integración de userbot.',
        );
      }
    } finally {
      setMtprotoLoading(false);
    }
  };

  const handleDiscoverBots = async () => {
    setDiscoveringBots(true);
    try {
      const res = await api.get('/vendors/me/integrations/telegram/bot/discover');
      setDiscoveredBots(res.data?.bots || []);
      if (res.data?.bots?.length === 0) {
        toast.info('No se encontraron bots vinculados a esta cuenta en BotFather.');
      } else {
        toast.success(`Se encontraron ${res.data?.bots?.length} bots.`);
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudieron buscar bots.');
    } finally {
      setDiscoveringBots(false);
    }
  };

  const handleImportToken = async (token?: string) => {
    const finalToken = token || manualToken;
    if (!finalToken) {
      toast.error('Ingresá un token válido.');
      return;
    }
    setImportingToken(true);
    try {
      const res = await api.post('/vendors/me/integrations/telegram/bot/import', {
        token: finalToken,
      });
      toast.success(`Bot @${res.data.bot_username} importado y vinculado.`);
      setManualToken('');
      await refreshIntegrationStatus();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'No se pudo importar el bot.');
    } finally {
      setImportingToken(false);
    }
  };

  /* Deshabilitar ya no es parte del flujo principal */

  const handleMtprotoRevoke = async () => {
    const ok = window.confirm(
      '¿Revocar la sesión MTProto? Deberás volver a hacer login.',
    );
    if (!ok) return;
    setMtprotoSessionLoading(true);
    try {
      await api.post('/vendors/me/integrations/telegram/mtproto/revoke');
      toast.info('Sesión MTProto revocada.');
      setMtprotoPhone('');
      setMtprotoCode('');
      setMtprotoLoginStep(1);
      await refreshMtprotoStatus();
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (detail === 'session_not_found') {
        toast.error('No hay sesión MTProto configurada.');
      } else {
        toast.error(detail || 'No se pudo revocar la sesión MTProto.');
      }
    } finally {
      setMtprotoSessionLoading(false);
    }
  };

  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display">
            Integración Telegram
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-2 font-medium">
            Vinculá tu propio bot de Telegram y conectalo al grafo de agentes de EMACE.
          </p>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,1.4fr)]">
        <div className="panel-industrial p-6 border-0 shadow-xl space-y-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold tracking-tight">Estado del bot de Telegram</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Revisá el estado de la integración, probá mensajes y gestioná el bot.
              </p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="space-y-3">
              <h3 className="text-lg font-bold tracking-tight">Estado de la integración</h3>
              {hasIntegration ? (
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-3 text-xs">
                    <span className="inline-flex items-center rounded-full border border-slate-700/60 bg-slate-900/40 px-2.5 py-1">
                      <span
                        className={`mr-2 h-2 w-2 rounded-full ${
                          integration?.status === 'healthy'
                            ? 'bg-emerald-400'
                            : integration?.status === 'degraded'
                            ? 'bg-amber-400'
                            : 'bg-slate-500'
                        }`}
                      />
                      {integration?.status === 'healthy'
                        ? 'Saludable'
                        : integration?.status === 'degraded'
                        ? 'Degradado'
                        : 'Inactivo'}
                    </span>
                    {integration?.last_latency_ms != null && (
                      <span className="text-slate-400">
                        Latencia reciente:{' '}
                        <span className="font-mono font-semibold">{integration.last_latency_ms} ms</span>
                      </span>
                    )}
                    {integration?.last_metric_at && (
                      <span className="text-slate-400">
                        Último mensaje:{' '}
                        <span className="font-mono">
                          {new Date(integration.last_metric_at).toLocaleString()}
                        </span>
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-slate-500 dark:text-slate-400 space-y-1">
                    <p>
                      Bot vinculado:{' '}
                      <span className="font-mono font-semibold">@{integration?.bot_username}</span>
                    </p>
                    <p className="break-all">
                      Webhook:{' '}
                      <span className="font-mono text-xs">
                        {integration?.webhook_url
                          ? integration.webhook_url.replace(
                              /(https?:\/\/[^\/]+\/).*/,
                              (_, base) => `${base}…/webhook/{vendor}/{secret}`,
                            )
                          : ''}
                      </span>
                    </p>
                    {integration?.last_error && (
                      <p className="text-xs text-amber-400">
                        Último error registrado: {integration.last_error}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Todavía no hay un bot vinculado. Podés crearlo automáticamente usando la
                  integración de userbot.
                </p>
              )}
            </div>

            {hasIntegration && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold">Gestión del bot</h3>
                <div className="flex flex-wrap gap-3">
                  <Button
                    onClick={handlePause}
                    disabled={
                      loading ||
                      integration?.state === 'paused' ||
                      integration?.state === 'deleted'
                    }
                    variant="secondary"
                  >
                    Pausar bot
                  </Button>
                  <Button
                    onClick={handleResume}
                    disabled={
                      loading ||
                      integration?.state === 'active' ||
                      integration?.state === 'deleted'
                    }
                  >
                    Reanudar bot
                  </Button>
                  <Button
                    onClick={handleRegenerateWebhookSecret}
                    disabled={loading || integration?.state === 'deleted'}
                    variant="outline"
                  >
                    Regenerar secreto de webhook
                  </Button>
                  <Button
                    onClick={handleDeleteIntegration}
                    disabled={loading || integration?.state === 'deleted'}
                    variant="destructive"
                  >
                    Desvincular
                  </Button>
                  {mtprotoStatus?.mtproto_enabled && (
                    <Button
                      onClick={handleHardDeleteBot}
                      disabled={loading || integration?.state === 'deleted'}
                      variant="destructive"
                      className="bg-red-900/40 hover:bg-red-800/60 border-red-500/50"
                    >
                      Eliminar de Telegram
                    </Button>
                  )}
                </div>
                <div className="space-y-1 text-xs text-slate-500 dark:text-slate-400">
                  <p>
                    Estado actual:{' '}
                    <span className="font-semibold">
                      {integration?.state === 'paused'
                        ? 'Pausado'
                        : integration?.state === 'deleted'
                        ? 'Eliminado'
                        : 'Activo'}
                    </span>
                  </p>
                  <p>
                    Si sospechás que compartiste la URL del bot con alguien externo (por ejemplo
                    en un ticket o captura de pantalla), podés regenerar este secreto. Esto
                    actualiza el “código de seguridad” interno que usa Telegram para hablar con
                    EMACE, sin que tengas que cambiar nada más.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="panel-industrial p-6 border-0 shadow-xl space-y-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold tracking-tight">
                Userbot MTProto (creación automática de bot)
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Conecta una cuenta real de Telegram (userbot) con EMACE. Esa sesión se usa exclusivamente para hablar con
                BotFather y automatizar la creación y mantenimiento de tu bot público. Las conversaciones con clientes
                siempre pasan por tu bot público, no por tu cuenta personal.
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                En resumen, esta integración se compone de: 1) tu cuenta personal de Telegram,
                2) una sesión MTProto segura en EMACE y 3) un bot público que puede crearse
                automáticamente y vincularse a tu tienda.
              </p>
            </div>
         
          </div>

          {!mtprotoStatus?.mtproto_enabled && (
          <div className="space-y-4 rounded-lg border border-slate-800/60 bg-black/20 p-3">
            <h3 className="text-sm font-semibold">Wizard de login MTProto</h3>
            <div className="flex flex-wrap gap-2 text-[11px] font-semibold uppercase tracking-wide">
              <span
                className={`px-2 py-1 rounded-full ${
                  mtprotoLoginStep === 1 ? 'bg-primary text-white' : 'bg-slate-800 text-slate-300'
                }`}
              >
                Paso 1 · Conectar cuenta
              </span>
              <span
                className={`px-2 py-1 rounded-full ${
                  mtprotoLoginStep === 2 ? 'bg-primary text-white' : 'bg-slate-800 text-slate-300'
                }`}
              >
                Paso 2 · Confirmar código
              </span>
              <span
                className={`px-2 py-1 rounded-full ${
                  mtprotoLoginStep === 3 ? 'bg-primary text-white' : 'bg-slate-800 text-slate-300'
                }`}
              >
                Paso 3 · Consentimiento
              </span>
            </div>

            {mtprotoLoginStep === 1 && (
              <div className="space-y-3 text-sm">
                <p className="text-slate-500 dark:text-slate-400">
                  Ingresá el número de teléfono de la cuenta de Telegram que vas a usar como
                  userbot. Esta cuenta es la que la integración de userbot va a usar para hablar
                  con BotFather y automatizar tareas.
                </p>
                <input
                  type="tel"
                  value={mtprotoPhone}
                  onChange={(e) => setMtprotoPhone(e.target.value)}
                  placeholder="Número de teléfono (ej. +54911...)"
                  className="w-full px-3 py-2 rounded-md border border-border-ui/60 bg-black/20 text-sm"
                />
                <Button
                  onClick={handleMtprotoInit}
                  disabled={
                    mtprotoSessionLoading ||
                    mtprotoStatusLoading ||
                    !mtprotoStatus?.allowed
                  }
                >
                  {mtprotoSessionLoading ? 'Enviando código...' : 'Enviar código'}
                </Button>
              </div>
            )}

            {mtprotoLoginStep === 2 && (
              <div className="space-y-3 text-sm">
                <p className="text-slate-500 dark:text-slate-400">
                  Ingresá el código que recibiste por Telegram. Si tardás demasiado, pedí un código nuevo.
                </p>
                <input
                  type="text"
                  value={mtprotoCode}
                  onChange={(e) => setMtprotoCode(e.target.value)}
                  placeholder="Código de Telegram (ej. 12345)"
                  className="w-full px-3 py-2 rounded-md border border-border-ui/60 bg-black/20 text-sm"
                />
                <Button
                  onClick={handleMtprotoConfirmCode}
                  disabled={
                    mtprotoSessionLoading ||
                    mtprotoStatusLoading ||
                    !mtprotoStatus?.allowed
                  }
                >
                  {mtprotoSessionLoading ? 'Confirmando...' : 'Confirmar código'}
                </Button>
                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    variant="secondary"
                    onClick={handleMtprotoResendCode}
                    disabled={
                      mtprotoSessionLoading ||
                      mtprotoStatusLoading ||
                      !mtprotoStatus?.allowed
                    }
                  >
                    {mtprotoSessionLoading ? 'Enviando...' : 'Pedir nuevo código'}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={handleMtprotoResetPhone}
                    disabled={mtprotoSessionLoading || mtprotoStatusLoading}
                  >
                    Cambiar número
                  </Button>
                </div>
              </div>
            )}

            {
              <div className="space-y-3 text-sm">
                <p className="text-slate-500 dark:text-slate-400">
                  La sesión MTProto está configurada. Aceptá los términos y habilitá la
                  integración de userbot. Después vas a poder usar esta sesión para crear
                  automáticamente un bot dedicado a tu tienda.
                </p>
                <label className="flex items-start gap-3 text-sm text-slate-200">
                  <input
                    type="checkbox"
                    checked={mtprotoAccepted}
                    onChange={(e) => setMtprotoAccepted(e.target.checked)}
                    className="mt-1 h-4 w-4 rounded border border-slate-600 bg-black/40"
                  />
                    <span>
                    Confirmo que leí y acepto los términos específicos de uso de la integración
                    de userbot MTProto, incluyendo límites, riesgos y políticas de uso aceptable.{' '}
                    <a
                      href="https://example.com/legal/telegram-mtproto"
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary underline-offset-4 hover:underline"
                    >
                      Ver términos completos
                    </a>
                    .
                  </span>
                </label>
                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    onClick={handleConsentAndEnable}
                    disabled={
                      mtprotoLoading ||
                      mtprotoStatus?.mtproto_enabled
                    }
                  >
                    {mtprotoLoading
                      ? 'Habilitando...'
                      : 'Guardar consentimiento y habilitar userbot'}
                  </Button>
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    La disponibilidad real puede depender de tu plan y aprobación manual.
                  </span>
                </div>
              </div>
            }
          </div>
          )}

          {mtprotoStatusLoading && !mtprotoStatus && (
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Cargando estado de la integración de userbot...
            </p>
          )}

          {mtprotoStatus && (
            <div className="space-y-3 rounded-lg border border-slate-800/60 bg-black/20 p-3">
              <h3 className="text-sm font-semibold">Estado de la integración de userbot</h3>
              <div className="flex flex-wrap items-center gap-3 text-xs">
                <span className="inline-flex items-center rounded-full border border-slate-700/60 bg-slate-900/40 px-2.5 py-1">
                  <span
                    className={`mr-2 h-2 w-2 rounded-full ${
                      !mtprotoStatus.allowed
                        ? 'bg-slate-500'
                        : mtprotoStatus.mtproto_enabled && !mtprotoStatus.last_error
                        ? 'bg-emerald-400'
                        : mtprotoStatus.last_error
                        ? 'bg-amber-400'
                        : 'bg-slate-500'
                    }`}
                  />
                  {!mtprotoStatus.allowed
                    ? 'No disponible'
                    : mtprotoStatus.mtproto_enabled && !mtprotoStatus.last_error
                    ? 'Saludable'
                    : mtprotoStatus.last_error
                    ? 'Degradado'
                    : 'Inactivo'}
                </span>
                {mtprotoStatus.last_heartbeat_at && (
                  <span className="text-slate-400">
                    Último heartbeat:{' '}
                    <span className="font-mono">
                      {new Date(mtprotoStatus.last_heartbeat_at).toLocaleString()}
                    </span>
                  </span>
                )}
                {mtprotoStatus.last_error && (
                  <span className="text-xs text-amber-400">
                    Último error: {mtprotoStatus.last_error}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                {mtprotoStatus.mtproto_enabled && (
                  <Button
                    variant="destructive"
                    onClick={handleMtprotoRevoke}
                    disabled={mtprotoSessionLoading || mtprotoStatusLoading}
                  >
                    Revocar sesión
                  </Button>
                )}
              </div>
            </div>
          )}

          {canAutoCreate && (
            <div className="space-y-3 rounded-lg border border-slate-800/60 bg-black/20 p-3">
              <h3 className="text-sm font-semibold">Crear bot automáticamente</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Usamos tu sesión de userbot MTProto para hablar con BotFather y crear un bot
                dedicado a tu tienda.
              </p>
              <label className="block text-xs text-slate-400">Nombre público del bot</label>
              <input
                type="text"
                value={autoBotName}
                onChange={(e) => setAutoBotName(e.target.value)}
                placeholder="Ej: Tienda Emace Assistant"
                className="w-full px-3 py-2 rounded-md border border-border-ui/60 bg-black/20 text-sm"
              />
              <label className="block text-xs text-slate-400">Username del bot</label>
              <input
                type="text"
                value={autoBotUsername}
                onChange={(e) => setAutoBotUsername(e.target.value)}
                placeholder="ej. emace_mitienda_bot"
                className="w-full px-3 py-2 rounded-md border border-border-ui/60 bg-black/20 text-sm"
              />
              <div className="flex items-center gap-3">
                <Button 
                  onClick={handleAutoCreate} 
                  disabled={autoBotStatus === 'creating' || hasIntegration}
                >
                  {autoBotStatus === 'creating' ? 'Creando...' : 'Crear bot automáticamente'}
                </Button>
                <span className="inline-flex items-center rounded-full border border-indigo-400/40 bg-indigo-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-indigo-300">
                  Estado:{' '}
                  <span className="ml-1 font-mono">
                    {autoBotStatus === 'none'
                      ? 'sin iniciar'
                      : autoBotStatus === 'creating'
                      ? 'creando'
                      : autoBotStatus === 'ready'
                      ? 'listo'
                      : 'error'}
                  </span>
                </span>
              </div>
              {autoBotError && <p className="text-xs text-amber-400">{autoBotError}</p>}
            </div>
          )}

          {mtprotoStatus?.mtproto_enabled && (
            <div className="space-y-4 rounded-lg border border-slate-800/60 bg-black/20 p-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold">Sincronizar bots existentes</h3>
                <Button 
                  onClick={handleDiscoverBots} 
                  disabled={discoveringBots || hasIntegration}
                  variant="secondary"
                  size="sm"
                >
                  {discoveringBots ? 'Buscando...' : 'Buscar mis bots en Telegram'}
                </Button>
              </div>
              
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Si ya tenés bots creados en tu cuenta de Telegram, podés buscarlos aquí. 
                Necesitarás el token que te dio BotFather para vincularlos.
              </p>

              {hasIntegration && (
                <p className="text-xs text-amber-400/80 font-medium bg-amber-400/5 p-2 rounded border border-amber-400/20">
                  Ya tenés un bot vinculado. Para vincular uno diferente, primero debés eliminar la integración actual.
                </p>
              )}

              {discoveredBots.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Bots encontrados:</p>
                  <div className="grid gap-2">
                    {discoveredBots.map((bot) => (
                      <div key={bot.username} className="flex items-center justify-between rounded border border-slate-800/40 bg-black/10 p-2">
                        <span className="font-mono text-sm text-slate-300">@{bot.username}</span>
                        <Button 
                          size="sm" 
                          variant="ghost"
                          className="text-xs"
                          disabled={hasIntegration}
                          onClick={() => {
                            const t = window.prompt(`Ingresá el token de BotFather para @${bot.username}`);
                            if (t) handleImportToken(t);
                          }}
                        >
                          Vincular con Token
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-2 border-t border-slate-800/40">
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">Vincular bot manualmente</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={manualToken}
                    onChange={(e) => setManualToken(e.target.value)}
                    placeholder="Token de BotFather (ej: 123456:ABC...)"
                    className="flex-1 px-3 py-1.5 rounded-md border border-border-ui/60 bg-black/20 text-xs font-mono"
                  />
                  <Button 
                    onClick={() => handleImportToken()} 
                    disabled={importingToken || !manualToken || hasIntegration}
                    size="sm"
                  >
                    {importingToken ? 'Vinculando...' : 'Vincular'}
                  </Button>
                </div>
              </div>
            </div>
          )}

    
        </div>
      </div>
    </div>
  );
}
