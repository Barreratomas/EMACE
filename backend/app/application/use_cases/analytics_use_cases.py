from typing import List, Optional, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from app.domain.ports.repositories import IAuditRepository, IProductRepository, IBillingRepository

class MetricItem(BaseModel):
    key: str
    label: str
    value: str
    trend: Optional[str] = None

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
                label="Operaciones últimas 24h",
                value=str(operations_24h),
            ),
            MetricItem(
                key="system_agents_active_24h",
                label="Agentes activos 24h",
                value=str(agents_active),
            ),
            MetricItem(
                key="system_audit_logs_7d",
                label="Eventos últimos 7d",
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
                label="Productos activos",
                value=str(products_total),
            ),
            MetricItem(
                key="inventory_low_stock_items",
                label="Productos con stock bajo",
                value=str(low_stock),
            ),
            MetricItem(
                key="inventory_categories",
                label="Categorías de producto",
                value=str(categories_total),
            ),
            MetricItem(
                key="inventory_value_estimated",
                label="Valor inventario estimado",
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
                label="Ingresos (30d)",
                value=f"{paid_summary['total']:.2f}",
            ),
            MetricItem(
                key="business_customers_total",
                label="Clientes totales",
                value=str(customers_total),
            ),
            MetricItem(
                key="business_pending_revenue",
                label="Pendiente de cobro",
                value=f"{unpaid_summary['total']:.2f}",
            ),
            MetricItem(
                key="business_pending_orders",
                label="Pedidos pendientes",
                value=str(pending_orders),
            )
        ]

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

    def _derive_level(self, action: Optional[str]) -> str:
        lower_action = (action or "").lower()
        if any(word in lower_action for word in ["error", "fail", "exception"]):
            return "ERROR"
        elif any(word in lower_action for word in ["warn", "high_load"]):
            return "WARN"
        elif any(word in lower_action for word in ["success", "ok", "complete"]):
            return "OK"
        return "INFO"
