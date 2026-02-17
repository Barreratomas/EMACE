'use client';

import { useEffect, useMemo, useState } from 'react';
import { listIAMUsers, createIAMUser, setUserPolicies, getUserPolicies, IAMUser } from '../actions/iam';
import { toast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/Button';
import { Plus, Shield, Users, KeyRound, Save, X, CheckCircle2 } from 'lucide-react';

const POLICY_CATALOG = [
  { key: 'inventory:read', label: 'Inventario: Leer' },
  { key: 'inventory:write', label: 'Inventario: Escribir' },
  { key: 'knowledge:ingest', label: 'Conocimiento: Ingesta' },
  { key: 'billing:view', label: 'Facturación: Ver' },
  { key: 'chat:use', label: 'Chat: Usar' },
];

export default function TeamManager() {
  const [users, setUsers] = useState<IAMUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [policiesOpenFor, setPoliciesOpenFor] = useState<number | null>(null);
  const [policySelection, setPolicySelection] = useState<Record<number, Set<string>>>({});
  const [savingPolicies, setSavingPolicies] = useState(false);
  const [policySummary, setPolicySummary] = useState<Record<number, string[]>>({});

  useEffect(() => {
    (async () => {
      try {
        const data = await listIAMUsers();
        setUsers(data);
        // Prefetch resumen de políticas para cada usuario
        const summaries: Record<number, string[]> = {};
        await Promise.all(
          data.map(async (u) => {
            try {
              summaries[u.id] = await getUserPolicies(u.id);
            } catch {
              summaries[u.id] = [];
            }
          })
        );
        setPolicySummary(summaries);
      } catch (e: any) {
        toast.error(e.message || 'No se pudo cargar el equipo', 'IAM_LIST_ERROR');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const limitedUsers = useMemo(() => users, [users]);

  const togglePolicy = (userId: number, key: string) => {
    setPolicySelection((prev) => {
      const current = new Set(prev[userId] || []);
      if (current.has(key)) current.delete(key);
      else current.add(key);
      return { ...prev, [userId]: current };
    });
  };

  const handleSavePolicies = async (userId: number) => {
    setSavingPolicies(true);
    try {
      const selected = Array.from(policySelection[userId] || []);
      await setUserPolicies(userId, selected, 'set');
      toast.success('Políticas actualizadas', 'IAM_POLICIES_UPDATED');
      setPoliciesOpenFor(null);
    } catch (e: any) {
      toast.error(e.message || 'No se pudieron guardar las políticas', 'IAM_POLICIES_ERROR');
    } finally {
      setSavingPolicies(false);
    }
  };

  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display">Gestión de Equipo (IAM)</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-2 font-medium">
            Crea usuarios limitados y asigna políticas de acceso granulares.
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)} variant="default" className="gap-2">
          <Plus size={16} /> Crear Usuario Limitado
        </Button>
      </div>

      <div className="panel-industrial p-0 overflow-hidden border-0 shadow-xl">
        <div className="grid grid-cols-6 gap-0 border-b border-border-ui/50 bg-background/50 backdrop-blur-md">
          <div className="p-5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Nombre</div>
          <div className="p-5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Email</div>
          <div className="p-5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Estado</div>
          <div className="p-5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Rol</div>
          <div className="p-5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Última Conexión</div>
          <div className="p-5 text-[10px] font-bold text-slate-500 uppercase tracking-widest text-right">Acciones</div>
        </div>
        <div className="divide-y divide-border-ui/30">
          {loading ? (
            <div className="p-12 text-center text-slate-400 text-sm">Cargando usuarios...</div>
          ) : limitedUsers.length === 0 ? (
            <div className="p-20 text-center flex flex-col items-center gap-4">
              <div className="w-16 h-16 rounded-3xl bg-slate-100 dark:bg-slate-900 flex items-center justify-center text-slate-300">
                <Users size={32} />
              </div>
              <p className="text-sm font-bold text-slate-400 uppercase tracking-wider">Sin usuarios limitados registrados</p>
            </div>
          ) : (
            limitedUsers.map((u) => (
              <div key={u.id} className="grid grid-cols-6 gap-0 hover:bg-primary/2 transition-colors group">
                <div className="p-5 flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-primary/10 text-primary border border-primary/20">
                    <Users size={16} />
                  </div>
                  <div className="text-sm font-bold text-slate-900 dark:text-slate-100">{u.name}</div>
                </div>
                <div className="p-5 flex items-center text-xs text-slate-600 dark:text-slate-400">{u.email}</div>
                <div className="p-5 flex items-center">
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-lg border ${u.is_active ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20' : 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-slate-800/50 dark:border-slate-700'}`}>
                    {u.is_active ? 'Activo' : 'Inactivo'}
                  </span>
                </div>
                <div className="p-5 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                  IAM User
                </div>
                <div className="p-5 flex items-center text-[10px] font-bold uppercase tracking-widest text-slate-500">
                  {u.last_login ? new Date(u.last_login).toLocaleString() : '—'}
                </div>
                <div className="p-5 flex items-center justify-end gap-2">
                  <div className="hidden md:flex gap-1 mr-3">
                    {(policySummary[u.id] || []).slice(0, 3).map((name) => (
                      <span key={name} className="px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-[10px] font-bold uppercase tracking-widest text-slate-600 border border-slate-200 dark:border-slate-700">
                        {name}
                      </span>
                    ))}
                    {((policySummary[u.id] || []).length > 3) && (
                      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">+{(policySummary[u.id] || []).length - 3}</span>
                    )}
                  </div>
                  <button
                    onClick={async () => {
                      if (policiesOpenFor === u.id) {
                        setPoliciesOpenFor(null);
                        return;
                      }
                      try {
                        const current = await getUserPolicies(u.id);
                        setPolicySelection((prev) => ({ ...prev, [u.id]: new Set(current) }));
                        setPoliciesOpenFor(u.id);
                      } catch (e: any) {
                        toast.error(e.message || 'No se pudieron cargar las políticas', 'IAM_POLICIES_FETCH_ERROR');
                      }
                    }}
                    className="px-3 py-2 rounded-xl bg-background/50 border border-border-ui/50 text-slate-600 hover:text-primary hover:border-primary/50 hover:shadow-lg transition-all text-[11px] font-bold uppercase tracking-wider flex items-center gap-2"
                  >
                    <Shield size={14} /> Políticas
                  </button>
                </div>
                {policiesOpenFor === u.id && (
                  <div className="col-span-5 border-t border-border-ui/30 bg-background/60">
                    <div className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                      <div className="flex flex-wrap gap-2">
                        {POLICY_CATALOG.map((p) => {
                          const selected = policySelection[u.id]?.has(p.key) ?? false;
                          return (
                            <label key={p.key} className={`px-3 py-2 rounded-xl border text-[11px] font-bold uppercase tracking-wider cursor-pointer transition-all ${selected ? 'bg-primary text-white border-primary/20' : 'bg-white dark:bg-slate-900 text-slate-600 border-border-ui/50 hover:border-primary/40'}`}>
                              <input
                                type="checkbox"
                                checked={selected}
                                onChange={() => togglePolicy(u.id, p.key)}
                                className="hidden"
                              />
                              <span className="inline-flex items-center gap-2">
                                <KeyRound size={14} /> {p.label}
                              </span>
                            </label>
                          );
                        })}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setPoliciesOpenFor(null)}
                          className="px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-border-ui/50 text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all text-[11px] font-bold uppercase tracking-wider flex items-center gap-2"
                        >
                          <X size={14} /> Cancelar
                        </button>
                        <button
                          onClick={() => handleSavePolicies(u.id)}
                          disabled={savingPolicies}
                          className="px-3 py-2 rounded-xl bg-primary text-white hover:shadow-primary/20 hover:shadow-lg transition-all text-[11px] font-bold uppercase tracking-wider flex items-center gap-2"
                        >
                          <Save size={14} /> Guardar
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {showCreate && <CreateUserModal onClose={() => setShowCreate(false)} onSubmit={async (payload) => {
        setCreating(true);
        try {
          const created = await createIAMUser(payload);
          setUsers((prev) => [created, ...prev]);
          toast.success('Usuario creado', 'IAM_USER_CREATED');
          setShowCreate(false);
        } catch (e: any) {
          toast.error(e.message || 'No se pudo crear el usuario', 'IAM_CREATE_ERROR');
        } finally {
          setCreating(false);
        }
      }} creating={creating} />}
    </div>
  );
}

function CreateUserModal({ onClose, onSubmit, creating }: { onClose: () => void; onSubmit: (payload: { name: string; email: string; password: string }) => Promise<void>; creating: boolean; }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const generatePassword = () => {
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}';
    const len = 14;
    let pass = '';
    for (let i = 0; i < len; i++) {
      pass += chars[Math.floor(Math.random() * chars.length)];
    }
    setPassword(pass);
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-300">
      <div className="panel-industrial p-0 w-full max-w-lg overflow-hidden border-0 shadow-2xl">
        <div className="border-b border-border-ui/50 p-6 flex justify-between items-center bg-background/50 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg text-primary">
              <Users size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight font-display">Nuevo Usuario Limitado</h2>
              <p className="text-xs text-slate-500">Ligado automáticamente al vendor actual</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all text-slate-500">
            <X size={20} />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Nombre</label>
            <input value={name} onChange={(e) => setName(e.target.value)} className="w-full px-3 py-2 rounded-xl border border-border-ui/50 bg-white dark:bg-slate-900 text-sm" placeholder="Nombre completo" />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-3 py-2 rounded-xl border border-border-ui/50 bg-white dark:bg-slate-900 text-sm" placeholder="usuario@empresa.com" />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Contraseña</label>
            <div className="flex gap-2">
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-3 py-2 rounded-xl border border-border-ui/50 bg-white dark:bg-slate-900 text-sm" placeholder="Mínimo 12 caracteres" />
              <button onClick={generatePassword} type="button" className="px-3 py-2 rounded-xl bg-background/50 border border-border-ui/50 text-[11px] font-bold uppercase tracking-wider hover:border-primary/50 hover:text-primary transition-all">
                Generar
              </button>
            </div>
          </div>
        </div>
        <div className="p-6 flex items-center justify-end gap-2 bg-background/40 border-t border-border-ui/50">
          <button onClick={onClose} className="px-4 py-2 rounded-xl bg-white dark:bg-slate-900 border border-border-ui/50 text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all text-[11px] font-bold uppercase tracking-wider">
            Cancelar
          </button>
          <button
            onClick={() => onSubmit({ name, email, password })}
            disabled={creating}
            className="px-4 py-2 rounded-xl bg-primary text-white hover:shadow-primary/20 hover:shadow-lg transition-all text-[11px] font-bold uppercase tracking-wider inline-flex items-center gap-2"
          >
            <CheckCircle2 size={14} /> Crear
          </button>
        </div>
      </div>
    </div>
  );
}
