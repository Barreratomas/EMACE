from typing import List, Optional, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from app.domain.ports.repositories import IAuditRepository, IProductRepository, IBillingRepository

class DashboardStat(BaseModel):
    key: str
    label: str
    value: str
    trend: Optional[str] = None
    trend_direction: Optional[str] = None

class DashboardAgentSummary(BaseModel):
    name: str
    status: str
    load: int
    activity: Optional[str] = None
    type: Optional[str] = None

class DashboardChartPoint(BaseModel):
    timestamp: datetime
    total_events: int

class DashboardOverviewResponse(BaseModel):
    stats: List[DashboardStat]
    agents: List[DashboardAgentSummary]
    chart_24h: List[DashboardChartPoint]

class DashboardUseCases:
    def __init__(
        self, 
        audit_repo: IAuditRepository, 
        product_repo: IProductRepository,
        billing_repo: IBillingRepository
    ):
        self.audit_repo = audit_repo
        self.product_repo = product_repo
        self.billing_repo = billing_repo

    async def get_overview(self, session: Any, user_id: int) -> DashboardOverviewResponse:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        since_24h = now - timedelta(hours=24)
        
        # Stats
        stats: List[DashboardStat] = []
        
        products_active = await self.product_repo.count_active_products(session, user_id)
        stats.append(DashboardStat(key="products_active", label="Productos activos", value=str(products_active)))
        
        customers_total = await self.billing_repo.count_customers(session, user_id)
        stats.append(DashboardStat(key="customers_total", label="Clientes", value=str(customers_total)))
        
        paid_summary = await self.billing_repo.get_paid_invoices_summary(session, user_id)
        stats.append(DashboardStat(key="revenue_total", label="Ingresos totales", value=f"${paid_summary['total']:.2f}"))
        
        # Agents (Simulated or from a more complex logic if needed)
        agents = [
            DashboardAgentSummary(name="Sales Agent", status="active", load=20, activity="Procesando pedido #102", type="sales"),
            DashboardAgentSummary(name="Support Agent", status="active", load=5, activity="Respondiendo FAQ", type="support"),
            DashboardAgentSummary(name="Ops Agent", status="idle", load=0, activity=None, type="ops"),
        ]
        
        # Chart 24h (Simulated for now as per original code or implement in repo)
        chart_24h = []
        for i in range(24):
            point_time = since_24h + timedelta(hours=i)
            chart_24h.append(DashboardChartPoint(timestamp=point_time, total_events=10 + (i * 2) % 15))
            
        return DashboardOverviewResponse(
            stats=stats,
            agents=agents,
            chart_24h=chart_24h
        )
