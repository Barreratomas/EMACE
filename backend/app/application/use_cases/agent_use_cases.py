from typing import List, Any
from app.domain.ports.repositories import IAuditRepository
from app.domain.models import AuditLog
from pydantic import BaseModel
from datetime import datetime

class AgentCatalogItem(BaseModel):
    id: str
    name: str
    role: str
    status: str
    load: int
    latency: str
    domain: str

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
        "id": "supervisor-bot",
        "name": "Supervisor Central",
        "role": "Orquestador de Misiones",
        "status": "online",
        "load": 12,
        "latency": "45ms",
        "domain": "GLOBAL"
    },
    {
        "id": "tech-bot",
        "name": "Agente Técnico",
        "role": "Soporte y Diagnóstico",
        "status": "online",
        "load": 45,
        "latency": "120ms",
        "domain": "SOPORTE"
    },
    {
        "id": "sales-bot",
        "name": "Agente Comercial",
        "role": "Ventas y Negociación",
        "status": "busy",
        "load": 88,
        "latency": "250ms",
        "domain": "VENTAS"
    },
    {
        "id": "billing-bot",
        "name": "Agente de Facturación",
        "role": "Gestión de Pagos",
        "status": "offline",
        "load": 0,
        "latency": "0ms",
        "domain": "FINANZAS"
    }
]

AGENT_TOOLS = [
    {
        "key": "rag-search",
        "label": "Búsqueda Semántica",
        "agents": ["tech-bot", "sales-bot"],
        "icon": "database"
    },
    {
        "key": "stock-manager",
        "label": "Control de Inventario",
        "agents": ["sales-bot"],
        "icon": "network"
    },
    {
        "key": "billing-api",
        "label": "Pasarela de Pagos",
        "agents": ["billing-bot"],
        "icon": "cpu"
    }
]

class AgentUseCases:
    def __init__(self, audit_repo: IAuditRepository):
        self.audit_repo = audit_repo

    async def get_catalog(self) -> List[AgentCatalogItem]:
        return [AgentCatalogItem(**item) for item in AGENT_CATALOG]

    async def get_tools(self) -> List[AgentToolItem]:
        return [AgentToolItem(**item) for item in AGENT_TOOLS]

    async def get_events(self, session: Any, user_id: int, limit: int = 50, offset: int = 0) -> List[AgentEventItem]:
        logs = await self.audit_repo.get_logs_by_user(session, user_id, limit, offset)
        events: List[AgentEventItem] = []
        for log in logs:
            level = "INFO"
            lower_action = (log.action or "").lower()
            if any(word in lower_action for word in ["error", "fail", "exception"]):
                level = "ERROR"
            elif any(word in lower_action for word in ["warn", "high_load"]):
                level = "WARN"
            elif any(word in lower_action for word in ["success", "ok", "complete"]):
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
