import { getAnalyticsOverview, AnalyticsDashboard } from '@/features/analytics';

export const dynamic = 'force-dynamic';

export default async function AnalyticsPage() {
  const data = await getAnalyticsOverview();

  return (
    <div className="container mx-auto py-10 px-4">
      <AnalyticsDashboard initialData={data} />
    </div>
  );
}
