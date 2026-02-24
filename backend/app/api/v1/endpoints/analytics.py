from typing import List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_tenant_owner_id
from app.core.config import settings
from app.core.database.models import (
    Product,
    User,
    Customer,
    Invoice,
    AuditLog,
    Order,
)
from app.core.database.session import get_async_session
from app.core.rate_limit import limiter


router = APIRouter()


class MetricItem(BaseModel):
    key: str
    label: str
    value: str
    trend: Optional[str] = None


class AuditStreamItem(BaseModel):
    timestamp: datetime
    level: str
    category: str
    message: str


@router.get("/metrics/system", response_model=List[MetricItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_system_metrics(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)
    metrics: List[MetricItem] = []
    operations_24h_result = await session.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_24h,
        )
    )
    operations_24h = operations_24h_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="system_operations_24h",
            label="Operaciones últimas 24h",
            value=str(operations_24h),
            trend=None,
        )
    )
    agents_active_result = await session.execute(
        select(func.count(func.distinct(AuditLog.agent_name))).where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_24h,
        )
    )
    agents_active = agents_active_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="system_agents_active_24h",
            label="Agentes activos 24h",
            value=str(agents_active),
            trend=None,
        )
    )
    logs_7d_result = await session.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_7d,
        )
    )
    logs_7d = logs_7d_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="system_audit_logs_7d",
            label="Eventos últimos 7d",
            value=str(logs_7d),
            trend=None,
        )
    )
    return metrics


@router.get("/metrics/inventory", response_model=List[MetricItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_inventory_metrics(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    metrics: List[MetricItem] = []
    products_result = await session.execute(
        select(func.count(Product.id)).where(
            Product.user_id == tenant_id,
            Product.status == "active",
        )
    )
    products_total = products_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="inventory_products_active",
            label="Productos activos",
            value=str(products_total),
            trend=None,
        )
    )
    low_stock_result = await session.execute(
        select(func.count(Product.id)).where(
            Product.user_id == tenant_id,
            Product.type == "physical",
            Product.stock.is_not(None),
            Product.stock <= func.coalesce(Product.min_stock_threshold, 5),
        )
    )
    low_stock = low_stock_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="inventory_low_stock_items",
            label="Productos con stock bajo",
            value=str(low_stock),
            trend=None,
        )
    )
    categories_result = await session.execute(
        select(func.count(func.distinct(Product.category))).where(
            Product.user_id == tenant_id,
        )
    )
    categories_total = categories_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="inventory_categories",
            label="Categorías de producto",
            value=str(categories_total),
            trend=None,
        )
    )
    inventory_value_result = await session.execute(
        select(
            func.coalesce(
                func.sum(
                    Product.price * func.coalesce(Product.stock, 0)
                ),
                0.0,
            )
        ).where(
            Product.user_id == tenant_id,
            Product.type == "physical",
            Product.stock.is_not(None),
        )
    )
    inventory_value = float(inventory_value_result.scalar() or 0.0)
    metrics.append(
        MetricItem(
            key="inventory_value_estimated",
            label="Valor inventario estimado",
            value=f"{inventory_value:.2f}",
            trend=None,
        )
    )
    return metrics


@router.get("/metrics/business", response_model=List[MetricItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_business_metrics(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    since_30d = now - timedelta(days=30)
    metrics: List[MetricItem] = []
    invoices_result = await session.execute(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.amount), 0.0),
        ).where(
            Invoice.user_id == tenant_id,
            Invoice.status == "paid",
            Invoice.issued_at >= since_30d,
        )
    )
    invoices_row = invoices_result.first()
    invoices_count = 0
    invoices_amount = 0.0
    if invoices_row:
        invoices_count = invoices_row[0] or 0
        invoices_amount = float(invoices_row[1] or 0.0)
    metrics.append(
        MetricItem(
            key="business_invoices_paid_30d",
            label="Facturas pagadas 30d",
            value=str(invoices_count),
            trend=None,
        )
    )
    metrics.append(
        MetricItem(
            key="business_revenue_30d",
            label="Ingresos 30d",
            value=f"{invoices_amount:.2f}",
            trend=None,
        )
    )
    customers_result = await session.execute(
        select(func.count(Customer.id)).where(Customer.user_id == tenant_id)
    )
    customers_total = customers_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="business_customers_total",
            label="Clientes totales",
            value=str(customers_total),
            trend=None,
        )
    )
    orders_result = await session.execute(
        select(func.count(Order.id)).where(
            Order.user_id == tenant_id,
            Order.created_at >= since_30d,
        )
    )
    orders_total = orders_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="business_orders_30d",
            label="Pedidos 30d",
            value=str(orders_total),
            trend=None,
        )
    )
    return metrics


@router.get("/audit/stream", response_model=List[AuditStreamItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_audit_stream(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    base_limit = limit + offset
    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.user_id == tenant_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(base_limit * 2)
    )
    logs = result.scalars().all()
    items: List[AuditStreamItem] = []
    category_filter = category.upper() if category else None
    for log in logs:
        text = (log.action or "") + " " + (log.details or "")
        lower_text = text.lower()
        derived_category = "SYSTEM"
        if "stock" in lower_text or "inventory" in lower_text or "product" in lower_text:
            derived_category = "INVENTORY"
        elif "sale" in lower_text or "order" in lower_text or "invoice" in lower_text:
            derived_category = "BUSINESS"
        elif "auth" in lower_text or "login" in lower_text or "register" in lower_text:
            derived_category = "AUTH"
        elif "latency" in lower_text or "network" in lower_text:
            derived_category = "NETWORK"
        elif "memory" in lower_text or "vector" in lower_text:
            derived_category = "MEMORY"
        elif log.agent_name:
            derived_category = "AGENT"
        level = "INFO"
        if "error" in lower_text or "fail" in lower_text or "exception" in lower_text:
            level = "ERROR"
        elif "warn" in lower_text or "high_load" in lower_text:
            level = "WARN"
        elif "success" in lower_text or "ok" in lower_text or "complete" in lower_text:
            level = "SUCCESS"
        if category_filter and derived_category != category_filter:
            continue
        message = log.details or log.action or ""
        items.append(
            AuditStreamItem(
                timestamp=log.timestamp,
                level=level,
                category=derived_category,
                message=message,
            )
        )
    sliced = items[offset : offset + limit]
    return sliced

