'use client';

import { useState } from 'react';
import { loginAction, loginIamAction } from '../actions/auth';
import { User, Lock, Mail, ArrowRight, Loader2, Building2, Users } from 'lucide-react';
import Link from 'next/link';

export default function LoginForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<'vendor' | 'iam'>('vendor');

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const formData = new FormData(e.currentTarget);
    
    try {
      if (mode === 'vendor') {
        await loginAction(formData);
      } else {
        if (!formData.get('vendor_identifier')) {
          throw new Error('Debe especificar el correo del Vendor');
        }
        await loginIamAction(formData);
      }
      window.location.href = '/inventory';
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setIsLoading(false);
    }
  }

  const inputClasses = "w-full bg-slate-100/50 dark:bg-slate-900/50 border border-border-ui/50 p-4 text-slate-900 dark:text-slate-100 rounded-2xl focus:border-primary/50 focus:ring-4 focus:ring-primary/5 outline-none transition-all placeholder:text-slate-500 font-medium text-sm pl-12";
  const labelClasses = "block text-[11px] uppercase tracking-wider font-bold text-slate-500 mb-2 ml-1";

  return (
    <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="panel-industrial p-0 overflow-hidden border-0 shadow-2xl">
        {/* Header */}
        <div className="border-b border-border-ui/50 p-10 bg-background/50 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1.5 bg-primary" />
          <div className="absolute -right-10 -top-10 w-40 h-40 bg-primary/5 rounded-full blur-3xl" />
          
          <div className="flex justify-between items-start mb-8 relative z-10">
            <div className="p-4 bg-primary/10 rounded-2xl border border-primary/20 text-primary shadow-sm backdrop-blur-sm">
              <User size={28} />
            </div>
            <div className="text-right">
              <div className="text-[10px] font-bold text-slate-400 tracking-widest uppercase">Acceso EMACE</div>
            </div>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display relative z-10">
            Bienvenido
          </h1>
          <p className="text-sm text-slate-500 font-medium mt-2 relative z-10">
            Inicie sesión para gestionar su ecosistema digital.
          </p>
          <div className="mt-6 bg-background/60 border border-border-ui/50 rounded-xl p-1 flex gap-1 w-full max-w-sm">
            <button
              type="button"
              onClick={() => setMode('vendor')}
              className={`flex-1 px-3 py-2 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all inline-flex items-center justify-center gap-2 ${mode === 'vendor' ? 'bg-primary text-white' : 'text-slate-500 hover:text-primary hover:bg-primary/5'}`}
            >
              <Building2 size={14} /> Usuarios
            </button>
            <button
              type="button"
              onClick={() => setMode('iam')}
              className={`flex-1 px-3 py-2 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all inline-flex items-center justify-center gap-2 ${mode === 'iam' ? 'bg-primary text-white' : 'text-slate-500 hover:text-primary hover:bg-primary/5'}`}
            >
              <Users size={14} /> Usuarios limitados
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-10 space-y-8 bg-background/30 backdrop-blur-sm">
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/20 p-4 rounded-2xl flex items-center gap-4 animate-in shake duration-500">
              <div className="w-1 h-10 bg-rose-500 rounded-full" />
              <p className="text-xs font-bold text-rose-600 dark:text-rose-400 uppercase tracking-tight">
                ERROR: {error}
              </p>
            </div>
          )}

          <div className="space-y-6">
            <div className="group">
              <label className={labelClasses}>Correo Electrónico</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" size={20} />
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
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" size={20} />
                <input
                  required
                  type="password"
                  name="password"
                  className={inputClasses}
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            {mode === 'iam' && (
              <div className="group">
                <label className={labelClasses}>Vendor (Email)</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" size={20} />
                  <input
                    required
                    type="email"
                    name="vendor_identifier"
                    className={inputClasses}
                    placeholder="vendor@empresa.com"
                  />
                </div>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary text-white py-4 rounded-2xl font-bold flex items-center justify-center gap-3 text-sm group shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:hover:scale-100"
          >
            {isLoading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <>
                Entrar al Sistema
                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>

          <div className="text-center pt-4">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              ¿No tiene una cuenta?{' '}
              <Link href="/auth/register" className="text-primary hover:text-primary/80 transition-colors ml-1">
                Registrarse
              </Link>
            </p>
          </div>
        </form>

      
      </div>
    </div>
  );
}
