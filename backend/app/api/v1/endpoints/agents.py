from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_tenant_owner_id
from app.core.config import settings
from app.core.database.models import AuditLog, User
from app.core.database.session import get_async_session
from app.core.rate_limit import limiter


router = APIRouter()


class AgentCatalogItem(BaseModel):
    id: str
    name: str
    role: str
    domain: str
    status: str
    load: int
    latency: str


class AgentToolItem(BaseModel):
    key: str
    label: str
    agents: List[str]
    icon: str


class AgentEventItem(BaseModel):
    timestamp: datetime
    level: str
    agent_name: str
    action: str
    details: str


AGENT_CATALOG = [
    {
        "id": "general",
        "name": "EMACE_CORE",
        "role": "Orquestador General",
        "status": "online",
        "load": 42,
        "latency": "1.2s",
        "domain": "Core Routing",
    },
    {
        "id": "inventory",
        "name": "AGENTE_INVENTARIO",
        "role": "Stock y Catálogo",
        "status": "online",
        "load": 68,
        "latency": "1.5s",
        "domain": "Inventory",
    },
    {
        "id": "sales",
        "name": "AGENTE_VENTAS",
        "role": "Pedidos y Clientes",
        "status": "busy",
        "load": 83,
        "latency": "2.1s",
        "domain": "Sales",
    },
    {
        "id": "logistics",
        "name": "AGENTE_LOGISTICA",
        "role": "Rutas y Entregas",
        "status": "online",
        "load": 37,
        "latency": "1.0s",
        "domain": "Logistics",
    },
]


AGENT_TOOLS = [
    {
        "key": "inventory",
        "label": "Inventario",
        "agents": ["AGENTE_INVENTARIO"],
        "icon": "Database",
    },
    {
        "key": "sales",
        "label": "Ventas",
        "agents": ["AGENTE_VENTAS"],
        "icon": "Network",
    },
    {
        "key": "logistics",
        "label": "Logística",
        "agents": ["AGENTE_LOGISTICA"],
        "icon": "Cpu",
    },
]


@router.get("/agents", response_model=List[AgentCatalogItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_agents_catalog(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    _ = tenant_id
    return [AgentCatalogItem(**item) for item in AGENT_CATALOG]


@router.get("/agents/tools", response_model=List[AgentToolItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_agents_tools(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    _ = tenant_id
    return [AgentToolItem(**item) for item in AGENT_TOOLS]


@router.get("/agents/events", response_model=List[AgentEventItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_agents_events(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.user_id == tenant_id)
        .order_by(AuditLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    logs = result.scalars().all()
    events: List[AgentEventItem] = []
    for log in logs:
        level = "INFO"
        lower_action = (log.action or "").lower()
        if "error" in lower_action or "fail" in lower_action or "exception" in lower_action:
            level = "ERROR"
        elif "warn" in lower_action or "high_load" in lower_action:
            level = "WARN"
        elif "success" in lower_action or "ok" in lower_action or "complete" in lower_action:
            level = "OK"
        events.append(
            AgentEventItem(
                timestamp=log.timestamp,
                level=level,
                agent_name=log.agent_name,
                action=log.action,
                details=log.details,
            )
        )
    return events

