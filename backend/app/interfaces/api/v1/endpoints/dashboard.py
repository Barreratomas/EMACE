from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.interfaces.api.deps import get_current_user, get_tenant_owner_id
from app.domain.models import User
from app.infrastructure.database.session import get_async_session
from app.infrastructure.adapters.rate_limit import limiter
from app.infrastructure.config import settings
from app.application.use_cases.dashboard_use_cases import DashboardUseCases, DashboardOverviewResponse
from app.infrastructure.repositories.audit import AuditRepository
from app.infrastructure.repositories.product import ProductRepository
from app.infrastructure.repositories.billing import BillingRepository

router = APIRouter()

audit_repo = AuditRepository()
product_repo = ProductRepository()
billing_repo = BillingRepository()
dashboard_use_cases = DashboardUseCases(audit_repo, product_repo, billing_repo)

@router.get("/overview", response_model=DashboardOverviewResponse)
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_dashboard_overview(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Obtiene una vista general consolidada para el panel principal del vendor"""
    tenant_id = get_tenant_owner_id(current_user)
    return await dashboard_use_cases.get_overview(session, tenant_id)
