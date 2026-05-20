from typing import List
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.interfaces.api.deps import get_current_user, get_tenant_owner_id
from app.domain.models import User
from app.infrastructure.database.session import get_async_session
from app.infrastructure.adapters.rate_limit import limiter
from app.infrastructure.config import settings
from app.application.use_cases.analytics_use_cases import AnalyticsUseCases, MetricItem
from app.infrastructure.repositories.audit import AuditRepository
from app.infrastructure.repositories.product import ProductRepository
from app.infrastructure.repositories.billing import BillingRepository

router = APIRouter()

audit_repo = AuditRepository()
product_repo = ProductRepository()
billing_repo = BillingRepository()
analytics_use_cases = AnalyticsUseCases(audit_repo, product_repo, billing_repo)

@router.get("/metrics/system", response_model=List[MetricItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_system_metrics(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Retorna métricas de salud y rendimiento técnico del sistema"""
    tenant_id = get_tenant_owner_id(current_user)
    return await analytics_use_cases.get_system_metrics(session, tenant_id)


@router.get("/metrics/inventory", response_model=List[MetricItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_inventory_metrics(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Obtiene indicadores clave sobre el estado del inventario y productos"""
    tenant_id = get_tenant_owner_id(current_user)
    return await analytics_use_cases.get_inventory_metrics(session, tenant_id)


@router.get("/metrics/business", response_model=List[MetricItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_business_metrics(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Muestra métricas de negocio, ventas y comportamiento de clientes"""
    tenant_id = get_tenant_owner_id(current_user)
    return await analytics_use_cases.get_business_metrics(session, tenant_id)


@router.get("/audit/stream")
async def get_audit_stream(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Obtiene el flujo de eventos de auditoría para el dashboard en tiempo real"""
    tenant_id = get_tenant_owner_id(current_user)
    return await analytics_use_cases.get_audit_stream(session, tenant_id, limit=limit)
