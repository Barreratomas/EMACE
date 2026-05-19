from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel

# Modelo de Ticket (Soporte)
class Ticket(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    user_id: int = Field(foreign_key="user.id") # Vendedor (Tenant Context)
    subject: str
    description: str
    priority: str # low, medium, high, critical
    status: str # open, in_progress, resolved, closed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# Modelo de Cita/Reunión (Nuevo para Fase de Escalamiento)
class Appointment(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    user_id: int = Field(foreign_key="user.id") # Vendedor
    agent_role: str # sales, tech
    datetime_slot: datetime
    status: str = "scheduled" # scheduled, cancelled, completed
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
