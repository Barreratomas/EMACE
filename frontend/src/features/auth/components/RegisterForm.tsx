'use client';

import { useState } from 'react';
import { registerAction } from '../actions/auth';
import { Shield, Lock, Mail, User, ArrowRight, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function RegisterForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const formData = new FormData(e.currentTarget);
    const password = formData.get('password') as string;
    const confirmPassword = formData.get('confirmPassword') as string;

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      setIsLoading(false);
      return;
    }

    if (password.length < 12) {
      setError('La contraseña debe tener al menos 12 caracteres');
      setIsLoading(false);
      return;
    }

    const userData = {
      email: formData.get('email'),
      password: password,
      name: formData.get('name'),
    };
    
    try {
      await registerAction({
        email: userData.email as string,
        password: userData.password,
        name: (userData.name as string) || '',
      });
      setSuccess(true);
      setTimeout(() => {
        window.location.href = '/auth/login';
      }, 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setIsLoading(false);
    }
  }

  const inputClasses = "w-full bg-slate-100/50 dark:bg-slate-900/50 border border-border-ui/50 p-4 text-slate-900 dark:text-slate-100 rounded-2xl focus:border-secondary/50 focus:ring-4 focus:ring-primary/5 outline-none transition-all placeholder:text-slate-500 font-medium text-sm pl-12";
  const labelClasses = "block text-[11px] uppercase tracking-wider font-bold text-slate-500 mb-2 ml-1";

  if (success) {
    return (
      <div className="w-full max-w-md animate-in fade-in zoom-in duration-500">
        <div className="panel-industrial p-12 text-center space-y-6 border-0 shadow-2xl">
          <div className="inline-flex p-6 bg-emerald-500/10 rounded-full text-emerald-500 mb-4 shadow-sm backdrop-blur-md">
            <Shield size={64} />
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight font-display">Registro Completado</h2>
          <p className="text-slate-500 font-medium text-sm">
            Credenciales validadas. Redireccionando al terminal de acceso...
          </p>
          <div className="flex justify-center gap-2">
            <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
            <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
            <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-bounce" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="panel-industrial p-0 overflow-hidden border-0 shadow-2xl">
        {/* Header */}
        <div className="border-b border-border-ui/50 p-10 bg-background/50 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1.5 bg-secondary" />
          <div className="absolute -right-10 -top-10 w-40 h-40 bg-secondary/5 rounded-full blur-3xl" />
          
          <div className="flex justify-between items-start mb-8 relative z-10">
            <div className="p-4 bg-secondary/10 rounded-2xl border border-secondary/20 text-secondary shadow-sm backdrop-blur-sm">
              <User size={28} />
            </div>
            <div className="text-right">
              <div className="text-[10px] font-bold text-slate-400 tracking-widest uppercase">Registro EMACE</div>
            </div>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display relative z-10">
            Crear Cuenta
          </h1>
          <p className="text-sm text-slate-500 font-medium mt-2 relative z-10">
            Solicite acceso al ecosistema digital.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-10 space-y-6 bg-background/30 backdrop-blur-sm">
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/20 p-4 rounded-2xl flex items-center gap-4 animate-in shake duration-500">
              <div className="w-1 h-10 bg-rose-500 rounded-full" />
              <p className="text-xs font-bold text-rose-600 dark:text-rose-400 uppercase tracking-tight">
                ERROR: {error}
              </p>
            </div>
          )}

          <div className="space-y-4">
            <div className="group">
              <label className={labelClasses}>Nombre Completo</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-secondary transition-colors" size={20} />
                <input
                  required
                  type="text"
                  name="name"
                  className={inputClasses}
                  placeholder="Ej: Juan Pérez"
                />
              </div>
            </div>

            <div className="group">
              <label className={labelClasses}>Correo Electrónico</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-secondary transition-colors" size={20} />
                <input
                  required
                  type="email"
                  name="email"
                  className={inputClasses}
                  placeholder="usuario@ejemplo.com"
                />
              </div>
            </div>

            <div className="group">
              <label className={labelClasses}>Contraseña</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-secondary transition-colors" size={20} />
                <input
                  required
                  type="password"
                  name="password"
                  className={inputClasses}
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <div className="group">
              <label className={labelClasses}>Confirmar Contraseña</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-secondary transition-colors" size={20} />
                <input
                  required
                  type="password"
                  name="confirmPassword"
                  className={inputClasses}
                  placeholder="••••••••••••"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-secondary text-slate-950 py-4 rounded-2xl font-bold flex items-center justify-center gap-3 text-sm group shadow-lg shadow-secondary/20 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:hover:scale-100"
          >
            {isLoading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <>
                Finalizar Registro
                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>

          <div className="text-center pt-2">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              ¿Ya tiene una cuenta?{' '}
              <Link href="/auth/login" className="text-secondary hover:text-secondary/80 transition-colors ml-1">
                Iniciar Sesión
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
