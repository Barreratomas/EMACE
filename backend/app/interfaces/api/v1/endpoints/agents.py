from typing import List
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.interfaces.api.deps import get_current_user, get_tenant_owner_id
from app.domain.models import User
from app.infrastructure.database.session import get_async_session
from app.infrastructure.adapters.rate_limit import limiter
from app.infrastructure.config import settings
from app.application.use_cases.agent_use_cases import (
    AgentUseCases, AgentCatalogItem, AgentToolItem, AgentEventItem
)
from app.infrastructure.repositories.audit import AuditRepository

router = APIRouter()
audit_repo = AuditRepository()
agent_use_cases = AgentUseCases(audit_repo)

@router.get("/agents", response_model=List[AgentCatalogItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_agents_catalog(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Obtiene el catálogo de agentes disponibles para el vendor"""
    return await agent_use_cases.get_catalog()


@router.get("/agents/tools", response_model=List[AgentToolItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_agents_tools(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Lista las herramientas técnicas que los agentes pueden utilizar"""
    return await agent_use_cases.get_tools()


@router.get("/agents/events", response_model=List[AgentEventItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_agents_events(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Recupera el historial de eventos y acciones realizadas por los agentes"""
    tenant_id = get_tenant_owner_id(current_user)
    return await agent_use_cases.get_events(session, tenant_id, limit, offset)
