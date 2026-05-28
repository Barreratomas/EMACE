'use client';

import { Bell, Search, Command, Sun, Moon, Globe } from 'lucide-react';
import { useState, useEffect } from 'react';
import Link from 'next/link';

function getInitialTheme(): 'dark' | 'light' {
  if (typeof window === 'undefined') return 'dark';
  return (localStorage.getItem('theme') as 'dark' | 'light') ?? 'dark';
}

export default function TopBar() {
  const [theme, setTheme] = useState<'dark' | 'light'>(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  function toggleTheme() {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  }

  return (
    <header className="h-16 panel-industrial rounded-none! border-x-0! border-t-0! sticky top-0 z-30 px-6 flex items-center justify-between" aria-label="System navigation bar">
      <div className="flex items-center gap-6 flex-1">
        <div className="relative group max-w-md w-full">
          <Search aria-hidden className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" size={14} />
          <input
            type="text"
            placeholder="EXECUTE_SEARCH..."
            className="w-full bg-black/40 border border-white/5 py-1.5 pl-10 pr-12 text-[12px] terminal-text focus:border-primary/40 focus:bg-black/60 outline-none transition-all placeholder:text-slate-600"
            aria-label="Search"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 px-1.5 py-0.5 bg-white/5 border border-white/10 text-[9px] font-bold text-slate-500 terminal-text">
            <Command size={8} /> K
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <button className="relative p-2 text-slate-500 hover:text-primary transition-all" aria-label="Notifications">
            <Bell size={18} />
            <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-primary shadow-[0_0_5px_rgba(255,95,31,0.5)]" />
          </button>

          <button onClick={toggleTheme} className="p-2 text-slate-500 hover:text-primary transition-all" aria-label="Toggle theme">
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          <div className="flex items-center gap-1 bg-black/40 px-2 py-1 border border-white/5 ml-2">
            <Globe size={12} className="text-slate-500" />
            <div className="flex items-center text-[10px] font-bold terminal-text">
              <Link href="/es" className="px-1 text-slate-500 hover:text-primary">ES</Link>
              <span className="text-white/10">/</span>
              <Link href="/en" className="px-1 text-primary">EN</Link>
            </div>
          </div>
        </div>

        <div className="ml-2 w-8 h-8 bg-primary/20 border border-primary/40 flex items-center justify-center font-bold text-[10px] terminal-text text-primary shadow-[0_0_10px_rgba(255,95,31,0.1)]">
          AD_01
        </div>
      </div>
    </header>
  );
}