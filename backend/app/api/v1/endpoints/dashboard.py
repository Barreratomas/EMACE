from typing import List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_tenant_owner_id
from app.core.config import settings
from app.core.database.models import Product, User, Customer, Invoice, AuditLog
from app.core.database.session import get_async_session
from app.core.rate_limit import limiter


router = APIRouter()


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


class DashboardActivityItem(BaseModel):
    id: int
    type: str
    message: str
    timestamp: datetime


@router.get("/overview", response_model=DashboardOverviewResponse)
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_dashboard_overview(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    since_24h = now - timedelta(hours=24)
    since_30d = now - timedelta(days=30)

    stats: List[DashboardStat] = []

    products_result = await session.execute(
        select(func.count(Product.id)).where(
            Product.user_id == tenant_id,
            Product.status == "active",
        )
    )
    products_total = products_result.scalar() or 0
    stats.append(
        DashboardStat(
            key="products_active",
            label="Productos activos",
            value=str(products_total),
        )
    )

    customers_result = await session.execute(
        select(func.count(Customer.id)).where(Customer.user_id == tenant_id)
    )
    customers_total = customers_result.scalar() or 0
    stats.append(
        DashboardStat(
            key="customers_total",
            label="Clientes",
            value=str(customers_total),
        )
    )

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
    stats.append(
        DashboardStat(
            key="invoices_paid_30d",
            label="Facturas pagadas (30d)",
            value=f"{invoices_count} / {invoices_amount:.2f}",
        )
    )

    operations_result = await session.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_24h,
        )
    )
    operations_total = operations_result.scalar() or 0
    stats.append(
        DashboardStat(
            key="operations_24h",
            label="Operaciones 24h",
            value=str(operations_total),
        )
    )

    agents: List[DashboardAgentSummary] = []
    agents_result = await session.execute(
        select(
            AuditLog.agent_name,
            func.count(AuditLog.id),
            func.max(AuditLog.timestamp),
        )
        .where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_24h,
        )
        .group_by(AuditLog.agent_name)
    )
    agent_rows = agents_result.all()
    max_events = max((row[1] for row in agent_rows), default=0)
    for agent_name, event_count, last_ts in agent_rows:
        load = int((event_count / max_events) * 100) if max_events > 0 else 0
        status_label = "Offline"
        if last_ts:
            if last_ts >= now - timedelta(minutes=15):
                status_label = "Online"
                if load > 70:
                    status_label = "Busy"
        activity_label = None
        if last_ts:
            delta = now - last_ts
            if delta.days >= 1:
                activity_label = f"Hace {delta.days}d"
            else:
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                if hours > 0:
                    activity_label = f"Hace {hours}h"
                elif minutes > 0:
                    activity_label = f"Hace {minutes}m"
                else:
                    activity_label = "Hace segundos"
        agent_type = "System"
        upper_name = agent_name.upper()
        if "VENTAS" in upper_name:
            agent_type = "Client"
        elif "LOGISTICA" in upper_name:
            agent_type = "Core"
        elif "ANALITICA" in upper_name:
            agent_type = "Service"
        agents.append(
            DashboardAgentSummary(
                name=agent_name,
                status=status_label,
                load=load,
                activity=activity_label,
                type=agent_type,
            )
        )

    chart_points: List[DashboardChartPoint] = []
    audit_result = await session.execute(
        select(AuditLog.timestamp).where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_24h,
        )
    )
    timestamps = audit_result.scalars().all()
    bucket_counts = {}
    for ts in timestamps:
        bucket_ts = ts.replace(minute=0, second=0, microsecond=0)
        key = bucket_ts
        bucket_counts[key] = bucket_counts.get(key, 0) + 1
    start_bucket = since_24h.replace(minute=0, second=0, microsecond=0)
    for i in range(24):
        bucket_ts = start_bucket + timedelta(hours=i)
        count = bucket_counts.get(bucket_ts, 0)
        chart_points.append(
            DashboardChartPoint(
                timestamp=bucket_ts,
                total_events=count,
            )
        )

    overview = DashboardOverviewResponse(
        stats=stats,
        agents=agents,
        chart_24h=chart_points,
    )
    return overview


@router.get("/activity/recent", response_model=List[DashboardActivityItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_recent_activity(
    request: Request,
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.user_id == tenant_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    items: List[DashboardActivityItem] = []
    for log in logs:
        level = "info"
        lower_action = (log.action or "").lower()
        if "error" in lower_action or "fail" in lower_action or "exception" in lower_action:
            level = "error"
        elif "warn" in lower_action or "high_load" in lower_action:
            level = "warning"
        elif "success" in lower_action or "ok" in lower_action or "complete" in lower_action:
            level = "success"
        text = log.details or log.action or ""
        items.append(
            DashboardActivityItem(
                id=log.id or 0,
                type=level,
                message=text,
                timestamp=log.timestamp,
            )
        )
    return items

