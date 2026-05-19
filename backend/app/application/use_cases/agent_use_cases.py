from typing import List, Any
from app.domain.ports.repositories import IAuditRepository
from app.domain.models import AuditLog
from pydantic import BaseModel
from datetime import datetime

class AgentCatalogItem(BaseModel):
    id: str
    name: str
    description: str
    capabilities: List[str]
    status: str
    icon: str

class AgentToolItem(BaseModel):
    id: str
    name: str
    description: str
    category: str

class AgentEventItem(BaseModel):
    timestamp: datetime
    level: str
    agent_name: str
    action: str
    details: str

AGENT_CATALOG = [
    {
        "id": "sales-bot",
        "name": "Agente de Ventas",
        "description": "Especializado en persuasión, cierre de ventas y manejo de objeciones.",
        "capabilities": ["Ventas", "Negociación", "Catálogo"],
        "status": "active",
        "icon": "ShoppingBag",
    },
    {
        "id": "support-bot",
        "name": "Agente de Soporte",
        "description": "Resolución de dudas técnicas, estado de pedidos y post-venta.",
        "capabilities": ["Soporte", "FAQs", "Pedidos"],
        "status": "active",
        "icon": "LifeBuoy",
    },
    {
        "id": "analyst-bot",
        "name": "Agente Analista",
        "description": "Análisis de datos de ventas, comportamiento de clientes y tendencias.",
        "capabilities": ["Analytics", "Reporting", "Insights"],
        "status": "active",
        "icon": "BarChart2",
    },
    {
        "id": "ops-bot",
        "name": "Agente de Operaciones",
        "description": "Gestión de inventario, logística y automatización de tareas.",
        "capabilities": ["Inventario", "Logística", "Automatización"],
        "status": "active",
        "icon": "Cpu",
    },
]

AGENT_TOOLS = [
    {"id": "t1", "name": "Búsqueda en RAG", "description": "Acceso a base de conocimiento", "category": "Conocimiento"},
    {"id": "t2", "name": "Gestor de Inventario", "description": "Consulta y reserva de stock", "category": "E-commerce"},
    {"id": "t3", "name": "Calculadora de Precios", "description": "Cálculo de impuestos y descuentos", "category": "Finanzas"},
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
