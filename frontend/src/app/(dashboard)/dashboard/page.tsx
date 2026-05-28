import { 
  getDashboardView,
  DashboardManager 
} from '@/features/dashboard';

export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  // Fetch consolidated dashboard view from Analytics
  const dashboardView = await getDashboardView();

  if (!dashboardView) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <p className="text-slate-500 font-mono text-xs uppercase tracking-widest animate-pulse">
          ERROR_LOADING_DASHBOARD_DATA
        </p>
      </div>
    );
  }

  return (
    <DashboardManager dashboardView={dashboardView} />
  );
}
