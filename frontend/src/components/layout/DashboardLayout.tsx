'use client';

import Sidebar from './Sidebar';
import TopBar from './TopBar';
import dynamic from 'next/dynamic';
import { Suspense } from 'react';
const ChatInterface = dynamic(() => import('@/features/chat/components/ChatInterface'), { ssr: false });

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-midnight text-foreground selection:bg-primary/20" aria-label="System Command Center Layout">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 relative h-screen overflow-y-auto custom-scrollbar">
        <TopBar />
        <main id="main-content" className="flex-1 p-4 md:p-6 relative z-20">
          <div className="max-w-1600px mx-auto">
            <Suspense fallback={
              <div className="flex items-center justify-center min-h-400px">
                <div className="flex flex-col items-center gap-4">
                  <div className="w-10 h-10 border-2 border-primary/20 border-t-primary animate-spin" />
                  <div className="h-2 w-24 bg-white/5 overflow-hidden relative">
                    <div className="absolute inset-0 bg-primary/40 animate-progress" />
                  </div>
                  <span className="text-[10px] font-bold terminal-text text-primary/60 animate-pulse">INITIALIZING_SYSTEM...</span>
                </div>
              </div>
            }>
              {children}
            </Suspense>
          </div>
        </main>

       
      </div>
      <Suspense fallback={null}>
        <ChatInterface />
      </Suspense>
    </div>
  );
}
