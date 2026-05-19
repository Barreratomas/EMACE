from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel

# Logs de Auditoría (Para QA y Trazabilidad)
class AuditLog(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id") # Vendedor responsable
    agent_name: str
    action: str
    details: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# Historial de Chat (Auditoría y Trazabilidad Legal)
class ChatHistory(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id") # Vendedor
    session_id: str = Field(index=True) # ID de la sesión/hilo de LangGraph
    user_message: str
    agent_message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    metadata_json: Optional[str] = None # JSON stringificado con detalles extra
