from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from app.domain.ports.repositories import IAuditRepository, IProductRepository, IBillingRepository

class MetricItem(BaseModel):
    key: str
    value: str
    trend: Optional[str] = None

class DashboardAgentSummary(BaseModel):
    name: str
    status: str
    load: int
    activity: Optional[str] = None
    type: Optional[str] = None

class DashboardChartPoint(BaseModel):
    timestamp: datetime
    total_events: int

class DashboardViewResponse(BaseModel):
    highlights: List[MetricItem]
    agents: List[DashboardAgentSummary]
    chart_24h: List[DashboardChartPoint]
    activity: List[Dict[str, Any]]

class AnalyticsUseCases:
    def __init__(
        self, 
        audit_repo: IAuditRepository, 
        product_repo: IProductRepository,
        billing_repo: IBillingRepository
    ):
        self.audit_repo = audit_repo
        self.product_repo = product_repo
        self.billing_repo = billing_repo

    async def get_system_metrics(self, session: Any, user_id: int) -> List[MetricItem]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        since_24h = now - timedelta(hours=24)
        since_7d = now - timedelta(days=7)
        
        operations_24h = await self.audit_repo.count_logs_by_user(session, user_id, since_24h)
        agents_active = await self.audit_repo.count_distinct_agents(session, user_id, since_24h)
        logs_7d = await self.audit_repo.count_logs_by_user(session, user_id, since_7d)
        
        return [
            MetricItem(
                key="system_operations_24h",
                value=str(operations_24h),
            ),
            MetricItem(
                key="system_agents_active_24h",
                value=str(agents_active),
            ),
            MetricItem(
                key="system_audit_logs_7d",
                value=str(logs_7d),
            )
        ]

    async def get_inventory_metrics(self, session: Any, user_id: int) -> List[MetricItem]:
        products_total = await self.product_repo.count_active_products(session, user_id)
        low_stock = await self.product_repo.count_low_stock_products(session, user_id)
        categories_total = await self.product_repo.count_categories(session, user_id)
        inventory_value = await self.product_repo.get_estimated_inventory_value(session, user_id)
        
        return [
            MetricItem(
                key="inventory_products_active",
                value=str(products_total),
            ),
            MetricItem(
                key="inventory_low_stock_items",
                value=str(low_stock),
            ),
            MetricItem(
                key="inventory_categories",
                value=str(categories_total),
            ),
            MetricItem(
                key="inventory_value_estimated",
                value=f"{inventory_value:.2f}",
            )
        ]

    async def get_business_metrics(self, session: Any, user_id: int) -> List[MetricItem]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        since_30d = now - timedelta(days=30)
        
        paid_summary = await self.billing_repo.get_paid_invoices_summary(session, user_id, since_30d)
        customers_total = await self.billing_repo.count_customers(session, user_id)
        unpaid_summary = await self.billing_repo.get_unpaid_invoices_summary(session, user_id)
        pending_orders = await self.billing_repo.count_orders_by_status(session, user_id, "pending")
        
        return [
            MetricItem(
                key="business_revenue_30d",
                value=f"{paid_summary['total']:.2f}",
            ),
            MetricItem(
                key="business_customers_total",
                value=str(customers_total),
            ),
            MetricItem(
                key="business_pending_revenue",
                value=f"{unpaid_summary['total']:.2f}",
            ),
            MetricItem(
                key="business_pending_orders",
                value=str(pending_orders),
            )
        ]

    async def get_dashboard_view(self, session: Any, user_id: int) -> DashboardViewResponse:
        # 1. Get highlights (consolidated from different areas)
        system = await self.get_system_metrics(session, user_id)
        inventory = await self.get_inventory_metrics(session, user_id)
        business = await self.get_business_metrics(session, user_id)
        
        # Select key metrics for the top highlights
        highlights = [
            next((m for m in inventory if m.key == "inventory_products_active"), None),
            next((m for m in business if m.key == "business_customers_total"), None),
            next((m for m in business if m.key == "business_revenue_30d"), None),
            next((m for m in system if m.key == "system_operations_24h"), None),
        ]
        # Filter out None and ensure we have labels/values
        highlights = [h for h in highlights if h is not None]

        # 2. Get agents, chart and activity
        agents = await self.get_agents_status(session, user_id)
        chart = await self.get_performance_chart(session, user_id)
        activity = await self.get_audit_stream(session, user_id, limit=10)

        return DashboardViewResponse(
            highlights=highlights,
            agents=agents,
            chart_24h=chart,
            activity=activity
        )

    async def get_audit_stream(self, session: Any, user_id: int, limit: int = 100) -> List[Any]:
        logs = await self.audit_repo.get_logs_by_user(session, user_id, limit=limit)
        return [
            {
                "timestamp": log.timestamp,
                "level": self._derive_level(log.action),
                "agent_name": log.agent_name,
                "action": log.action,
                "details": log.details,
            }
            for log in logs
        ]

    async def get_performance_chart(self, session: Any, user_id: int) -> List[DashboardChartPoint]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        since_24h = now - timedelta(hours=24)
        
        # simulated for now
        chart_24h = []
        for i in range(24):
            point_time = since_24h + timedelta(hours=i)
            chart_24h.append(DashboardChartPoint(timestamp=point_time, total_events=10 + (i * 2) % 15))
        return chart_24h

    async def get_agents_status(self, session: Any, user_id: int) -> List[DashboardAgentSummary]:
        # simulated for now
        return [
            DashboardAgentSummary(name="Sales Agent", status="Online", load=20, activity="Procesando pedido #102", type="sales"),
            DashboardAgentSummary(name="Support Agent", status="Online", load=5, activity="Respondiendo FAQ", type="support"),
            DashboardAgentSummary(name="Ops Agent", status="Offline", load=0, activity=None, type="ops"),
        ]

    def _derive_level(self, action: Optional[str]) -> str:
        lower_action = (action or "").lower()
        if any(word in lower_action for word in ["error", "fail", "exception"]):
            return "ERROR"
        elif any(word in lower_action for word in ["warn", "high_load"]):
            return "WARN"
        elif any(word in lower_action for word in ["success", "ok", "complete"]):
            return "OK"
        return "INFO"
