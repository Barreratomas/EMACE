'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Package, 
  Users, 
  Settings, 
  Activity, 
  Shield, 
  Terminal,
  LogOut,
  MessageCircle,
} from 'lucide-react';
import { logout } from '@/features/auth/actions/auth';
import { cn } from '@/lib/utils';

const menuItems = [
  { icon: LayoutDashboard, label: 'DASHBOARD_GENERAL', href: '/dashboard' },
  { icon: Package, label: 'GESTIÓN_INVENTARIO', href: '/inventory' },
  { icon: Terminal, label: 'BASE_CONOCIMIENTO', href: '/knowledge' },
  { icon: Users, label: 'PANEL_AGENTES', href: '/agents' },
  { icon: Activity, label: 'MÉTRICAS_SISTEMA', href: '/analytics' },
  // { icon: Settings, label: 'CONFIGURACIÓN', href: '/settings' },
  { icon: Settings, label: 'IAM', href: '/settings/iam' },
  { icon: Settings, label: 'EMAIL_TEMPLATES', href: '/settings/emails' },
  { icon: Settings, label: 'CENTRO_NOTIFICACIONES', href: '/settings/notifications' },
  { icon: Settings, label: 'BILLING', href: '/settings/billing' },
  { icon: MessageCircle, label: 'TELEGRAM', href: '/settings/telegram' },
];

export default function Sidebar() {
  const pathname = usePathname();

  const activeItem = [...menuItems]
    .sort((a, b) => b.href.length - a.href.length)
    .find(item => pathname.startsWith(item.href));

  return (
    <aside className="w-64 panel-industrial rounded-none! border-y-0! border-l-0! flex flex-col h-screen sticky top-0 z-10">
      {/* Logo Area */}
      <div className="p-8 border-b border-border-ui/50 relative overflow-hidden group">
        <div className="flex items-center gap-4 relative z-10">
          <div className="w-10 h-10 bg-primary/10 flex items-center justify-center text-primary shadow-[0_0_15px_rgba(255,95,31,0.2)] border border-primary/30">
            <Shield size={22} />
          </div>
          <div>
            <div className="text-lg font-bold tracking-tighter terminal-text">EMACE</div>
            <div className="text-[9px] font-bold text-cyber-lime uppercase tracking-[0.3em] opacity-80">Command Center</div>
          </div>
        </div>
        {/* Decorative scanning line */}
        <div className="absolute inset-0 bg-linear-to-b from-transparent via-primary/5 to-transparent h-1/2 -translate-y-full group-hover:animate-scan pointer-events-none" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto custom-scrollbar">
        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.25em] mb-4 px-3 opacity-50 terminal-text">
          Operations_Control
        </div>
        
        {menuItems.map((item) => {
          const isActive = activeItem?.href === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 px-4 py-2.5 transition-all duration-200 relative overflow-hidden border border-transparent",
                isActive 
                  ? "bg-primary/10 text-primary border-primary/20 shadow-[inset_0_0_10px_rgba(255,95,31,0.05)]" 
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-primary shadow-[0_0_10px_rgba(255,95,31,0.5)]" />
              )}
              
              <item.icon size={18} className={cn(
                "transition-all",
                isActive ? "text-primary scale-110" : "text-slate-500 group-hover:text-slate-300"
              )} />
              <span className="text-[13px] font-semibold tracking-tight terminal-text">
                {item.label}
              </span>

              {isActive && (
                <div className="absolute right-2 w-1 h-1 bg-primary rounded-full animate-pulse" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* System Status */}
      <div className="p-4 border-t border-border-ui/50 bg-black/20">
        <div className="bg-steel/40 p-3 border border-white/5 relative group overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest terminal-text">System_Pulse</span>
            <div className="flex gap-1">
              <div className="w-1 h-1 bg-cyber-lime rounded-full animate-pulse" />
              <div className="w-1 h-1 bg-cyber-lime rounded-full animate-pulse [animation-delay:200ms]" />
            </div>
          </div>
          <div className="flex items-center gap-2 opacity-70">
            <Terminal size={12} className="text-cyber-lime" />
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-tighter">v2.0.4_STABLE</span>
          </div>
          {/* Scanning effect on hover */}
          <div className="absolute inset-0 bg-linear-to-r from-transparent via-cyber-lime/5 to-transparent -translate-x-full group-hover:animate-scan-horizontal pointer-events-none" />
        </div>
        
        <button 
          onClick={() => logout()}
          className="w-full mt-4 flex items-center justify-center gap-2 py-2 text-[11px] font-bold text-rose-500/80 hover:text-rose-500 hover:bg-rose-500/5 border border-transparent hover:border-rose-500/20 transition-all terminal-text"
        >
          <LogOut size={14} />
          <span>TERMINATE_SESSION</span>
        </button>
      </div>
    </aside>
  );
}
